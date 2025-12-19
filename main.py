# main.py
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from config.settings import settings
from database.session import engine, Base, SessionLocal
from database.seed import seed_initial_data
from handlers import user_handlers, admin_handlers, payment_handlers, bot_creation, prayer_time
from services.scheduler import SchedulerService
from core.bot_factory import BotFactory
import middleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_DIR / 'bot_factory.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main application entry point"""
    try:
        logger.info("=" * 50)
        logger.info(f"Starting {settings.BOT_NAME} Bot Factory")
        logger.info("=" * 50)
        
        # Initialize database
        logger.info("Initializing database...")
        Base.metadata.create_all(bind=engine)
        
        # Seed initial data
        with SessionLocal() as db:
            seed_initial_data(db)
        
        # Initialize bot
        bot = Bot(token=settings.BOT_TOKEN, parse_mode=ParseMode.HTML)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Register middleware
        dp.update.middleware.register(middleware.LoggingMiddleware())
        dp.update.middleware.register(middleware.ThrottlingMiddleware())
        
        # Register routers
        dp.include_router(user_handlers.router)
        dp.include_router(admin_handlers.router)
        dp.include_router(payment_handlers.router)
        dp.include_router(bot_creation.router)
        dp.include_router(prayer_time.router)
        
        # Initialize scheduler
        scheduler = SchedulerService()
        scheduler.start()
        
        # Start prayer time notifications
        prayer_handler = prayer_time.PrayerTimeHandler()
        await prayer_handler.schedule_prayer_notifications()
        
        # Set bot commands
        await set_bot_commands(bot)
        
        logger.info("Bot Factory is running...")
        logger.info(f"Bot: {settings.BOT_NAME}")
        logger.info(f"Owner: {settings.OWNER_ID}")
        logger.info("Press Ctrl+C to stop")
        
        # Start polling
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        logger.info("Bot Factory stopped")

async def set_bot_commands(bot: Bot):
    """Set bot commands menu"""
    commands = [
        {"command": "start", "description": "বট শুরু করুন"},
        {"command": "createbot", "description": "নতুন বট তৈরি করুন"},
        {"command": "mybots", "description": "আপনার বটগুলো দেখুন"},
        {"command": "buyplan", "description": "প্ল্যান কিনুন"},
        {"command": "myplan", "description": "আপনার প্ল্যান দেখুন"},
        {"command": "payment", "description": "পেমেন্ট তথ্য"},
        {"command": "help", "description": "হেল্প গাইড"},
        {"command": "support", "description": "সাপোর্টে যোগাযোগ"},
        {"command": "info", "description": "বট তথ্য"},
        {"command": "prayertimes", "description": "আজানের সময়"}
    ]
    
    await bot.set_my_commands(commands)
    logger.info("Bot commands set successfully")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot Factory stopped by user")
    except Exception as e:
        logger.error(f"Application error: {e}")