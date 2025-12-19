# utils/validators.py
import re
from typing import Optional, Tuple

def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
    """Validate Bangladeshi phone number"""
    if not phone:
        return False, "Phone number is required"
    
    # Remove any spaces or special characters
    phone = re.sub(r'[^\d]', '', phone)
    
    # Check length
    if len(phone) != 11:
        return False, "Phone number must be 11 digits"
    
    # Check if starts with 01
    if not phone.startswith('01'):
        return False, "Phone number must start with 01"
    
    # Check if valid operator
    operators = ['3', '4', '5', '6', '7', '8', '9']
    if phone[2] not in operators:
        return False, "Invalid operator code"
    
    return True, phone

def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """Validate email address"""
    if not email:
        return False, "Email is required"
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    return True, email.lower()

def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """Validate URL"""
    if not url:
        return False, "URL is required"
    
    pattern = r'^(https?://)?(www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(/\S*)?$'
    
    if not re.match(pattern, url):
        return False, "Invalid URL format"
    
    return True, url

def validate_bot_token(token: str) -> Tuple[bool, Optional[str]]:
    """Validate Telegram bot token"""
    if not token:
        return False, "Bot token is required"
    
    pattern = r'^\d{9,10}:[A-Za-z0-9_-]{35}$'
    
    if not re.match(pattern, token):
        return False, "Invalid bot token format"
    
    return True, token

def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """Validate Telegram username"""
    if not username:
        return False, "Username is required"
    
    pattern = r'^[a-zA-Z0-9_]{5,32}$'
    
    if not re.match(pattern, username):
        return False, "Username must be 5-32 characters (letters, numbers, underscore)"
    
    return True, username.lower()

def validate_password(password: str, min_length: int = 6) -> Tuple[bool, Optional[str]]:
    """Validate password"""
    if not password:
        return False, "Password is required"
    
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters"
    
    # Check for at least one letter and one number
    if not re.search(r'[a-zA-Z]', password):
        return False, "Password must contain at least one letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, None

def validate_amount(amount_str: str) -> Tuple[bool, Optional[float]]:
    """Validate amount"""
    try:
        amount = float(amount_str)
        
        if amount <= 0:
            return False, None
        
        if amount > 1000000:  # 1 million
            return False, None
        
        return True, amount
    except:
        return False, None

def validate_date(date_str: str, format_str: str = "%Y-%m-%d") -> Tuple[bool, Optional[str]]:
    """Validate date string"""
    try:
        from datetime import datetime
        datetime.strptime(date_str, format_str)
        return True, date_str
    except:
        return False, None

def validate_time(time_str: str) -> Tuple[bool, Optional[str]]:
    """Validate time string (HH:MM)"""
    pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
    
    if not re.match(pattern, time_str):
        return False, None
    
    return True, time_str

def validate_json(json_str: str) -> Tuple[bool, Optional[dict]]:
    """Validate JSON string"""
    try:
        import json
        data = json.loads(json_str)
        return True, data
    except:
        return False, None

def validate_file_extension(filename: str, allowed_extensions: list) -> Tuple[bool, Optional[str]]:
    """Validate file extension"""
    if not filename:
        return False, "Filename is required"
    
    extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ""
    
    if not extension:
        return False, "File must have an extension"
    
    if extension not in allowed_extensions:
        return False, f"File extension must be one of: {', '.join(allowed_extensions)}"
    
    return True, extension