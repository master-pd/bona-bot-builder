# services/scheduler.py
import logging
import asyncio
from typing import Dict, List, Callable, Any
from datetime import datetime, time, timedelta
import schedule
import threading
from config.settings import settings

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        self.schedules: Dict[str, Dict] = {}
        self.running = False
        self.scheduler_thread = None
    
    def add_daily_schedule(self, name: str, hour: int, minute: int,
                          callback: Callable, args: tuple = None) -> bool:
        """Add daily schedule"""
        try:
            # Create time object
            schedule_time = time(hour=hour, minute=minute)
            
            # Store schedule
            self.schedules[name] = {
                "time": schedule_time,
                "callback": callback,
                "args": args or (),
                "type": "daily"
            }
            
            # Schedule with schedule library
            schedule.every().day.at(schedule_time.strftime("%H:%M")).do(
                self._execute_schedule, name
            )
            
            logger.info(f"Schedule added: {name} at {schedule_time}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding schedule {name}: {e}")
            return False
    
    def add_interval_schedule(self, name: str, interval_minutes: int,
                             callback: Callable, args: tuple = None) -> bool:
        """Add interval schedule"""
        try:
            self.schedules[name] = {
                "interval": interval_minutes,
                "callback": callback,
                "args": args or (),
                "type": "interval"
            }
            
            schedule.every(interval_minutes).minutes.do(
                self._execute_schedule, name
            )
            
            logger.info(f"Interval schedule added: {name} every {interval_minutes} minutes")
            return True
            
        except Exception as e:
            logger.error(f"Error adding interval schedule {name}: {e}")
            return False
    
    def add_cron_schedule(self, name: str, cron_expression: str,
                         callback: Callable, args: tuple = None) -> bool:
        """Add cron schedule"""
        try:
            # Parse cron expression (simplified)
            parts = cron_expression.split()
            if len(parts) != 5:
                raise ValueError("Invalid cron expression")
            
            minute, hour, day_of_month, month, day_of_week = parts
            
            self.schedules[name] = {
                "cron": cron_expression,
                "callback": callback,
                "args": args or (),
                "type": "cron"
            }
            
            # Note: schedule library doesn't support full cron
            # This is a simplified implementation
            # For production, use apscheduler or similar
            
            logger.info(f"Cron schedule added: {name} with {cron_expression}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding cron schedule {name}: {e}")
            return False
    
    def _execute_schedule(self, name: str):
        """Execute scheduled task"""
        try:
            if name not in self.schedules:
                logger.warning(f"Schedule not found: {name}")
                return
            
            schedule_data = self.schedules[name]
            callback = schedule_data["callback"]
            args = schedule_data["args"]
            
            # Run in asyncio event loop
            asyncio.create_task(self._run_async_callback(callback, args))
            
            logger.debug(f"Executed schedule: {name}")
            
        except Exception as e:
            logger.error(f"Error executing schedule {name}: {e}")
    
    async def _run_async_callback(self, callback: Callable, args: tuple):
        """Run async callback"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args)
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, callback, *args)
                
        except Exception as e:
            logger.error(f"Error in scheduled callback: {e}")
    
    def remove_schedule(self, name: str) -> bool:
        """Remove schedule"""
        try:
            if name in self.schedules:
                del self.schedules[name]
                
                # Clear from schedule library
                schedule.clear(name)
                
                logger.info(f"Schedule removed: {name}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error removing schedule {name}: {e}")
            return False
    
    def clear_schedules(self, prefix: str = None) -> int:
        """Clear schedules (optionally by prefix)"""
        try:
            count = 0
            schedules_to_remove = []
            
            for name in list(self.schedules.keys()):
                if prefix is None or name.startswith(prefix):
                    schedules_to_remove.append(name)
            
            for name in schedules_to_remove:
                if self.remove_schedule(name):
                    count += 1
            
            logger.info(f"Cleared {count} schedules")
            return count
            
        except Exception as e:
            logger.error(f"Error clearing schedules: {e}")
            return 0
    
    def _run_scheduler(self):
        """Run scheduler in background thread"""
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Scheduler thread error: {e}")
    
    def start(self):
        """Start scheduler"""
        if self.running:
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(
            target=self._run_scheduler,
            daemon=True
        )
        self.scheduler_thread.start()
        
        logger.info("Scheduler started")
    
    def stop(self):
        """Stop scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        schedule.clear()
        logger.info("Scheduler stopped")
    
    def get_schedule_list(self) -> List[Dict[str, Any]]:
        """Get list of all schedules"""
        result = []
        
        for name, data in self.schedules.items():
            result.append({
                "name": name,
                "type": data.get("type", "unknown"),
                "next_run": self._get_next_run(name),
                "callback": data["callback"].__name__ if hasattr(data["callback"], "__name__") else "anonymous"
            })
        
        return result
    
    def _get_next_run(self, name: str) -> str:
        """Get next run time for schedule"""
        try:
            # Get next run from schedule library
            job = schedule.get_jobs(name)
            if job:
                return str(job[0].next_run)
            return "Unknown"
        except:
            return "Unknown"