# ⚡ EnergyTech - Smart Meter Whisperer ⚡

An **intuitive**, beautifully designed app that makes meter data processing **simple and seamless**. Built in just **3 days** at **GigaHack 2025!** 🚀

---

## ✨ Features

- 🖥 **Modern, user-friendly UI**  
- ⏱ **Real-Time Processing**  
- 📊 **Data Visualization**  
- 🔔 **Alerts and Notifications**

---

## 🛠 Tech Stack

- **Frontend:** React Native  
- **Backend:** Python  
- **Database:** MariaDB

---

## 📦 Requirements

- Python 3.9+ 🐍  
- MariaDB (or MySQL) server running locally 🗄  
- Git 🔧  

---

## ⚡ Installation

### 1️⃣ Clone the repository
```bash
git clone https://github.com/AndriesuXred/GigaHackMn241.git
cd GigaHackMn241
```

### 2️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 3️⃣.Set up MariaDB
Install MariaDB (if not already installed).

Create a database:
CREATE DATABASE mydatabase;

### Edit the connection details in server.py if needed:
```python
def get_connection():
    return mariadb.connect(
        user="root",
        password="1234",   # change this if different
        host="localhost",
        port=3306,
        database="mydatabase"
    )
```

### 4️⃣.(Optional) Import energy data

Place your .csv files into a folder (default: A:\PythonShitHackaton\EnergyTech)

Run:
```bash
curl -X POST http://127.0.0.1:5000/import_csv -H "Content-Type: application/json" -d '{"folder_path": "YOUR_PATH"}'
```

### Running the server
```bash
python server.py
```


