# core/ghost_bot.py
import logging
import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
from database import crud, models
from database.session import get_db
from config.settings import settings
from config.constants import Constants
from core.ai_engine import AIEngine
from services.telegram_api import TelegramAPI
from services.encryption import EncryptionService
from utils.text_templates import TextTemplates
from utils.language import LanguageManager
import aiohttp

logger = logging.getLogger(__name__)

class GhostBot:
    def __init__(self, bot_token: str, bot_id: int, admin_chat_id: int):
        self.bot = Bot(token=bot_token, parse_mode=ParseMode.HTML)
        self.dp = Dispatcher()
        self.bot_id = bot_id
        self.admin_chat_id = admin_chat_id
        self.ai_engine = AIEngine()
        self.telegram_api = TelegramAPI()
        self.templates = TextTemplates()
        self.language_manager = LanguageManager()
        self.admin_profile = None
        self.is_cloning = False
        self.setup_handlers()
    
    async def load_admin_profile(self):
        """Load admin profile for cloning"""
        try:
            with next(get_db()) as db:
                bot = crud.get_bot(db, self.bot_id)
                if bot and bot.clone_profile:
                    self.admin_profile = bot.clone_profile
                    self.is_cloning = True
                    return True
                
                # Try to fetch from Telegram
                admin_user = await self.bot.get_chat(self.admin_chat_id)
                if admin_user:
                    self.admin_profile = {
                        "id": admin_user.id,
                        "username": admin_user.username,
                        "first_name": admin_user.first_name,
                        "last_name": admin_user.last_name,
                        "is_premium": getattr(admin_user, 'is_premium', False),
                        "language_code": getattr(admin_user, 'language_code', 'en')
                    }
                    
                    # Save to database
                    if bot:
                        bot.clone_profile = self.admin_profile
                        db.commit()
                    
                    self.is_cloning = True
                    return True
        except Exception as e:
            logger.error(f"Error loading admin profile: {e}")
        
        return False
    
    def setup_handlers(self):
        """Setup message handlers for ghost bot"""
        
        # Handle all private messages
        @self.dp.message(F.chat.type == "private")
        async def handle_private_message(message: Message):
            await self.handle_incoming_message(message)
        
        # Handle group messages if bot is added to group
        @self.dp.message(F.chat.type.in_({"group", "supergroup"}))
        async def handle_group_message(message: Message):
            if message.text and self.bot.username in message.text:
                await self.handle_mention(message)
        
        # Handle callback queries
        @self.dp.callback_query()
        async def handle_callback(callback: CallbackQuery):
            await self.handle_callback_query(callback)
    
    async def handle_incoming_message(self, message: Message):
        """Handle incoming private message"""
        try:
            user_id = message.from_user.id
            chat_id = message.chat.id
            message_text = message.text or message.caption or ""
            
            # Don't respond to self or admin
            if user_id == self.admin_chat_id or user_id == self.bot.id:
                return
            
            with next(get_db()) as db:
                # Check bot status
                bot = crud.get_bot(db, self.bot_id)
                if not bot or bot.status != "active":
                    return
                
                # Check subscription
                subscription = crud.get_active_subscription(db, self.bot_id)
                if not subscription:
                    # Check trial
                    if bot.plan_type == "trial" and bot.trial_expiry < datetime.now():
                        return
                
                # Get learning data
                learning = crud.get_learning(db, self.bot_id)
                
                # Generate response using AI
                context = {
                    "bot_id": self.bot_id,
                    "user_id": user_id,
                    "admin_id": self.admin_chat_id,
                    "message_text": message_text,
                    "message_type": "text",
                    "previous_context": learning.context_data if learning else {}
                }
                
                # Generate AI response
                ai_response = await self.ai_engine.generate_response(context)
                
                # Clone admin profile if enabled
                if bot.settings.get("profile_clone", True) and self.is_cloning:
                    # Send as admin (simulate admin typing and response)
                    await self.send_as_admin(message, ai_response)
                else:
                    # Send as bot
                    await message.answer(ai_response)
                
                # Save conversation
                crud.create_conversation(
                    db=db,
                    bot_id=self.bot_id,
                    from_user=user_id,
                    to_user=self.admin_chat_id,
                    message_text=message_text,
                    bot_response=ai_response,
                    is_ghost_mode=True
                )
                
                # Update learning
                if learning:
                    self.update_learning_patterns(learning, message_text, ai_response)
                
                # Update bot activity
                bot.last_active = datetime.now()
                bot.total_messages += 1
                db.commit()
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def send_as_admin(self, original_message: Message, response_text: str):
        """Send message as admin (profile cloning)"""
        try:
            # Simulate admin typing
            await self.bot.send_chat_action(
                chat_id=original_message.chat.id,
                action="typing"
            )
            
            # Add small delay for realism
            await asyncio.sleep(1)
            
            # Send response
            await original_message.answer(
                response_text,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Error sending as admin: {e}")
            # Fallback to normal send
            await original_message.answer(response_text)
    
    def update_learning_patterns(self, learning: models.Learning, 
                                 user_message: str, bot_response: str):
        """Update learning patterns from conversation"""
        try:
            user_patterns = learning.user_patterns or {}
            response_patterns = learning.response_patterns or {}
            context_data = learning.context_data or {}
            
            # Extract keywords from user message
            words = user_message.lower().split()
            for word in words:
                if len(word) > 3:  # Ignore short words
                    if word not in user_patterns:
                        user_patterns[word] = 1
                    else:
                        user_patterns[word] += 1
            
            # Extract patterns from bot response
            response_words = bot_response.lower().split()
            for word in response_words:
                if len(word) > 3:
                    if word not in response_patterns:
                        response_patterns[word] = 1
                    else:
                        response_patterns[word] += 1
            
            # Update context
            context_data["last_interaction"] = datetime.now().isoformat()
            context_data["total_interactions"] = context_data.get("total_interactions", 0) + 1
            
            # Update learning record
            learning.user_patterns = user_patterns
            learning.response_patterns = response_patterns
            learning.context_data = context_data
            learning.training_count += 1
            learning.last_trained = datetime.now()
            
        except Exception as e:
            logger.error(f"Error updating learning patterns: {e}")
    
    async def handle_mention(self, message: Message):
        """Handle bot mention in groups"""
        try:
            # Extract message without mention
            text = message.text or ""
            mention = f"@{self.bot.username}"
            
            if mention in text:
                query = text.replace(mention, "").strip()
                
                if query:
                    # Generate response
                    context = {
                        "bot_id": self.bot_id,
                        "user_id": message.from_user.id,
                        "admin_id": self.admin_chat_id,
                        "message_text": query,
                        "message_type": "group_mention",
                        "group_id": message.chat.id
                    }
                    
                    ai_response = await self.ai_engine.generate_response(context)
                    
                    # Reply in group
                    await message.reply(ai_response)
        
        except Exception as e:
            logger.error(f"Error handling mention: {e}")
    
    async def handle_callback_query(self, callback: CallbackQuery):
        """Handle callback queries"""
        # Implement callback handling if needed
        await callback.answer()
    
    async def start(self):
        """Start the ghost bot"""
        try:
            # Load admin profile
            await self.load_admin_profile()
            
            # Set bot commands
            commands = [
                types.BotCommand(command="start", description="Start bot"),
                types.BotCommand(command="help", description="Help guide"),
                types.BotCommand(command="settings", description="Bot settings")
            ]
            
            await self.bot.set_my_commands(commands)
            
            # Start polling
            logger.info(f"Ghost Bot {self.bot_id} started")
            await self.dp.start_polling(self.bot)
            
        except Exception as e:
            logger.error(f"Error starting ghost bot: {e}")
    
    async def stop(self):
        """Stop the ghost bot"""
        try:
            await self.bot.session.close()
        except:
            pass
    
    async def send_message_as_admin(self, chat_id: int, text: str):
        """Send message as admin to specific chat"""
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=ParseMode.HTML
            )
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    async def get_chat_history(self, chat_id: int, limit: int = 50):
        """Get chat history for learning"""
        # This would require storing messages in database
        # For now, return from database
        with next(get_db()) as db:
            conversations = crud.get_conversations(db, self.bot_id, limit)
            return [
                {
                    "from": conv.from_user,
                    "to": conv.to_user,
                    "message": conv.message_text,
                    "response": conv.bot_response,
                    "time": conv.timestamp
                }
                for conv in conversations
            ]