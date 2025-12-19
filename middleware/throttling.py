# middleware/throttling.py
import time
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from collections import defaultdict

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 1.0):
        super().__init__()
        self.rate_limit = rate_limit
        self.user_last_calls = defaultdict(float)
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        current_time = time.time()
        last_call = self.user_last_calls.get(user_id, 0)
        
        # Check rate limit
        if current_time - last_call < self.rate_limit:
            # Too many requests
            if isinstance(event, Message):
                await event.answer("⏳ খুব দ্রুত রিকোয়েস্ট করছেন। একটু পরে চেষ্টা করুন।")
            return
        
        # Update last call time
        self.user_last_calls[user_id] = current_time
        
        return await handler(event, data)