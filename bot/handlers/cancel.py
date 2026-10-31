from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.services.supabase import cancel_last_order
from bot.keyboards.inline import back_to_menu_kb

router = Router(name="cancel")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, db_user: dict):
    order = await cancel_last_order(db_user["id"])

    if not order:
        await message.answer(
            "Нет заказов, которые можно отменить.\n"
            "Отменять можно только заказы со статусом <b>pending</b> или <b>queued</b>.",
            parse_mode="HTML",
            reply_markup=back_to_menu_kb(),
        )
        return

    await message.answer(
        f"🚫 Заказ <b>#{order['id']}</b> отменён.",
        parse_mode="HTML",
        reply_markup=back_to_menu_kb(),
    )
