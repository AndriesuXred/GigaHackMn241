import requests

def Cost():
    API_URL = "http://127.0.0.1:5000/daily_cost"

    # Payload with meter_id
    payload = {"meter_id": 13836498}

    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()  # raise exception if request failed

        # Print the JSON response
        print("Daily cost data:")
        for entry in response.json():
            print(f"Date: {entry['date']}, Cost: {entry['cost_lei']} lei")

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

##GRAPH REQUEST
def Graph():
    url = "http://127.0.0.1:5000/meter_hourly_data"
    payload = {"meter_id": 13836498, "date": "2025-06-01"}
    response = requests.post(url, json=payload)

    if response.status_code == 200:
       data = response.json()
       for entry in data:
            print(entry)



    else:
       print("Error:", response.status_code, response.text)

#LOGIN REQUEST
def Register():
    url = "http://127.0.0.1:5000/register"
    payload = {"username": "Slime", "password": "1234", "meter": 14101611}
    response = requests.post(url, json=payload)
    print(response.json())

#PEAK REQUEST
def PEAK():
# URL of your running Flask server
    url = "http://127.0.0.1:5000/avg_hourly_energy"

    try:
        # Send GET request
        response = requests.get(url)

        # Check if request was successful
        if response.status_code == 200:
            data = response.json()  # parse JSON response
            print("Average Hourly Energy:")
            for entry in data:
                print(entry)
        else:
            print(f"Request failed with status code {response.status_code}")
            print(response.text)

    except Exception as e:
        print("Error:", e)


def Point():
    #Point Calculator
    url = "http://127.0.0.1:5000/calculate_points"
    payload = {"date": "2025-06-01"}
    response = requests.post(url, json=payload)  # `json=` sets Content-Type automatically
    print(response.json())

def Import():
    url = "http://127.0.0.1:5000/import_csv"
    payload = {"folder_path": r"A:\PythonShitHackaton\GigaHackMn241\EnergyTech"}  # optional, uses default if missing
    response = requests.post(url, json=payload)

    print(response.json())

    import requests

def login_test(username, password):
    url = "http://127.0.0.1:5000/login"
    payload = {
        "username": username,
        "password": password
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # will raise an error if status code >= 400

        data = response.json()
        if response.status_code == 200:
            print("Login successful!")
            print(data)
        else:
            print("Login failed.")
            print(data)

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

def PredictEnergy():
    meter_id = 13836498
    url = "http://127.0.0.1:5000/predict_next_6_hours"
    payload = {"meter_id": meter_id}

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raises error for bad status codes

        data = response.json()
        print(f"Predicted energy for meter {meter_id}:")
        for entry in data:
            print(f"Time: {entry['label']}, Import: {entry['Import']} kWh, id: {entry['id']}")

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

PredictEnergy()



