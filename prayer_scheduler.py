# prayer_scheduler.py
import asyncio
import logging
from datetime import datetime, time
from services.scheduler import SchedulerService
from handlers.prayer_time import PrayerTimeHandler

logger = logging.getLogger(__name__)

class PrayerScheduler:
    def __init__(self):
        self.scheduler = SchedulerService()
        self.prayer_handler = PrayerTimeHandler()
        self.running = False
    
    async def start(self):
        """Start prayer scheduler"""
        try:
            self.running = True
            logger.info("Starting Prayer Scheduler...")
            
            # Schedule prayer times
            await self.prayer_handler.schedule_prayer_notifications()
            
            # Start scheduler
            self.scheduler.start()
            
            # Schedule daily update
            self.scheduler.add_daily_schedule(
                name="prayer_time_update",
                hour=0,
                minute=1,
                callback=self.update_prayer_times
            )
            
            logger.info("Prayer Scheduler started")
            
        except Exception as e:
            logger.error(f"Error starting Prayer Scheduler: {e}")
    
    async def update_prayer_times(self):
        """Update prayer times (can be called to refresh)"""
        try:
            # In production, this would fetch updated prayer times
            # For now, just reload from current settings
            self.prayer_handler.load_prayer_times()
            await self.prayer_handler.schedule_prayer_notifications()
            
            logger.info("Prayer times updated")
            
        except Exception as e:
            logger.error(f"Error updating prayer times: {e}")
    
    async def update_single_prayer(self, prayer_name: str, hour: int, minute: int, azan: bool = True):
        """Update single prayer time"""
        try:
            success = self.prayer_handler.update_prayer_time(prayer_name, hour, minute, azan)
            
            if success:
                logger.info(f"Updated {prayer_name} prayer to {hour:02d}:{minute:02d}")
                return True
            else:
                logger.error(f"Failed to update {prayer_name} prayer")
                return False
                
        except Exception as e:
            logger.error(f"Error updating {prayer_name} prayer: {e}")
            return False
    
    def get_prayer_times(self):
        """Get current prayer times"""
        return self.prayer_handler.get_prayer_times()
    
    def get_next_prayer(self):
        """Get next prayer time"""
        return self.prayer_handler.get_next_prayer()
    
    async def stop(self):
        """Stop prayer scheduler"""
        try:
            self.running = False
            self.scheduler.stop()
            logger.info("Prayer Scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping Prayer Scheduler: {e}")

# Singleton instance
prayer_scheduler = PrayerScheduler()

async def start_prayer_scheduler():
    """Start the prayer scheduler"""
    await prayer_scheduler.start()

async def stop_prayer_scheduler():
    """Stop the prayer scheduler"""
    await prayer_scheduler.stop()