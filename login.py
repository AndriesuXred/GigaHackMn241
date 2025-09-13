from flask import Flask, request, jsonify
import mariadb

app = Flask(__name__)

# -----------------------------
# Database connection helper
# -----------------------------
def get_connection():
    return mariadb.connect(
        user="root",
        password="1234",
        host="localhost",
        port=3306,
        database="mydatabase"
    )

# -----------------------------
# Initialize DB table
# -----------------------------
conn = get_connection()
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    point BIGINT DEFAULT 0,
    meter BIGINT
)
""")
conn.commit()
cursor.close()
conn.close()

# -----------------------------
# Login attempts tracking
# -----------------------------
login_attempts = {}

# -----------------------------
# Register endpoint
# -----------------------------
@app.route("/register", methods=["POST"])
def register_endpoint():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    meter = data.get("meter")

    if not username or not password or not meter:
        return jsonify({"error": "Missing fields"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO accounts (username, password, meter) VALUES (?, ?, ?)",
            (username, password, meter)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Account created!"}), 201
    except mariadb.IntegrityError:
        return jsonify({"error": "Username already exists!"}), 400

# -----------------------------
# Login endpoint
# -----------------------------
@app.route("/login", methods=["POST"])
def login_endpoint():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    # Too many attempts
    if login_attempts.get(username, 0) >= 3:
        return jsonify({"error": "Too many failed attempts. Access blocked!"}), 403

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM accounts WHERE username = ?", (username,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row and row[0] == password:
        login_attempts[username] = 0  # reset attempts
        return jsonify({"message": "Login successful!"}), 200
    else:
        login_attempts[username] = login_attempts.get(username, 0) + 1
        return jsonify({"error": "Wrong username or password"}), 401

# -----------------------------
# Run server
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
