# keyboards/user_keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

def get_main_menu(is_owner: bool = False) -> ReplyKeyboardMarkup:
    """Get main menu keyboard"""
    builder = ReplyKeyboardBuilder()
    
    builder.row(
        KeyboardButton(text="🤖 নতুন বট তৈরি"),
        KeyboardButton(text="📋 আমার বটগুলো")
    )
    
    builder.row(
        KeyboardButton(text="💰 প্ল্যান কিনুন"),
        KeyboardButton(text="📊 প্ল্যান তথ্য")
    )
    
    builder.row(
        KeyboardButton(text="💳 পেমেন্ট তথ্য"),
        KeyboardButton(text="🆘 সাহায্য")
    )
    
    builder.row(
        KeyboardButton(text="📞 সাপোর্ট"),
        KeyboardButton(text="ℹ️ বট তথ্য")
    )
    
    if is_owner:
        builder.row(KeyboardButton(text="👑 অ্যাডমিন প্যানেল"))
    
    return builder.as_markup(resize_keyboard=True)

def get_my_bots_keyboard() -> InlineKeyboardMarkup:
    """Get my bots keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🔄 রিফ্রেশ", callback_data="refresh_bots"),
        InlineKeyboardButton(text="➕ নতুন বট", callback_data="create_new_bot")
    )
    
    builder.row(
        InlineKeyboardButton(text="⚙️ সেটিংস", callback_data="bot_settings"),
        InlineKeyboardButton(text="📊 স্ট্যাটস", callback_data="bot_stats")
    )
    
    builder.row(
        InlineKeyboardButton(text="🔙 মেনু", callback_data="back_to_menu")
    )
    
    return builder.as_markup()

def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Get settings keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🌐 ভাষা পরিবর্তন", callback_data="change_language"),
        InlineKeyboardButton(text="⏰ নামাজ সময়", callback_data="prayer_time_settings")
    )
    
    builder.row(
        InlineKeyboardButton(text="🤖 বট সেটিংস", callback_data="ghost_bot_settings"),
        InlineKeyboardButton(text="🔔 নোটিফিকেশন", callback_data="notification_settings")
    )
    
    builder.row(
        InlineKeyboardButton(text="🔒 সিকিউরিটি", callback_data="security_settings"),
        InlineKeyboardButton(text="📱 প্রোফাইল", callback_data="profile_settings")
    )
    
    builder.row(
        InlineKeyboardButton(text="💾 ব্যাকআপ", callback_data="backup_settings"),
        InlineKeyboardButton(text="🔙 পিছনে", callback_data="back_to_bots")
    )
    
    return builder.as_markup()

def get_help_keyboard() -> InlineKeyboardMarkup:
    """Get help keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📖 টিউটোরিয়াল", callback_data="tutorial"),
        InlineKeyboardButton(text="❓ FAQ", callback_data="faq")
    )
    
    builder.row(
        InlineKeyboardButton(text="🎥 ভিডিও", callback_data="video_tutorial"),
        InlineKeyboardButton(text="📚 গাইড", callback_data="user_guide")
    )
    
    builder.row(
        InlineKeyboardButton(text="🐞 বাগ রিপোর্ট", callback_data="bug_report"),
        InlineKeyboardButton(text="💡 ফিচার রিকোয়েস্ট", callback_data="feature_request")
    )
    
    builder.row(
        InlineKeyboardButton(text="📞 জরুরি যোগাযোগ", callback_data="emergency_contact"),
        InlineKeyboardButton(text="🔙 মেনু", callback_data="back_to_menu")
    )
    
    return builder.as_markup()