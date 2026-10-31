from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

from bot.keyboards.inline import main_menu_kb

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, db_user: dict):
    text = (
        f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
        "<b>InboxGate</b> — проверка входа в Google-аккаунты.\n\n"
        "Отправь логин и пароль (один или списком) → сервер проверит → "
        "я пришлю ZIP с результатом.\n\n"
        "⚠️ <i>2FA пока не поддерживается.</i>\n\n"
        "Нажми кнопку ниже, чтобы открыть удобный WebApp:"
    )
    await message.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()
