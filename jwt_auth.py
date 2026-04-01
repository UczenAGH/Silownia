import sqlite3
import jwt
import datetime
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

# ustaw zmienną środowiskową SECRET_KEY
SECRET_KEY = os.environ.get('SECRET_KEY')
DB_FILE = "smartgym.db"

if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password_hash TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS workouts 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, exercise TEXT, reps INTEGER, peak REAL, date DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"error": "Uzupełnij wszystkie pola"}), 400
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        hashed_password = generate_password_hash(password)
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        return jsonify({"message": "Rejestracja udana"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Użytkownik o takim loginie już istnieje"}), 400
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[0], password):
        token = jwt.encode({
            'user': username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, SECRET_KEY, algorithm="HS256")
        return jsonify({"token": token, "username": username})
    
    return jsonify({"error": "Podaj poprawne dane"}), 401

@app.route('/sync', methods=['POST'])
def sync():
    token = request.headers.get('Authorization')
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username = decoded['user']
        d = request.get_json()
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO workouts (username, exercise, reps, peak) VALUES (?, ?, ?, ?)",
                       (username, d['exercise'], int(d['reps']), float(d['peak'])))
        conn.commit()
        conn.close()
        return jsonify({"status": "Zsynchronizowano"})
    except:
        return jsonify({"error": "Brak autoryzacji"}), 401

@app.route('/history', methods=['GET'])
def history():
    token = request.headers.get('Authorization')
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT exercise, reps, peak, date FROM workouts WHERE username = ? ORDER BY date DESC", (decoded['user'],))
        rows = cursor.fetchall()
        conn.close()
        return jsonify([{"exercise": r[0], "reps": r[1], "peak": r[2], "date": r[3]} for r in rows])
    except:
        return jsonify({"error": "Brak autoryzacji"}), 401

if __name__ == "__main__":
    init_db()
    app.run(port=10000, debug=False)