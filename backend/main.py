import socketio
from fastapi import FastAPI,Depends,HTTPException,status,Response,Cookie,Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis,random,jwt,json
from typing import Optional
from models import *
from auth import hash_password, verify_password,create_jwt_token,decode_jwt_token
from sqlalchemy import or_, desc, func,text

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

origins = [
    "http://localhost:5173",  # your Vue dev server
    "http://127.0.0.1:5173",
    "https://ppl5tcfc-5173.inc1.devtunnels.ms/"
]

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # or ["*"] to allow all origins (not recommended in prod)
    allow_credentials=True,
    allow_methods=["*"],        # allow POST, GET, OPTIONS, etc.
    allow_headers=["*"],
)

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
asgi_app = socketio.ASGIApp(sio, other_asgi_app=app)

#app.mount("/static", StaticFiles(directory="static"), name="static")

class LoginRequest(BaseModel):
    phoneNo: str
    password: str

class SignupRequest(BaseModel):
    name: str
    phoneNo: str
    password: str
    otp: str

@app.post("/login",response_model=LoginRequest)
async def login(data:LoginRequest,response:Response,db:Session=Depends(get_db)):
    user = db.query(Users).filter(Users.phoneNo == data.phoneNo).first()
    
    if not user or not True:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    print(user.userId)
    payload = {"userId": user.userId, "phoneNo": user.phoneNo} 
    token=create_jwt_token(payload)
    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Login successful", "userId":user.userId}  # Include token in JSON
    )
    
    sql="""update status set isOnline='Y', lastSeen=now() where userId=:userId"""
    db.execute(text(sql),{"userId":user.userId})
    db.commit()
    # Set HttpOnly cookie on the same response object
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,          # JS cannot access
        secure=False,           # False if testing on localhost
        samesite="strict"
    )

    return response
@app.post("/logout")
async def logout(request:Request,response: Response):
    sql="""update status set isOnline='N', lastSeen=now() where userId=:userId"""
    db: Session = next(get_db())
    token=request.cookies.get("token")
    if token:
        payload = decode_jwt_token(token)
        if payload:
            userId=payload.get("userId")
            db.execute(text(sql),{"userId":userId})
            db.commit()
    # Delete the cookie by setting it to expire immediately
    response.delete_cookie(
        key="token",
        path="/",
        httponly=True,
        secure=False,
        samesite="strict"
    )
    
    # Also set an expired cookie to ensure browser removes it
    response.set_cookie(
        key="token",
        value="",
        max_age=0,
        expires=0,
        path="/",
        httponly=True,
        secure=False,
        samesite="strict"
    )
    
    return {"message": "Logged out successfully"}
   
