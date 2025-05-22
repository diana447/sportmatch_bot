from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def match_keyboard(to_user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❤️ Лайк", callback_data=f"like:{to_user_id}"),
            InlineKeyboardButton(text="❌ Дизлайк", callback_data=f"dislike:{to_user_id}")
        ]
    ])
