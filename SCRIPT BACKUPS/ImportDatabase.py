import pandas as pd
import mariadb
import os
from tqdm import tqdm

#Setup MariaDB connection -----------------------------------

conn = mariadb.connect(
    user="root",           # change to your MariaDB username
    password="1234",   # change to your MariaDB password
    host="localhost",        # or your MariaDB host
    port=3306,
    database="mydatabase"    # change to your database
)
cursor = conn.cursor()
print("Connected to MariaDB successfully!")

#------------------------------------------------------------
#Create the table
cursor.execute("""
CREATE TABLE IF NOT EXISTS energy_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Meter BIGINT,
    Clock DATETIME,
    Active_Energy_Import FLOAT,
    Active_Energy_Export FLOAT,
    TransFullCoef FLOAT
)
""")
#-------------------------------------------------------------


#Get Data from cvs file -------------------------------
folderPath = r"A:\PythonShitHackaton\EnergyTech"

csvFiles = [f for f in os.listdir(folderPath) if f.endswith(".csv")]

for fileName in csvFiles:
    filePath = os.path.join(folderPath, fileName)

    if os.stat(filePath).st_size == 0:
        print(f"Skipping empty file: {fileName}")
        continue

    #Load CSV
    df = pd.read_csv(filePath, sep=";")

    # Drop extra empty column if exists
    if "Unnamed: 5" in df.columns:
        df = df.drop(columns=["Unnamed: 5"])

    # Rename columns
    df.columns = ["Meter", "Clock", "Active_Energy_Import", "Active_Energy_Export", "TransFullCoef"]

    # Convert Clock to datetime
    df['Clock'] = pd.to_datetime(df['Clock'], format="%d.%m.%Y %H:%M:%S")

    # Force numeric columns and handle empty values
    for col in ["Active_Energy_Import", "Active_Energy_Export", "TransFullCoef"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows where critical values are missing
    df = df.dropna(subset=["Active_Energy_Import", "Active_Energy_Export"])

    # Prepare data for bulk insert
    data_to_insert = df.values.tolist()

    # Insert data
    cursor.executemany("""
        INSERT INTO energy_data (Meter, Clock, Active_Energy_Import, Active_Energy_Export, TransFullCoef)
        VALUES (?, ?, ?, ?, ?)
    """, data_to_insert)
    conn.commit()
    print(f"{len(df)} rows from {fileName} inserted successfully!")



cursor.execute("SELECT COUNT(*) FROM energy_data;")
count = cursor.fetchone()[0]
print(f"Total rows in energy_data table: {count}")
# Fetch first 5 rows
cursor.execute("SELECT * FROM energy_data LIMIT 5;")
for row in cursor.fetchall():
    print(row)
conn.close()


