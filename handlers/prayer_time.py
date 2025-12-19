# handlers/prayer_time.py
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pytz
from aiogram import Router
from aiogram.types import Message
from database import crud
from database.session import get_db
from services.scheduler import SchedulerService
from utils.time_utils import TimeUtils

logger = logging.getLogger(__name__)
router = Router()

class PrayerTimeHandler:
    def __init__(self):
        self.scheduler = SchedulerService()
        self.time_utils = TimeUtils()
        self.bangladesh_tz = pytz.timezone('Asia/Dhaka')
        self.prayer_times = {}
        self.load_prayer_times()
    
    def load_prayer_times(self):
        """Load prayer times (default for Dhaka)"""
        # Default prayer times for Dhaka (can be updated via admin panel)
        self.prayer_times = {
            "fajr": {"hour": 5, "minute": 0, "name": "ফজর", "azan": True},
            "dhuhr": {"hour": 12, "minute": 30, "name": "যোহর", "azan": True},
            "asr": {"hour": 15, "minute": 45, "name": "আসর", "azan": True},
            "maghrib": {"hour": 18, "minute": 0, "name": "মাগরিব", "azan": True},
            "isha": {"hour": 19, "minute": 30, "name": "ইশা", "azan": True}
        }
    
    async def schedule_prayer_notifications(self):
        """Schedule prayer time notifications"""
        try:
            # Clear existing schedules
            self.scheduler.clear_schedules("prayer")
            
            # Schedule for each prayer
            for prayer_name, prayer_data in self.prayer_times.items():
                if prayer_data.get("azan", True):
                    await self.schedule_single_prayer(prayer_name, prayer_data)
            
            logger.info("Prayer time notifications scheduled")
            
        except Exception as e:
            logger.error(f"Error scheduling prayer notifications: {e}")
    
    async def schedule_single_prayer(self, prayer_name: str, prayer_data: Dict):
        """Schedule single prayer notification"""
        hour = prayer_data["hour"]
        minute = prayer_data["minute"]
        prayer_display = prayer_data["name"]
        
        # Schedule azan time
        self.scheduler.add_daily_schedule(
            name=f"prayer_{prayer_name}_azan",
            hour=hour,
            minute=minute,
            callback=self.send_azan_notification,
            args=(prayer_display,)
        )
        
        # Schedule reminder 10 minutes before
        reminder_time = datetime.now().replace(
            hour=hour, minute=minute
        ) - timedelta(minutes=10)
        
        self.scheduler.add_daily_schedule(
            name=f"prayer_{prayer_name}_reminder",
            hour=reminder_time.hour,
            minute=reminder_time.minute,
            callback=self.send_prayer_reminder,
            args=(prayer_display,)
        )
    
    async def send_azan_notification(self, prayer_name: str):
        """Send azan notification to all users"""
        try:
            with next(get_db()) as db:
                active_users = crud.get_active_users(db)
                
                for user in active_users:
                    try:
                        # Check if user has prayer notifications enabled
                        user_bots = crud.get_user_bots(db, user.id)
                        for bot in user_bots:
                            if bot.settings.get("prayer_time", False):
                                # Send notification
                                message_text = (
                                    f"🕌 {prayer_name} এর আজানের সময় হয়েছে!\n\n"
                                    f"আল্লাহু আকবার! আল্লাহু আকবার!\n"
                                    f"আশহাদু আল্লা ইলাহা ইল্লাল্লাহ!\n"
                                    f"আশহাদু আন্না মুহাম্মাদার রাসুলুল্লাহ!\n\n"
                                    f"হাইয়া আলাস সালাহ! হাইয়া আলাল ফালাহ!\n"
                                    f"আল্লাহু আকবার! আল্লাহু আকবার!\n"
                                    f"লা ইলাহা ইল্লাল্লাহ!\n\n"
                                    f"🌙 নামাজের সময় হলে পড়ে নিন।"
                                )
                                
                                # In actual implementation, send via bot
                                # await bot.send_message(user.telegram_id, message_text)
                                
                    except Exception as e:
                        logger.error(f"Error sending azan to user {user.id}: {e}")
            
            logger.info(f"Azan notification sent for {prayer_name}")
            
        except Exception as e:
            logger.error(f"Error sending azan notification: {e}")
    
    async def send_prayer_reminder(self, prayer_name: str):
        """Send prayer reminder"""
        try:
            with next(get_db()) as db:
                active_users = crud.get_active_users(db)
                
                for user in active_users:
                    try:
                        user_bots = crud.get_user_bots(db, user.id)
                        for bot in user_bots:
                            if bot.settings.get("prayer_time", False):
                                message_text = (
                                    f"⏰ {prayer_name} এর আজান হতে ১০ মিনিট বাকি!\n\n"
                                    f"নামাজের প্রস্তুতি নিন।\n"
                                    f"ওজু করে নিন।\n"
                                    f"নামাজের জন্য তৈরি হন।\n\n"
                                    f"📿 আল্লাহ তায়ালা আমাদের নামাজ কবুল করুন। আমিন।"
                                )
                                
                                # In actual implementation, send via bot
                                # await bot.send_message(user.telegram_id, message_text)
                                
                    except Exception as e:
                        logger.error(f"Error sending reminder to user {user.id}: {e}")
            
            logger.info(f"Prayer reminder sent for {prayer_name}")
            
        except Exception as e:
            logger.error(f"Error sending prayer reminder: {e}")
    
    def update_prayer_time(self, prayer_name: str, hour: int, minute: int, azan: bool = True):
        """Update prayer time"""
        if prayer_name in self.prayer_times:
            self.prayer_times[prayer_name] = {
                "hour": hour,
                "minute": minute,
                "name": self.prayer_times[prayer_name]["name"],
                "azan": azan
            }
            
            # Reschedule
            asyncio.create_task(self.schedule_prayer_notifications())
            return True
        
        return False
    
    def get_prayer_times(self) -> Dict:
        """Get current prayer times"""
        return self.prayer_times
    
    def get_next_prayer(self) -> Dict:
        """Get next prayer time"""
        now = datetime.now(self.bangladesh_tz)
        current_time = now.time()
        
        next_prayer = None
        min_diff = float('inf')
        
        for prayer_name, prayer_data in self.prayer_times.items():
            prayer_time = datetime.now(self.bangladesh_tz).replace(
                hour=prayer_data["hour"],
                minute=prayer_data["minute"],
                second=0,
                microsecond=0
            ).time()
            
            # Calculate time difference
            current_seconds = current_time.hour * 3600 + current_time.minute * 60 + current_time.second
            prayer_seconds = prayer_time.hour * 3600 + prayer_time.minute * 60
            
            diff = prayer_seconds - current_seconds
            if diff < 0:
                diff += 24 * 3600  # Next day
            
            if diff < min_diff:
                min_diff = diff
                next_prayer = {
                    "name": prayer_data["name"],
                    "time": prayer_time.strftime("%I:%M %p"),
                    "minutes_left": diff // 60
                }
        
        return next_prayer

# Webhook endpoint for admin to update prayer times
@router.message(Command("prayertimes"))
async def prayer_times_command(message: Message):
    """Show current prayer times"""
    handler = PrayerTimeHandler()
    prayer_times = handler.get_prayer_times()
    next_prayer = handler.get_next_prayer()
    
    times_text = "🕌 আজানের সময়সূচি:\n\n"
    
    for prayer_name, prayer_data in prayer_times.items():
        time_str = f"{prayer_data['hour']:02d}:{prayer_data['minute']:02d}"
        azan_status = "✅" if prayer_data.get("azan", True) else "❌"
        times_text += f"{azan_status} {prayer_data['name']}: {time_str}\n"
    
    if next_prayer:
        times_text += f"\n⏳ পরবর্তী আজান: {next_prayer['name']}\n"
        times_text += f"🕐 সময়: {next_prayer['time']}\n"
        times_text += f"⏰ বাকি: {next_prayer['minutes_left']} মিনিট\n"
    
    times_text += "\n⚙️ সময় পরিবর্তন করতে অ্যাডমিনের সাথে যোগাযোগ করুন।"
    
    await message.answer(times_text)