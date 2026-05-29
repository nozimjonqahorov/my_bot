from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from utils.keyboards import student_start_keyboard, anonymity_inline
from utils.helpers import get_user_role
from utils.keyboards import answer_inline
from db import AsyncSessionLocal, User, Question
from sqlalchemy import select, update
from states.student_states import StudentState

router = Router()

# Student /start command
@router.message(Command('start'))
async def cmd_start_student(message: Message, state: FSMContext):
    role = await get_user_role(message.from_user.id)
    if role == 'teacher':
        # forward to teacher start (handled in teacher router)
        return
    await message.answer(
        "Assalomu alaykum! Siz talaba sifatida savol yuborishingiz mumkin.",
        reply_markup=student_start_keyboard()
    )

# Ask anonymity
@router.message(F.text.in_({"✍️ Savol yoʻlash", "Savol yoʻlash"}))
async def ask_anonymity(message: Message, state: FSMContext):
    await state.set_state(StudentState.waiting_anonymity)
    await message.answer("Savolni anonim jo'natishni xohlaysizmi?", reply_markup=anonymity_inline())

# Process anonymity selection
@router.callback_query(F.data.startswith('anon_'))
async def process_anonymity(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    is_anon = callback.data == 'anon_yes'
    await state.update_data(is_anonymous=is_anon)
    await state.set_state(StudentState.waiting_content)
    await callback.message.edit_text("Savolingizni yuboring (matn, ovoz, video yoki hujjat).")

# Receive question content
@router.message(StudentState.waiting_content, F.content_type.in_({'text', 'voice', 'video', 'document'}))
async def receive_question(message: Message, state: FSMContext):
    data = await state.get_data()
    is_anon = data.get('is_anonymous', False)
    async with AsyncSessionLocal() as session:
        # Ensure user exists
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(telegram_id=message.from_user.id, role='student')
            session.add(user)
            await session.flush()
        # Determine content
        text = message.text if message.text else None
        file_id = None
        file_type = None
        if message.voice:
            file_id = message.voice.file_id
            file_type = 'voice'
        elif message.video:
            file_id = message.video.file_id
            file_type = 'video'
        elif message.document:
            file_id = message.document.file_id
            file_type = 'document'
        elif message.text:
            file_type = 'text'
        q = Question(
            student_id=message.from_user.id,
            is_anonymous=is_anon,
            text_content=text,
            file_id=file_id,
            file_type=file_type,
            status='pending'
        )
        session.add(q)
        await session.commit()
        await session.refresh(q)
        q_id = q.id
    await message.answer("Savolingiz qabul qilindi! 🎉")
    # Notify teacher if exists
    async with AsyncSessionLocal() as sess:
        teacher_res = await sess.execute(select(User.telegram_id).where(User.role == 'teacher'))
        teacher_id = teacher_res.scalar_one_or_none()
        if teacher_id:
            bot: Bot = message.bot
            anon_prefix = "🔒 Anonim" if is_anon else f"👤 {message.from_user.full_name}"
            caption = f"{anon_prefix}\nID: {q_id}\nYangi savol:"
            if text:
                await bot.send_message(teacher_id, caption + "\n" + text, reply_markup=answer_inline(q_id))
            else:
                if file_type == 'voice':
                    await bot.send_voice(teacher_id, file_id, caption=caption, reply_markup=answer_inline(q_id))
                elif file_type == 'video':
                    await bot.send_video(teacher_id, file_id, caption=caption, reply_markup=answer_inline(q_id))
                elif file_type == 'document':
                    await bot.send_document(teacher_id, file_id, caption=caption, reply_markup=answer_inline(q_id))
    await state.clear()

# Student history
@router.message(F.text.in_({"👤 Savollarim tarixi", "Savollarim tarixi"}))
async def student_history(message: Message):
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Question).where(Question.student_id == message.from_user.id))
        questions = res.scalars().all()
        if not questions:
            await message.answer("Siz hali savol yubormagansiz.")
            return
        for q in questions:
            status = "✅ Javob berildi" if q.status == 'answered' else "⏳ Javob kutilmoqda"
            txt = f"ID: {q.id}\nStatus: {status}\n"
            if q.text_content:
                txt += f"Savol: {q.text_content}\n"
            await message.answer(txt)
