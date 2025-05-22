from aiogram import Router, F, Bot, types
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
from models import User, async_session_maker, get_matches_for, save_like, check_mutual_like
from inline_keyboard import match_keyboard
from sqlalchemy import select
from reply_keyboard import pace_keyboard, time_keyboard

router = Router()

class Form(StatesGroup):
    name = State()
    city = State()
    location = State()
    pace = State()
    time = State()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await message.answer("Сәлем! Атыңды енгізші 😊")
    await state.set_state(Form.name)

@router.message(Form.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Қай қаладансың?")
    await state.set_state(Form.city)

@router.message(Form.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("Нақты локация (мысалы, парк, аудан)?")
    await state.set_state(Form.location)

@router.message(Form.location)
async def process_location(message: Message, state: FSMContext):
    await state.update_data(location=message.text)
    await message.answer("Темп қандай? (минут/км — таңдаңыз ең жақын мәнді)", reply_markup=pace_keyboard())
    await state.set_state(Form.pace)

@router.message(Form.pace)
async def process_pace(message: Message, state: FSMContext):
    await state.update_data(pace=message.text)
    await message.answer("Қай уақытта жүгіргіңіз келеді? 🕓", reply_markup=time_keyboard())
    await state.set_state(Form.time)

@router.message(Form.time)
async def process_time(message: Message, state: FSMContext):
    user_data = await state.get_data()
    await state.clear()

    async with async_session_maker() as session:
        session.add(User(
            telegram_id=message.from_user.id,
            name=user_data["name"],
            city=user_data["city"],
            location=user_data["location"],
            pace=user_data["pace"],
            time=message.text
        ))
        await session.commit()

    await message.answer("Рақмет! Анкета сақталды ✅")
    await show_next_match(message.from_user.id, message.bot)

async def show_next_match(user_id: int, bot: Bot):
    matches = await get_matches_for(user_id)
    if not matches:
        await bot.send_message(user_id, "Пока нет подходящих людей. Попробуйте позже 💫")
        return

    match = matches[0]

    text = (
        f"👤 <b>{match.name}</b>\n"
        f"📍 Локация: {match.location}\n"
        f"🏙 Қала: {match.city}\n"
        f"🕓 Уақыт: {match.time}\n"
        f"🏃 Темп: {match.pace}"
    )

    keyboard = match_keyboard(match.id)
    await bot.send_message(user_id, text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("like:") | F.data.startswith("dislike:"))
async def process_feedback(callback: CallbackQuery):
    from_user = callback.from_user.id
    data = callback.data.split(":")
    action, to_user = data[0], int(data[1])

    await save_like(from_user, to_user, action)

    if action == "like":
        mutual = await check_mutual_like(from_user, to_user)
        if mutual:
            async with async_session_maker() as session:
                from_user_obj = await session.scalar(select(User).where(User.telegram_id == from_user))
                to_user_obj = await session.scalar(select(User).where(User.telegram_id == to_user))

            if from_user_obj and to_user_obj:
                text = (
                    f"🎉 <b>{from_user_obj.name} и {to_user_obj.name} решили метчиться!</b>\n"
                    f"Бот нашёл совпадение 💖"
                )
                await callback.message.answer(text, parse_mode="HTML")

    await callback.message.edit_reply_markup()  # убрать кнопки
    await show_next_match(from_user, callback.bot)

def register_handlers(dp):
    dp.include_router(router)
