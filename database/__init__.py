# database/__init__.py
from .session import SessionLocal, engine, Base
from .models import User, Bot, Subscription, Payment, Conversation, Learning
from .crud import (
    create_user, get_user, update_user, delete_user,
    create_bot, get_bot, get_user_bots, update_bot_status,
    create_subscription, get_active_subscription,
    create_payment, get_payment, update_payment_status,
    create_conversation, get_conversations,
    create_learning, update_learning
)

__all__ = [
    'SessionLocal', 'engine', 'Base',
    'User', 'Bot', 'Subscription', 'Payment', 'Conversation', 'Learning',
    'create_user', 'get_user', 'update_user', 'delete_user',
    'create_bot', 'get_bot', 'get_user_bots', 'update_bot_status',
    'create_subscription', 'get_active_subscription',
    'create_payment', 'get_payment', 'update_payment_status',
    'create_conversation', 'get_conversations',
    'create_learning', 'update_learning'
]