from flask import Flask, jsonify, request
import requests

app = Flask(__name__)
API_URL = "https://3bd0cb850907.ngrok-free.app/predict_next_6_hours"

@app.route("/data", methods=["GET", "POST"])
def get_data():
    payload = {"meter_id": 15005950, "date": "2025-06-06"}
    print("Sending payload to external API:", payload)
    
    try:
        response = requests.post(API_URL, json=payload)
        print("Status code:", response.status_code)
        raw_data = response.json()
        print("Raw data received:", raw_data[:5], "...")  # show first 5 entries
        
        if not raw_data:
            print("No data returned from API.")
            return jsonify({"message": "No data available for this meter/date"}), 200
        
        # Use the data as-is since keys are already 'label' and 'value'
        data = []
        for entry in raw_data:
            label = entry.get("label")
            value = entry.get("Import")
            id = entry.get("id")
            if label is not None and value is not None:
                data.append({"label": label, "value": float(value), "id":int(id)})
        
        print("Final data to return:", data[:5], "...")  # show first 5 entries
        return jsonify(data)
    
    except Exception as e:
        print("Error occurred:", e)
        return jsonify({"error": str(e)}), 500
        

        

import csv


CSV_FILE = "login_data.csv"

# Get all users
def get_users():
    users = []
    with open(CSV_FILE, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            users.append({
                "login": row["login"],
                "username": row["username"],
                "password": row["password"],
                "address": row["address"],
                "contor_id": int(row["contor_id"]),
                "bonus_points": int(row["bonus_points"])
            })
    return users

# Login route
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    
    users = get_users()
    for user in users:
        if user["username"] == username and user["password"] == password:
            return jsonify({"success": True, "user": user})
    
    return jsonify({"success": False, "message": "Invalid username or password"})

# Register route
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    login_name = data.get("login")
    username = data.get("username")
    password = data.get("password")
    address = data.get("address")
    contor_id = int(data.get("contor_id"))
    bonus_points = int(data.get("bonus_points", 0))
    
    # Check if username already exists
    users = get_users()
    for user in users:
        if user["username"] == username:
            return jsonify({"success": False, "message": "Username already exists"})
    
    # Append to CSV
    with open(CSV_FILE, "a", newline='') as f:
        writer = csv.writer(f)
        writer.writerow([login_name, username, password, address, contor_id, bonus_points])
    
    return jsonify({"success": True, "message": "User registered successfully"})

if __name__ == "__main__":
    print("Starting Flask app...")
    app.run(debug=True)
