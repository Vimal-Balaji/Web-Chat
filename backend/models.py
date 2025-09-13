from sqlalchemy import (
    Column, Integer, BigInteger, String, Enum, ForeignKey, DateTime, Text, func, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

DATABASE_URL = "mysql+pymysql://chatuser:12345678@localhost/chatdb"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Users(Base):
    __tablename__ = "users"

    userId=Column(Integer,primary_key=True,index=True)
    phoneNo=Column(String(10),unique=True,nullable=False)
    username=Column(String(50),unique=True,nullable=False)
    email=Column(String(100),unique=True,nullable=False)
    password=Column(String(255),nullable=False)
   
class Status(Base):
    __tablename__ = "status"

    userId=Column(Integer,ForeignKey("users.userId"),primary_key=True)
    createdAt=Column(DateTime(timezone=True), server_default=func.now())
    isOnline=Column(Enum('Y','N'),default='N')
    lastSeen=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
class Messages(Base):
    __tablename__ = "messages"

    messageId=Column(BigInteger,primary_key=True,index=True)
    senderId=Column(Integer,ForeignKey("users.userId"),nullable=False)
    receiverId=Column(Integer,ForeignKey("users.userId"),nullable=False)
    message=Column(Text,nullable=False)
    timestamp=Column(DateTime(timezone=True), server_default=func.now())
    status=Column(Enum('sent','delivered','read'),default='sent')

    __table_args__ = (UniqueConstraint('messageId', 'senderId', 'receiverId', name='_message_sender_receiver_uc'),)

class BlockedUsers(Base):
    __tablename__ = "blocked_users"

    blockId=Column(BigInteger,primary_key=True,index=True)
    userId=Column(Integer,ForeignKey("users.userId"),nullable=False)
    blockedUserId=Column(Integer,ForeignKey("users.userId"),nullable=False)
    timestamp=Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint('userId', 'blockedUserId', name='_user_blockeduser_uc'),)