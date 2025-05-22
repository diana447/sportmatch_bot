from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
from models import User, async_session_maker
from sqlalchemy import select
from aiogram import types

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
    await message.answer("Темп қандай? (жәй, орташа, жылдам)")
    await state.set_state(Form.pace)

@router.message(Form.pace)
async def process_pace(message: Message, state: FSMContext):
    await state.update_data(pace=message.text)
    await message.answer("Қай уақытта ыңғайлы? (таңертең/кешке)")
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
def register_handlers(dp):
    dp.include_router(router)

