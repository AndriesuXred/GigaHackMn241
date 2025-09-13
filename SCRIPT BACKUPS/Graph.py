import mariadb
import pandas as pd
import json

def MakeGraphJSON(meterId, date_str, output_file):
    """
    meterId: int, the ID of the meter
    date_str: str, date in format 'YYYY-MM-DD'
    output_file: str, path to save JSON file
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

    # Query data
    query = """
    SELECT Clock, Active_Energy_Import
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
    df = pd.DataFrame(rows, columns=['Clock', 'Import'])
    df['Clock'] = pd.to_datetime(df['Clock'])
    df = df.set_index('Clock')

    # Calculate energy per interval
    df['Import_Interval_kWh'] = df['Import'].diff()
    df = df.dropna()

    # Resample to hourly intervals
    hourly_df = df.resample('h').sum()

    # Prepare JSON structure
    json_list = []
    for idx, row in hourly_df.iterrows():
        json_list.append({
            "label": idx.strftime("%Y-%m-%d %H:%M"),
            "Import": round(row['Import_Interval_kWh'], 2)
        })

    # Save to JSON file
    with open(output_file, "w") as f:
        json.dump(json_list, f, indent=2)

    print(f"JSON saved to {output_file}")
    conn.close()


# Example usage
meterId = 15005950
date_str = "2025-06-06"
output_file = "A:\PythonShitHackaton\GigaHackMn241\JSONDay\energy_data.json"
MakeGraphJSON(meterId, date_str, output_file)
