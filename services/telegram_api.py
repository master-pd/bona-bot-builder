# services/telegram_api.py
import logging
import aiohttp
from typing import Dict, Optional, Any
from config.settings import settings

logger = logging.getLogger(__name__)

class TelegramAPI:
    def __init__(self):
        self.base_url = "https://api.telegram.org/bot"
        self.session = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def validate_bot_token(self, token: str) -> bool:
        """Validate bot token with Telegram API"""
        try:
            session = await self.get_session()
            url = f"{self.base_url}{token}/getMe"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("ok", False)
                return False
                
        except Exception as e:
            logger.error(f"Error validating bot token: {e}")
            return False
    
    async def get_bot_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get bot information from Telegram"""
        try:
            session = await self.get_session()
            url = f"{self.base_url}{token}/getMe"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("ok", False):
                        return data.get("result", {})
                return None
                
        except Exception as e:
            logger.error(f"Error getting bot info: {e}")
            return None
    
    async def validate_user_id(self, user_id: int) -> bool:
        """Validate user ID (simplified - in production would need different approach)"""
        # Note: Telegram API doesn't provide a direct way to validate user IDs
        # This is a simplified version
        try:
            # Check if it's a valid Telegram ID format
            if 100000000 <= user_id <= 9999999999:
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error validating user ID: {e}")
            return False
    
    async def send_message(self, token: str, chat_id: int, text: str, 
                          parse_mode: str = "HTML", **kwargs) -> bool:
        """Send message via bot"""
        try:
            session = await self.get_session()
            url = f"{self.base_url}{token}/sendMessage"
            
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                **kwargs
            }
            
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("ok", False)
                return False
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    async def get_chat(self, token: str, chat_id: int) -> Optional[Dict[str, Any]]:
        """Get chat information"""
        try:
            session = await self.get_session()
            url = f"{self.base_url}{token}/getChat"
            
            data = {"chat_id": chat_id}
            
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("ok", False):
                        return result.get("result", {})
                return None
                
        except Exception as e:
            logger.error(f"Error getting chat: {e}")
            return None
    
    async def set_webhook(self, token: str, url: str) -> bool:
        """Set webhook for bot"""
        try:
            session = await self.get_session()
            endpoint = f"{self.base_url}{token}/setWebhook"
            
            data = {"url": url}
            
            async with session.post(endpoint, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("ok", False)
                return False
                
        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            return False
    
    async def delete_webhook(self, token: str) -> bool:
        """Delete webhook"""
        try:
            session = await self.get_session()
            endpoint = f"{self.base_url}{token}/deleteWebhook"
            
            async with session.post(endpoint) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("ok", False)
                return False
                
        except Exception as e:
            logger.error(f"Error deleting webhook: {e}")
            return False
    
    async def close(self):
        """Close session"""
        if self.session and not self.session.closed:
            await self.session.close()