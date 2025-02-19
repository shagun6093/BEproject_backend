from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import time
from .models.model import assistant

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Global in-memory chat history
chat_history = []  # Each element is a dict: {"role": "user" or "server", "msg": message, "timestamp": timestamp}

@app.route('/user')
def user():
    # Render the user chat interface and pass the current chat history.
    return render_template('user.html', chat_history=chat_history)

@app.route('/server')
def server():
    # Render the server chat interface and pass the current chat history.
    return render_template('server.html', chat_history=chat_history)

@socketio.on('connect')
def handle_connect():
    # When a client connects, send the full chat history.
    emit('load_history', chat_history)

@socketio.on('send_message')
def handle_send_message(data):
    # Data should contain "role" and "msg"
    role = data.get('role')
    msg = data.get('msg')
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    message = {
        'role': role,
        'msg': msg,
        'timestamp': timestamp
    }
    chat_history.append(message)
    # Broadcast the new message to all connected clients
    socketio.emit('chat_message', message)

if __name__ == '__main__':
    socketio.run(app, debug=True)
