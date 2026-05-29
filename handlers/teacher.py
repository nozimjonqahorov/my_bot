from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from utils.keyboards import teacher_start_keyboard, answer_inline, broadcast_confirm_inline
from utils.helpers import get_user_role
from db import AsyncSessionLocal, User, Question, Answer
from sqlalchemy import select, update, func
from states.teacher_states import TeacherState

router = Router()

# Teacher /setup command handled elsewhere, but ensure teacher role
@router.message(Command('setup_ustoz_2026'))
async def setup_teacher(message: Message):
    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(User).where(User.role == 'teacher'))
        if existing.scalar_one_or_none():
            await message.answer("❌ Xatolik: Ustoz allaqachon tayinlangan.")
            return
        # Upsert user as teacher
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar_one_or_none()
        if user:
            user.role = 'teacher'
        else:
            user = User(telegram_id=message.from_user.id, role='teacher')
            session.add(user)
        await session.commit()
    await message.answer("✅ Siz bosh ustoz (teacher) sifatida ro'yxatdan o'tdingiz!")

# List pending questions
@router.message(F.text.in_({"📥 Kelgan savollar", "Kelgan savollar"}))
async def list_pending(message: Message):
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Question).where(Question.status == 'pending'))
        pending = res.scalars().all()
        if not pending:
            await message.answer("Hozirda savollar yo'q.")
            return
        bot: Bot = message.bot
        for q in pending:
            anon = "🔒 Anonim" if q.is_anonymous else f"👤 {q.student_id}"
            caption = f"{anon}\nID: {q.id}\nSavol:"
            if q.text_content:
                await bot.send_message(message.chat.id, caption + "\n" + q.text_content,
                                       reply_markup=answer_inline(q.id))
            else:
                if q.file_type == 'voice':
                    await bot.send_voice(message.chat.id, q.file_id, caption=caption,
                                          reply_markup=answer_inline(q.id))
                elif q.file_type == 'video':
                    await bot.send_video(message.chat.id, q.file_id, caption=caption,
                                          reply_markup=answer_inline(q.id))
                elif q.file_type == 'document':
                    await bot.send_document(message.chat.id, q.file_id, caption=caption,
                                            reply_markup=answer_inline(q.id))

# Start answering a question
@router.callback_query(F.data.startswith('answer_'))
async def start_answer(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    q_id = int(callback.data.split('_')[1])
    await state.update_data(question_id=q_id)
    await state.set_state(TeacherState.waiting_answer)
    await callback.message.edit_text("Javobingizni yuboring (matn, ovoz, video yoki hujjat).")

# Receive answer from teacher
@router.message(TeacherState.waiting_answer, F.content_type.in_({'text', 'voice', 'video', 'document'}))
async def receive_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    q_id = data.get('question_id')
    async with AsyncSessionLocal() as session:
        # fetch question and student id
        q_res = await session.execute(select(Question).where(Question.id == q_id))
        question = q_res.scalar_one()
        # Prepare answer record
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
        ans = Answer(question_id=q_id,
                     teacher_id=message.from_user.id,
                     text_content=text,
                     file_id=file_id,
                     file_type=file_type)
        session.add(ans)
        await session.execute(update(Question).where(Question.id == q_id).values(status='answered'))
        await session.commit()
    # Forward answer to student
    bot: Bot = message.bot
    if question.is_anonymous:
        prefix = "🗨️ Ustoz javob berdi (anonim)."
    else:
        prefix = f"🗨️ Ustoz {message.from_user.full_name} javob berdi."
    if text:
        await bot.send_message(question.student_id, f"{prefix}\n{text}")
    else:
        if file_type == 'voice':
            await bot.send_voice(question.student_id, file_id, caption=prefix)
        elif file_type == 'video':
            await bot.send_video(question.student_id, file_id, caption=prefix)
        elif file_type == 'document':
            await bot.send_document(question.student_id, file_id, caption=prefix)
    await message.answer("Javob yuborildi! ✅")
    await state.clear()

# Statistics
@router.message(F.text.in_({"📊 Statistika", "Statistika"}))
async def stats(message: Message):
    async with AsyncSessionLocal() as session:
        total_q = await session.scalar(select(func.count(Question.id)))
        answered_q = await session.scalar(select(func.count(Question.id)).where(Question.status == 'answered'))
        pending_q = total_q - answered_q
        await message.answer(
            f"📈 Statistika\nUmumiy savollar: {total_q}\nJavob berilgan: {answered_q}\nKutilayotgan: {pending_q}"
        )

# Broadcast flow
@router.message(F.text.in_({"📢 Hammaga xabar yuborish", "Hammaga xabar yuborish"}))
async def start_broadcast(message: Message, state: FSMContext):
    await state.set_state(TeacherState.waiting_broadcast)
    await message.answer("Xabar matnini yuboring (matn, ovoz, video yoki hujjat).")

@router.message(TeacherState.waiting_broadcast, F.content_type.in_({'text', 'voice', 'video', 'document'}))
async def receive_broadcast(message: Message, state: FSMContext):
    data = {}
    if message.text:
        data['broadcast_text'] = message.text
    elif message.voice:
        data['broadcast_file_id'] = message.voice.file_id
        data['broadcast_file_type'] = 'voice'
    elif message.video:
        data['broadcast_file_id'] = message.video.file_id
        data['broadcast_file_type'] = 'video'
    elif message.document:
        data['broadcast_file_id'] = message.document.file_id
        data['broadcast_file_type'] = 'document'
    await state.update_data(**data)
    await message.answer("Tasdiqlash uchun quyidagi tugmalarni bosing:", reply_markup=broadcast_confirm_inline())

@router.callback_query(F.data == 'broadcast_confirm')
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    text = data.get('broadcast_text')
    file_id = data.get('broadcast_file_id')
    file_type = data.get('broadcast_file_type')
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(User.telegram_id).where(User.role == 'student'))
        students = [row[0] for row in res.fetchall()]
        bot: Bot = callback.bot
        for sid in students:
            if text:
                await bot.send_message(sid, text)
            else:
                if file_type == 'voice':
                    await bot.send_voice(sid, file_id)
                elif file_type == 'video':
                    await bot.send_video(sid, file_id)
                elif file_type == 'document':
                    await bot.send_document(sid, file_id)
    await callback.message.edit_text("Xabar barcha talabalarga yuborildi.")
    await state.clear()

@router.callback_query(F.data == 'broadcast_cancel')
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("Xabar yuborish bekor qilindi.")
    await state.clear()
