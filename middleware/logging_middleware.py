# middleware/logging_middleware.py
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from datetime import datetime

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        username = event.from_user.username
        
        if isinstance(event, Message):
            log_msg = f"Message from {user_id} (@{username}): {event.text}"
        elif isinstance(event, CallbackQuery):
            log_msg = f"Callback from {user_id} (@{username}): {event.data}"
        else:
            log_msg = f"Update from {user_id} (@{username})"
        
        logger.info(log_msg)
        
        try:
            result = await handler(event, data)
            return result
        except Exception as e:
            logger.error(f"Error handling update from {user_id}: {e}")
            raise