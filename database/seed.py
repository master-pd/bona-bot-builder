# database/seed.py
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from config.security import Security
from . import models
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

def seed_owner(db: Session):
    """Seed owner account"""
    # Check if owner already exists
    existing_owner = db.query(models.User).filter(
        models.User.telegram_id == settings.OWNER_ID
    ).first()
    
    if existing_owner:
        logger.info("Owner already exists in database")
        return existing_owner
    
    # Create owner user
    owner = models.User(
        telegram_id=settings.OWNER_ID,
        username=settings.OWNER_USERNAME,
        first_name="RANA",
        last_name="(MASTER 🪓)",
        phone=settings.OWNER_PHONE,
        email=settings.OWNER_EMAIL,
        plan_type="400",  # Premium plan
        plan_start=datetime.now(),
        plan_end=datetime.now() + timedelta(days=3650),  # 10 years
        is_active=True,
        credits=1000000,
        trial_used=True
    )
    
    db.add(owner)
    db.commit()
    db.refresh(owner)
    
    logger.info(f"Owner seeded successfully: {owner.telegram_id}")
    return owner

def seed_initial_data(db: Session):
    """Seed initial database data"""
    try:
        # Seed owner
        owner = seed_owner(db)
        
        # Create default plans in database if needed
        # (Plans are managed in settings, but we can create reference records)
        
        logger.info("Database seeding completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        return False