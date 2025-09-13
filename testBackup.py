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
        user_id = int(input("Enter your ID: "))
    except ValueError:
        print("Invalid ID")
        return

    password = getpass("Enter password: ")

    # Too many attempts
    if user_id in login_attempts and login_attempts[user_id] >= 3:
        print("Too many failed attempts. Access blocked!")
        return

    cursor.execute("SELECT password FROM accounts WHERE id = ?", (user_id,))
    row = cursor.fetchone()

    if row and row[0] == password:
        print("Login successful!")
        login_attempts[user_id] = 0  # reset attempts
    else:
        print("Wrong password or ID")
        login_attempts[user_id] = login_attempts.get(user_id, 0) + 1

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























