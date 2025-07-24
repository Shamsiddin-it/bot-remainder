from db import Base, Task, engine, async_session
from aiogram import Dispatcher, Bot, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import datetime
from config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

scheduler = AsyncIOScheduler()

class MyStates(StatesGroup):
    title = State()
    description = State()
    remaining_time = State()


@dp.message(F.text == '/start')
async def start(message: Message, state: FSMContext):
    await message.answer("Salom aleykum! Enter task title: ")
    await state.set_state(MyStates.title)

@dp.message(MyStates.title)
async def get_title(message: Message, state: FSMContext):
    title = message.text
    await state.update_data(title=title)
    await message.answer("Enter task's description: ")
    await state.set_state(MyStates.description)

@dp.message(MyStates.description)
async def get_description(message: Message, state: FSMContext):
    description = message.text
    await state.update_data(description=description)
    await message.answer("Enter task's remaining time (YYYY-MM-DD HH:MM): ")
    await state.set_state(MyStates.remaining_time)

def parse_datetime(dt_str: str):
    try:
        # Adjust format as needed, here expecting '2025-07-18 21:30'
        return datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    except ValueError:
        return None

async def send(chat_id, text):
    await bot.send_message(chat_id=chat_id, text=text)

async def add_task_job(task: Task):
    # now = datetime.datetime.utcnow()
    # if task.remaining_time > datetime.datetime.now():
        try:
            scheduler.add_job(
                send,
                trigger='date',
                run_date=task.remaining_time,
                args=(task.tg_id, f"{task.title} -- {task.description} -- {task.remaining_time}"),
                id=str(task.id),
                replace_existing=True
            )
        except Exception as e:
            print(f"Error scheduling task {task.id}: {e}")

@dp.message(MyStates.remaining_time)
async def get_time(message: Message, state: FSMContext):
    dt = message.text
    if dt is None:
        await message.answer("Invalid datetime format. Please use YYYY-MM-DD HH:MM")
        return
    data = await state.get_data()
    title = data.get('title')
    description = data.get('description')
    async with async_session() as session:
        task = Task(title=title, description=description, remaining_time=dt, tg_id=message.from_user.id)
        session.add(task)
        await session.commit()
        await state.clear()
        await message.answer(f"We will remind you about this task on {dt}")
        await add_task_job(task)

async def remind():
    async with async_session() as session:
        res = await session.execute(select(Task))
        tasks = res.scalars().all()
    # now = datetime.datetime.utcnow()
    # for task in tasks:
    #     if task.remaining_time > now:
    #         await add_task_job(task)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def main():
    await init_db()
    scheduler.start()
    await remind()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
