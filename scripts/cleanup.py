# scripts/cleanup.py
#!/usr/bin/env python3
"""
Cleanup script for BONA Bot Builder
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import shutil
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from database.session import SessionLocal
import database.models as models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_system():
    """Clean up old data and temporary files"""
    try:
        logger.info("Starting system cleanup...")
        
        # Cleanup expired trials
        cleanup_expired_trials()
        
        # Cleanup expired plans
        cleanup_expired_plans()
        
        # Cleanup old conversations
        cleanup_old_conversations()
        
        # Cleanup old logs
        cleanup_old_logs()
        
        # Cleanup temporary files
        cleanup_temp_files()
        
        logger.info("System cleanup completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return False

def cleanup_expired_trials():
    """Clean up expired trial users"""
    try:
        with SessionLocal() as db:
            # Find users with expired trials
            expired_users = db.query(models.User).filter(
                models.User.plan_type == "trial",
                models.User.trial_end < datetime.now()
            ).all()
            
            for user in expired_users:
                # Mark trial as expired
                user.plan_type = "expired"
                user.is_active = False
                
                # Deactivate user's bots
                user_bots = db.query(models.Bot).filter(
                    models.Bot.owner_id == user.id
                ).all()
                
                for bot in user_bots:
                    bot.status = "inactive"
            
            db.commit()
            logger.info(f"Cleaned up {len(expired_users)} expired trials")
    
    except Exception as e:
        logger.error(f"Error cleaning up expired trials: {e}")

def cleanup_expired_plans():
    """Clean up expired plans"""
    try:
        with SessionLocal() as db:
            # Find users with expired plans
            expired_users = db.query(models.User).filter(
                models.User.plan_end < datetime.now(),
                models.User.plan_type != "trial",
                models.User.is_active == True
            ).all()
            
            for user in expired_users:
                user.is_active = False
                
                # Deactivate user's bots
                user_bots = db.query(models.Bot).filter(
                    models.Bot.owner_id == user.id
                ).all()
                
                for bot in user_bots:
                    bot.status = "inactive"
            
            db.commit()
            logger.info(f"Cleaned up {len(expired_users)} expired plans")
    
    except Exception as e:
        logger.error(f"Error cleaning up expired plans: {e}")

def cleanup_old_conversations():
    """Clean up old conversations"""
    try:
        with SessionLocal() as db:
            # Delete conversations older than 30 days
            cutoff_date = datetime.now() - timedelta(days=30)
            
            deleted_count = db.query(models.Conversation).filter(
                models.Conversation.timestamp < cutoff_date
            ).delete()
            
            db.commit()
            logger.info(f"Cleaned up {deleted_count} old conversations")
    
    except Exception as e:
        logger.error(f"Error cleaning up old conversations: {e}")

def cleanup_old_logs():
    """Clean up old log files"""
    try:
        log_dir = settings.LOG_DIR
        if not log_dir.exists():
            return
        
        cutoff_date = datetime.now() - timedelta(days=7)
        
        for log_file in log_dir.glob("*.log"):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                log_file.unlink()
                logger.info(f"Removed old log file: {log_file.name}")
    
    except Exception as e:
        logger.error(f"Error cleaning up old logs: {e}")

def cleanup_temp_files():
    """Clean up temporary files"""
    try:
        temp_dirs = [
            settings.UPLOAD_DIR,
            settings.PROOF_DIR
        ]
        
        cutoff_date = datetime.now() - timedelta(days=3)
        
        for temp_dir in temp_dirs:
            if not temp_dir.exists():
                continue
            
            for temp_file in temp_dir.glob("*"):
                if temp_file.is_file() and temp_file.stat().st_mtime < cutoff_date.timestamp():
                    temp_file.unlink()
        
        logger.info("Cleaned up temporary files")
    
    except Exception as e:
        logger.error(f"Error cleaning up temp files: {e}")

if __name__ == "__main__":
    success = cleanup_system()
    if success:
        print("✅ System cleanup completed successfully!")
        sys.exit(0)
    else:
        print("❌ System cleanup failed!")
        sys.exit(1)