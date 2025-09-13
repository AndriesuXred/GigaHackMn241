from flask import Flask, request, jsonify
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
# Function to generate hourly JSON
# -----------------------------
def make_graph_json(meter_id, date_str):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT Clock, Active_Energy_Import
    FROM energy_data
    WHERE Meter = ?
      AND DATE(Clock) = ?
    ORDER BY Clock ASC
    """
    cursor.execute(query, (meter_id, date_str))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return []

    df = pd.DataFrame(rows, columns=['Clock', 'Import'])
    df['Clock'] = pd.to_datetime(df['Clock'])
    df = df.set_index('Clock')
    df['Import_Interval_kWh'] = df['Import'].diff()
    df = df.dropna()
    hourly_df = df.resample('h').sum()

    json_list = [
        {"label": idx.strftime("%Y-%m-%d %H:%M"), "Import": round(row['Import_Interval_kWh'], 2)}
        for idx, row in hourly_df.iterrows()
    ]
    return json_list

# -----------------------------
# Flask endpoint
# -----------------------------
@app.route("/meter_hourly_data", methods=["POST"])
def meter_hourly_data_endpoint():
    data = request.get_json()
    meter_id = data.get("meter_id")
    date_str = data.get("date")

    if not meter_id or not date_str:
        return jsonify({"error": "Missing meter_id or date"}), 400

    result = make_graph_json(meter_id, date_str)
    if not result:
        return jsonify({"message": f"No data found for meter {meter_id} on {date_str}"}), 404

    return jsonify(result)

# -----------------------------
# Run server
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
