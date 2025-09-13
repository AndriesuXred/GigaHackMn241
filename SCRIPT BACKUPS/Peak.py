import mariadb
import pandas as pd
import json

# -----------------------------
# Connect to MariaDB
# -----------------------------
conn = mariadb.connect(
    user="root",
    password="1234",
    host="localhost",
    port=3306,
    database="mydatabase"
)
cursor = conn.cursor()
print("Connected to MariaDB successfully!")

# -----------------------------
# Get all data
# -----------------------------
query = """
SELECT Meter, Clock, Active_Energy_Import, Active_Energy_Export
FROM energy_data
ORDER BY Meter, Clock
"""
cursor.execute(query)
rows = cursor.fetchall()
conn.close()

# -----------------------------
# Load into DataFrame
# -----------------------------
df = pd.DataFrame(rows, columns=['Meter', 'Clock', 'Import', 'Export'])
df['Clock'] = pd.to_datetime(df['Clock'])
df = df.sort_values(['Meter', 'Clock'])

# Add date column
df['Date'] = df['Clock'].dt.date

# Calculate per-interval usage (per meter + per day to avoid midnight spikes)
df['Import_Interval_kWh'] = df.groupby(['Meter', 'Date'])['Import'].diff()
df['Export_Interval_kWh'] = df.groupby(['Meter', 'Date'])['Export'].diff()

# Clean invalid values
df = df.dropna()
df = df[(df['Import_Interval_kWh'] >= 0) & (df['Export_Interval_kWh'] >= 0)]

# Extract HOUR of the day
df['Hour'] = df['Clock'].dt.hour

# -----------------------------
# Calculate average consumption per hour
# -----------------------------
threshold = df['Import_Interval_kWh'].quantile(0.98)  # remove top 2%
df_clean = df[df['Import_Interval_kWh'] <= threshold]

hourly_mean = df_clean.groupby('Hour')['Import_Interval_kWh'].mean()

# -----------------------------
# Prepare JSON output
# -----------------------------
json_list = []
for hour, value in hourly_mean.items():
    json_list.append({
        "label": f"{hour:02d}:00",
        "value": round(value, 2)
    })

# Save JSON file
output_file = r"A:\PythonShitHackaton\GigaHackMn241\JSONPeak\avg_hourly_energy.json"
with open(output_file, "w") as f:
    json.dump(json_list, f, indent=2)

print(f"JSON saved to {output_file}")
