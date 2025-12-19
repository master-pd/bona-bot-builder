# database/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from database.session import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    email = Column(String(100))
    
    # Subscription Info
    plan_type = Column(String(10), default="trial")
    plan_start = Column(DateTime, default=func.now())
    plan_end = Column(DateTime)
    is_active = Column(Boolean, default=True)
    credits = Column(Float, default=0)
    
    # Trial Info
    trial_used = Column(Boolean, default=False)
    trial_start = Column(DateTime)
    trial_end = Column(DateTime)
    trial_messages = Column(Integer, default=0)
    
    # Security
    is_blocked = Column(Boolean, default=False)
    block_reason = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    bots = relationship("Bot", back_populates="owner", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")

class Bot(Base):
    __tablename__ = "bots"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Bot Info
    bot_token = Column(Text, nullable=False)  # Encrypted
    bot_username = Column(String(100))
    admin_chat_id = Column(Integer, nullable=False)
    bot_name = Column(String(100))
    
    # Settings
    plan_type = Column(String(10), default="trial")
    status = Column(String(20), default="pending")  # active/inactive/pending/suspended
    is_ghost = Column(Boolean, default=True)
    settings = Column(JSON, default={
        "stealth_mode": True,
        "profile_clone": True,
        "ai_learning": True,
        "auto_reply": True,
        "prayer_time": False,
        "extra_replies": [],
        "language": "banglish"
    })
    
    # Ghost Features
    clone_profile = Column(JSON, default={})  # Admin profile data
    ai_model = Column(String(50), default="basic")
    
    # Activity
    last_active = Column(DateTime)
    total_messages = Column(Integer, default=0)
    
    # Trial
    trial_expiry = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="bots")
    subscriptions = relationship("Subscription", back_populates="bot", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="bot", cascade="all, delete-orphan")
    learnings = relationship("Learning", back_populates="bot", cascade="all, delete-orphan")

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False)
    
    # Plan Info
    plan_type = Column(String(10), nullable=False)
    amount = Column(Float, nullable=False)
    
    # Payment Info
    payment_method = Column(String(20))
    transaction_id = Column(String(100))
    payment_proof = Column(Text)  # File path
    
    # Status
    status = Column(String(20), default="pending")
    verified_by = Column(Integer)  # Admin/owner ID
    verified_at = Column(DateTime)
    
    # Dates
    start_date = Column(DateTime, default=func.now())
    end_date = Column(DateTime)
    
    # Notes
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    bot = relationship("Bot", back_populates="subscriptions")

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Payment Details
    amount = Column(Float, nullable=False)
    method = Column(String(20), nullable=False)  # nagad/bkash/rocket
    sender_number = Column(String(20))
    receiver_number = Column(String(20), default="01847634486")
    transaction_id = Column(String(100), nullable=False)
    proof_image = Column(Text)  # File path
    
    # Status
    status = Column(String(20), default="pending")
    verified_by = Column(Integer)  # Owner ID
    verified_at = Column(DateTime)
    
    # Notes
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="payments")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False)
    
    # Message Info
    from_user = Column(Integer, nullable=False)
    to_user = Column(Integer, nullable=False)
    message_text = Column(Text)
    bot_response = Column(Text)
    message_type = Column(String(20), default="text")
    
    # Ghost Mode
    is_ghost_mode = Column(Boolean, default=True)
    used_clone_profile = Column(Boolean, default=False)
    
    # Learning
    is_learned = Column(Boolean, default=False)
    accuracy = Column(Float, default=0.0)
    
    # Timestamp
    timestamp = Column(DateTime, default=func.now())
    
    # Relationships
    bot = relationship("Bot", back_populates="conversations")

class Learning(Base):
    __tablename__ = "learning"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False)
    
    # Learning Data
    user_patterns = Column(JSON, default={})
    response_patterns = Column(JSON, default={})
    context_data = Column(JSON, default={})
    
    # Training Info
    accuracy_score = Column(Float, default=0.0)
    training_count = Column(Integer, default=0)
    
    # Dates
    last_trained = Column(DateTime, default=func.now())
    next_training = Column(DateTime)
    
    # Model Data (encrypted)
    model_data = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    bot = relationship("Bot", back_populates="learnings")