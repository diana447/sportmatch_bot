from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def pace_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="5"), KeyboardButton(text="6"), KeyboardButton(text="7")],
            [KeyboardButton(text="8"), KeyboardButton(text="9"), KeyboardButton(text="10")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def time_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="6:00"), KeyboardButton(text="6:30")],
            [KeyboardButton(text="7:00"), KeyboardButton(text="7:30")],
            [KeyboardButton(text="8:00"), KeyboardButton(text="8:30")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
