# core/admin_panel.py
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from aiogram import types
from database import crud, models
from database.session import get_db
from config.settings import settings
from config.security import Security
from services.broadcast import BroadcastService

logger = logging.getLogger(__name__)

class AdminPanel:
    def __init__(self):
        self.broadcast_service = BroadcastService()
    
    def verify_owner(self, user_id: int, password: str) -> bool:
        """Verify owner identity"""
        # Hidden password verification
        correct_password = Security.verify_password(password, 
            Security.hash_password("rana2005"))
        
        return user_id == settings.OWNER_ID and correct_password
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        try:
            with next(get_db()) as db:
                total_users = crud.get_user_count(db)
                total_bots = crud.get_bot_count(db)
                active_bots = crud.get_active_bot_count(db)
                
                # Payment stats
                payment_stats = {
                    "total": db.query(models.Payment).count(),
                    "verified": db.query(models.Payment).filter(
                        models.Payment.status == "verified"
                    ).count(),
                    "pending": db.query(models.Payment).filter(
                        models.Payment.status == "pending"
                    ).count(),
                    "rejected": db.query(models.Payment).filter(
                        models.Payment.status == "rejected"
                    ).count()
                }
                
                # Bot status stats
                bot_stats = {
                    "active": db.query(models.Bot).filter(
                        models.Bot.status == "active"
                    ).count(),
                    "pending": db.query(models.Bot).filter(
                        models.Bot.status == "pending"
                    ).count(),
                    "inactive": db.query(models.Bot).filter(
                        models.Bot.status == "inactive"
                    ).count(),
                    "suspended": db.query(models.Bot).filter(
                        models.Bot.status == "suspended"
                    ).count()
                }
                
                # Recent activity
                recent_payments = db.query(models.Payment).order_by(
                    models.Payment.created_at.desc()
                ).limit(10).all()
                
                recent_bots = db.query(models.Bot).order_by(
                    models.Bot.created_at.desc()
                ).limit(10).all()
                
                return {
                    "total_users": total_users,
                    "total_bots": total_bots,
                    "active_bots": active_bots,
                    "payment_stats": payment_stats,
                    "bot_stats": bot_stats,
                    "recent_payments": [
                        {
                            "id": p.id,
                            "user_id": p.user_id,
                            "amount": p.amount,
                            "status": p.status,
                            "created_at": p.created_at
                        }
                        for p in recent_payments
                    ],
                    "recent_bots": [
                        {
                            "id": b.id,
                            "name": b.bot_name,
                            "owner_id": b.owner_id,
                            "status": b.status,
                            "created_at": b.created_at
                        }
                        for b in recent_bots
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return {}
    
    def approve_bot(self, bot_id: int, verified_by: int) -> bool:
        """Approve pending bot"""
        try:
            with next(get_db()) as db:
                bot = crud.update_bot_status(
                    db=db,
                    bot_id=bot_id,
                    status="active",
                    verified_by=verified_by
                )
                return bot is not None
        except Exception as e:
            logger.error(f"Error approving bot: {e}")
            return False
    
    def reject_bot(self, bot_id: int, reason: str = None) -> bool:
        """Reject pending bot"""
        try:
            with next(get_db()) as db:
                bot = crud.update_bot_status(
                    db=db,
                    bot_id=bot_id,
                    status="rejected"
                )
                
                # Send notification to user
                if bot:
                    user = crud.get_user_by_id(db, bot.owner_id)
                    # In actual implementation, send Telegram message
                    
                return bot is not None
        except Exception as e:
            logger.error(f"Error rejecting bot: {e}")
            return False
    
    def block_user(self, user_id: int, reason: str = None) -> bool:
        """Block user"""
        try:
            with next(get_db()) as db:
                user = crud.get_user(db, user_id)
                if not user:
                    return False
                
                user.is_blocked = True
                user.block_reason = reason
                
                # Block all user's bots
                user_bots = crud.get_user_bots(db, user.id)
                for bot in user_bots:
                    bot.status = "suspended"
                
                db.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error blocking user: {e}")
            return False
    
    def unblock_user(self, user_id: int) -> bool:
        """Unblock user"""
        try:
            with next(get_db()) as db:
                user = crud.get_user(db, user_id)
                if not user:
                    return False
                
                user.is_blocked = False
                user.block_reason = None
                db.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error unblocking user: {e}")
            return False
    
    async def broadcast_message(self, message_text: str, 
                               message_type: str = "text") -> Dict[str, Any]:
        """Broadcast message to all users"""
        try:
            result = await self.broadcast_service.broadcast(
                message=message_text,
                message_type=message_type
            )
            
            return {
                "success": True,
                "sent": result.get("sent", 0),
                "failed": result.get("failed", 0),
                "total": result.get("total", 0)
            }
            
        except Exception as e:
            logger.error(f"Error broadcasting message: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_system_logs(self, limit: int = 100) -> List[str]:
        """Get system logs"""
        try:
            log_file = settings.LOG_DIR / "bot_factory.log"
            if not log_file.exists():
                return []
            
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return lines[-limit:]
                
        except Exception as e:
            logger.error(f"Error reading logs: {e}")
            return []
    
    def reset_system(self, confirm: bool = False) -> bool:
        """Reset system (dangerous operation)"""
        if not confirm:
            return False
        
        try:
            # This would reset the system
            # For now, just log
            logger.warning("SYSTEM RESET REQUESTED")
            
            # In actual implementation:
            # 1. Backup database
            # 2. Clear temporary data
            # 3. Reset configurations
            
            return True
            
        except Exception as e:
            logger.error(f"Error resetting system: {e}")
            return False