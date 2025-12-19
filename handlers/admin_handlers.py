# handlers/admin_handlers.py
import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import crud
from database.session import get_db
from config.settings import settings
from core.admin_panel import AdminPanel
from keyboards import admin_keyboards
from config.security import Security

logger = logging.getLogger(__name__)
router = Router()
admin_panel = AdminPanel()

class AdminStates(StatesGroup):
    awaiting_password = State()
    awaiting_broadcast = State()
    awaiting_user_id = State()
    awaiting_bot_id = State()

@router.message(Command("admin"))
async def admin_command(message: Message, state: FSMContext):
    """Handle /admin command"""
    user_id = message.from_user.id
    
    if user_id != settings.OWNER_ID:
        await message.answer("❌ অনুমতি নেই।")
        return
    
    await message.answer(
        "🔐 অ্যাডমিন প্যানেলে প্রবেশ করতে পাসওয়ার্ড দিন:",
        reply_markup=types.ForceReply(selective=True)
    )
    await state.set_state(AdminStates.awaiting_password)

@router.message(AdminStates.awaiting_password)
async def admin_password(message: Message, state: FSMContext):
    """Handle admin password"""
    password = message.text
    
    if admin_panel.verify_owner(message.from_user.id, password):
        await message.answer(
            "✅ লগইন সফল!\n\nঅ্যাডমিন প্যানেল:",
            reply_markup=admin_keyboards.get_admin_main_menu()
        )
        await state.clear()
    else:
        await message.answer("❌ ভুল পাসওয়ার্ড।")
        await state.clear()

@router.callback_query(F.data == "admin_dashboard")
async def admin_dashboard(callback: CallbackQuery):
    """Show admin dashboard"""
    stats = admin_panel.get_dashboard_stats()
    
    dashboard_text = "📊 অ্যাডমিন ড্যাশবোর্ড:\n\n"
    dashboard_text += f"👥 মোট ইউজার: {stats.get('total_users', 0)}\n"
    dashboard_text += f"🤖 মোট বট: {stats.get('total_bots', 0)}\n"
    dashboard_text += f"✅ একটিভ বট: {stats.get('active_bots', 0)}\n\n"
    
    dashboard_text += "💰 পেমেন্ট স্ট্যাটাস:\n"
    payment_stats = stats.get('payment_stats', {})
    dashboard_text += f"  • মোট: {payment_stats.get('total', 0)}\n"
    dashboard_text += f"  • ভেরিফাইড: {payment_stats.get('verified', 0)}\n"
    dashboard_text += f"  • পেন্ডিং: {payment_stats.get('pending', 0)}\n"
    dashboard_text += f"  • রিজেক্টেড: {payment_stats.get('rejected', 0)}\n\n"
    
    await callback.message.edit_text(
        dashboard_text,
        reply_markup=admin_keyboards.get_admin_dashboard_menu()
    )

