import matplotlib.pyplot as plt
import mariadb
import pandas as pd

# Connect to MariaDB
conn = mariadb.connect(
    user="root",
    password="1234",
    host="localhost",
    port=3306,
    database="mydatabase"
)
cursor = conn.cursor()
print("Connected to MariaDB successfully!")

# Get all data
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

# Calculate average consumption per hour across all days & all meters
# Remove top 1% of values
threshold = df['Import_Interval_kWh'].quantile(0.99)
df_clean = df[df['Import_Interval_kWh'] <= threshold]

hourly_mean = df_clean.groupby('Hour')['Import_Interval_kWh'].mean()


# -----------------------------
# Plot average load curve
# -----------------------------
plt.figure(figsize=(10,5))
plt.plot(hourly_mean.index, hourly_mean.values, marker='o', color='blue', label='Avg Import (kWh)')
plt.xlabel('Hour of Day')
plt.ylabel('Average Consumption (kWh)')
plt.title('Average Hourly Energy Consumption (All Meters)')
plt.xticks(range(0,24))  # show all 24 hours
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
