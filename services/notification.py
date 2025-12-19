# services/notification.py
import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from aiogram import Bot
from database import crud
from database.session import get_db
from config.settings import settings
from utils.text_templates import TextTemplates

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, bot_token: str = None):
        self.bot = None
        if bot_token:
            self.bot = Bot(token=bot_token)
        elif settings.BOT_TOKEN:
            self.bot = Bot(token=settings.BOT_TOKEN)
    
    async def send_notification(self, user_id: int, message: str,
                              parse_mode: str = "HTML", **kwargs) -> bool:
        """Send notification to single user"""
        try:
            if not self.bot:
                return False
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=parse_mode,
                **kwargs
            )
            return True
            
        except Exception as e:
            logger.error(f"Error sending notification to {user_id}: {e}")
            return False
    
    async def notify_bot_approved(self, user_id: int, bot_name: str):
        """Notify user about bot approval"""
        message = (
            "✅ আপনার বট অনুমোদিত হয়েছে!\n\n"
            f"🤖 বট: {bot_name}\n"
            f"🎉 এখন আপনার বট ব্যবহার করতে পারবেন।\n\n"
            "ইউজ করতে:\n"
            "১. আপনার ঘোস্ট বটে যান\n"
            "২. /start দিন\n"
            "৩. চ্যাট শুরু করুন\n\n"
            "সাপোর্টের জন্য /help দিন।"
        )
        
        return await self.send_notification(user_id, message)
    
    async def notify_bot_rejected(self, user_id: int, bot_name: str, reason: str = None):
        """Notify user about bot rejection"""
        message = (
            "❌ আপনার বট রিকোয়েস্ট রিজেক্ট হয়েছে।\n\n"
            f"🤖 বট: {bot_name}\n"
        )
        
        if reason:
            message += f"📝 কারণ: {reason}\n\n"
        
        message += (
            "আবার চেষ্টা করতে:\n"
            "১. সঠিক তথ্য দিন\n"
            "২. ভ্যালিড টোকেন দিন\n"
            "৩. আবার /createbot দিন\n\n"
            "সাহায্যের জন্য /support দিন।"
        )
        
        return await self.send_notification(user_id, message)
    
    async def notify_payment_verified(self, user_id: int, plan_name: str,
                                    amount: float, days: int):
        """Notify user about payment verification"""
        message = (
            "✅ আপনার পেমেন্ট ভেরিফাই হয়েছে!\n\n"
            f"📦 প্ল্যান: {plan_name}\n"
            f"💵 পরিমাণ: {amount} টাকা\n"
            f"⏳ সময়: {days} দিন\n\n"
            "🎉 এখন আপনি সম্পূর্ণ ফিচার ব্যবহার করতে পারবেন।\n\n"
            "ধন্যবাদ! 💝"
        )
        
        return await self.send_notification(user_id, message)
    
    async def notify_payment_rejected(self, user_id: int, reason: str = None):
        """Notify user about payment rejection"""
        message = (
            "❌ আপনার পেমেন্ট রিজেক্ট হয়েছে।\n\n"
        )
        
        if reason:
            message += f"📝 কারণ: {reason}\n\n"
        
        message += (
            "পুনরায় চেষ্টা করতে:\n"
            "১. সঠিক ট্রানজেকশন আইডি দিন\n"
            "২. স্পষ্ট স্ক্রিনশট পাঠান\n"
            "৩. আবার /buyplan দিন\n\n"
            "সমস্যা হলে /support দিন।"
        )
        
        return await self.send_notification(user_id, message)
    
    async def notify_plan_expiring(self, user_id: int, plan_name: str,
                                 days_left: int):
        """Notify user about plan expiry"""
        message = (
            "⏰ আপনার প্ল্যান শীঘ্রই শেষ হচ্ছে!\n\n"
            f"📦 প্ল্যান: {plan_name}\n"
            f"⏳ বাকি সময়: {days_left} দিন\n\n"
            "রিনিউ করতে:\n"
            "১. /buyplan দিন\n"
            "২. নতুন প্ল্যান সিলেক্ট করুন\n"
            "৩. পেমেন্ট করুন\n\n"
            "প্ল্যান শেষ হলে সার্ভিস বন্ধ হয়ে যাবে।"
        )
        
        return await self.send_notification(user_id, message)
    
    async def notify_trial_ending(self, user_id: int, days_left: int):
        """Notify user about trial ending"""
        message = (
            "⚠️ আপনার ট্রায়াল শেষ হতে চলেছে!\n\n"
            f"⏳ বাকি সময়: {days_left} দিন\n\n"
            "ট্রায়াল শেষ হলে:\n"
            "• বট কাজ করবে না\n"
            "• নতুন মেসেজ রিপ্লাই দেবে না\n\n"
            "চালিয়ে যেতে প্ল্যান কিনুন:\n"
            " /buyplan"
        )
        
        return await self.send_notification(user_id, message)
    
    async def send_system_notification(self, user_id: int, title: str,
                                     content: str, notification_type: str = "info"):
        """Send system notification"""
        emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "success": "✅",
            "update": "🔄"
        }.get(notification_type, "📢")
        
        message = f"{emoji} {title}\n\n{content}"
        
        return await self.send_notification(user_id, message)
    
    async def broadcast_announcement(self, announcement: str,
                                   exclude_users: List[int] = None) -> Dict[str, Any]:
        """Broadcast announcement to all users"""
        try:
            with next(get_db()) as db:
                users = crud.get_all_users(db)
                
                sent = 0
                failed = 0
                
                for user in users:
                    if exclude_users and user.telegram_id in exclude_users:
                        continue
                    
                    if user.is_blocked or not user.is_active:
                        continue
                    
                    success = await self.send_notification(
                        user.telegram_id,
                        f"📢 ঘোষণা:\n\n{announcement}"
                    )
                    
                    if success:
                        sent += 1
                    else:
                        failed += 1
                    
                    await asyncio.sleep(0.05)  # Rate limiting
                
                return {
                    "success": True,
                    "sent": sent,
                    "failed": failed,
                    "total": len(users)
                }
                
        except Exception as e:
            logger.error(f"Error broadcasting announcement: {e}")
            return {"success": False, "error": str(e)}
    
    async def close(self):
        """Close bot session"""
        if self.bot:
            await self.bot.session.close()