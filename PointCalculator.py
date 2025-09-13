from flask import Flask, request, jsonify
import mariadb
import pandas as pd

app = Flask(__name__)

# -----------------------------
# Database connection
# -----------------------------
def get_connection():
    return mariadb.connect(
        user="root",
        password="1234",
        host="localhost",
        port=3306,
        database="mydatabase"
    )


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


# -----------------------------
# Flask routes
# -----------------------------
@app.route("/calculate_points", methods=["POST"])
def calculate_points_endpoint():
    data = request.get_json()
    date_str = data.get("date")

    if not date_str:
        return jsonify({"error": "Missing date parameter"}), 400

    results = calculate_points_for_all(date_str)
    return jsonify(results)


# -----------------------------
# Run server
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
