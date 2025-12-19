# scripts/monitor.py
#!/usr/bin/env python3
"""
System monitoring script for BONA Bot Builder
"""

import sys
import psutil
from pathlib import Path
from datetime import datetime
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from database.session import SessionLocal
import database.models as models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def monitor_system():
    """Monitor system status and resources"""
    try:
        logger.info("Starting system monitoring...")
        
        status = {
            "timestamp": datetime.now().isoformat(),
            "system": check_system_resources(),
            "database": check_database_status(),
            "services": check_services_status(),
            "storage": check_storage_usage()
        }
        
        # Log status
        log_status(status)
        
        # Check for issues
        issues = check_for_issues(status)
        
        if issues:
            logger.warning(f"Found {len(issues)} issues")
            for issue in issues:
                logger.warning(f"Issue: {issue}")
        
        logger.info("System monitoring completed")
        return status
        
    except Exception as e:
        logger.error(f"Error during monitoring: {e}")
        return None

def check_system_resources():
    """Check system resources"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available": memory.available / (1024 ** 3),  # GB
            "disk_percent": disk.percent,
            "disk_free": disk.free / (1024 ** 3)  # GB
        }
    except Exception as e:
        logger.error(f"Error checking system resources: {e}")
        return {}

def check_database_status():
    """Check database status"""
    try:
        with SessionLocal() as db:
            # Check connection
            db.execute("SELECT 1")
            
            # Get counts
            user_count = db.query(models.User).count()
            bot_count = db.query(models.Bot).count()
            active_bot_count = db.query(models.Bot).filter(
                models.Bot.status == "active"
            ).count()
            
            return {
                "status": "connected",
                "user_count": user_count,
                "bot_count": bot_count,
                "active_bot_count": active_bot_count
            }
    
    except Exception as e:
        logger.error(f"Error checking database status: {e}")
        return {"status": "disconnected", "error": str(e)}

def check_services_status():
    """Check services status"""
    try:
        # Check if required directories exist
        required_dirs = [
            settings.LOG_DIR,
            settings.UPLOAD_DIR,
            settings.PROOF_DIR,
            settings.BACKUP_DIR
        ]
        
        dir_status = {}
        for directory in required_dirs:
            dir_status[directory.name] = directory.exists()
        
        # Check log files
        log_files = list(settings.LOG_DIR.glob("*.log"))
        
        return {
            "directories": dir_status,
            "log_files": len(log_files),
            "has_errors": check_for_errors()
        }
    
    except Exception as e:
        logger.error(f"Error checking services status: {e}")
        return {}

def check_storage_usage():
    """Check storage usage"""
    try:
        storage_info = {}
        
        # Check each directory size
        directories = [
            ("database", Path("database")),
            ("logs", settings.LOG_DIR),
            ("uploads", settings.UPLOAD_DIR),
            ("proofs", settings.PROOF_DIR),
            ("backups", settings.BACKUP_DIR)
        ]
        
        for name, directory in directories:
            if directory.exists():
                size = get_directory_size(directory) / (1024 ** 2)  # MB
                storage_info[name] = f"{size:.2f} MB"
            else:
                storage_info[name] = "Not found"
        
        return storage_info
    
    except Exception as e:
        logger.error(f"Error checking storage usage: {e}")
        return {}

def get_directory_size(directory: Path) -> int:
    """Get directory size in bytes"""
    total_size = 0
    for file in directory.rglob('*'):
        if file.is_file():
            total_size += file.stat().st_size
    return total_size

def check_for_errors():
    """Check for errors in log files"""
    try:
        error_keywords = ["ERROR", "CRITICAL", "FAILED", "EXCEPTION"]
        
        for log_file in settings.LOG_DIR.glob("*.log"):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for keyword in error_keywords:
                        if keyword in content:
                            return True
            except:
                continue
        
        return False
    
    except Exception as e:
        logger.error(f"Error checking for errors: {e}")
        return False

def check_for_issues(status: dict):
    """Check for system issues"""
    issues = []
    
    # Check CPU usage
    system = status.get("system", {})
    if system.get("cpu_percent", 0) > 90:
        issues.append(f"High CPU usage: {system['cpu_percent']}%")
    
    # Check memory usage
    if system.get("memory_percent", 0) > 90:
        issues.append(f"High memory usage: {system['memory_percent']}%")
    
    # Check disk usage
    if system.get("disk_percent", 0) > 90:
        issues.append(f"High disk usage: {system['disk_percent']}%")
    
    # Check database
    database = status.get("database", {})
    if database.get("status") != "connected":
        issues.append(f"Database disconnected: {database.get('error', 'Unknown error')}")
    
    # Check services
    services = status.get("services", {})
    if services.get("has_errors"):
        issues.append("Errors found in log files")
    
    return issues

def log_status(status: dict):
    """Log system status"""
    try:
        status_file = settings.LOG_DIR / "system_status.log"
        
        with open(status_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"System Status: {status['timestamp']}\n")
            f.write(f"{'='*50}\n\n")
            
            # System resources
            f.write("System Resources:\n")
            system = status.get("system", {})
            f.write(f"  CPU: {system.get('cpu_percent', 'N/A')}%\n")
            f.write(f"  Memory: {system.get('memory_percent', 'N/A')}%\n")
            f.write(f"  Disk: {system.get('disk_percent', 'N/A')}%\n\n")
            
            # Database
            f.write("Database:\n")
            database = status.get("database", {})
            f.write(f"  Status: {database.get('status', 'N/A')}\n")
            f.write(f"  Users: {database.get('user_count', 'N/A')}\n")
            f.write(f"  Bots: {database.get('bot_count', 'N/A')}\n")
            f.write(f"  Active Bots: {database.get('active_bot_count', 'N/A')}\n\n")
            
            # Storage
            f.write("Storage Usage:\n")
            storage = status.get("storage", {})
            for name, size in storage.items():
                f.write(f"  {name}: {size}\n")
        
        logger.info(f"Status logged to {status_file}")
    
    except Exception as e:
        logger.error(f"Error logging status: {e}")

if __name__ == "__main__":
    status = monitor_system()
    if status:
        print("✅ System monitoring completed successfully!")
        print(f"Timestamp: {status['timestamp']}")
        
        # Print summary
        system = status.get('system', {})
        print(f"CPU: {system.get('cpu_percent', 'N/A')}%")
        print(f"Memory: {system.get('memory_percent', 'N/A')}%")
        print(f"Disk: {system.get('disk_percent', 'N/A')}%")
        
        sys.exit(0)
    else:
        print("❌ System monitoring failed!")
        sys.exit(1)