# core/bot_factory.py
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
from database import crud, models
from database.session import get_db
from config.settings import settings
from config.constants import Constants
from keyboards import user_keyboards, inline_keyboards
from utils.text_templates import TextTemplates
from utils.language import LanguageManager
from services.telegram_api import TelegramAPI
from services.encryption import EncryptionService
import json

logger = logging.getLogger(__name__)

class BotFactory:
    def __init__(self, token: str):
        self.bot = Bot(token=token, parse_mode=ParseMode.HTML)
        self.dp = Dispatcher()
        self.language_manager = LanguageManager()
        self.templates = TextTemplates()
        self.telegram_api = TelegramAPI()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all command handlers"""
        
        # Start command
        @self.dp.message(CommandStart())
        async def start_command(message: Message):
            await self.handle_start(message)
        
        # Create bot command
        @self.dp.message(Command("createbot"))
        async def create_bot_command(message: Message):
            await self.handle_create_bot(message)
        
        # My bots command
        @self.dp.message(Command("mybots"))
        async def my_bots_command(message: Message):
            await self.handle_my_bots(message)
        
        # Buy plan command
        @self.dp.message(Command("buyplan"))
        async def buy_plan_command(message: Message):
            await self.handle_buy_plan(message)
        
        # My plan command
        @self.dp.message(Command("myplan"))
        async def my_plan_command(message: Message):
            await self.handle_my_plan(message)
        
        # Payment command
        @self.dp.message(Command("payment"))
        async def payment_command(message: Message):
            await self.handle_payment_info(message)
        
        # Help command
        @self.dp.message(Command("help"))
        async def help_command(message: Message):
            await self.handle_help(message)
        
        # Support command
        @self.dp.message(Command("support"))
        async def support_command(message: Message):
            await self.handle_support(message)
        
        # Info command
        @self.dp.message(Command("info"))
        async def info_command(message: Message):
            await self.handle_info(message)
        
        # Callback query handlers
        @self.dp.callback_query()
        async def callback_handler(callback: CallbackQuery):
            await self.handle_callback(callback)
    
    async def handle_start(self, message: Message):
        """Handle /start command"""
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        
        with next(get_db()) as db:
            # Check if user exists
            user = crud.get_user(db, user_id)
            
            if not user:
                # Create new user
                user = crud.create_user(db, user_id, username, first_name, last_name)
                welcome_text = self.templates.get_welcome_new_user(user)
            else:
                welcome_text = self.templates.get_welcome_existing_user(user)
            
            # Check trial status
            if user.trial_used and user.trial_end < datetime.now():
                trial_text = self.templates.get_trial_expired()
            elif user.trial_used:
                trial_text = self.templates.get_trial_remaining(user.trial_end)
            else:
                trial_text = self.templates.get_trial_available()
        
        # Send welcome message
        text = f"{welcome_text}\n\n{trial_text}"
        keyboard = user_keyboards.get_main_menu(user_id == settings.OWNER_ID)
        
        await message.answer(text, reply_markup=keyboard)
    
    async def handle_create_bot(self, message: Message):
        """Handle /createbot command"""
        user_id = message.from_user.id
        
        with next(get_db()) as db:
            user = crud.get_user(db, user_id)
            if not user:
                await message.answer("❌ আপনার অ্যাকাউন্ট পাওয়া যায়নি। /start কমান্ড দিন।")
                return
            
            # Check if user can create more bots
            user_bots = crud.get_user_bots(db, user.id)
            if len(user_bots) >= Constants.MAX_BOTS_PER_USER:
                await message.answer("❌ আপনি সর্বোচ্চ ৫টি বট তৈরি করতে পারবেন।")
                return
            
            # Check trial/plan validity
            if user.plan_type == "trial" and user.trial_end < datetime.now():
                await message.answer("❌ আপনার ট্রায়াল শেষ হয়েছে। প্ল্যান কিনে নিন।")
                return
            
            # Start bot creation process
            await message.answer(
                "🤖 নতুন ঘোস্ট বট তৈরি করুন:\n\n"
                "১. প্রথমে @BotFather এ যান\n"
                "২. /newbot কমান্ড দিন\n"
                "৩. বটের নাম দিন\n"
                "৪. ইউজারনেম দিন\n"
                "৫. টোকেন সংগ্রহ করুন\n\n"
                "এরপর নিচের বাটনে ক্লিক করে টোকেন দিন:",
                reply_markup=inline_keyboards.get_token_input_keyboard()
            )
    
    async def handle_my_bots(self, message: Message):
        """Handle /mybots command"""
        user_id = message.from_user.id
        
        with next(get_db()) as db:
            user = crud.get_user(db, user_id)
            if not user:
                await message.answer("❌ আপনার অ্যাকাউন্ট পাওয়া যায়নি।")
                return
            
            user_bots = crud.get_user_bots(db, user.id)
            
            if not user_bots:
                await message.answer("🤖 আপনার কোন বট নেই। /createbot দিয়ে নতুন বট তৈরি করুন।")
                return
            
            # Create bots list
            bots_text = "📋 আপনার বটগুলোর তালিকা:\n\n"
            for i, bot in enumerate(user_bots, 1):
                status_icon = "✅" if bot.status == "active" else "⏳" if bot.status == "pending" else "❌"
                bots_text += f"{i}. {bot.bot_name} - {status_icon} {bot.status}\n"
            
            await message.answer(bots_text, reply_markup=user_keyboards.get_my_bots_keyboard())
    
    async def handle_buy_plan(self, message: Message):
        """Handle /buyplan command"""
        user_id = message.from_user.id
        
        with next(get_db()) as db:
            user = crud.get_user(db, user_id)
            if not user:
                await message.answer("❌ আপনার অ্যাকাউন্ট পাওয়া যায়নি।")
                return
            
            # Show plans
            plans_text = "💰 প্যাকেজ সিলেক্ট করুন:\n\n"
            for plan_id, plan_data in settings.PLANS.items():
                plans_text += f"📦 {plan_data['name']}\n"
                plans_text += f"   💵 মূল্য: {plan_data['price']} টাকা\n"
                plans_text += f"   ⏳ সময়: {plan_data['days']} দিন\n"
                plans_text += f"   ✅ আনলিমিটেড চ্যাট\n\n"
            
            plans_text += "সিলেক্ট করতে নিচের বাটনে ক্লিক করুন:"
            
            await message.answer(
                plans_text,
                reply_markup=inline_keyboards.get_plans_keyboard()
            )
    
    async def handle_my_plan(self, message: Message):
        """Handle /myplan command"""
        user_id = message.from_user.id
        
        with next(get_db()) as db:
            user = crud.get_user(db, user_id)
            if not user:
                await message.answer("❌ আপনার অ্যাকাউন্ট পাওয়া যায়নি।")
                return
            
            # Get plan info
            if user.plan_type == "trial":
                plan_name = "ট্রায়াল"
                expiry = user.trial_end
            else:
                plan_data = settings.PLANS.get(user.plan_type, {})
                plan_name = plan_data.get('name', 'Unknown')
                expiry = user.plan_end
            
            # Create plan info text
            plan_text = "📊 আপনার প্ল্যান তথ্য:\n\n"
            plan_text += f"👤 ইউজার: {user.first_name or user.username}\n"
            plan_text += f"📦 প্ল্যান: {plan_name}\n"
            
            if expiry:
                remaining = expiry - datetime.now()
                if remaining.days > 0:
                    plan_text += f"⏳ বাকি সময়: {remaining.days} দিন\n"
                else:
                    plan_text += "❌ প্ল্যান শেষ\n"
            
            plan_text += f"💎 ক্রেডিট: {user.credits}\n"
            plan_text += f"✅ স্ট্যাটাস: {'একটিভ' if user.is_active else 'নন-একটিভ'}\n\n"
            
            if user.plan_type == "trial" and user.trial_end < datetime.now():
                plan_text += "⚠️ আপনার ট্রায়াল শেষ হয়েছে। প্ল্যান কিনুন।\n"
            
            await message.answer(plan_text)
    
    async def handle_payment_info(self, message: Message):
        """Handle /payment command"""
        payment_text = "💳 পেমেন্ট তথ্য:\n\n"
        payment_text += f"📞 পেমেন্ট নম্বর: {settings.OWNER_PHONE}\n"
        payment_text += "📋 পেমেন্ট মেথড:\n"
        payment_text += "  • বিকাশ (Bkash)\n"
        payment_text += "  • নগদ (Nagad)\n"
        payment_text += "  • রকেট (Rocket)\n\n"
        payment_text += "⚠️ পেমেন্ট করার আগে অবশ্যই মালিকের সাথে কথা বলুন!\n\n"
        payment_text += "পেমেন্ট করার পর:\n"
        payment_text += "১. ট্রানজেকশন আইডি নোট করুন\n"
        payment_text += "২. স্ক্রিনশট নিন\n"
        payment_text += "৩. প্রুফ মালিককে পাঠান\n\n"
        payment_text += "পেমেন্ট ভেরিফাই হওয়ার পর আপনার প্ল্যান অ্যাক্টিভ হবে।"
        
        await message.answer(payment_text)
    
    async def handle_help(self, message: Message):
        """Handle /help command"""
        help_text = "🆘 হেল্প ও গাইড:\n\n"
        help_text += "📖 বেসিক কমান্ড:\n"
        help_text += "/start - বট শুরু করুন\n"
        help_text += "/createbot - নতুন বট তৈরি করুন\n"
        help_text += "/mybots - আপনার বটগুলো দেখুন\n"
        help_text += "/buyplan - প্ল্যান কিনুন\n"
        help_text += "/myplan - আপনার প্ল্যান দেখুন\n"
        help_text += "/payment - পেমেন্ট তথ্য\n"
        help_text += "/help - হেল্প গাইড\n"
        help_text += "/support - সাপোর্টে যোগাযোগ\n"
        help_text += "/info - বট তথ্য\n\n"
        
        help_text += "🤖 বট তৈরি গাইড:\n"
        help_text += "১. @BotFather এ যান\n"
        help_text += "২. /newbot কমান্ড দিন\n"
        help_text += "৩. বটের নাম দিন\n"
        help_text += "৪. ইউজারনেম দিন (bot সহ)\n"
        help_text += "৫. টোকেন সংগ্রহ করুন\n\n"
        
        help_text += "ℹ️ অতিরিক্ত তথ্য:\n"
        help_text += "• নতুন ইউজার ৩ দিন ফ্রি ট্রায়াল পাবেন\n"
        help_text += "• ট্রায়ালে দৈনিক ১০টি মেসেজ\n"
        help_text += "• পেমেন্ট ম্যানুয়ালি ভেরিফাই হয়\n"
        
        await message.answer(help_text)
    
    async def handle_support(self, message: Message):
        """Handle /support command"""
        support_text = "📞 সাপোর্ট ও যোগাযোগ:\n\n"
        support_text += f"👤 মালিক: রানা (MASTER 🪓)\n"
        support_text += f"📧 ইমেইল: {settings.OWNER_EMAIL}\n"
        support_text += f"📱 ফোন: {settings.OWNER_PHONE}\n"
        support_text += f"📢 টেলিগ্রাম: @{settings.OWNER_USERNAME}\n"
        support_text += f"🤖 বট: @{settings.BOT_USERNAME}\n\n"
        
        support_text += "📢 চ্যানেল: https://t.me/master_account_remover_channel\n\n"
        
        support_text += "⚠️ সমস্যা হলে সরাসরি মালিকের সাথে যোগাযোগ করুন।\n"
        support_text += "পেমেন্ট সম্পর্কিত যেকোনো সমস্যার জন্য সরাসরি কল করুন।"
        
        await message.answer(support_text)
    
    async def handle_info(self, message: Message):
        """Handle /info command"""
        info_text = f"🤖 বট তথ্য:\n\n"
        info_text += f"• বট নাম: {settings.BOT_NAME}\n"
        info_text += f"• ডেভেলপার: রানা (MASTER 🪓)\n"
        info_text += f"• বয়স: ২০ বছর\n"
        info_text += f"• অবস্থা: সিঙ্গেল\n"
        info_text += f"• শিক্ষা: এসএসসি ব্যাচ ২০২২\n"
        info_text += f"• অবস্থান: ফরিদপুর, ঢাকা, বাংলাদেশ\n\n"
        
        info_text += "👨‍💻 পেশাগত তথ্য:\n"
        info_text += "• পেশা: সিকিউরিটি ফিল্ড\n"
        info_text += "• কাজ: এক্সপেরিমেন্ট / টেকনিক্যাল অপারেশন\n"
        info_text += "• দক্ষতা:\n"
        info_text += "  - ভিডিও এডিটিং\n"
        info_text += "  - ফটো এডিটিং\n"
        info_text += "  - মোবাইল টেকনোলজি\n"
        info_text += "  - অনলাইন অপারেশন\n"
        info_text += "  - সাইবার সিকিউরিটি (বর্তমানে শিখছি)\n\n"
        
        info_text += "🎯 লক্ষ্য ও স্বপ্ন:\n"
        info_text += "• স্বপ্ন: প্রফেশনাল ডেভেলপার হওয়া\n"
        info_text += "• প্রজেক্ট: ওয়েবসাইট (শীঘ্রই আসছে)\n\n"
        
        info_text += "📞 যোগাযোগ:\n"
        info_text += f"• ইমেইল: {settings.OWNER_EMAIL}\n"
        info_text += f"• ফোন: {settings.OWNER_PHONE}\n"
        info_text += "• টেলিগ্রাম বট: @black_lovers1_bot\n"
        info_text += f"• টেলিগ্রাম প্রোফাইল: @{settings.OWNER_USERNAME}\n"
        info_text += "• সাপোর্ট চ্যানেল: https://t.me/master_account_remover_channel"
        
        await message.answer(info_text)
    
    async def handle_callback(self, callback: CallbackQuery):
        """Handle callback queries"""
        data = callback.data
        
        if data.startswith("plan_"):
            await self.handle_plan_selection(callback)
        elif data.startswith("token_input"):
            await self.handle_token_input(callback)
        elif data.startswith("confirm_bot"):
            await self.handle_bot_confirmation(callback)
        
        await callback.answer()
    
    async def handle_plan_selection(self, callback: CallbackQuery):
        """Handle plan selection"""
        plan_id = callback.data.split("_")[1]
        user_id = callback.from_user.id
        
        if plan_id not in settings.PLANS:
            await callback.message.answer("❌ ইনভ্যালিড প্ল্যান।")
            return
        
        plan_data = settings.PLANS[plan_id]
        
        # Show payment instructions
        payment_text = f"💰 পেমেন্ট তথ্য:\n\n"
        payment_text += f"প্ল্যান: {plan_data['name']}\n"
        payment_text += f"মূল্য: {plan_data['price']} টাকা\n"
        payment_text += f"সময়: {plan_data['days']} দিন\n\n"
        
        payment_text += f"📞 পেমেন্ট নম্বর: {settings.OWNER_PHONE}\n\n"
        
        payment_text += "পেমেন্ট করার আগে:\n"
        payment_text += "১. মালিকের সাথে কথা বলুন\n"
        payment_text += "২. নিশ্চিত করুন\n\n"
        
        payment_text += "পেমেন্ট করার পর:\n"
        payment_text += "১. ট্রানজেকশন আইডি নোট করুন\n"
        payment_text += "২. স্ক্রিনশট নিন\n"
        payment_text += "৩. প্রুফ মালিককে পাঠান\n\n"
        
        payment_text += "⚠️ প্রুফ ছাড়া পেমেন্ট ভেরিফাই হবে না!"
        
        await callback.message.answer(payment_text)
    
    async def handle_token_input(self, callback: CallbackQuery):
        """Handle token input"""
        await callback.message.answer(
            "🔑 বট টোকেন দিন:\n\n"
            "টোকেন ফরম্যাট:\n"
            "7952399872:AAGTxvtziWmgRM5p_rlu77ljBVq-QVxElyg\n\n"
            "টোকেন পাঠান:",
            reply_markup=types.ForceReply(selective=True)
        )
    
    async def handle_bot_confirmation(self, callback: CallbackQuery):
        """Handle bot confirmation"""
        # This will be implemented in the full bot creation flow
        pass
    
    async def run(self):
        """Run the bot factory"""
        logger.info("Starting Bot Factory...")
        await self.dp.start_polling(self.bot)