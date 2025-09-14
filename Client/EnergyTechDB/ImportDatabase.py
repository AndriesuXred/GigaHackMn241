from flask import Flask, request, jsonify
import pandas as pd
import mariadb
import os

app = Flask(__name__)

# -----------------------------
# Database connection helper
# -----------------------------
def get_connection():
    try:
        return mariadb.connect(
            user="root",
            password="1234",
            host="localhost",
            port=3306,
            database="mydatabase"
        )
    except mariadb.ProgrammingError:
        # Database doesn't exist, create it
        conn = mariadb.connect(
            user="root",
            password="1234",
            host="localhost",
            port=3306
        )
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS mydatabase")
        conn.commit()
        conn.close()
        # Retry connection
        return mariadb.connect(
            user="root",
            password="1234",
            host="localhost",
            port=3306,
            database="mydatabase"
        )

# -----------------------------
# Endpoint: Import CSVs
# -----------------------------
@app.route("/import_csv", methods=["POST"])
def import_csv_endpoint():
    try:
        data = request.get_json()
        folder_path = data.get("folder_path", r"A:\\EnergyTech")

        if not os.path.exists(folder_path):
            return jsonify({"error": f"Folder not found: {folder_path}"}), 400

        conn = get_connection()
        cursor = conn.cursor()

        # Create table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS energy_data (
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

# -----------------------------
# Run server
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
