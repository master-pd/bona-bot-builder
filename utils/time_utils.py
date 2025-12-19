# utils/time_utils.py
import pytz
from datetime import datetime, time, timedelta
from typing import Dict, Optional, Tuple

class TimeUtils:
    
    BANGLADESH_TZ = pytz.timezone('Asia/Dhaka')
    
    @staticmethod
    def get_current_time(timezone: str = 'Asia/Dhaka') -> datetime:
        """Get current time in specified timezone"""
        tz = pytz.timezone(timezone)
        return datetime.now(tz)
    
    @staticmethod
    def format_time(dt: datetime, format_str: str = "%I:%M %p") -> str:
        """Format datetime to time string"""
        if not dt:
            return ""
        
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        
        bd_time = dt.astimezone(TimeUtils.BANGLADESH_TZ)
        return bd_time.strftime(format_str)
    
    @staticmethod
    def format_datetime(dt: datetime, format_str: str = "%d %b %Y, %I:%M %p") -> str:
        """Format datetime to string"""
        if not dt:
            return ""
        
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        
        bd_time = dt.astimezone(TimeUtils.BANGLADESH_TZ)
        return bd_time.strftime(format_str)
    
    @staticmethod
    def parse_time(time_str: str, format_str: str = "%H:%M") -> Optional[time]:
        """Parse time string to time object"""
        try:
            return datetime.strptime(time_str, format_str).time()
        except:
            return None
    
    @staticmethod
    def parse_datetime(dt_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
        """Parse datetime string to datetime object"""
        try:
            dt = datetime.strptime(dt_str, format_str)
            return TimeUtils.BANGLADESH_TZ.localize(dt)
        except:
            return None
    
    @staticmethod
    def get_time_until(target_time: time) -> Tuple[int, int]:
        """Get hours and minutes until target time"""
        now = TimeUtils.get_current_time()
        target_dt = datetime.combine(now.date(), target_time)
        
        if target_dt < now:
            target_dt += timedelta(days=1)
        
        diff = target_dt - now
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        
        return hours, minutes
    
    @staticmethod
    def is_time_between(start_time: time, end_time: time, check_time: time = None) -> bool:
        """Check if time is between start and end times"""
        if check_time is None:
            check_time = TimeUtils.get_current_time().time()
        
        if start_time <= end_time:
            return start_time <= check_time <= end_time
        else:
            #跨越午夜
            return check_time >= start_time or check_time <= end_time
    
    @staticmethod
    def get_next_prayer_time(prayer_times: Dict[str, Dict]) -> Optional[Dict]:
        """Get next prayer time from prayer times dictionary"""
        now = TimeUtils.get_current_time()
        current_time = now.time()
        
        next_prayer = None
        min_diff = float('inf')
        
        for prayer_name, prayer_data in prayer_times.items():
            prayer_time = time(
                hour=prayer_data["hour"],
                minute=prayer_data["minute"]
            )
            
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
                    "time": prayer_time,
                    "minutes_left": diff // 60
                }
        
        return next_prayer
    
    @staticmethod
    def add_days(dt: datetime, days: int) -> datetime:
        """Add days to datetime"""
        return dt + timedelta(days=days)
    
    @staticmethod
    def subtract_days(dt: datetime, days: int) -> datetime:
        """Subtract days from datetime"""
        return dt - timedelta(days=days)
    
    @staticmethod
    def get_weekday_name(dt: datetime) -> str:
        """Get weekday name in Bangla"""
        weekdays = {
            0: "সোমবার",
            1: "মঙ্গলবার",
            2: "বুধবার",
            3: "বৃহস্পতিবার",
            4: "শুক্রবার",
            5: "শনিবার",
            6: "রবিবার"
        }
        
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        
        bd_time = dt.astimezone(TimeUtils.BANGLADESH_TZ)
        return weekdays.get(bd_time.weekday(), "")
    
    @staticmethod
    def get_month_name(dt: datetime) -> str:
        """Get month name in Bangla"""
        months = {
            1: "জানুয়ারি",
            2: "ফেব্রুয়ারি",
            3: "মার্চ",
            4: "এপ্রিল",
            5: "মে",
            6: "জুন",
            7: "জুলাই",
            8: "আগস্ট",
            9: "সেপ্টেম্বর",
            10: "অক্টোবর",
            11: "নভেম্বর",
            12: "ডিসেম্বর"
        }
        
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        
        bd_time = dt.astimezone(TimeUtils.BANGLADESH_TZ)
        return months.get(bd_time.month, "")
    
    @staticmethod
    def get_current_season() -> str:
        """Get current season in Bangladesh"""
        month = TimeUtils.get_current_time().month
        
        if 3 <= month <= 5:
            return "গ্রীষ্মকাল"
        elif 6 <= month <= 9:
            return "বর্ষাকাল"
        elif 10 <= month <= 11:
            return "শরৎকাল"
        else:
            return "শীতকাল"
    
    @staticmethod
    def calculate_age(birth_date: datetime) -> int:
        """Calculate age from birth date"""
        today = TimeUtils.get_current_time()
        
        age = today.year - birth_date.year
        
        # Check if birthday has occurred this year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
        
        return age