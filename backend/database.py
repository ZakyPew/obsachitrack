from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./streamtracker.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    steam_id = Column(String, unique=True, index=True)
    username = Column(String, index=True)
    avatar = Column(String)
    email = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_premium = Column(Boolean, default=False)
    
    api_keys = relationship("ApiKey", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")

class ApiKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    key = Column(String, unique=True, index=True)
    name = Column(String, default="Default")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="api_keys")

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    stripe_customer_id = Column(String)
    stripe_subscription_id = Column(String)
    status = Column(String, default="inactive")  # active, inactive, cancelled
    tier = Column(String, default="free")  # free, premium
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    
    user = relationship("User", back_populates="subscriptions")

class GameSession(Base):
    __tablename__ = "game_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    app_id = Column(String)
    game_name = Column(String)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    unlock_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
