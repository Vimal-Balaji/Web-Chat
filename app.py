from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = "secret!"
socketio = SocketIO(app, cors_allowed_origins="*")

# sid -> username
user_map = {}
user_count = 0

@app.route("/")
def home():
    return render_template("index.html")

@socketio.on("connect")
def handle_connect():
    global user_count
    user_count += 1
    username = f"User{user_count}"
    user_map[request.sid] = username
    print(f"{username} connected")

    # Send updated user list to everyone
    emit("user_list", list(user_map.values()), broadcast=True)

@socketio.on("disconnect")
def handle_disconnect():
    if request.sid in user_map:
        username = user_map[request.sid]
        print(f"{username} disconnected")
        del user_map[request.sid]
        # Update user list
        emit("user_list", list(user_map.values()), broadcast=True)

@socketio.on("private_message")
def handle_private_message(data):
    sender = user_map.get(request.sid, "Unknown")
    receiver = data["to"]
    message = data["msg"]

    # Find receiver sid
    receiver_sid = None
    for sid, uname in user_map.items():
        if uname == receiver:
            receiver_sid = sid
            break

    if receiver_sid:
        # Send message to receiver only
        emit("private_message", {
            "from": sender,
            "to": receiver,
            "msg": message
        }, to=receiver_sid)

        # Also show sender’s own sent message
        emit("private_message", {
            "from": sender,
            "to": receiver,
            "msg": message
        }, to=request.sid)

if __name__ == "__main__":
    socketio.run(app, debug=True)
