from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.keyboards.inline import main_menu_kb

router = Router(name="new")


@router.message(Command("new"))
async def cmd_new(message: Message):
    text = (
        "🚀 <b>Новая проверка</b>\n\n"
        "Лучше всего использовать WebApp — там удобно вставлять один аккаунт или список.\n\n"
        "Нажми кнопку ниже:"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_kb())
