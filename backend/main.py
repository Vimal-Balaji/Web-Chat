import socketio
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import redis

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

app = FastAPI()

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
asgi_app = socketio.ASGIApp(sio, other_asgi_app=app)

#app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def home():
    with open("../templates/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@sio.event
async def connect(sid, environ):
    user_count = r.incr("user_count")  # auto increment in Redis
    username = f"User{user_count}"
    r.hset("user_map", sid, username)
    print(f"{username} connected")

    await sio.emit("user_list", list(r.hvals("user_map")))

@sio.event
async def disconnect(sid):
    username = r.hget("user_map", sid)
    if username:
        print(f"{username} disconnected")
        r.hdel("user_map", sid)
        await sio.emit("user_list", list(r.hvals("user_map")))

@sio.on("private_message")
async def handle_private_message(sid, data):
    sender = r.hget("user_map", sid) or "Unknown"
    receiver = data["to"]
    message = data["msg"]

    # Find receiver sid by username
    receiver_sid = None
    for s, uname in r.hgetall("user_map").items():
        if uname == receiver:
            receiver_sid = s
            break

    if receiver_sid:
        await sio.emit("private_message", {
            "from": sender,
            "to": receiver,
            "msg": message
        }, to=receiver_sid)

        await sio.emit("private_message", {
            "from": sender,
            "to": receiver,
            "msg": message
        }, to=sid)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(asgi_app, host="0.0.0.0", port=8000, reload=True)
