from aiogram import Router, F, Bot, types
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
from sqlalchemy import select

from models import User, async_session_maker, get_matches_for, save_like, check_mutual_like
from reply_keyboard import pace_keyboard, time_keyboard
from inline_keyboard import match_keyboard
from location_matcher import suggest_location

import asyncio

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

@router.message(Command("menu"))
async def show_main_menu(message: Message):
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="⚙ Өзгерту анкетаны")],
            [types.KeyboardButton(text="🔄 Обновить совпадения")],
            [types.KeyboardButton(text="👀 Анкетаны көру")],
            [types.KeyboardButton(text="🚀 Жаңа адамды табу")]
        ],
        resize_keyboard=True
    )
    await message.answer("Басты мәзір:", reply_markup=keyboard)

@router.message(F.text == "👀 Анкетаны көру")
async def view_profile(message: Message):
    async with async_session_maker() as session:
        user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
        if user:
            text = (
                f"👤 <b>{user.name}</b>\n"
                f"🏙 Қала: {user.city}\n"
                f"📍 Локация: {user.location}\n"
                f"⏱ Темп: {user.pace} мин/км\n"
                f"🕓 Уақыт: {user.time}"
            )
            await message.answer(text, parse_mode="HTML")
        else:
            await message.answer("Сізде анкета әлі жоқ сияқты. /start арқылы бастаңыз ✍️")

@router.message(F.text == "🔄 Обновить совпадения")
async def refresh_matches(message: Message):
    await show_next_match(message.from_user.id, message.bot)

@router.message(F.text == "🚀 Жаңа адамды табу")
async def find_new_match(message: Message):
    await show_next_match(message.from_user.id, message.bot)

@router.message(Form.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Қай қаладансың?")
    await state.set_state(Form.city)

@router.message(Form.city)
async def process_city(message: Message, state: FSMContext):
    edit = await state.get_data()
    if edit.get("edit_mode"):
        async with async_session_maker() as session:
            user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
            if user:
                user.city = message.text
                await session.commit()
        await message.answer("✅ Қала өзгертілді", reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
        return
    await state.update_data(city=message.text)
    await message.answer("Нақты локация (мысалы, парк, аудан)?")
    await state.set_state(Form.location)

@router.message(Form.location)
async def process_location(message: Message, state: FSMContext):
    edit = await state.get_data()
    if edit.get("edit_mode"):
        async with async_session_maker() as session:
            user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
            if user:
                user.location = message.text
                await session.commit()
        await message.answer("✅ Локация өзгертілді", reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
        return
    suggested = suggest_location(message.text)
    location = suggested if suggested else message.text
    await state.update_data(location=location)
    await message.answer("Темп қандай? (минут/км — таңдаңыз ең жақын мәнді)", reply_markup=pace_keyboard())
    await state.set_state(Form.pace)

@router.message(Form.pace)
async def process_pace(message: Message, state: FSMContext):
    edit = await state.get_data()
    if edit.get("edit_mode"):
        async with async_session_maker() as session:
            user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
            if user:
                user.pace = message.text
                await session.commit()
        await message.answer("✅ Темп өзгертілді", reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
        return
    await state.update_data(pace=message.text)
    await message.answer("Қай уақытта жүгіргіңіз келеді? 🕓", reply_markup=time_keyboard())
    await state.set_state(Form.time)

@router.message(Form.time)
async def process_time(message: Message, state: FSMContext):
    edit = await state.get_data()
    if edit.get("edit_mode"):
        async with async_session_maker() as session:
            user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
            if user:
                user.time = message.text
                await session.commit()
        await message.answer("✅ Уақыт өзгертілді", reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
        return
    user_data = await state.get_data()
    await state.clear()
    async with async_session_maker() as session:
        existing_user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
        if existing_user:
            existing_user.name = user_data["name"]
            existing_user.city = user_data["city"]
            existing_user.location = user_data["location"]
            existing_user.pace = user_data["pace"]
            existing_user.time = message.text
        else:
            session.add(User(
                telegram_id=message.from_user.id,
                name=user_data["name"],
                city=user_data["city"],
                location=user_data["location"],
                pace=user_data["pace"],
                time=message.text
            ))
        await session.commit()
    await message.answer("Рақмет! Анкета сақталды ✅", reply_markup=types.ReplyKeyboardRemove())
    await show_next_match(message.from_user.id, message.bot)

async def remind_if_no_response(user_id: int, match_id: int, bot: Bot):
    await asyncio.sleep(600)
    async with async_session_maker() as session:
        stmt = select(User).where(User.telegram_id == user_id)
        user = await session.scalar(stmt)
        if user:
            liked = await session.execute(select(User).where(User.id == match_id))
            if liked.scalar():
                await bot.send_message(user_id, "Сіз әлі жауап берген жоқсыз 🕓. Бұл адаммен жүгіргіңіз келе ме?", reply_markup=match_keyboard(match_id))

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
        f"⏱ Темп: {match.pace} мин/км"
    )
    keyboard = match_keyboard(match.id)
    await bot.send_message(user_id, text, reply_markup=keyboard, parse_mode="HTML")
    asyncio.create_task(remind_if_no_response(user_id, match.id, bot))

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
    await callback.message.edit_reply_markup()
    await show_next_match(from_user, callback.bot)

@router.message(F.text == "⚙ Өзгерту анкетаны")
@router.message(Command("edit"))
async def edit_profile(message: Message):
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📍 Локация"), types.KeyboardButton(text="🕓 Уақыт")],
            [types.KeyboardButton(text="⏱ Темп"), types.KeyboardButton(text="🏙 Қала")],
            [types.KeyboardButton(text="🔁 Бәрін қайта толтыру")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("Қандай ақпаратты өзгерткіңіз келеді?", reply_markup=keyboard)

@router.message(F.text.in_({"📍 Локация", "🕓 Уақыт", "⏱ Темп", "🏙 Қала", "🔁 Бәрін қайта толтыру"}))
async def edit_field(message: Message, state: FSMContext):
    field = message.text
    await state.set_data({"edit_mode": True})
    if field == "📍 Локация":
        await message.answer("Жаңа локацияны енгізіңіз:")
        await state.set_state(Form.location)
    elif field == "🕓 Уақыт":
        await message.answer("Жаңа уақытты таңдаңыз:", reply_markup=time_keyboard())
        await state.set_state(Form.time)
    elif field == "⏱ Темп":
        await message.answer("Жаңа темпті таңдаңыз:", reply_markup=pace_keyboard())
        await state.set_state(Form.pace)
    elif field == "🏙 Қала":
        await message.answer("Жаңа қаланы енгізіңіз:")
        await state.set_state(Form.city)
    elif field == "🔁 Бәрін қайта толтыру":
        await message.answer("Бастаймыз! Атыңды енгізші 😊", reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
        await state.set_state(Form.name)

def register_handlers(dp):
    dp.include_router(router)
