from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from bot.keyboards.inline import back_to_menu_kb

router = Router(name="help")

HELP_TEXT = """
📖 <b>Помощь — InboxGate</b>

<b>Формат одного аккаунта:</b>
<code>login:password</code>
или
<code>login;password</code>

<b>Формат списка:</b>
<code>
user1@gmail.com:pass123
user2@gmail.com;qwerty
user3@gmail.com:secret
</code>

<b>Команды:</b>
/new — Новая проверка (открыть WebApp)
/status &lt;номер&gt; — Статус заказа
/my — Мои последние заказы
/queue — Состояние очереди сервера
/cancel — Отменить последний заказ
/help — Эта справка

⚠️ <b>Ограничения:</b>
• 2FA пока не поддерживается
• Максимум 50 аккаунтов в одном заказе
• Не отправляйте один и тот же список слишком часто

Результат придёт уведомлением + ZIP-файл.
"""


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(HELP_TEXT, parse_mode="HTML", reply_markup=back_to_menu_kb())


@router.callback_query(F.data == "help")
async def cb_help(callback: CallbackQuery):
    await callback.message.edit_text(
        HELP_TEXT, parse_mode="HTML", reply_markup=back_to_menu_kb()
    )
    await callback.answer()
