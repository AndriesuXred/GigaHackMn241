import requests


url = "http://127.0.0.1:5000/import_csv"
payload = {"folder_path": r"A:\PythonShitHackaton\GigaHackMn241\EnergyTech"}  # optional, uses default if missing
response = requests.post(url, json=payload)

print(response.json())



##GRAPH REQUEST
#url = "http://127.0.0.1:5000/meter_hourly_data"
#payload = {"meter_id": 15005950, "date": "2025-06-06"}
#response = requests.post(url, json=payload)
#
#if response.status_code == 200:
#    data = response.json()
#    for entry in data:
#        print(entry)
#else:
#    print("Error:", response.status_code, response.text)








#LOGIN REQUEST
# url = "http://127.0.0.1:5000/register"
# payload = {"username": "alice", "password": "1234", "meter": 13836498}
# response = requests.post(url, json=payload)
# print(response.json())





#PEAK REQUEST

# # URL of your running Flask server
# url = "http://127.0.0.1:5000/avg_hourly_energy"

# try:
#     # Send GET request
#     response = requests.get(url)

#     # Check if request was successful
#     if response.status_code == 200:
#         data = response.json()  # parse JSON response
#         print("Average Hourly Energy:")
#         for entry in data:
#             print(entry)
#     else:
#         print(f"Request failed with status code {response.status_code}")
#         print(response.text)

# except Exception as e:
#     print("Error:", e)







##Point Calculator
# url = "http://127.0.0.1:5000/calculate_points"
# payload = {"date": "2025-06-06"}
# response = requests.post(url, json=payload)  # `json=` sets Content-Type automatically
# print(response.json())
