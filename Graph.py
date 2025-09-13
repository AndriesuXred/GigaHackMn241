import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mariadb
import pandas as pd

def MakeGraph(meterId, date_str):
    """
    meterId: int, the ID of the meter
    date_str: str, date in format 'YYYY-MM-DD'
    """

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

    # Query data for that meter and selected date
    query = """
    SELECT Clock, Active_Energy_Import, Active_Energy_Export
    FROM energy_data
    WHERE Meter = ?
      AND DATE(Clock) = ?
    ORDER BY Clock ASC
    """
    cursor.execute(query, (meterId, date_str))
    rows = cursor.fetchall()


    if not rows:
        print(f"No data found for Meter {meterId} on {date_str}")
        conn.close()
        return

    # Load into DataFrame
    df = pd.DataFrame(rows, columns=['Clock', 'Import', 'Export'])
    df['Clock'] = pd.to_datetime(df['Clock'])
    df = df.set_index('Clock')

    # Calculate energy per 15-min interval
    df['Import_Interval_kWh'] = df['Import'].diff()
    df['Export_Interval_kWh'] = df['Export'].diff()
    df = df.dropna()

    # Resample to hourly intervals
    hourly_df = df.resample('h').sum()

    # Plot hourly energy
    plt.figure(figsize=(12,6))
    plt.bar(hourly_df.index, hourly_df['Import_Interval_kWh'], width=0.03, label='Import Energy (kWh)', color='blue', alpha=0.7)
    plt.bar(hourly_df.index, hourly_df['Export_Interval_kWh'], width=0.03, label='Export Energy (kWh)', color='orange', alpha=0.7)
    plt.xlabel('Time')
    plt.ylabel('Energy per Hour (kWh)')
    plt.title(f'Hourly Energy Usage for Meter {meterId} on {date_str}')

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.xticks(rotation=45)

    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    

    conn.close()

# -----------------------------
# Example usage
# -----------------------------
meterId = 15005950
date_str = "2025-06-06"
MakeGraph(meterId, date_str)
