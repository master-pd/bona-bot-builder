# core/ai_engine.py
import logging
import json
import random
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp
from database import crud
from database.session import get_db
from config.settings import settings
from utils.language import LanguageManager
from utils.text_templates import TextTemplates

logger = logging.getLogger(__name__)

class AIEngine:
    def __init__(self):
        self.language_manager = LanguageManager()
        self.templates = TextTemplates()
        self.responses_cache = {}
        self.learning_data = {}
    
    async def generate_response(self, context: Dict[str, Any]) -> str:
        """Generate AI response based on context"""
        try:
            bot_id = context.get("bot_id")
            user_id = context.get("user_id")
            message_text = context.get("message_text", "").strip().lower()
            message_type = context.get("message_type", "text")
            
            # Get learning data for this bot
            learning = self.get_learning_data(bot_id)
            
            # Check for predefined responses
            predefined = self.check_predefined_responses(message_text)
            if predefined:
                return self.language_manager.translate(predefined, "banglish")
            
            # Check learning patterns
            learned_response = self.check_learned_patterns(learning, message_text)
            if learned_response:
                return learned_response
            
            # Generate new response based on context
            response = await self.generate_contextual_response(context, learning)
            
            # Translate if needed
            if context.get("language", "banglish") != "banglish":
                response = self.language_manager.translate(response, context["language"])
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self.get_fallback_response()
    
    def get_learning_data(self, bot_id: int) -> Dict[str, Any]:
        """Get or load learning data for bot"""
        if bot_id not in self.learning_data:
            with next(get_db()) as db:
                learning = crud.get_learning(db, bot_id)
                if learning:
                    self.learning_data[bot_id] = {
                        "user_patterns": learning.user_patterns or {},
                        "response_patterns": learning.response_patterns or {},
                        "context_data": learning.context_data or {},
                        "accuracy": learning.accuracy_score or 0.0
                    }
                else:
                    self.learning_data[bot_id] = {
                        "user_patterns": {},
                        "response_patterns": {},
                        "context_data": {},
                        "accuracy": 0.0
                    }
        
        return self.learning_data[bot_id]
    
    def check_predefined_responses(self, message: str) -> Optional[str]:
        """Check for predefined/greeting responses"""
        greetings = {
            "hello": "হ্যালো! কেমন আছেন? 😊",
            "hi": "হাই! ভালো আছি, আপনি? 💝",
            "hola": "ওহে! কী খবর? ✨",
            "hey": "হেই! কেমন চলছে? 🎯",
            "সালাম": "ওয়ালাইকুম আসসালাম! কেমন আছেন? 🤲",
            "হ্যালো": "হ্যালো! ভালো আছি, আপনিও ভালো থাকুন 🌟",
            "কেমন আছ": "আলহামদুলিল্লাহ ভালো আছি! আপনি কেমন আছেন? 😊",
            "খবর কি": "সব ভালো! আপনার কী খবর? 💫",
            "কি কর": "আপনার সাথে চ্যাট করছি! 😄",
            "ভাই": "জি বলুন ভাই, কীভাবে সাহায্য করতে পারি? 🛠️",
            "আপু": "জি আপু, কী করতে হবে? 💖",
            "বন্ধু": "হ্যালো বন্ধু! কেমন আছ? 👋"
        }
        
        for key, response in greetings.items():
            if key in message.lower():
                return response
        
        # Check for help requests
        help_keywords = ["help", "হেল্প", "সাহায্য", "জানি না", "কিভাবে"]
        for keyword in help_keywords:
            if keyword in message.lower():
                return "কীভাবে সাহায্য করতে পারি? বিস্তারিত বলুন। 🤔"
        
        return None
    
    def check_learned_patterns(self, learning: Dict[str, Any], message: str) -> Optional[str]:
        """Check learned response patterns"""
        user_patterns = learning.get("user_patterns", {})
        response_patterns = learning.get("response_patterns", {})
        
        if not user_patterns or not response_patterns:
            return None
        
        # Find similar patterns
        message_words = set(message.lower().split())
        best_match = None
        best_score = 0
        
        for pattern, count in user_patterns.items():
            if pattern in message_words:
                score = count / len(message_words)
                if score > best_score:
                    best_score = score
                    best_match = pattern
        
        if best_match and best_score > 0.3:
            # Find corresponding response pattern
            for word, frequency in response_patterns.items():
                if frequency > 5:  # Frequently used response word
                    return f"{word.capitalize()}... আরও বলুন।"
        
        return None
    
    async def generate_contextual_response(self, context: Dict[str, Any], 
                                          learning: Dict[str, Any]) -> str:
        """Generate contextual response"""
        message = context.get("message_text", "")
        message_type = context.get("message_type", "text")
        
        # Get conversation history
        previous_context = learning.get("context_data", {})
        
        # Analyze message sentiment and intent
        sentiment = self.analyze_sentiment(message)
        intent = self.detect_intent(message)
        
        # Generate response based on intent and sentiment
        response_templates = self.templates.get_response_templates()
        
        if intent == "greeting":
            responses = response_templates.get("greetings", [])
        elif intent == "question":
            responses = response_templates.get("questions", [])
        elif intent == "request":
            responses = response_templates.get("requests", [])
        elif intent == "complaint":
            responses = response_templates.get("complaints", [])
        else:
            responses = response_templates.get("general", [])
        
        # Select random response
        if responses:
            response = random.choice(responses)
        else:
            response = "জি বলুন, আমি শুনছি। 😊"
        
        # Personalize based on learning
        if previous_context.get("user_name"):
            response = response.replace("{name}", previous_context["user_name"])
        
        # Add emoji based on sentiment
        if sentiment == "positive":
            response += " 😊"
        elif sentiment == "negative":
            response += " 😔"
        else:
            response += " 💫"
        
        return response
    
    def analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis"""
        positive_words = ["ভালো", "খুশি", "আনন্দ", "ধন্যবাদ", "থ্যাংকস", "সুপার", "এক্সিলেন্ট", "বিউটিফুল"]
        negative_words = ["খারাপ", "বাজে", "দুঃখ", "কষ্ট", "প্রবলেম", "সমস্যা", "বিরক্ত", "অসুস্থ"]
        
        text_lower = text.lower()
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        else:
            return "neutral"
    
    def detect_intent(self, text: str) -> str:
        """Detect user intent"""
        text_lower = text.lower()
        
        greeting_words = ["হ্যালো", "হাই", "সালাম", "কেমন", "খবর"]
        question_words = ["কি", "কেন", "কিভাবে", "কখন", "কোথায়", "কে"]
        request_words = ["চাই", "দাও", "করো", "করুন", "সাহায্য", "হেল্প"]
        complaint_words = ["সমস্যা", "প্রবলেম", "ভুল", "এরর", "কাজ করে না"]
        
        if any(word in text_lower for word in greeting_words):
            return "greeting"
        elif any(word in text_lower for word in question_words):
            return "question"
        elif any(word in text_lower for word in request_words):
            return "request"
        elif any(word in text_lower for word in complaint_words):
            return "complaint"
        else:
            return "general"
    
    def get_fallback_response(self) -> str:
        """Get fallback response when AI fails"""
        fallbacks = [
            "দুঃখিত, বুঝতে পারিনি। আবার বলুন। 🤔",
            "কী বললেন? একটু ক্লিয়ার বলবেন? 💭",
            "একটু অন্যভাবে বলুন দেখি। ✨",
            "আমি এখনো শিখছি, সহজ ভাষায় বলুন। 📚",
            "একটু বিশদভাবে বলুন কী চান। 💫"
        ]
        return random.choice(fallbacks)
    
    async def train_from_conversations(self, bot_id: int, conversations: List[Dict]):
        """Train AI from conversation history"""
        try:
            learning = self.get_learning_data(bot_id)
            
            for conv in conversations:
                user_msg = conv.get("message", "")
                bot_resp = conv.get("response", "")
                
                if user_msg and bot_resp:
                    # Update patterns
                    self.update_patterns(learning, user_msg, bot_resp)
            
            # Save to database
            with next(get_db()) as db:
                db_learning = crud.get_learning(db, bot_id)
                if db_learning:
                    db_learning.user_patterns = learning["user_patterns"]
                    db_learning.response_patterns = learning["response_patterns"]
                    db_learning.context_data = learning["context_data"]
                    db_learning.accuracy_score = learning["accuracy"]
                    db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error training from conversations: {e}")
            return False
    
    def update_patterns(self, learning: Dict[str, Any], user_message: str, bot_response: str):
        """Update learning patterns"""
        # Update user patterns
        words = user_message.lower().split()
        for word in words:
            if len(word) > 2:
                learning["user_patterns"][word] = learning["user_patterns"].get(word, 0) + 1
        
        # Update response patterns
        resp_words = bot_response.lower().split()
        for word in resp_words:
            if len(word) > 2:
                learning["response_patterns"][word] = learning["response_patterns"].get(word, 0) + 1
        
        # Update accuracy (simple calculation)
        total_patterns = len(learning["user_patterns"]) + len(learning["response_patterns"])
        if total_patterns > 0:
            learning["accuracy"] = min(1.0, total_patterns / 1000)