@app.post("/signup",response_model=SignupRequest)
async def signup(data:SignupRequest,db:Session=Depends(get_db)):
    user = db.query(Users).filter(Users.phoneNo == data.phoneNo).first()
    userId=''
    while True:
        userId = str(random.randint(100000, 999999))
        if not db.query(Users).filter_by(userId=userId).first():
            break
    print("hi")
    if user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    hashed_password = hash_password(data.password)
    new_user = Users(userId=userId,name=data.name, phoneNo=data.phoneNo, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Initialize status
    new_status = Status(userId=new_user.userId, isOnline='N',createdAt=func.now(), lastSeen=func.now())
    db.add(new_status)
    db.commit()
    
    return JSONResponse(status_code=status.HTTP_201_CREATED, content={"message": "User created successfully"})

@app.get("/check-auth")
async def check_auth(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("token")
    
    if not token:
        return {"authenticated": False}
    
    try:
        # Verify JWT token (you'll need to implement this based on your auth setup)
        payload = jwt.decode(token, "your_secret_key", algorithms=["HS256"])
        user_id = payload.get("userId")
        
        # Check if user exists
        user = db.query(Users).filter(Users.userId == user_id).first()
        if user:
            return {"authenticated": True, "user": {"userId": user.userId, "name": user.name}}
        
    except jwt.ExpiredSignatureError:
        return {"authenticated": False}
    except jwt.InvalidTokenError:
        return {"authenticated": False}
    
    return {"authenticated": False}
    
@app.get("/message/{otherUserId}")
def get_messages(request:Request,otherUserId:int, db: Session = Depends(get_db)):
    token=request.cookies.get("token")
    if not token :
        raise HTTPException(status_code=401, detail="Unauthorized")
    payload = decode_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Unauthorized")
    userId=payload.get("userId")
    isBlocked=False
    if db.query(BlockedUsers).filter_by(userId=userId, blockedUserId=otherUserId).first():
        isBlocked=True
    chatId='-'.join(sorted([str(userId),str(otherUserId)]))
    messages = db.query(Messages).filter(Messages.chatId == chatId).order_by(Messages.timestamp).all()
    return {"messages":messages,"isBlocked":isBlocked}
    

@app.get("/lastMessage")
def get_names(request:Request,db: Session = Depends(get_db)):
    token=request.cookies.get("token")
    if not token :
        raise HTTPException(status_code=401, detail="Unauthorized")
    payload = decode_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Unauthorized")
    userId=payload.get("userId")
    
    sql = text("""
        SELECT m.senderId, m.receiverId, m.message, m.timestamp, m.chatId, m.messageId,
               CASE 
                   WHEN m.senderId = :userId THEN m.receiverId 
                   ELSE m.senderId 
               END AS otherId
        FROM messages m
        JOIN (
            SELECT chatId, MAX(timestamp) AS last_time
            FROM messages
            WHERE senderId = :userId OR receiverId = :userId
            GROUP BY chatId
        ) AS t
        ON m.chatId = t.chatId AND m.timestamp = t.last_time
        ORDER BY m.timestamp DESC
    """)
    result = db.execute(sql, {"userId": userId}).fetchall()
    users = db.query(Users.userId, Users.name).filter(Users.userId.in_([row.otherId for row in result])).all()
    user_map = {u.userId: u.name for u in users}
    return [{"otherId": row.otherId, "name": user_map.get(row.otherId, "Unknown"), "timestamp": row.timestamp, "chatId": row.chatId, "messageId": row.messageId,"message":row.message,"receiverId":row.receiverId,"senderId":row.senderId} for row in result]

@app.get("/block/{otherUserId}")
def block_user(request:Request,otherUserId:int, db: Session = Depends(get_db)):
    token=request.cookies.get("token")
    if not token :
        raise HTTPException(status_code=401, detail="Unauthorized")
    payload = decode_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Unauthorized")
    userId=payload.get("userId")
    chatId='-'.join(sorted([str(userId),str(otherUserId)]))
    blocked_entry = db.query(BlockedUsers).filter_by(userId=userId, blockedUserId=otherUserId).first()
    if blocked_entry:
        raise HTTPException(status_code=400, detail="User already blocked")
    new_block = BlockedUsers(userId=userId, blockedUserId=otherUserId)
    db.add(new_block)
    db.commit()
    return {"message": "User blocked successfully"}

@app.get("/unblock/{otherUserId}")
def unblock_user(request:Request,otherUserId:int, db: Session = Depends(get_db)):
    token=request.cookies.get("token")
    if not token :
        raise HTTPException(status_code=401, detail="Unauthorized")
    payload = decode_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Unauthorized")
    userId=payload.get("userId")
    chatId='-'.join(sorted([str(userId),str(otherUserId)]))
    blocked_entry = db.query(BlockedUsers).filter_by(userId=userId, blockedUserId=otherUserId).first()
    if not blocked_entry:
        raise HTTPException(status_code=400, detail="User is not blocked")
    db.delete(blocked_entry)
    db.commit()
    return {"message": "User unblocked successfully"}

@sio.event
async def connect(sid, environ):
   token=environ.get('HTTP_COOKIE', '').split('token=')[-1] if 'token=' in environ.get('HTTP_COOKIE', '') else None
   if not token:
        return False
   payload = decode_jwt_token(token)
   if not payload:
        return False
   userId=payload.get("userId")
   r.hset("sidMap", sid, str(userId))
   r.hset("userMap", str(userId), sid)
   print(f"Client connected: {sid},{userId}")
   offline_key = f"offline:{userId}"
   while True:
    msg_json = r.rpop(offline_key)  # get messages in correct order (FIFO)
    if not msg_json:
        break
    msg_payload = json.loads(msg_json)
    await sio.emit("new_message", msg_payload, room=sid)
    print(f"Delivered offline message to {userId}")

@sio.event
async def disconnect(sid):
    userId = r.hget("sidMap", sid)
    if userId:
        r.hdel("userMap", userId)
    r.hdel("sidMap", sid)
    print(f"Client disconnected: {sid}")

@sio.on("private_message")
async def handle_messages(sid,data):

    db: Session = next(get_db())
    senderId=r.hget("sidMap", sid)
    if not senderId:
        print("Unauthorized user")
        return
    receiverId=data.get("receiverId")
    if db.query(BlockedUsers).filter_by(userId=receiverId, blockedUserId=senderId).first() :
        return
    print(f"Message from {senderId} to {receiverId}: {data.get('message')}")
    receiver_sid = r.hget("userMap", str(receiverId))
    print(receiver_sid)
    name=db.query(Users).filter(Users.userId==senderId).first().name
    message=data.get("message")
    chatId='-'.join(sorted([str(senderId),str(receiverId)]))
    new_message = Messages(chatId=chatId, senderId=senderId, receiverId=receiverId, message=message)
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    msg_payload= {
        "otherId": senderId,
        "name": name,
        "messageId": new_message.messageId,
        "chatId": chatId,
        "senderId": senderId,
        "receiverId": receiverId,
        "message": message,
        "timestamp": new_message.timestamp.isoformat(),
    }

    if not receiver_sid:
        r.lpush(f"offline:{receiverId}", json.dumps(msg_payload))
        print(f"Stored offline message for {receiverId}")
        return
    
    await sio.emit("new_message", {"otherId":senderId,"name":name,"messageId":new_message.messageId,"chatId":chatId, "senderId": senderId, "receiverId": receiverId, "message": message,"timestamp":new_message.timestamp.isoformat()}, room=receiver_sid) 
    #await sio.emit("new_message", {"messageId":new_message.messageId,"chatId":chatId, "senderId": senderId, "receiverId": receiverId, "message": message,"timestamp":new_message.timestamp}, room=sid)

if  __name__ == "__main__":
    import uvicorn
    uvicorn.run(asgi_app, host="0.0.0.0", port=8000, reload=True)
