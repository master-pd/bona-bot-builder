# services/broadcast.py
import logging
import asyncio
from typing import Dict, List, Any
from datetime import datetime
from aiogram import Bot
from aiogram.types import Message
from database import crud
from database.session import get_db
from config.settings import settings

logger = logging.getLogger(__name__)

class BroadcastService:
    def __init__(self):
        self.bot = None
    
    async def initialize(self, bot_token: str = None):
        """Initialize with bot token"""
        if bot_token:
            self.bot = Bot(token=bot_token)
        elif settings.BOT_TOKEN:
            self.bot = Bot(token=settings.BOT_TOKEN)
    
    async def broadcast(self, message: str, message_type: str = "text",
                       photo_path: str = None, **kwargs) -> Dict[str, Any]:
        """Broadcast message to all users"""
        try:
            if not self.bot:
                await self.initialize()
                if not self.bot:
                    return {"success": False, "error": "Bot not initialized"}
            
            with next(get_db()) as db:
                users = crud.get_all_users(db)
                
                total = len(users)
                sent = 0
                failed = 0
                failed_users = []
                
                for user in users:
                    try:
                        if user.is_blocked or not user.is_active:
                            continue
                        
                        if message_type == "text":
                            await self.bot.send_message(
                                chat_id=user.telegram_id,
                                text=message,
                                parse_mode="HTML",
                                **kwargs
                            )
                        elif message_type == "photo" and photo_path:
                            with open(photo_path, 'rb') as photo:
                                await self.bot.send_photo(
                                    chat_id=user.telegram_id,
                                    photo=photo,
                                    caption=message,
                                    parse_mode="HTML",
                                    **kwargs
                                )
                        
                        sent += 1
                        logger.debug(f"Broadcast sent to user {user.telegram_id}")
                        
                        # Small delay to avoid rate limiting
                        await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        failed += 1
                        failed_users.append(user.telegram_id)
                        logger.error(f"Failed to send to user {user.telegram_id}: {e}")
                
                result = {
                    "success": True,
                    "sent": sent,
                    "failed": failed,
                    "total": total,
                    "failed_users": failed_users
                }
                
                logger.info(f"Broadcast completed: {sent}/{total} sent")
                return result
                
        except Exception as e:
            logger.error(f"Error in broadcast: {e}")
            return {"success": False, "error": str(e)}
    
    async def broadcast_to_group(self, group_ids: List[int], message: str,
                                message_type: str = "text", **kwargs) -> Dict[str, Any]:
        """Broadcast to specific groups"""
        try:
            if not self.bot:
                await self.initialize()
            
            sent = 0
            failed = 0
            
            for group_id in group_ids:
                try:
                    if message_type == "text":
                        await self.bot.send_message(
                            chat_id=group_id,
                            text=message,
                            parse_mode="HTML",
                            **kwargs
                        )
                    
                    sent += 1
                    logger.debug(f"Broadcast sent to group {group_id}")
                    
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    failed += 1
                    logger.error(f"Failed to send to group {group_id}: {e}")
            
            return {
                "success": True,
                "sent": sent,
                "failed": failed,
                "total": len(group_ids)
            }
            
        except Exception as e:
            logger.error(f"Error in group broadcast: {e}")
            return {"success": False, "error": str(e)}
    
    async def broadcast_to_active_users(self, message: str, 
                                       min_activity_days: int = 7) -> Dict[str, Any]:
        """Broadcast to active users only"""
        try:
            if not self.bot:
                await self.initialize()
            
            with next(get_db()) as db:
                # Get active users (with recent activity)
                all_users = crud.get_all_users(db)
                active_users = []
                
                cutoff_date = datetime.now() - timedelta(days=min_activity_days)
                
                for user in all_users:
                    if not user.is_active or user.is_blocked:
                        continue
                    
                    # Check if user has active bots
                    user_bots = crud.get_user_bots(db, user.id)
                    active_bots = [b for b in user_bots if b.status == "active"]
                    
                    if active_bots:
                        active_users.append(user)
                
                # Send to active users
                total = len(active_users)
                sent = 0
                failed = 0
                
                for user in active_users:
                    try:
                        await self.bot.send_message(
                            chat_id=user.telegram_id,
                            text=message,
                            parse_mode="HTML"
                        )
                        sent += 1
                        await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        failed += 1
                        logger.error(f"Failed to send to active user {user.telegram_id}: {e}")
                
                return {
                    "success": True,
                    "sent": sent,
                    "failed": failed,
                    "total": total
                }
                
        except Exception as e:
            logger.error(f"Error in active users broadcast: {e}")
            return {"success": False, "error": str(e)}
    
    async def close(self):
        """Close bot session"""
        if self.bot:
            await self.bot.session.close()