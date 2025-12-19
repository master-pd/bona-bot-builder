# core/payment_handler.py
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from aiogram.types import Message, PhotoSize
from database import crud
from database.session import get_db
from config.settings import settings
from config.constants import Constants
import shutil

logger = logging.getLogger(__name__)

class PaymentHandler:
    def __init__(self):
        self.proof_dir = settings.PROOF_DIR
        self.proof_dir.mkdir(parents=True, exist_ok=True)
    
    async def handle_payment_proof(self, message: Message, user_id: int, 
                                  plan_type: str, amount: float, 
                                  method: str, transaction_id: str,
                                  sender_number: str = None) -> Dict[str, Any]:
        """Handle payment proof submission"""
        try:
            # Save proof photo if exists
            proof_path = None
            if message.photo:
                proof_path = await self.save_proof_photo(message, user_id, transaction_id)
            
            # Create payment record
            with next(get_db()) as db:
                payment = crud.create_payment(
                    db=db,
                    user_id=user_id,
                    amount=amount,
                    method=method,
                    transaction_id=transaction_id,
                    sender_number=sender_number,
                    proof_image=proof_path
                )
                
                # Create subscription
                user = crud.get_user(db, user_id)
                if user:
                    # Get user's active bot
                    user_bots = crud.get_user_bots(db, user.id)
                    active_bots = [b for b in user_bots if b.status == "pending"]
                    
                    if active_bots:
                        bot = active_bots[0]
                        subscription = crud.create_subscription(
                            db=db,
                            user_id=user.id,
                            bot_id=bot.id,
                            plan_type=plan_type,
                            amount=amount
                        )
                        
                        # Send notification to owner
                        await self.notify_owner(payment, subscription, user)
                        
                        return {
                            "success": True,
                            "payment_id": payment.id,
                            "subscription_id": subscription.id,
                            "message": "পেমেন্ট প্রুফ সাবমিট করা হয়েছে। মালিক ভেরিফাই করবেন।"
                        }
            
            return {
                "success": False,
                "message": "পেমেন্ট সাবমিট করতে সমস্যা হয়েছে।"
            }
            
        except Exception as e:
            logger.error(f"Error handling payment proof: {e}")
            return {
                "success": False,
                "message": f"এরর: {str(e)}"
            }
    
    async def save_proof_photo(self, message: Message, user_id: int, 
                              transaction_id: str) -> str:
        """Save payment proof photo"""
        try:
            # Get largest photo
            photo: PhotoSize = message.photo[-1]
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"proof_{user_id}_{transaction_id}_{timestamp}.jpg"
            filepath = self.proof_dir / filename
            
            # Download photo
            file = await message.bot.get_file(photo.file_id)
            await message.bot.download_file(file.file_path, filepath)
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error saving proof photo: {e}")
            return ""
    
    async def notify_owner(self, payment, subscription, user):
        """Notify owner about new payment"""
        try:
            # This would send notification to owner's Telegram
            # For now, just log
            logger.info(f"New payment: User {user.telegram_id}, "
                       f"Amount: {payment.amount}, "
                       f"Transaction: {payment.transaction_id}")
            
            # In actual implementation, send message to owner
            # await self.send_owner_notification(payment, subscription, user)
            
        except Exception as e:
            logger.error(f"Error notifying owner: {e}")
    
    def verify_payment(self, payment_id: int, verified_by: int, 
                      status: str, notes: str = None) -> bool:
        """Verify or reject payment"""
        try:
            with next(get_db()) as db:
                payment = crud.get_payment(db, payment_id)
                if not payment:
                    return False
                
                # Update payment status
                crud.update_payment_status(
                    db=db,
                    payment_id=payment_id,
                    status=status,
                    verified_by=verified_by,
                    notes=notes
                )
                
                # If verified, also verify subscription
                if status == "verified":
                    subscription = db.query(models.Subscription).filter(
                        models.Subscription.payment_id == payment_id
                    ).first()
                    
                    if subscription:
                        crud.verify_subscription(
                            db=db,
                            subscription_id=subscription.id,
                            verified_by=verified_by
                        )
                
                return True
                
        except Exception as e:
            logger.error(f"Error verifying payment: {e}")
            return False
    
    def get_pending_payments(self) -> List[Dict[str, Any]]:
        """Get all pending payments"""
        try:
            with next(get_db()) as db:
                payments = crud.get_pending_payments(db)
                
                result = []
                for payment in payments:
                    user = crud.get_user_by_id(db, payment.user_id)
                    result.append({
                        "payment_id": payment.id,
                        "user_id": user.telegram_id if user else None,
                        "username": user.username if user else None,
                        "amount": payment.amount,
                        "method": payment.method,
                        "transaction_id": payment.transaction_id,
                        "sender_number": payment.sender_number,
                        "proof_image": payment.proof_image,
                        "created_at": payment.created_at
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Error getting pending payments: {e}")
            return []
    
    def get_payment_stats(self) -> Dict[str, Any]:
        """Get payment statistics"""
        try:
            with next(get_db()) as db:
                total_payments = db.query(models.Payment).count()
                verified_payments = db.query(models.Payment).filter(
                    models.Payment.status == "verified"
                ).count()
                pending_payments = db.query(models.Payment).filter(
                    models.Payment.status == "pending"
                ).count()
                
                total_amount = db.query(func.sum(models.Payment.amount)).filter(
                    models.Payment.status == "verified"
                ).scalar() or 0
                
                today_amount = crud.get_today_payments(db)
                
                return {
                    "total_payments": total_payments,
                    "verified_payments": verified_payments,
                    "pending_payments": pending_payments,
                    "total_amount": total_amount,
                    "today_amount": today_amount
                }
                
        except Exception as e:
            logger.error(f"Error getting payment stats: {e}")
            return {}