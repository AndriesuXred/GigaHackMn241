import mariadb
import pandas as pd

# -----------------------------
# Database connection
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


def calculate_points_for_all(date_str):
    """
    For each meter in accounts:
    - Calculate ratio of off-peak vs peak kWh
    - Convert to points
    - Add to user's total points
    """

    # Get all meters from accounts
    cursor.execute("SELECT id, meter, COALESCE(point, 0) FROM accounts")
    accounts = cursor.fetchall()

    for acc_id, meter, current_points in accounts:
        # Get meter data for given date
        query = """
        SELECT Clock, Active_Energy_Import
        FROM energy_data
        WHERE Meter = ? AND DATE(Clock) = ?
        ORDER BY Clock
        """
        cursor.execute(query, (meter, date_str))
        rows = cursor.fetchall()

        if not rows:
            print(f"No energy data for meter {meter} on {date_str}. Skipping...")
            continue

        # Load into DataFrame
        df = pd.DataFrame(rows, columns=['Clock', 'Import'])
        df['Clock'] = pd.to_datetime(df['Clock'])
        df = df.sort_values('Clock')

        # Calculate interval kWh
        df['kWh'] = df['Import'].diff()
        df = df.dropna()
        df = df[df['kWh'] >= 0]

        # Add hour column
        df['Hour'] = df['Clock'].dt.hour

        # Define peak hours (17:00–23:00)
        peak = df[(df['Hour'] >= 17) & (df['Hour'] < 23)]['kWh'].sum()
        offpeak = df['kWh'].sum() - peak

        # Avoid divide-by-zero
        total = peak + offpeak
        ratio = (offpeak / total) if total > 0 else 0

        # Points = 100 × ratio (rounded)
        new_points = int(round(ratio * 100))
        updated_points = current_points + new_points

        # Update user points in accounts
        cursor.execute("UPDATE accounts SET point = ? WHERE id = ?", (updated_points, acc_id))
        conn.commit()

        print(f"Meter {meter} - Peak: {peak:.2f} kWh, Off-peak: {offpeak:.2f} kWh")
        print(f"Off-peak ratio = {ratio:.2%}")
        print(f"Awarded {new_points} points (Total: {updated_points})")
        print("-" * 40)


# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    date_str = input("Enter date (YYYY-MM-DD): ")
    calculate_points_for_all(date_str)

# Close connection
cursor.close()
conn.close()
