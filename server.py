from flask import Flask, request, jsonify
import mariadb
import pandas as pd
import os
from statsmodels.tsa.arima.model import ARIMA
import numpy as np


app = Flask(__name__)

#GRAPH APP
@app.route("/meter_hourly_data", methods=["POST"])
def meter_hourly_data_endpoint():
    data = request.get_json()
    meter_id = data.get("meter_id")

    if not meter_id:
        return jsonify({"error": "Missing meter_id"}), 400

    result = make_graph_json_all_time(meter_id)
    if not result:
        return jsonify({"message": f"No data found for meter {meter_id}"}), 404

    return jsonify(result)

def get_connection():
    return mariadb.connect(
        user="root",
        password="1234",
        host="localhost",
        port=3306,
        database="mydatabase"
    )

def make_graph_json_all_time(meter_id):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT Clock, Active_Energy_Import
    FROM energy_data
    WHERE Meter = ?
    ORDER BY Clock ASC
    """
    cursor.execute(query, (meter_id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return []

    df = pd.DataFrame(rows, columns=['Clock', 'Import'])
    df['Clock'] = pd.to_datetime(df['Clock'])
    df = df.set_index('Clock')

    # Calculate energy per interval
    df['Import_Interval_kWh'] = df['Import'].diff() / 1000.0
    df = df.dropna()

    # Resample to hourly intervals
    hourly_df = df.resample('h').sum()

    # Prepare JSON for historical data with id=1
    result = [
        {"label": idx.strftime("%Y-%m-%d %H:%M"), "Import": round(row['Import_Interval_kWh'], 2), "id": 1}
        for idx, row in hourly_df.iterrows()
    ]

    # --- ARIMA prediction for next 6 hours ---
    if len(hourly_df) >= 10:  # need enough points for ARIMA
        model = ARIMA(hourly_df['Import_Interval_kWh'], order=(1,1,1))
        model_fit = model.fit()
        forecast = model_fit.forecast(steps=6)
        last_time = hourly_df.index[-1]

        for i, value in enumerate(forecast):
            result.append({
                "label": (last_time + pd.Timedelta(hours=i+1)).strftime("%Y-%m-%d %H:%M"),
                "Import": round(max(value, 0), 2),  # avoid negative forecasts
                "id": 2
            })

    return result

#PEAK APP
@app.route("/avg_hourly_energy", methods=["GET"])
def avg_hourly_energy_endpoint():
    data = get_avg_hourly_energy()
    if not data:
        return jsonify({"message": "No data found"}), 404
    return jsonify(data)

def get_avg_hourly_energy():
    conn = get_connection()
    cursor = conn.cursor()

    # Fetch all data
    query = """
    SELECT Meter, Clock, Active_Energy_Import, Active_Energy_Export
    FROM energy_data
    ORDER BY Meter, Clock
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return []

    # Load into DataFrame
    df = pd.DataFrame(rows, columns=['Meter', 'Clock', 'Import', 'Export'])
    df['Clock'] = pd.to_datetime(df['Clock'])
    df = df.sort_values(['Meter', 'Clock'])

    # Calculate per-interval usage (across full history, not daily reset)
    df['Import_Interval_kWh'] = df.groupby('Meter')['Import'].diff() / 1000.0
    df['Export_Interval_kWh'] = df.groupby('Meter')['Export'].diff()

    # Drop invalid rows
    df = df.dropna()
    df = df[(df['Import_Interval_kWh'] >= 0) & (df['Export_Interval_kWh'] >= 0)]

    # Extract hour of day
    df['Hour'] = df['Clock'].dt.hour

    # Remove top 2% of outliers
    threshold = df['Import_Interval_kWh'].quantile(0.98)
    df_clean = df[df['Import_Interval_kWh'] <= threshold]

    # Average hourly import across all history
    hourly_mean = df_clean.groupby('Hour')['Import_Interval_kWh'].mean()

    # Prepare JSON output
    json_list = [{"label": f"{hour:02d}:00", "value": round(value, 2)} for hour, value in hourly_mean.items()]
    return json_list

#CalculateDay APP
@app.route("/daily_cost", methods=["POST"])
def daily_cost_endpoint():
    data = request.get_json()
    meter_id = data.get("meter_id")

    if not meter_id:
        return jsonify({"error": "Missing meter_id"}), 400

    result = calculate_daily_cost(meter_id)
    if not result:
        return jsonify({"message": f"No data found for meter {meter_id}"}), 404

    return jsonify(result)
