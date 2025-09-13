import mariadb
import pandas as pd
import os
from getpass import getpass
from tqdm import tqdm

# Setup MariaDB connection -----------------------------------
conn = mariadb.connect(
    user="root",             # change to your MariaDB username
    password="1234",         # change to your MariaDB password
    host="localhost",
    port=3306,
    database="mydatabase"    # change to your database
)
cursor = conn.cursor()
print("Connected to MariaDB successfully!")



# Get Data from CSV files ------------------------------------
folderPath = "/home/singeon/Documents/EnergyTech"

csvFiles = [f for f in os.listdir(folderPath) if f.endswith(".csv")]

for fileName in csvFiles:
    filePath = os.path.join(folderPath, fileName)

    # Load CSV
    df = pd.read_csv(filePath, sep=";")

    # Drop extra empty column if exists
    if "Unnamed: 5" in df.columns:
        df = df.drop(columns=["Unnamed: 5"])

    # Rename columns
    df.columns = ["Meter", "Clock", "Active_Energy_Import", "Active_Energy_Export", "TransFullCoef"]

    # Convert Clock to datetime
    df['Clock'] = pd.to_datetime(df['Clock'], format="%d.%m.%Y %H:%M:%S")

    # Prepare data for bulk insert
    data_to_insert = df.values.tolist()

    # Insert data
    cursor.executemany("""
        INSERT INTO energy_data (Meter, Clock, Active_Energy_Import, Active_Energy_Export, TransFullCoef)
        VALUES (?, ?, ?, ?, ?)
    """, data_to_insert)
    conn.commit()
    print(f"{len(df)} rows from {fileName} inserted successfully!")




# Count login failed
login_attempts = {}

# Register function ------------------------------------------
def register():
    username = input("Enter username: ")
    password = input("Enter password: ")

    try:
        cursor.execute("INSERT INTO accounts (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        print("Account created!")
    except mariadb.IntegrityError:
        print("Username already exists!")

# Login function ---------------------------------------------
def login():
    try:
        user_Mater = ("Enter your Mater: ")
    except ValueError:
        print("Invalid ID")
        return

    password = getpass("Enter password: ")

    # Too many attempts
    if user_Mater in login_attempts and login_attempts[user_Mater] >= 3:
        print("Too many failed attempts. Access blocked!")
        return

    cursor.execute("SELECT password FROM accounts WHERE Mater = ?", (user_Mater,))
    row = cursor.fetchone()

    if row and row[0] == password:
        print("Login successful!")
        login_attempts[user_Mater] = 0  # reset attempts
    else:
        print("Wrong password or ID")
        login_attempts[user_Mater] = login_attempts.get(user_Mater, 0)

# Menu loop ---------------------------------------------------
while True:
    print("\n--- MENU ---")
    print("1. Register")
    print("2. Login")
    print("3. Exit")
    choice = input("Choose: ")

    if choice == "1":
        register()
    elif choice == "2":
        login()
    elif choice == "3":
        break
    else:
        print("Invalid choice")

#-------------------------------------------------------------
# Create the energy_data table
cursor.execute("""
CREATE TABLE IF NOT EXISTS energy_data (
    Mater BIGINT  PRIMARY KEY,
    Meter BIGINT,
    Clock DATETIME,
    Active_Energy_Import FLOAT,
    Active_Energy_Export FLOAT,
    TransFullCoef FLOAT
)
""")
#-------------------------------------------------------------
# Check inserted rows
cursor.execute("SELECT COUNT(*) FROM energy_data;")
count = cursor.fetchone()[0]
print(f"Total rows in energy_data table: {count}")

cursor.execute("SELECT * FROM energy_data LIMIT 5;")
for row in cursor.fetchall():
    print(row)

# Close connection
cursor.close()
conn.close()

























