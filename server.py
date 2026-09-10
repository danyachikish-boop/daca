import os
import sqlite3
from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'nexus_secret_key_2026'

# Запуск в режиме threading (без eventlet)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "messenger.db")
active_users = {}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    return conn, conn.cursor()

def init_db():
    conn, cursor = get_db()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            avatar TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            text TEXT,
            media_url TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    html_path = os.path.join(BASE_DIR, 'index.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        return render_template_string(f.read())

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    avatar = data.get('avatar', '')

    if not username or not password:
        return jsonify({"success": False, "message": "Заполните все поля"}), 400

    conn, cursor = get_db()
    try:
        cursor.execute("INSERT INTO users (username, password, avatar) VALUES (?, ?, ?)", (username, password, avatar))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "user": {"username": username, "avatar": avatar}})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"success": False, "message": "Пользователь с таким именем уже существует!"}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')

    conn, cursor = get_db()
    cursor.execute("SELECT username, avatar FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({"success": True, "user": {"username": user[0], "avatar": user[1]}})
    return jsonify({"success": False, "message": "Неверный логин или пароль"}), 401

@app.route('/api/check_user/<username>', methods=['GET'])
def check_user(username):
    conn, cursor = get_db()
    cursor.execute("SELECT username, avatar FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({"exists": True, "user": {"username": user[0], "avatar": user[1]}})
    return jsonify({"exists": False}), 404

@app.route('/api/history/<user1>/<user2>', methods=['GET'])
def get_history(user1, user2):
    conn, cursor = get_db()
    cursor.execute('''
        SELECT sender, receiver, text, media_url, timestamp FROM messages
        WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
        ORDER BY timestamp ASC
    ''', (user1, user2, user2, user1))
    rows = cursor.fetchall()
    conn.close()

    history = [
        {"sender": r[0], "receiver": r[1], "text": r[2], "media_url": r[3], "timestamp": str(r[4])}
        for r in rows
    ]
    return jsonify(history)

@socketio.on('register_socket')
def handle_register_socket(username):
    active_users[username] = request.sid
    join_room(username)

@socketio.on('send_message')
def handle_send_message(data):
    sender = data.get('sender')
    receiver = data.get('receiver')
    text = data.get('text', '')
    media_url = data.get('media_url', '')

    conn, cursor = get_db()
    cursor.execute("INSERT INTO messages (sender, receiver, text, media_url) VALUES (?, ?, ?, ?)",
                   (sender, receiver, text, media_url))
    conn.commit()
    conn.close()

    payload = {"sender": sender, "receiver": receiver, "text": text, "media_url": media_url}

    receiver_sid = active_users.get(receiver)
    if receiver_sid:
        emit('receive_message', payload, room=receiver_sid)
    emit('receive_message', payload, room=request.sid)

@socketio.on('signal')
def handle_signal(data):
    target = data.get('target')
    target_sid = active_users.get(target)
    if target_sid:
        emit('signal', {'sender': data.get('sender'), 'signal': data.get('signal')}, room=target_sid)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
