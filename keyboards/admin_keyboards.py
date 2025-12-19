# keyboards/admin_keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List

def get_admin_main_menu() -> InlineKeyboardMarkup:
    """Get admin main menu"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📊 ড্যাশবোর্ড", callback_data="admin_dashboard"),
        InlineKeyboardButton(text="💰 পেমেন্ট", callback_data="admin_pending_payments")
    )
    
    builder.row(
        InlineKeyboardButton(text="🤖 বট রিকোয়েস্ট", callback_data="admin_pending_bots"),
        InlineKeyboardButton(text="👥 ইউজার ম্যানেজ", callback_data="admin_users")
    )
    
    builder.row(
        InlineKeyboardButton(text="📢 ব্রডকাস্ট", callback_data="admin_broadcast"),
        InlineKeyboardButton(text="⚙️ সিস্টেম সেটিংস", callback_data="admin_system_settings")
    )
    
    builder.row(
        InlineKeyboardButton(text="📜 লগস", callback_data="admin_logs"),
        InlineKeyboardButton(text="🔄 রিসেট", callback_data="admin_reset")
    )
    
    builder.row(
        InlineKeyboardButton(text="🔙 মেনু", callback_data="back_to_menu")
    )
    
    return builder.as_markup()

def get_admin_dashboard_menu() -> InlineKeyboardMarkup:
    """Get admin dashboard menu"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🔄 রিফ্রেশ", callback_data="admin_dashboard"),
        InlineKeyboardButton(text="📊 ডিটেইলড রিপোর্ট", callback_data="admin_detailed_report")
    )
    
    builder.row(
        InlineKeyboardButton(text="📈 গ্রাফ", callback_data="admin_graphs"),
        InlineKeyboardButton(text="📋 এক্সপোর্ট", callback_data="admin_export")
    )
    
    builder.row(
        InlineKeyboardButton(text="🔙 অ্যাডমিন মেনু", callback_data="back_to_admin")
    )
    
    return builder.as_markup()

def get_payments_menu(payments: List) -> InlineKeyboardMarkup:
    """Get payments menu"""
    builder = InlineKeyboardBuilder()
    
    for payment in payments:
        builder.row(
            InlineKeyboardButton(
                text=f"✅ ভেরিফাই {payment.id}",
                callback_data=f"{payment.id}_verify"
            ),
            InlineKeyboardButton(
                text=f"❌ রিজেক্ট {payment.id}",
                callback_data=f"{payment.id}_reject"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="🔄 রিফ্রেশ", callback_data="admin_pending_payments"),
        InlineKeyboardButton(text="🔙 অ্যাডমিন মেনু", callback_data="back_to_admin")
    )
    
    return builder.as_markup()

def get_pending_bots_menu(bots: List) -> InlineKeyboardMarkup:
    """Get pending bots menu"""
    builder = InlineKeyboardBuilder()
    
    for bot in bots:
        builder.row(
            InlineKeyboardButton(
                text=f"✅ এপ্রুভ {bot.bot_name}",
                callback_data=f"{bot.id}_approve"
            ),
            InlineKeyboardButton(
                text=f"❌ রিজেক্ট {bot.bot_name}",
                callback_data=f"{bot.id}_reject_bot"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="🔄 রিফ্রেশ", callback_data="admin_pending_bots"),
        InlineKeyboardButton(text="🔙 অ্যাডমিন মেনু", callback_data="back_to_admin")
    )
    
    return builder.as_markup()

def get_cancel_menu() -> InlineKeyboardMarkup:
    """Get cancel menu"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="❌ বাতিল", callback_data="cancel_action")
    )
    
    return builder.as_markup()

def get_reset_confirmation_menu() -> InlineKeyboardMarkup:
    """Get reset confirmation menu"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="⚠️ হ্যাঁ, রিসেট করুন", callback_data="confirm_reset"),
        InlineKeyboardButton(text="❌ না, বাতিল করুন", callback_data="cancel_reset")
    )
    
    return builder.as_markup()