# keyboards/inline_keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config.settings import settings

def get_plans_keyboard() -> InlineKeyboardMarkup:
    """Get plans selection keyboard"""
    builder = InlineKeyboardBuilder()
    
    for plan_id, plan_data in settings.PLANS.items():
        builder.row(
            InlineKeyboardButton(
                text=f"{plan_data['name']} - {plan_data['price']} টাকা",
                callback_data=f"plan_{plan_id}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="❌ বাতিল", callback_data="cancel_payment")
    )
    
    return builder.as_markup()

def get_payment_methods_keyboard() -> InlineKeyboardMarkup:
    """Get payment methods keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📱 বিকাশ", callback_data="method_bkash"),
        InlineKeyboardButton(text="💳 নগদ", callback_data="method_nagad")
    )
    
    builder.row(
        InlineKeyboardButton(text="🚀 রকেট", callback_data="method_rocket"),
        InlineKeyboardButton(text="❌ বাতিল", callback_data="cancel_payment")
    )
    
    return builder.as_markup()

def get_payment_instructions_keyboard() -> InlineKeyboardMarkup:
    """Get payment instructions keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✅ পেমেন্ট সম্পন্ন", callback_data="payment_done"),
        InlineKeyboardButton(text="❌ বাতিল", callback_data="cancel_payment")
    )
    
    return builder.as_markup()

def get_token_input_keyboard() -> InlineKeyboardMarkup:
    """Get token input keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🔑 টোকেন দিন", callback_data="token_input"),
        InlineKeyboardButton(text="❌ বাতিল", callback_data="cancel_creation")
    )
    
    return builder.as_markup()

def get_bot_creation_plans_keyboard() -> InlineKeyboardMarkup:
    """Get bot creation plans keyboard"""
    builder = InlineKeyboardBuilder()
    
    for plan_id, plan_data in settings.PLANS.items():
        builder.row(
            InlineKeyboardButton(
                text=f"{plan_data['name']} - {plan_data['price']} টাকা",
                callback_data=f"create_plan_{plan_id}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="🎁 ট্রায়াল ব্যবহার করুন", callback_data="use_trial"),
        InlineKeyboardButton(text="❌ বাতিল", callback_data="cancel_creation")
    )
    
    return builder.as_markup()

def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Get simple cancel keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="❌ বাতিল", callback_data="cancel_action")
    )
    
    return builder.as_markup()

def get_language_selection_keyboard() -> InlineKeyboardMarkup:
    """Get language selection keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🇧🇩 বাংলা", callback_data="lang_bangla"),
        InlineKeyboardButton(text="🌐 বাংলিশ", callback_data="lang_banglish")
    )
    
    builder.row(
        InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_english"),
        InlineKeyboardButton(text="🔙 পিছনে", callback_data="back_to_settings")
    )
    
    return builder.as_markup()

def get_yes_no_keyboard() -> InlineKeyboardMarkup:
    """Get yes/no keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✅ হ্যাঁ", callback_data="yes"),
        InlineKeyboardButton(text="❌ না", callback_data="no")
    )
    
    return builder.as_markup()