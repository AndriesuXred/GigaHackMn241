import mariadb
from getpass import getpass

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

cursor.execute("""CREATE TABLE IF NOT EXISTS accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    poin BIGINT,
    mater BIGINT

);""")

# Count login failed
login_attempts = {}

# Register function ------------------------------------------
def register():
    username = input("Enter username: ")
    password = input("Enter password: ")
    mater = input("Enter mater: ")

    try:
        cursor.execute(
            "INSERT INTO accounts (username, password, mater) VALUES (?, ?, ?)",
            (username, password, mater)
        )
        conn.commit()
        print("Account created!")
    except mariadb.IntegrityError:
        print("Username already exists!")

# Login function ---------------------------------------------
def login():
    username = input("Enter your username: ")
    password = getpass("Enter password: ")

    # Too many attempts
    if username in login_attempts and login_attempts[username] >= 3:
        print("Too many failed attempts. Access blocked!")
        return

    cursor.execute("SELECT password FROM accounts WHERE username = ?", (username,))
    row = cursor.fetchone()

    if row and row[0] == password:
        print("Login successful!")
        login_attempts[username] = 0  # reset attempts
    else:
        print("Wrong password or username")
        login_attempts[username] = login_attempts.get(username, 0) + 1

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

# Close connection
cursor.close()
conn.close()
