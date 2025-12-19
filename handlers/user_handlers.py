# handlers/user_handlers.py
import logging
from aiogram import Router, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from database import crud
from database.session import get_db
from config.settings import settings
from keyboards import user_keyboards
from utils.text_templates import TextTemplates

logger = logging.getLogger(__name__)
router = Router()

@router.message(CommandStart())
async def start_handler(message: Message):
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
            welcome_text = TextTemplates.get_welcome_new_user(user)
        else:
            welcome_text = TextTemplates.get_welcome_existing_user(user)
        
        # Send welcome message
        keyboard = user_keyboards.get_main_menu(user_id == settings.OWNER_ID)
        await message.answer(welcome_text, reply_markup=keyboard)

@router.message(Command("help"))
async def help_handler(message: Message):
    """Handle /help command"""
    help_text = TextTemplates.get_help_text()
    await message.answer(help_text)

@router.message(Command("myplan"))
async def myplan_handler(message: Message):
    """Handle /myplan command"""
    user_id = message.from_user.id
    
    with next(get_db()) as db:
        user = crud.get_user(db, user_id)
        if not user:
            await message.answer("❌ আপনার অ্যাকাউন্ট পাওয়া যায়নি।")
            return
        
        plan_text = TextTemplates.get_plan_text(user)
        await message.answer(plan_text)

@router.message(Command("support"))
async def support_handler(message: Message):
    """Handle /support command"""
    support_text = TextTemplates.get_support_text()
    await message.answer(support_text)

@router.message(Command("info"))
async def info_handler(message: Message):
    """Handle /info command"""
    info_text = TextTemplates.get_info_text()
    await message.answer(info_text)

@router.message(F.text.contains("সালাম") | F.text.contains("স্যালাম"))
async def salam_handler(message: Message):
    """Auto respond to Salam"""
    responses = [
        "ওয়ালাইকুম আসসালাম! কেমন আছেন? 🤲",
        "ওয়ালাইকুম আসসালাম ভাই! ভালো আছি, আপনিও ভালো থাকুন 😊",
        "ওয়ালাইকুম আসসালাম আপু! কী খবর? 💫"
    ]
    
    import random
    response = random.choice(responses)
    await message.answer(response)