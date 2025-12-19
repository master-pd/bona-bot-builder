# ghost_manager.py
import asyncio
import logging
from typing import Dict, List
from database import crud
from database.session import get_db
from core.ghost_bot import GhostBot

logger = logging.getLogger(__name__)

class GhostBotManager:
    def __init__(self):
        self.active_bots: Dict[int, GhostBot] = {}
        self.running = False
    
    async def start(self):
        """Start ghost bot manager"""
        try:
            self.running = True
            logger.info("Starting Ghost Bot Manager...")
            
            # Load and start all active bots
            await self.load_active_bots()
            
            # Start monitoring
            asyncio.create_task(self.monitor_bots())
            
            logger.info(f"Ghost Bot Manager started with {len(self.active_bots)} bots")
            
        except Exception as e:
            logger.error(f"Error starting Ghost Bot Manager: {e}")
    
    async def load_active_bots(self):
        """Load all active bots from database"""
        try:
            with next(get_db()) as db:
                active_bots = crud.get_active_bots(db)
                
                for bot in active_bots:
                    if bot.status == "active" and bot.bot_token:
                        await self.start_bot(bot)
                
                logger.info(f"Loaded {len(active_bots)} active bots")
                
        except Exception as e:
            logger.error(f"Error loading active bots: {e}")
    
    async def start_bot(self, bot):
        """Start individual ghost bot"""
        try:
            if bot.id in self.active_bots:
                logger.warning(f"Bot {bot.id} is already running")
                return
            
            # Create and start ghost bot
            ghost_bot = GhostBot(
                bot_token=bot.bot_token,
                bot_id=bot.id,
                admin_chat_id=bot.admin_chat_id
            )
            
            # Start in background
            asyncio.create_task(ghost_bot.start())
            
            # Store reference
            self.active_bots[bot.id] = ghost_bot
            
            logger.info(f"Started ghost bot {bot.id} ({bot.bot_name})")
            
        except Exception as e:
            logger.error(f"Error starting bot {bot.id}: {e}")
    
    async def stop_bot(self, bot_id: int):
        """Stop individual ghost bot"""
        try:
            if bot_id in self.active_bots:
                ghost_bot = self.active_bots[bot_id]
                await ghost_bot.stop()
                del self.active_bots[bot_id]
                logger.info(f"Stopped ghost bot {bot_id}")
                
        except Exception as e:
            logger.error(f"Error stopping bot {bot_id}: {e}")
    
    async def restart_bot(self, bot_id: int):
        """Restart ghost bot"""
        try:
            await self.stop_bot(bot_id)
            
            # Get bot from database
            with next(get_db()) as db:
                bot = crud.get_bot(db, bot_id)
                if bot and bot.status == "active":
                    await self.start_bot(bot)
            
        except Exception as e:
            logger.error(f"Error restarting bot {bot_id}: {e}")
    
    async def monitor_bots(self):
        """Monitor and manage bot status"""
        while self.running:
            try:
                with next(get_db()) as db:
                    # Get all active bots from database
                    db_active_bots = crud.get_active_bots(db)
                    db_active_ids = {bot.id for bot in db_active_bots}
                    
                    # Stop bots that are no longer active in database
                    for bot_id in list(self.active_bots.keys()):
                        if bot_id not in db_active_ids:
                            await self.stop_bot(bot_id)
                    
                    # Start bots that are active in database but not running
                    for bot in db_active_bots:
                        if bot.id not in self.active_bots:
                            await self.start_bot(bot)
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in bot monitor: {e}")
                await asyncio.sleep(30)
    
    async def get_bot_status(self, bot_id: int) -> Dict:
        """Get bot status"""
        try:
            if bot_id in self.active_bots:
                return {
                    "status": "running",
                    "bot_id": bot_id,
                    "in_manager": True
                }
            else:
                with next(get_db()) as db:
                    bot = crud.get_bot(db, bot_id)
                    if bot:
                        return {
                            "status": bot.status,
                            "bot_id": bot_id,
                            "in_manager": False,
                            "db_status": bot.status
                        }
            
            return {"status": "not_found", "bot_id": bot_id}
            
        except Exception as e:
            logger.error(f"Error getting bot status {bot_id}: {e}")
            return {"status": "error", "bot_id": bot_id, "error": str(e)}
    
    async def get_all_bot_statuses(self) -> List[Dict]:
        """Get status of all bots"""
        try:
            statuses = []
            
            # Get from active bots
            for bot_id, ghost_bot in self.active_bots.items():
                statuses.append({
                    "bot_id": bot_id,
                    "status": "running",
                    "in_memory": True
                })
            
            # Get from database
            with next(get_db()) as db:
                all_bots = db.query(models.Bot).all()
                for bot in all_bots:
                    if bot.id not in [s["bot_id"] for s in statuses]:
                        statuses.append({
                            "bot_id": bot.id,
                            "status": bot.status,
                            "in_memory": False
                        })
            
            return statuses
            
        except Exception as e:
            logger.error(f"Error getting all bot statuses: {e}")
            return []
    
    async def stop_all(self):
        """Stop all ghost bots"""
        try:
            logger.info("Stopping all ghost bots...")
            
            for bot_id in list(self.active_bots.keys()):
                await self.stop_bot(bot_id)
            
            self.running = False
            logger.info("All ghost bots stopped")
            
        except Exception as e:
            logger.error(f"Error stopping all bots: {e}")
    
    async def send_message_via_bot(self, bot_id: int, chat_id: int, text: str) -> bool:
        """Send message via specific bot"""
        try:
            if bot_id in self.active_bots:
                ghost_bot = self.active_bots[bot_id]
                return await ghost_bot.send_message_as_admin(chat_id, text)
            return False
        except Exception as e:
            logger.error(f"Error sending message via bot {bot_id}: {e}")
            return False

# Singleton instance
ghost_manager = GhostBotManager()

async def start_ghost_manager():
    """Start the ghost bot manager"""
    await ghost_manager.start()

async def stop_ghost_manager():
    """Stop the ghost bot manager"""
    await ghost_manager.stop_all()