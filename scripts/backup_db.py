# scripts/backup_db.py
#!/usr/bin/env python3
"""
Database backup script for BONA Bot Builder
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from services.encryption import EncryptionService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def backup_database():
    """Backup database file"""
    try:
        logger.info("Starting database backup...")
        
        # Source database file
        if settings.USE_POSTGRES:
            logger.info("PostgreSQL database - manual backup required")
            return True
        
        db_path = Path("database/bona.db")
        if not db_path.exists():
            logger.error(f"Database file not found: {db_path}")
            return False
        
        # Create backup directory
        backup_dir = settings.BACKUP_DIR
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"bona_backup_{timestamp}.db"
        backup_path = backup_dir / backup_name
        
        # Copy database file
        shutil.copy2(db_path, backup_path)
        logger.info(f"Database backed up to: {backup_path}")
        
        # Encrypt backup
        encryption = EncryptionService()
        encrypted_backup = backup_path.with_suffix('.db.enc')
        
        if encryption.encrypt_file(str(backup_path), str(encrypted_backup)):
            # Remove unencrypted backup
            backup_path.unlink()
            logger.info(f"Encrypted backup created: {encrypted_backup}")
        else:
            logger.warning("Failed to encrypt backup, keeping unencrypted version")
        
        # Clean old backups (keep last 7 days)
        cleanup_old_backups(backup_dir)
        
        logger.info("Database backup completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error backing up database: {e}")
        return False

def cleanup_old_backups(backup_dir: Path, days_to_keep: int = 7):
    """Clean up old backup files"""
    try:
        cutoff_date = datetime.now().timestamp() - (days_to_keep * 86400)
        
        for backup_file in backup_dir.glob("*.db.enc"):
            if backup_file.stat().st_mtime < cutoff_date:
                backup_file.unlink()
                logger.info(f"Removed old backup: {backup_file.name}")
    
    except Exception as e:
        logger.error(f"Error cleaning up old backups: {e}")

if __name__ == "__main__":
    success = backup_database()
    if success:
        print("✅ Database backup completed successfully!")
        sys.exit(0)
    else:
        print("❌ Database backup failed!")
        sys.exit(1)