def calculate_daily_cost(meter_id):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT Clock, Active_Energy_Import
    FROM energy_data
    WHERE Meter = ?
    ORDER BY Clock ASC
    """
    cursor.execute(query, (meter_id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return []

    # Load into DataFrame
    df = pd.DataFrame(rows, columns=["Clock", "Import_Wh"])
    df["Clock"] = pd.to_datetime(df["Clock"])
    df = df.set_index("Clock")

    # Convert Wh → kWh
    df["Import_kWh"] = df["Import_Wh"] / 1000.0

    # Calculate interval consumption
    df["Interval_kWh"] = df["Import_kWh"].diff()
    df = df.dropna()
    df = df[df["Interval_kWh"] >= 0]  # remove resets or bad data

    # Determine tariff per row
    df["Hour"] = df.index.hour
    df["Tariff"] = df["Hour"].apply(
        lambda h: 3.31 if (h >= 23 or h < 7) else 3.59
    )

    # Calculate cost for each interval
    df["Cost"] = df["Interval_kWh"] * df["Tariff"]

    # Group by date and sum
    daily_cost = df.groupby(df.index.date)["Cost"].sum()

    # Convert to JSON-friendly format
    result = [
        {"date": str(date), "cost_lei": round(cost, 2)}
        for date, cost in daily_cost.items()
    ]
    return result

#LOGIN+REGISTER APP
@app.route("/login", methods=["POST"])
def login_endpoint():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    # Too many attempts
    if login_attempts.get(username, 0) >= 3:
        return jsonify({"error": "Too many failed attempts. Access blocked!"}), 403

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM accounts WHERE username = ?", (username,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row and row[0] == password:
        login_attempts[username] = 0  # reset attempts
        return jsonify({"message": "Login successful!"}), 200
    else:
        login_attempts[username] = login_attempts.get(username, 0) + 1
        return jsonify({"error": "Wrong username or password"}), 401
    
conn = get_connection()
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    point BIGINT DEFAULT 0,
    meter BIGINT
)
""")
conn.commit()
cursor.close()
conn.close()

# -----------------------------
# Login attempts tracking
# -----------------------------
login_attempts = {}

# -----------------------------
# Register endpoint
# -----------------------------

