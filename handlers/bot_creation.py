# handlers/bot_creation.py
import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import crud
from database.session import get_db
from config.settings import settings
from services.telegram_api import TelegramAPI
from keyboards import inline_keyboards
from utils.text_templates import TextTemplates
import re

logger = logging.getLogger(__name__)
router = Router()
telegram_api = TelegramAPI()

class BotCreationStates(StatesGroup):
    awaiting_token = State()
    awaiting_admin_id = State()
    awaiting_bot_name = State()
    confirming_details = State()

@router.message(Command("createbot"))
async def create_bot_command(message: Message, state: FSMContext):
    """Start bot creation process"""
    user_id = message.from_user.id
    
    with next(get_db()) as db:
        user = crud.get_user(db, user_id)
        if not user:
            await message.answer("❌ আপনার অ্যাকাউন্ট পাওয়া যায়নি। /start দিন")
            return
        
        # Check if user can create more bots
        user_bots = crud.get_user_bots(db, user.id)
        if len(user_bots) >= 5:
            await message.answer("❌ আপনি সর্বোচ্চ ৫টি বট তৈরি করতে পারবেন।")
            return
        
        # Check trial/plan validity
        if user.plan_type == "trial" and user.trial_end and user.trial_end < datetime.now():
            await message.answer("❌ আপনার ট্রায়াল শেষ হয়েছে। প্ল্যান কিনুন।")
            return
    
    # Start bot creation
    await message.answer(
        "🤖 নতুন ঘোস্ট বট তৈরি করুন:\n\n"
        "প্রথমে আপনার বট টোকেন দিন:\n\n"
        "টোকেন পেতে:\n"
        "১. @BotFather এ যান\n"
        "২. /newbot কমান্ড দিন\n"
        "৩. বটের নাম দিন\n"
        "৪. ইউজারনেম দিন\n"
        "৫. টোকেন সংগ্রহ করুন\n\n"
        "টোকেন ফরম্যাট:\n"
        "7952399872:AAGTxvtziWmgRM5p_rlu77ljBVq-QVxElyg\n\n"
        "টোকেন পাঠান:",
        reply_markup=types.ForceReply(selective=True)
    )
    await state.set_state(BotCreationStates.awaiting_token)

@router.message(BotCreationStates.awaiting_token)
async def handle_bot_token(message: Message, state: FSMContext):
    """Handle bot token input"""
    token = message.text.strip()
    
    # Validate token format
    token_pattern = r'^\d{9,10}:[A-Za-z0-9_-]{35}$'
    if not re.match(token_pattern, token):
        await message.answer(
            "❌ ভুল টোকেন ফরম্যাট।\n\n"
            "সঠিক ফরম্যাট: 7952399872:AAGTxvtziWmgRM5p_rlu77ljBVq-QVxElyg\n\n"
            "আবার টোকেন দিন:",
            reply_markup=types.ForceReply(selective=True)
        )
        return
    
    # Validate token with Telegram API
    is_valid = await telegram_api.validate_bot_token(token)
    if not is_valid:
        await message.answer(
            "❌ ইনভ্যালিড টোকেন।\n\n"
            "টোকেন চেক করুন এবং আবার দিন:",
            reply_markup=types.ForceReply(selective=True)
        )
        return
    
    await state.update_data(bot_token=token)
    
    # Ask for admin chat ID
    await message.answer(
        "👤 এখন অ্যাডমিন চ্যাট আইডি দিন:\n\n"
        "চ্যাট আইডি পেতে:\n"
        "১. @userinfobot এ যান\n"
        "২. /start দিন\n"
        "৩. Your ID দেখুন\n\n"
        "চ্যাট আইডি (সংখ্যা) পাঠান:",
        reply_markup=types.ForceReply(selective=True)
    )
    await state.set_state(BotCreationStates.awaiting_admin_id)

@router.message(BotCreationStates.awaiting_admin_id)
async def handle_admin_id(message: Message, state: FSMContext):
    """Handle admin chat ID input"""
    admin_id_text = message.text.strip()
    
    # Validate chat ID
    if not admin_id_text.isdigit():
        await message.answer(
            "❌ ভুল চ্যাট আইডি। শুধু সংখ্যা দিন:\n\n"
            "উদাহরণ: 123456789",
            reply_markup=types.ForceReply(selective=True)
        )
        return
    
    admin_chat_id = int(admin_id_text)
    
    # Check if it's a valid user
    is_valid_user = await telegram_api.validate_user_id(admin_chat_id)
    if not is_valid_user:
        await message.answer(
            "❌ ইনভ্যালিড ইউজার আইডি।\n\n"
            "আবার চ্যাট আইডি দিন:",
            reply_markup=types.ForceReply(selective=True)
        )
        return
    
    await state.update_data(admin_chat_id=admin_chat_id)
    
    # Ask for bot name
    await message.answer(
        "📛 আপনার বটের নাম কি রাখবেন?\n\n"
        "উদাহরণ:\n"
        "• আমার অ্যাসিস্ট্যান্ট\n"
        "• মাই বট\n"
        "• ঘোস্ট হেল্পার\n\n"
        "বটের নাম দিন:",
        reply_markup=types.ForceReply(selective=True)
    )
    await state.set_state(BotCreationStates.awaiting_bot_name)

