# config/constants.py
class Constants:
    # User Status
    STATUS_ACTIVE = "active"
    STATUS_INACTIVE = "inactive"
    STATUS_BLOCKED = "blocked"
    STATUS_PENDING = "pending"
    
    # Bot Status
    BOT_ACTIVE = "active"
    BOT_INACTIVE = "inactive"
    BOT_PENDING = "pending"
    BOT_SUSPENDED = "suspended"
    
    # Payment Status
    PAYMENT_PENDING = "pending"
    PAYMENT_VERIFIED = "verified"
    PAYMENT_REJECTED = "rejected"
    PAYMENT_CANCELLED = "cancelled"
    
    # Payment Methods
    PAYMENT_BKASH = "bkash"
    PAYMENT_NAGAD = "nagad"
    PAYMENT_ROCKET = "rocket"
    
    # Plan Types
    PLAN_TRIAL = "trial"
    PLAN_BASIC = "60"
    PLAN_STANDARD = "100"
    PLAN_PREMIUM = "400"
    
    # Message Types
    MSG_TEXT = "text"
    MSG_VOICE = "voice"
    MSG_IMAGE = "image"
    MSG_VIDEO = "video"
    MSG_DOCUMENT = "document"
    
    # AI Response Types
    RESPONSE_NORMAL = "normal"
    RESPONSE_GHOST = "ghost"
    RESPONSE_CLONE = "clone"
    
    # Learning Status
    LEARNING_PENDING = "pending"
    LEARNING_TRAINED = "trained"
    LEARNING_EXPIRED = "expired"
    
    # Security Levels
    SECURITY_LOW = "low"
    SECURITY_MEDIUM = "medium"
    SECURITY_HIGH = "high"
    
    # Time Constants
    SECOND = 1
    MINUTE = 60
    HOUR = 3600
    DAY = 86400
    
    # Limits
    MAX_MESSAGES_PER_DAY = 1000
    MAX_BOTS_PER_USER = 5
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB