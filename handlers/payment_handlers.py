# handlers/payment_handlers.py
import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import crud
from database.session import get_db
from config.settings import settings
from core.payment_handler import PaymentHandler
from keyboards import inline_keyboards
from utils.text_templates import TextTemplates

logger = logging.getLogger(__name__)
router = Router()
payment_handler = PaymentHandler()

class PaymentStates(StatesGroup):
    awaiting_plan = State()
    awaiting_payment_method = State()
    awaiting_transaction_id = State()
    awaiting_sender_number = State()
    awaiting_proof = State()

@router.message(Command("buyplan"))
async def buy_plan_command(message: Message, state: FSMContext):
    """Start plan purchase process"""
    user_id = message.from_user.id
    
    with next(get_db()) as db:
        user = crud.get_user(db, user_id)
        if not user:
            await message.answer("❌ আপনার অ্যাকাউন্ট পাওয়া যায়নি। /start দিন")
            return
    
    # Show plans
    plans_text = TextTemplates.get_plans_text()
    
    await message.answer(
        plans_text,
        reply_markup=inline_keyboards.get_plans_keyboard()
    )
    await state.set_state(PaymentStates.awaiting_plan)

@router.callback_query(F.data.startswith("plan_"))
async def select_plan(callback: CallbackQuery, state: FSMContext):
    """Handle plan selection"""
    plan_id = callback.data.split("_")[1]
    
    if plan_id not in settings.PLANS:
        await callback.answer("❌ ইনভ্যালিড প্ল্যান")
        return
    
    plan_data = settings.PLANS[plan_id]
    
    await state.update_data(plan_id=plan_id, amount=plan_data["price"])
    
    # Ask for payment method
    await callback.message.edit_text(
        f"💰 প্ল্যান: {plan_data['name']}\n"
        f"💵 মূল্য: {plan_data['price']} টাকা\n\n"
        f"পেমেন্ট মেথড সিলেক্ট করুন:",
        reply_markup=inline_keyboards.get_payment_methods_keyboard()
    )
    await state.set_state(PaymentStates.awaiting_payment_method)

@router.callback_query(F.data.startswith("method_"))
async def select_method(callback: CallbackQuery, state: FSMContext):
    """Handle payment method selection"""
    method = callback.data.split("_")[1]
    
    if method not in ["bkash", "nagad", "rocket"]:
        await callback.answer("❌ ইনভ্যালিড মেথড")
        return
    
    await state.update_data(method=method)
    
    # Show payment details
    payment_details = TextTemplates.get_payment_details_text()
    
    await callback.message.edit_text(
        payment_details,
        reply_markup=inline_keyboards.get_payment_instructions_keyboard()
    )

@router.message(F.text)
async def handle_transaction_id(message: Message, state: FSMContext):
    """Handle transaction ID input"""
    current_state = await state.get_state()
    
    if current_state == PaymentStates.awaiting_transaction_id:
        transaction_id = message.text.strip()
        
        if len(transaction_id) < 5:
            await message.answer("❌ ভুল ট্রানজেকশন আইডি। আবার দিন:")
            return
        
        await state.update_data(transaction_id=transaction_id)
        
        # Ask for sender number
        await message.answer(
            "📱 আপনার নাম্বার দিন (যে নাম্বার থেকে পেমেন্ট করেছেন):\n\n"
            "ফরম্যাট: 01XXXXXXXXX",
            reply_markup=types.ForceReply(selective=True)
        )
        await state.set_state(PaymentStates.awaiting_sender_number)
    
    elif current_state == PaymentStates.awaiting_sender_number:
        sender_number = message.text.strip()
        
        # Validate phone number
        if not sender_number.isdigit() or len(sender_number) != 11:
            await message.answer("❌ ভুল নাম্বার। আবার দিন:")
            return
        
        await state.update_data(sender_number=sender_number)
        
        # Ask for proof
        await message.answer(
            "📸 পেমেন্ট প্রুফ (স্ক্রিনশট) পাঠান:\n\n"
            "⚠️ স্ক্রিনশটে দেখতে হবে:\n"
            "• ট্রানজেকশন আইডি\n"
            "• পরিমাণ\n"
            "• সময়\n"
            "• রিসিভার নাম্বার\n\n"
            "ছবি আপলোড করুন:",
            reply_markup=inline_keyboards.get_cancel_keyboard()
        )
        await state.set_state(PaymentStates.awaiting_proof)

@router.message(F.photo)
async def handle_payment_proof(message: Message, state: FSMContext):
    """Handle payment proof photo"""
    current_state = await state.get_state()
    
    if current_state != PaymentStates.awaiting_proof:
        return
    
    # Get state data
    data = await state.get_data()
    plan_id = data.get("plan_id")
    amount = data.get("amount")
    method = data.get("method")
    transaction_id = data.get("transaction_id")
    sender_number = data.get("sender_number")
    
    if not all([plan_id, amount, method, transaction_id]):
        await message.answer("❌ তথ্য ইনকমপ্লিট। আবার চেষ্টা করুন।")
        await state.clear()
        return
    
    # Handle payment proof
    result = await payment_handler.handle_payment_proof(
        message=message,
        user_id=message.from_user.id,
        plan_type=plan_id,
        amount=amount,
        method=method,
        transaction_id=transaction_id,
        sender_number=sender_number
    )
    
    if result["success"]:
        await message.answer(
            "✅ পেমেন্ট প্রুফ সাবমিট করা হয়েছে!\n\n"
            f"পেমেন্ট আইডি: {result['payment_id']}\n"
            "মালিক ভেরিফাই করলে নোটিফিকেশন পাবেন।\n\n"
            "⏳ ভেরিফিকেশনের জন্য অপেক্ষা করুন..."
        )
    else:
        await message.answer(
            f"❌ পেমেন্ট সাবমিট ব্যর্থ: {result['message']}\n\n"
            "আবার চেষ্টা করুন /buyplan"
        )
    
    await state.clear()

@router.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback: CallbackQuery, state: FSMContext):
    """Cancel payment process"""
    await state.clear()
    await callback.message.edit_text(
        "❌ পেমেন্ট প্রক্রিয়া বাতিল করা হয়েছে।\n\n"
        "আবার শুরু করতে /buyplan দিন।"
    )