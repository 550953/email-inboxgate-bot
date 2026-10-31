from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from bot.services.supabase import get_user_orders
from bot.keyboards.inline import back_to_menu_kb
from bot.handlers.status import STATUS_EMOJI

router = Router(name="my_orders")


@router.message(Command("my"))
async def cmd_my(message: Message, db_user: dict):
    orders = await get_user_orders(db_user["id"], limit=8)

    if not orders:
        await message.answer(
            "У тебя пока нет заказов.\nНажми /new чтобы создать первый.",
            reply_markup=back_to_menu_kb(),
        )
        return

    lines = ["📋 <b>Твои последние заказы:</b>\n"]
    for o in orders:
        emoji = STATUS_EMOJI.get(o["status"], "❓")
        lines.append(
            f"{emoji} <b>#{o['id']}</b> — {o['status']} ({o['accounts_count']} акк.)"
        )

    lines.append("\nПодробнее: <code>/status 47</code>")
    await message.answer(
        "\n".join(lines), parse_mode="HTML", reply_markup=back_to_menu_kb()
    )


@router.callback_query(F.data == "my_orders")
async def cb_my_orders(callback: CallbackQuery, db_user: dict):
    orders = await get_user_orders(db_user["id"], limit=8)

    if not orders:
        text = "У тебя пока нет заказов."
    else:
        lines = ["📋 <b>Твои последние заказы:</b>\n"]
        for o in orders:
            emoji = STATUS_EMOJI.get(o["status"], "❓")
            lines.append(
                f"{emoji} <b>#{o['id']}</b> — {o['status']} ({o['accounts_count']} акк.)"
            )
        lines.append("\nПодробнее: <code>/status 47</code>")
        text = "\n".join(lines)

    await callback.message.edit_text(
        text, parse_mode="HTML", reply_markup=back_to_menu_kb()
    )
    await callback.answer()
