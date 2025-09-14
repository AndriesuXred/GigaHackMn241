from flask import Flask, jsonify
import requests

app = Flask(__name__)

API_URL = "https://a429bbebcbd7.ngrok-free.app/meter_hourly_data"

@app.route("/data")
def get_data():
    payload = {"meter_id": 15005950, "date": "2025-06-06"}
    
    print("=== Flask /data route called ===")
    print("Payload we will send to external API:", payload)
    
    try:
        response = requests.post(API_URL, json=payload)
        print("Request sent to external API.")
        print("HTTP status code received:", response.status_code)
        
        response.raise_for_status()
        raw_data = response.json()
        print("Raw data received from external API:", raw_data)
        
        data = [{"label": entry["datetime"], "value": float(entry["kW"])} for entry in raw_data]
        print("Transformed data to label/value format:", data)
        
        return jsonify(data)
    
    except requests.exceptions.RequestException as e:
        print("Error occurred while fetching data:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("Starting Flask app...")
    app.run(debug=True)
