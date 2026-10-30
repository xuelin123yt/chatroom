from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")


@app.route("/")
def index():
    return render_template("index.html")


clients = {}  # 紀錄線上使用者 { sid: {"username": str} }


def broadcast_user_count():
    emit("user_count",
         {"count": len([c for c in clients.values() if c["username"]])},
         broadcast=True)


@socketio.on("connect")
def on_connect():
    clients[request.sid] = {"username": None}
    print("Client connect:", request.sid)


@socketio.on("disconnect")
def on_disconnect():
    info = clients.pop(request.sid, None)
    if info and info["username"]:
        emit("user_left", {"username": info["username"]}, broadcast=True)
        broadcast_user_count()
    print("Client disconnect:", request.sid)


@socketio.on("join")
def on_join(data):
    username = data.get("username", "匿名")
    clients[request.sid]["username"] = username
    emit("user_joined", {"username": username}, broadcast=True)
    broadcast_user_count()
    print(username, "joined")


@socketio.on("send_message")
def on_message(data):
    emit("chat_message", data, broadcast=True, include_self=False)


@socketio.on("typing")
def on_typing(data):
    emit("typing", data, broadcast=True, include_self=False)


@socketio.on("change_username")
def on_change(data):
    old = data.get("oldUsername")
    new = data.get("newUsername")
    if request.sid in clients:
        clients[request.sid]["username"] = new
    emit("user_changed_name",
         {"oldUsername": old, "newUsername": new},
         broadcast=True)


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)