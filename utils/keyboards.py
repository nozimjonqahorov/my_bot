from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def student_start_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✍️ Savol yoʻlash")],
            [KeyboardButton(text="👤 Savollarim tarixi")]
        ],
        resize_keyboard=True,
        selective=True
    )

def teacher_start_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📥 Kelgan savollar"), KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="📢 Hammaga xabar yuborish")]
        ],
        resize_keyboard=True,
        selective=True
    )

def anonymity_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="🔒 Anonim (Yashirin)", callback_data="anon_yes"),
            InlineKeyboardButton(text="👤 Ochiq (Ismim ko'rinsin)", callback_data="anon_no")
        ]]
    )

def answer_inline(question_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="✍️ Javob berish", callback_data=f"answer_{question_id}")]]
    )

def broadcast_confirm_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="broadcast_confirm"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="broadcast_cancel")
        ]]
    )
