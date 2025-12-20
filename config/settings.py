# config/settings.py
import os
from dotenv import load_dotenv
from pathlib import Path
import hashlib

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    # Owner Configuration - Hidden Password System
    OWNER_ID = 6454347745
    OWNER_USERNAME = "rana_editz_00"
    # Password is hidden and encrypted in database only
    OWNER_EMAIL = "ranaeditz333@gmail.com"
    OWNER_PHONE = "01847634486"
    
    # Payment Numbers
    PAYMENT_NUMBERS = ["01847634486"]
    
    # Bot Configuration
    BOT_NAME = "YOUR CRUSH ⟵o_0"
    BOT_USERNAME = os.getenv("BOT_USERNAME", "your_crush_bot")
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/bona.db")
    USE_POSTGRES = os.getenv("USE_POSTGRES", "false").lower() == "true"
    
    # Security Keys (Loaded from env or generated)
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
    if not ENCRYPTION_KEY:
        # Generate from owner info (hidden in source)
        secret_base = f"{OWNER_ID}{OWNER_PHONE}{OWNER_EMAIL}"
        ENCRYPTION_KEY = hashlib.sha256(secret_base.encode()).hexdigest()[:32]
    
    SALT = os.getenv("SALT")
    if not SALT:
        secret_salt = f"bona_{OWNER_ID}_{OWNER_PHONE[-4:]}"
        SALT = hashlib.sha256(secret_salt.encode()).hexdigest()[:16]
    
    # Security
    ALLOWED_IPS = ["127.0.0.1"]
    SESSION_TIMEOUT = 3600
    
    # Plans
    PLANS = {
        "60": {"days": 30, "price": 60, "name": "১ মাস"},
        "100": {"days": 60, "price": 100, "name": "২ মাস"},
        "400": {"days": 365, "price": 400, "name": "১ বছর"}
    }
    
    # Trial Settings
    TRIAL_DAYS = 3
    TRIAL_MESSAGES = 10
    
    # Paths
    LOG_DIR = BASE_DIR / "logs"
    UPLOAD_DIR = BASE_DIR / "storage" / "uploads"
    PROOF_DIR = BASE_DIR / "storage" / "proofs"
    BACKUP_DIR = BASE_DIR / "storage" / "backups"
    
    # Create directories
    for dir_path in [LOG_DIR, UPLOAD_DIR, PROOF_DIR, BACKUP_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Webhook (if using)
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
    
    # Admin Panel
    ADMIN_PANEL_PORT = int(os.getenv("ADMIN_PANEL_PORT", 8080))
    ADMIN_PANEL_HOST = os.getenv("ADMIN_PANEL_HOST", "0.0.0.0")

# config/settings.py ফাইলের শেষে এই লাইন যোগ করুন:
settings = Settings()
