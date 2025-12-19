# middleware/authentication.py
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from database import crud
from database.session import get_db
from config.settings import settings

class AuthenticationMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Skip authentication for certain updates
        if isinstance(event, Message) and event.text:
            if event.text.startswith('/start'):
                return await handler(event, data)
        
        # Check if user exists
        user_id = event.from_user.id
        
        with next(get_db()) as db:
            user = crud.get_user(db, user_id)
            
            if not user:
                # User doesn't exist, only allow /start
                if isinstance(event, Message) and event.text and event.text.startswith('/start'):
                    return await handler(event, data)
                else:
                    if isinstance(event, Message):
                        await event.answer("❌ আপনার অ্যাকাউন্ট পাওয়া যায়নি। /start দিন")
                    return
            
            # Check if user is blocked
            if user.is_blocked:
                if isinstance(event, Message):
                    await event.answer("❌ আপনার অ্যাকাউন্ট ব্লক করা হয়েছে।")
                return
            
            # Check if user is active
            if not user.is_active:
                if isinstance(event, Message):
                    await event.answer("❌ আপনার অ্যাকাউন্ট নন-একটিভ।")
                return
            
            # Add user to data
            data['user'] = user
        
        return await handler(event, data)