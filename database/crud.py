# database/crud.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from . import models
from config.settings import settings
from config.security import Security

# User CRUD
def create_user(db: Session, telegram_id: int, username: str = None, 
                first_name: str = None, last_name: str = None) -> models.User:
    """Create new user with trial"""
    trial_end = datetime.now() + timedelta(days=settings.TRIAL_DAYS)
    
    user = models.User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        plan_type="trial",
        trial_used=True,
        trial_start=datetime.now(),
        trial_end=trial_end,
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user(db: Session, telegram_id: int) -> Optional[models.User]:
    """Get user by telegram ID"""
    return db.query(models.User).filter(models.User.telegram_id == telegram_id).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    """Get user by ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()

def update_user(db: Session, telegram_id: int, **kwargs) -> Optional[models.User]:
    """Update user information"""
    user = get_user(db, telegram_id)
    if user:
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        user.updated_at = datetime.now()
        db.commit()
        db.refresh(user)
    return user

def delete_user(db: Session, telegram_id: int) -> bool:
    """Delete user"""
    user = get_user(db, telegram_id)
    if user:
        db.delete(user)
        db.commit()
        return True
    return False

def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    """Get all users"""
    return db.query(models.User).offset(skip).limit(limit).all()

def get_active_users(db: Session) -> List[models.User]:
    """Get active users"""
    return db.query(models.User).filter(models.User.is_active == True).all()

# Bot CRUD
def create_bot(db: Session, owner_id: int, bot_token: str, admin_chat_id: int,
               bot_name: str, plan_type: str = "trial") -> models.Bot:
    """Create new bot"""
    # Encrypt token
    encrypted_token = Security.encrypt_token(bot_token)
    
    bot = models.Bot(
        owner_id=owner_id,
        bot_token=encrypted_token,
        admin_chat_id=admin_chat_id,
        bot_name=bot_name,
        plan_type=plan_type,
        status="pending",
        is_ghost=True,
        trial_expiry=datetime.now() + timedelta(days=settings.TRIAL_DAYS) if plan_type == "trial" else None
    )
    
    db.add(bot)
    db.commit()
    db.refresh(bot)
    return bot

def get_bot(db: Session, bot_id: int) -> Optional[models.Bot]:
    """Get bot by ID"""
    bot = db.query(models.Bot).filter(models.Bot.id == bot_id).first()
    if bot and bot.bot_token:
        # Decrypt token when accessed
        bot.bot_token = Security.decrypt_token(bot.bot_token)
    return bot

def get_user_bots(db: Session, owner_id: int) -> List[models.Bot]:
    """Get all bots owned by user"""
    bots = db.query(models.Bot).filter(models.Bot.owner_id == owner_id).all()
    for bot in bots:
        if bot.bot_token:
            bot.bot_token = Security.decrypt_token(bot.bot_token)
    return bots

def update_bot_status(db: Session, bot_id: int, status: str, 
                      verified_by: int = None) -> Optional[models.Bot]:
    """Update bot status"""
    bot = db.query(models.Bot).filter(models.Bot.id == bot_id).first()
    if bot:
        bot.status = status
        bot.updated_at = datetime.now()
        if status == "active" and verified_by:
            bot.verified_by = verified_by
        db.commit()
        db.refresh(bot)
    return bot

def get_pending_bots(db: Session) -> List[models.Bot]:
    """Get all pending bots"""
    bots = db.query(models.Bot).filter(models.Bot.status == "pending").all()
    for bot in bots:
        if bot.bot_token:
            bot.bot_token = Security.decrypt_token(bot.bot_token)
    return bots

def get_active_bots(db: Session) -> List[models.Bot]:
    """Get all active bots"""
    bots = db.query(models.Bot).filter(models.Bot.status == "active").all()
    for bot in bots:
        if bot.bot_token:
            bot.bot_token = Security.decrypt_token(bot.bot_token)
    return bots

# Subscription CRUD
def create_subscription(db: Session, user_id: int, bot_id: int,
                        plan_type: str, amount: float) -> models.Subscription:
    """Create new subscription"""
    plan_days = settings.PLANS.get(plan_type, {}).get("days", 30)
    end_date = datetime.now() + timedelta(days=plan_days)
    
    subscription = models.Subscription(
        user_id=user_id,
        bot_id=bot_id,
        plan_type=plan_type,
        amount=amount,
        status="pending",
        start_date=datetime.now(),
        end_date=end_date
    )
    
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription

def get_active_subscription(db: Session, bot_id: int) -> Optional[models.Subscription]:
    """Get active subscription for bot"""
    return db.query(models.Subscription).filter(
        and_(
            models.Subscription.bot_id == bot_id,
            models.Subscription.status == "verified",
            models.Subscription.end_date > datetime.now()
        )
    ).first()

def verify_subscription(db: Session, subscription_id: int, 
                        verified_by: int) -> Optional[models.Subscription]:
    """Verify subscription"""
    subscription = db.query(models.Subscription).filter(
        models.Subscription.id == subscription_id
    ).first()
    
    if subscription:
        subscription.status = "verified"
        subscription.verified_by = verified_by
        subscription.verified_at = datetime.now()
        
        # Update bot plan
        bot = db.query(models.Bot).filter(models.Bot.id == subscription.bot_id).first()
        if bot:
            bot.plan_type = subscription.plan_type
            bot.status = "active"
        
        # Update user plan
        user = db.query(models.User).filter(models.User.id == subscription.user_id).first()
        if user:
            user.plan_type = subscription.plan_type
            user.plan_end = subscription.end_date
        
        db.commit()
        db.refresh(subscription)
    
    return subscription

# Payment CRUD
def create_payment(db: Session, user_id: int, amount: float, method: str,
                   transaction_id: str, sender_number: str = None,
                   proof_image: str = None) -> models.Payment:
    """Create payment record"""
    payment = models.Payment(
        user_id=user_id,
        amount=amount,
        method=method,
        sender_number=sender_number,
        transaction_id=transaction_id,
        proof_image=proof_image,
        status="pending"
    )
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment

def get_payment(db: Session, payment_id: int) -> Optional[models.Payment]:
    """Get payment by ID"""
    return db.query(models.Payment).filter(models.Payment.id == payment_id).first()

def update_payment_status(db: Session, payment_id: int, status: str,
                          verified_by: int = None, notes: str = None) -> Optional[models.Payment]:
    """Update payment status"""
    payment = get_payment(db, payment_id)
    if payment:
        payment.status = status
        if verified_by:
            payment.verified_by = verified_by
            payment.verified_at = datetime.now()
        if notes:
            payment.notes = notes
        db.commit()
        db.refresh(payment)
    return payment

def get_pending_payments(db: Session) -> List[models.Payment]:
    """Get all pending payments"""
    return db.query(models.Payment).filter(models.Payment.status == "pending").all()

# Conversation CRUD
def create_conversation(db: Session, bot_id: int, from_user: int, to_user: int,
                        message_text: str, bot_response: str = None,
                        message_type: str = "text", is_ghost_mode: bool = True) -> models.Conversation:
    """Create conversation record"""
    conversation = models.Conversation(
        bot_id=bot_id,
        from_user=from_user,
        to_user=to_user,
        message_text=message_text,
        bot_response=bot_response,
        message_type=message_type,
        is_ghost_mode=is_ghost_mode,
        timestamp=datetime.now()
    )
    
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation

def get_conversations(db: Session, bot_id: int, limit: int = 100) -> List[models.Conversation]:
    """Get conversations for bot"""
    return db.query(models.Conversation).filter(
        models.Conversation.bot_id == bot_id
    ).order_by(desc(models.Conversation.timestamp)).limit(limit).all()

def get_recent_conversations(db: Session, from_user: int, to_user: int,
                            limit: int = 10) -> List[models.Conversation]:
    """Get recent conversations between users"""
    return db.query(models.Conversation).filter(
        or_(
            and_(
                models.Conversation.from_user == from_user,
                models.Conversation.to_user == to_user
            ),
            and_(
                models.Conversation.from_user == to_user,
                models.Conversation.to_user == from_user
            )
        )
    ).order_by(desc(models.Conversation.timestamp)).limit(limit).all()

# Learning CRUD
def create_learning(db: Session, bot_id: int) -> models.Learning:
    """Create learning record for bot"""
    learning = models.Learning(
        bot_id=bot_id,
        user_patterns={},
        response_patterns={},
        context_data={},
        accuracy_score=0.0,
        training_count=0,
        last_trained=datetime.now(),
        next_training=datetime.now() + timedelta(hours=24)
    )
    
    db.add(learning)
    db.commit()
    db.refresh(learning)
    return learning

def update_learning(db: Session, learning_id: int, user_patterns: Dict = None,
                   response_patterns: Dict = None, context_data: Dict = None,
                   accuracy_score: float = None) -> Optional[models.Learning]:
    """Update learning data"""
    learning = db.query(models.Learning).filter(models.Learning.id == learning_id).first()
    if learning:
        if user_patterns:
            learning.user_patterns = user_patterns
        if response_patterns:
            learning.response_patterns = response_patterns
        if context_data:
            learning.context_data = context_data
        if accuracy_score:
            learning.accuracy_score = accuracy_score
        
        learning.training_count += 1
        learning.last_trained = datetime.now()
        learning.next_training = datetime.now() + timedelta(hours=24)
        
        db.commit()
        db.refresh(learning)
    
    return learning

def get_learning(db: Session, bot_id: int) -> Optional[models.Learning]:
    """Get learning data for bot"""
    return db.query(models.Learning).filter(models.Learning.bot_id == bot_id).first()

# Statistics
def get_user_count(db: Session) -> int:
    """Get total user count"""
    return db.query(models.User).count()

def get_bot_count(db: Session) -> int:
    """Get total bot count"""
    return db.query(models.Bot).count()

def get_active_bot_count(db: Session) -> int:
    """Get active bot count"""
    return db.query(models.Bot).filter(models.Bot.status == "active").count()

def get_today_payments(db: Session) -> float:
    """Get today's total payments"""
    today = datetime.now().date()
    payments = db.query(models.Payment).filter(
        and_(
            models.Payment.status == "verified",
            models.Payment.verified_at >= datetime.combine(today, datetime.min.time()),
            models.Payment.verified_at <= datetime.combine(today, datetime.max.time())
        )
    ).all()
    
    return sum(p.amount for p in payments)

def get_user_stats(db: Session, telegram_id: int) -> Dict[str, Any]:
    """Get user statistics"""
    user = get_user(db, telegram_id)
    if not user:
        return {}
    
    bots = get_user_bots(db, user.id)
    active_bots = [b for b in bots if b.status == "active"]
    
    return {
        "user": user,
        "total_bots": len(bots),
        "active_bots": len(active_bots),
        "trial_expired": user.trial_end < datetime.now() if user.trial_end else False,
        "plan_expired": user.plan_end < datetime.now() if user.plan_end else False,
        "is_premium": user.plan_type in ["100", "400"]
    }