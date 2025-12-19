# utils/helpers.py
import re
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import pytz

def format_date(date_obj: datetime, format_str: str = "%d %b %Y %I:%M %p") -> str:
    """Format datetime object to string"""
    if not date_obj:
        return ""
    
    # Convert to Bangladesh time
    bd_tz = pytz.timezone('Asia/Dhaka')
    if date_obj.tzinfo is None:
        date_obj = pytz.utc.localize(date_obj)
    
    bd_time = date_obj.astimezone(bd_tz)
    return bd_time.strftime(format_str)

def format_currency(amount: float, currency: str = "৳") -> str:
    """Format currency amount"""
    try:
        if amount.is_integer():
            return f"{currency}{int(amount):,}"
        else:
            return f"{currency}{amount:,.2f}"
    except:
        return f"{currency}{amount}"

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def generate_random_id(length: int = 8) -> str:
    """Generate random ID"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=length))

def calculate_time_remaining(end_date: datetime) -> Dict[str, Any]:
    """Calculate time remaining until end date"""
    if not end_date:
        return {"days": 0, "hours": 0, "minutes": 0, "total_seconds": 0}
    
    now = datetime.now(pytz.utc)
    if end_date.tzinfo is None:
        end_date = pytz.utc.localize(end_date)
    
    if end_date < now:
        return {"days": 0, "hours": 0, "minutes": 0, "total_seconds": 0}
    
    diff = end_date - now
    
    return {
        "days": diff.days,
        "hours": diff.seconds // 3600,
        "minutes": (diff.seconds % 3600) // 60,
        "total_seconds": diff.total_seconds()
    }

def is_valid_telegram_id(user_id: int) -> bool:
    """Check if Telegram ID is valid"""
    return 100000000 <= user_id <= 9999999999

def sanitize_filename(filename: str) -> str:
    """Sanitize filename"""
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1)
        filename = name[:255 - len(ext) - 1] + '.' + ext
    
    return filename

def parse_duration(duration_str: str) -> Optional[timedelta]:
    """Parse duration string (e.g., '30d', '2h', '15m')"""
    try:
        duration_str = duration_str.lower().strip()
        
        if duration_str.endswith('d'):
            days = int(duration_str[:-1])
            return timedelta(days=days)
        elif duration_str.endswith('h'):
            hours = int(duration_str[:-1])
            return timedelta(hours=hours)
        elif duration_str.endswith('m'):
            minutes = int(duration_str[:-1])
            return timedelta(minutes=minutes)
        else:
            # Try to parse as number of days
            days = int(duration_str)
            return timedelta(days=days)
    except:
        return None

def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """Merge two dictionaries (dict2 overwrites dict1)"""
    result = dict1.copy()
    result.update(dict2)
    return result

def get_file_extension(filename: str) -> str:
    """Get file extension"""
    return filename.rsplit('.', 1)[-1].lower() if '.' in filename else ""

def human_readable_size(size_bytes: int) -> str:
    """Convert bytes to human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def generate_password(length: int = 12) -> str:
    """Generate random password"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(random.choices(characters, k=length))
    
    # Ensure at least one of each type
    if not any(c.islower() for c in password):
        password = password[:-1] + random.choice(string.ascii_lowercase)
    if not any(c.isupper() for c in password):
        password = password[:-1] + random.choice(string.ascii_uppercase)
    if not any(c.isdigit() for c in password):
        password = password[:-1] + random.choice(string.digits)
    
    return password