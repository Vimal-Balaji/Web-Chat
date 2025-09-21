from sqlalchemy import (
    Column, Integer, BigInteger, String, Enum, ForeignKey, DateTime, Text, func, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy import create_engine

DATABASE_URL = "mysql+pymysql://chatuser:12345678@localhost/chatdb"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Users(Base):
    __tablename__ = "users"

    userId = Column(Integer, primary_key=True, index=True)
    phoneNo = Column(String(10), unique=True, nullable=False)
    name = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

    # Relationships with cascade delete
    status = relationship(
        "Status",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    chats1 = relationship(
        "Chats",
        back_populates="user1",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="Chats.user1Id"
    )
    chats2 = relationship(
        "Chats",
        back_populates="user2",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="Chats.user2Id"
    )
    messages_sent = relationship(
        "Messages",
        back_populates="sender",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="Messages.senderId"
    )
    messages_received = relationship(
        "Messages",
        back_populates="receiver",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="Messages.receiverId"
    )


class Status(Base):
    __tablename__ = "status"

    userId = Column(
        Integer,
        ForeignKey("users.userId", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True
    )
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    isOnline = Column(Enum('Y', 'N'), default='N')
    lastSeen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship back to user
    user = relationship("Users", back_populates="status")


class Chats(Base):
    __tablename__ = "chats"

    chatId = Column(String(100), primary_key=True, index=True)
    user1Id = Column(
        Integer,
        ForeignKey("users.userId", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )
    user2Id = Column(
        Integer,
        ForeignKey("users.userId", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )

    user1 = relationship("Users", back_populates="chats1", foreign_keys=[user1Id])
    user2 = relationship("Users", back_populates="chats2", foreign_keys=[user2Id])

    __table_args__ = (UniqueConstraint('user1Id', 'user2Id', name='_user_chatuser_uc'),)


class Messages(Base):
    __tablename__ = "messages"

    chatId = Column(
        String(100),
        ForeignKey("chats.chatId", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )
    messageId = Column(BigInteger, primary_key=True, index=True,autoincrement=True)
    senderId = Column(
        Integer,
        ForeignKey("users.userId", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )
    receiverId = Column(
        Integer,
        ForeignKey("users.userId", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(Enum('sent', 'delivered', 'read'), default='sent')

    # Relationships
    sender = relationship("Users", back_populates="messages_sent", foreign_keys=[senderId])
    receiver = relationship("Users", back_populates="messages_received", foreign_keys=[receiverId])
    chat = relationship("Chats", foreign_keys=[chatId])

    __table_args__ = (UniqueConstraint('messageId', 'senderId', 'receiverId', name='_message_sender_receiver_uc'),)


class BlockedUsers(Base):
    __tablename__ = "blocked_users"

    blockId = Column(BigInteger, primary_key=True, index=True)
    userId = Column(
        Integer,
        ForeignKey("users.userId", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )
    blockedUserId = Column(
        Integer,
        ForeignKey("users.userId", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint('userId', 'blockedUserId', name='_user_blockeduser_uc'),)



    



# Create all tables
Base.metadata.create_all(bind=engine)
