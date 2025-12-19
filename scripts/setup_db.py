# scripts/setup_db.py
#!/usr/bin/env python3
"""
Database setup script for BONA Bot Builder
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.session import engine, Base
from database.seed import seed_initial_data
from database.session import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """Setup database tables and seed initial data"""
    try:
        logger.info("Setting up database...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")
        
        # Seed initial data
        with SessionLocal() as db:
            seed_initial_data(db)
        
        logger.info("Database setup completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        return False

if __name__ == "__main__":
    success = setup_database()
    if success:
        print("✅ Database setup completed successfully!")
        sys.exit(0)
    else:
        print("❌ Database setup failed!")
        sys.exit(1)