@app.route("/register", methods=["POST"])
def register_endpoint():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    meter = data.get("meter")

    if not username or not password or not meter:
        return jsonify({"error": "Missing fields"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO accounts (username, password, meter) VALUES (?, ?, ?)",
            (username, password, meter)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Account created!"}), 201
    except mariadb.IntegrityError:
        return jsonify({"error": "Username already exists!"}), 400

#ImportDatabase APP
@app.route("/import_csv", methods=["POST"])
def import_csv_endpoint():
    try:
        data = request.get_json()
        folder_path = data.get("folder_path", r"A:\PythonShitHackaton\EnergyTech")

        if not os.path.exists(folder_path):
            return jsonify({"error": f"Folder not found: {folder_path}"}), 400

        conn = get_connection()
        cursor = conn.cursor()

        # Delete the old table if exists
        cursor.execute("DROP TABLE IF EXISTS energy_data")

        # Recreate table
        cursor.execute("""
        CREATE TABLE energy_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            Meter BIGINT,
            Clock DATETIME,
            Active_Energy_Import FLOAT,
            Active_Energy_Export FLOAT,
            TransFullCoef FLOAT
        )
        """)
        conn.commit()

        csv_files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]
        summary = []

        for file_name in csv_files:
            file_path = os.path.join(folder_path, file_name)
            if os.stat(file_path).st_size == 0:
                summary.append({"file": file_name, "inserted_rows": 0, "status": "empty file"})
                continue

            df = pd.read_csv(file_path, sep=";")

            # Drop extra empty column if exists
            if "Unnamed: 5" in df.columns:
                df = df.drop(columns=["Unnamed: 5"])

            # Rename columns
            df.columns = ["Meter", "Clock", "Active_Energy_Import", "Active_Energy_Export", "TransFullCoef"]

            # Convert Clock to datetime
            df['Clock'] = pd.to_datetime(df['Clock'], format="%d.%m.%Y %H:%M:%S")

            # Force numeric columns and handle empty values
            for col in ["Active_Energy_Import", "Active_Energy_Export", "TransFullCoef"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            # Drop rows with missing critical values
            df = df.dropna(subset=["Active_Energy_Import", "Active_Energy_Export"])
            data_to_insert = df.values.tolist()

            if data_to_insert:
                cursor.executemany("""
                    INSERT INTO energy_data (Meter, Clock, Active_Energy_Import, Active_Energy_Export, TransFullCoef)
                    VALUES (?, ?, ?, ?, ?)
                """, data_to_insert)
                conn.commit()

            summary.append({"file": file_name, "inserted_rows": len(df), "status": "success"})

        # Total rows in table
        cursor.execute("SELECT COUNT(*) FROM energy_data;")
        total_rows = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return jsonify({"summary": summary, "total_rows": total_rows})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
#CalculatePoints App
@app.route("/calculate_points", methods=["POST"])
def calculate_points_endpoint():
    data = request.get_json()
    date_str = data.get("date")

    if not date_str:
        return jsonify({"error": "Missing date parameter"}), 400

    results = calculate_points_for_all(date_str)
    return jsonify(results)
def calculate_points_for_all(date_str):
    results = []
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, meter, COALESCE(point, 0) FROM accounts")
    accounts = cursor.fetchall()

    for acc_id, meter, current_points in accounts:
        query = """
        SELECT Clock, Active_Energy_Import
        FROM energy_data
        WHERE Meter = ? AND DATE(Clock) = ?
        ORDER BY Clock
        """
        cursor.execute(query, (meter, date_str))
        rows = cursor.fetchall()

        if not rows:
            results.append({
                "meter": meter,
                "message": f"No energy data for {date_str}"
            })
            continue

        df = pd.DataFrame(rows, columns=['Clock', 'Import'])
        df['Clock'] = pd.to_datetime(df['Clock'])
        df = df.sort_values('Clock')
        df['kWh'] = df['Import'].diff()
        df = df.dropna()
        df = df[df['kWh'] >= 0]
        df['Hour'] = df['Clock'].dt.hour

        peak = df[(df['Hour'] >= 17) & (df['Hour'] < 23)]['kWh'].sum()
        offpeak = df['kWh'].sum() - peak
        total = peak + offpeak
        ratio = (offpeak / total) if total > 0 else 0

        new_points = int(round(ratio * 100))
        updated_points = current_points + new_points

        cursor.execute("UPDATE accounts SET point = ? WHERE id = ?", (updated_points, acc_id))
        conn.commit()

        results.append({
            "meter": meter,
            "peak_kWh": round(peak, 2),
            "offpeak_kWh": round(offpeak, 2),
            "offpeak_ratio": round(ratio, 2),
            "awarded_points": new_points,
            "total_points": updated_points
        })

    cursor.close()
    conn.close()
    return results

#ARIMA APP
@app.route("/predict_next_6_hours", methods=["POST"])
def predict_next_6_hours():
    data = request.get_json()
    meter_id = data.get("meter_id")
    if not meter_id:
        return jsonify({"error": "Missing meter_id"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Clock, Active_Energy_Import
        FROM energy_data
        WHERE Meter = ?
        ORDER BY Clock ASC
    """, (meter_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        return jsonify({"message": f"No data found for meter {meter_id}"}), 404

    df = pd.DataFrame(rows, columns=["Clock", "Import_Wh"])
    df["Clock"] = pd.to_datetime(df["Clock"])
    df = df.sort_values("Clock")
    df = df.set_index("Clock")

    # Compute interval consumption in kWh
    df["Interval_kWh"] = df["Import_Wh"].diff() / 1000.0
    df = df[df["Interval_kWh"] >= 0]  # remove resets
    df = df.dropna()

    if df.empty:
        return jsonify({"message": "No valid intervals to forecast"}), 404

    # Scale data for ARIMA
    scale_factor = 10000
    training_series = df["Interval_kWh"] * scale_factor

    # Fit ARIMA
    model = ARIMA(training_series, order=(1,1,1))
    model_fit = model.fit()

    # Forecast next 6 hours and scale back
    forecast = model_fit.forecast(steps=6) / scale_factor

    result = []

    # Historical data
    for timestamp, value in df["Interval_kWh"].items():
        result.append({
            "label": timestamp.strftime("%Y-%m-%d %H:%M"),
            "Import": round(value, 4),
            "id": 1
        })

    # Predicted data
    last_time = df.index[-1]
    for i, value in enumerate(forecast):
        result.append({
            "label": (last_time + pd.Timedelta(hours=i+1)).strftime("%Y-%m-%d %H:%M"),
            "Import": round(max(value, 0), 4),
            "id": 2
        })

    return jsonify(result)


# -----------------------------
# Run server
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)