@router.message(BotCreationStates.awaiting_bot_name)
async def handle_bot_name(message: Message, state: FSMContext):
    """Handle bot name input"""
    bot_name = message.text.strip()
    
    if len(bot_name) < 2 or len(bot_name) > 50:
        await message.answer(
            "❌ বটের নাম খুব ছোট বা বড়।\n\n"
            "২-৫০ অক্ষরের মধ্যে নাম দিন:",
            reply_markup=types.ForceReply(selective=True)
        )
        return
    
    await state.update_data(bot_name=bot_name)
    
    # Get all data
    data = await state.get_data()
    bot_token = data.get("bot_token")
    admin_chat_id = data.get("admin_chat_id")
    
    # Get bot info from token
    bot_info = await telegram_api.get_bot_info(bot_token)
    
    if not bot_info:
        await message.answer("❌ বট তথ্য পাওয়া যায়নি। আবার চেষ্টা করুন।")
        await state.clear()
        return
    
    # Show confirmation
    confirmation_text = (
        "✅ বট তথ্য সংগ্রহ সম্পূর্ণ!\n\n"
        f"🤖 বট: {bot_name}\n"
        f"🔗 ইউজারনেম: @{bot_info.get('username')}\n"
        f"👤 অ্যাডমিন আইডি: {admin_chat_id}\n\n"
        f"📦 প্ল্যান সিলেক্ট করুন:"
    )
    
    await message.answer(
        confirmation_text,
        reply_markup=inline_keyboards.get_bot_creation_plans_keyboard()
    )
    await state.set_state(BotCreationStates.confirming_details)

@router.callback_query(F.data.startswith("create_plan_"))
async def confirm_bot_creation(callback: CallbackQuery, state: FSMContext):
    """Confirm bot creation with selected plan"""
    plan_id = callback.data.split("_")[2]
    
    if plan_id not in settings.PLANS:
        await callback.answer("❌ ইনভ্যালিড প্ল্যান")
        return
    
    # Get state data
    data = await state.get_data()
    bot_token = data.get("bot_token")
    admin_chat_id = data.get("admin_chat_id")
    bot_name = data.get("bot_name")
    
    if not all([bot_token, admin_chat_id, bot_name]):
        await callback.answer("❌ তথ্য ইনকমপ্লিট")
        await state.clear()
        return
    
    user_id = callback.from_user.id
    
    with next(get_db()) as db:
        user = crud.get_user(db, user_id)
        if not user:
            await callback.answer("❌ ইউজার নেই")
            await state.clear()
            return
        
        # Create bot record
        bot = crud.create_bot(
            db=db,
            owner_id=user.id,
            bot_token=bot_token,
            admin_chat_id=admin_chat_id,
            bot_name=bot_name,
            plan_type=plan_id
        )
        
        # Create learning record
        crud.create_learning(db, bot.id)
        
        # Send to owner for approval
        await send_approval_request(bot, user)
        
        await callback.message.edit_text(
            "✅ বট তৈরি অনুরোধ সাবমিট করা হয়েছে!\n\n"
            f"🤖 বট: {bot_name}\n"
            f"📦 প্ল্যান: {settings.PLANS[plan_id]['name']}\n"
            f"⏳ স্ট্যাটাস: অপেক্ষাধীন\n\n"
            "মালিক অনুমোদন দিলে নোটিফিকেশন পাবেন।\n\n"
            "পেমেন্ট করতে /buyplan দিন।"
        )
    
    await state.clear()

async def send_approval_request(bot, user):
    """Send approval request to owner"""
    # This would send a message to owner's Telegram
    # For now, just log
    logger.info(f"Bot approval requested: Bot {bot.id}, User {user.telegram_id}")
    
    # In actual implementation:
    # 1. Send message to owner with inline buttons for approve/reject
    # 2. Handle owner's response
    
    approval_text = (
        "🆕 নতুন বট রিকোয়েস্ট:\n\n"
        f"👤 ইউজার: @{user.username or user.first_name}\n"
        f"🤖 বট নাম: {bot.bot_name}\n"
        f"📦 প্ল্যান: {bot.plan_type}\n"
        f"🆔 বট আইডি: {bot.id}\n\n"
        f"✅ [এপ্রুভ](approve_{bot.id}) | ❌ [রিজেক্ট](reject_{bot.id})"
    )
    
    # This would be sent to owner's chat
    # await bot_factory.bot.send_message(
    #     chat_id=settings.OWNER_ID,
    #     text=approval_text,
    #     parse_mode="Markdown"
    # )

@router.callback_query(F.data == "cancel_creation")
async def cancel_creation(callback: CallbackQuery, state: FSMContext):
    """Cancel bot creation"""
    await state.clear()
    await callback.message.edit_text(
        "❌ বট তৈরি বাতিল করা হয়েছে।\n\n"
        "আবার শুরু করতে /createbot দিন।"
    )