@router.callback_query(F.data == "admin_pending_payments")
async def pending_payments(callback: CallbackQuery):
    """Show pending payments"""
    with next(get_db()) as db:
        payments = crud.get_pending_payments(db)
        
        if not payments:
            await callback.message.edit_text(
                "✅ কোন পেন্ডিং পেমেন্ট নেই।",
                reply_markup=admin_keyboards.get_admin_main_menu()
            )
            return
        
        payments_text = "💰 পেন্ডিং পেমেন্ট:\n\n"
        for i, payment in enumerate(payments, 1):
            user = crud.get_user_by_id(db, payment.user_id)
            payments_text += f"{i}. ইউজার: @{user.username if user else 'N/A'}\n"
            payments_text += f"   💵 {payment.amount} টাকা ({payment.method})\n"
            payments_text += f"   🆔 ট্রানজেকশন: {payment.transaction_id}\n"
            payments_text += f"   ⏰ {payment.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            payments_text += f"   [ভেরিফাই]({payment.id}_verify) | [রিজেক্ট]({payment.id}_reject)\n\n"
        
        await callback.message.edit_text(
            payments_text,
            reply_markup=admin_keyboards.get_payments_menu(payments),
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

@router.callback_query(F.data.contains("_verify"))
async def verify_payment(callback: CallbackQuery):
    """Verify payment"""
    payment_id = int(callback.data.split("_")[0])
    
    success = admin_panel.verify_payment(
        payment_id=payment_id,
        verified_by=callback.from_user.id,
        status="verified"
    )
    
    if success:
        await callback.answer("✅ পেমেন্ট ভেরিফাই করা হয়েছে।")
    else:
        await callback.answer("❌ ভেরিফাই করতে সমস্যা।")
    
    # Refresh payments list
    await pending_payments(callback)

@router.callback_query(F.data.contains("_reject"))
async def reject_payment(callback: CallbackQuery):
    """Reject payment"""
    payment_id = int(callback.data.split("_")[0])
    
    success = admin_panel.verify_payment(
        payment_id=payment_id,
        verified_by=callback.from_user.id,
        status="rejected",
        notes="মালিক কর্তৃক রিজেক্ট"
    )
    
    if success:
        await callback.answer("❌ পেমেন্ট রিজেক্ট করা হয়েছে।")
    else:
        await callback.answer("❌ রিজেক্ট করতে সমস্যা।")
    
    # Refresh payments list
    await pending_payments(callback)

@router.callback_query(F.data == "admin_pending_bots")
async def pending_bots(callback: CallbackQuery):
    """Show pending bots"""
    with next(get_db()) as db:
        bots = crud.get_pending_bots(db)
        
        if not bots:
            await callback.message.edit_text(
                "✅ কোন পেন্ডিং বট নেই।",
                reply_markup=admin_keyboards.get_admin_main_menu()
            )
            return
        
        bots_text = "🤖 পেন্ডিং বট রিকোয়েস্ট:\n\n"
        for i, bot in enumerate(bots, 1):
            user = crud.get_user_by_id(db, bot.owner_id)
            bots_text += f"{i}. বট: {bot.bot_name}\n"
            bots_text += f"   👤 মালিক: @{user.username if user else 'N/A'}\n"
            bots_text += f"   📅 {bot.created_at.strftime('%Y-%m-%d')}\n"
            bots_text += f"   [এপ্রুভ]({bot.id}_approve) | [রিজেক্ট]({bot.id}_reject_bot)\n\n"
        
        await callback.message.edit_text(
            bots_text,
            reply_markup=admin_keyboards.get_pending_bots_menu(bots),
            parse_mode="Markdown"
        )

@router.callback_query(F.data.contains("_approve"))
async def approve_bot(callback: CallbackQuery):
    """Approve bot"""
    bot_id = int(callback.data.split("_")[0])
    
    success = admin_panel.approve_bot(
        bot_id=bot_id,
        verified_by=callback.from_user.id
    )
    
    if success:
        await callback.answer("✅ বট এপ্রুভ করা হয়েছে।")
    else:
        await callback.answer("❌ এপ্রুভ করতে সমস্যা।")
    
    # Refresh bots list
    await pending_bots(callback)

@router.callback_query(F.data.contains("_reject_bot"))
async def reject_bot(callback: CallbackQuery):
    """Reject bot"""
    bot_id = int(callback.data.split("_")[0])
    
    success = admin_panel.reject_bot(
        bot_id=bot_id,
        reason="মালিক কর্তৃক রিজেক্ট"
    )
    
    if success:
        await callback.answer("❌ বট রিজেক্ট করা হয়েছে।")
    else:
        await callback.answer("❌ রিজেক্ট করতে সমস্যা।")
    
    # Refresh bots list
    await pending_bots(callback)

@router.callback_query(F.data == "admin_broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    """Start broadcast"""
    await callback.message.edit_text(
        "📢 ব্রডকাস্ট মেসেজ দিন:\n\n"
        "মেসেজ টাইপ:\n"
        "• টেক্সট\n"
        "• ফটো ক্যাপশন\n"
        "• যেকোনো মিডিয়া",
        reply_markup=admin_keyboards.get_cancel_menu()
    )
    await state.set_state(AdminStates.awaiting_broadcast)

@router.message(AdminStates.awaiting_broadcast)
async def broadcast_send(message: Message, state: FSMContext):
    """Send broadcast"""
    result = await admin_panel.broadcast_message(
        message_text=message.text or message.caption,
        message_type="text"
    )
    
    if result["success"]:
        await message.answer(
            f"✅ ব্রডকাস্ট সফল!\n\n"
            f"✅ পাঠানো: {result['sent']}\n"
            f"❌ ব্যর্থ: {result['failed']}\n"
            f"📊 মোট: {result['total']}"
        )
    else:
        await message.answer(f"❌ ব্রডকাস্ট ব্যর্থ: {result['error']}")
    
    await state.clear()

@router.callback_query(F.data == "admin_block_user")
async def block_user_start(callback: CallbackQuery, state: FSMContext):
    """Start block user process"""
    await callback.message.edit_text(
        "🔒 ব্লক করতে চান ইউজার আইডি দিন:",
        reply_markup=admin_keyboards.get_cancel_menu()
    )
    await state.set_state(AdminStates.awaiting_user_id)

@router.message(AdminStates.awaiting_user_id)
async def block_user_execute(message: Message, state: FSMContext):
    """Execute user block"""
    try:
        user_id = int(message.text)
        success = admin_panel.block_user(user_id, "মালিক কর্তৃক ব্লক")
        
        if success:
            await message.answer(f"✅ ইউজার {user_id} ব্লক করা হয়েছে।")
        else:
            await message.answer(f"❌ ইউজার {user_id} ব্লক করতে সমস্যা।")
    except ValueError:
        await message.answer("❌ ভুল ইউজার আইডি। সংখ্যা দিন।")
    
    await state.clear()

@router.callback_query(F.data == "admin_logs")
async def show_logs(callback: CallbackQuery):
    """Show system logs"""
    logs = admin_panel.get_system_logs(limit=20)
    
    if not logs:
        await callback.message.edit_text(
            "📜 কোন লগ নেই।",
            reply_markup=admin_keyboards.get_admin_main_menu()
        )
        return
    
    logs_text = "📜 সর্বশেষ লগ (২০ টি):\n\n"
    logs_text += "".join(logs[-20:])
    
    # Truncate if too long
    if len(logs_text) > 4000:
        logs_text = logs_text[:4000] + "..."
    
    await callback.message.edit_text(
        logs_text,
        reply_markup=admin_keyboards.get_admin_main_menu()
    )

@router.callback_query(F.data == "admin_reset")
async def reset_system(callback: CallbackQuery):
    """Reset system confirmation"""
    await callback.message.edit_text(
        "⚠️ ⚠️ ⚠️ সতর্কতা ⚠️ ⚠️ ⚠️\n\n"
        "সিস্টেম রিসেট করলে:\n"
        "• সব ডাটা মুছে যাবে\n"
        "• সব ইউজার রিমুভ হবে\n"
        "• সব বট ডিলিট হবে\n"
        "• সব পেমেন্ট ডিলিট হবে\n\n"
        "নিশ্চিত হলে নিচের বাটনে ক্লিক করুন:",
        reply_markup=admin_keyboards.get_reset_confirmation_menu()
    )

@router.callback_query(F.data == "confirm_reset")
async def confirm_reset(callback: CallbackQuery):
    """Confirm system reset"""
    success = admin_panel.reset_system(confirm=True)
    
    if success:
        await callback.message.edit_text(
            "✅ সিস্টেম রিসেট করা হয়েছে।",
            reply_markup=admin_keyboards.get_admin_main_menu()
        )
    else:
        await callback.message.edit_text(
            "❌ রিসেট করতে সমস্যা।",
            reply_markup=admin_keyboards.get_admin_main_menu()
        )