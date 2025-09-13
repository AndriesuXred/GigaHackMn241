from flask import Flask, jsonify
import mariadb
import pandas as pd

app = Flask(__name__)

# -----------------------------
# Database connection helper
# -----------------------------
def get_connection():
    return mariadb.connect(
        user="root",
        password="1234",
        host="localhost",
        port=3306,
        database="mydatabase"
    )

# -----------------------------
# Function to calculate avg hourly energy
# -----------------------------
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

    # Load into DataFrame
    df = pd.DataFrame(rows, columns=['Meter', 'Clock', 'Import', 'Export'])
    df['Clock'] = pd.to_datetime(df['Clock'])
    df = df.sort_values(['Meter', 'Clock'])
    df['Date'] = df['Clock'].dt.date

    # Calculate per-interval usage
    df['Import_Interval_kWh'] = df.groupby(['Meter', 'Date'])['Import'].diff()
    df['Export_Interval_kWh'] = df.groupby(['Meter', 'Date'])['Export'].diff()

    df = df.dropna()
    df = df[(df['Import_Interval_kWh'] >= 0) & (df['Export_Interval_kWh'] >= 0)]
    df['Hour'] = df['Clock'].dt.hour

    # Remove top 2% of values
    threshold = df['Import_Interval_kWh'].quantile(0.98)
    df_clean = df[df['Import_Interval_kWh'] <= threshold]

    # Average hourly import
    hourly_mean = df_clean.groupby('Hour')['Import_Interval_kWh'].mean()

    # Prepare JSON output
    json_list = [{"label": f"{hour:02d}:00", "value": round(value, 2)} for hour, value in hourly_mean.items()]
    return json_list

# -----------------------------
# Flask endpoint
# -----------------------------
@app.route("/avg_hourly_energy", methods=["GET"])
def avg_hourly_energy_endpoint():
    data = get_avg_hourly_energy()
    return jsonify(data)

# -----------------------------
# Run server
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
