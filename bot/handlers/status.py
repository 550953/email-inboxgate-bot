from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandObject

from bot.services.supabase import get_order_by_id
from bot.keyboards.inline import order_actions_kb

router = Router(name="status")

STATUS_EMOJI = {
    "pending": "⏳",
    "queued": "📋",
    "processing": "🔄",
    "completed": "✅",
    "failed": "❌",
    "cancelled": "🚫",
}


def format_order(order: dict) -> str:
    emoji = STATUS_EMOJI.get(order["status"], "❓")
    text = (
        f"{emoji} <b>Заказ #{order['id']}</b>\n\n"
        f"Статус: <b>{order['status']}</b>\n"
    )
    if order.get("status_message"):
        text += f"Сообщение: {order['status_message']}\n"
    if order.get("estimated_minutes"):
        text += f"Примерное время: ~{order['estimated_minutes']} мин\n"
    if order.get("accounts_count"):
        text += f"Аккаунтов: {order['accounts_count']}\n"
    if order.get("result_file_url"):
        text += f'\n📦 <a href="{order["result_file_url"]}">Скачать ZIP</a>'
    if order.get("error_message"):
        text += f"\n\n⚠️ {order['error_message']}"
    return text


@router.message(Command("status"))
async def cmd_status(message: Message, command: CommandObject, db_user: dict):
    if not command.args:
        await message.answer(
            "Укажи номер заказа.\nПример: <code>/status 47</code>",
            parse_mode="HTML",
        )
        return

    try:
        order_id = int(command.args.strip().lstrip("#"))
    except ValueError:
        await message.answer("Номер заказа должен быть числом.")
        return

    order = await get_order_by_id(order_id)
    if not order:
        await message.answer(f"Заказ #{order_id} не найден.")
        return

    if order["user_id"] != db_user["id"]:
        await message.answer("Это не ваш заказ.")
        return

    await message.answer(
        format_order(order),
        parse_mode="HTML",
        reply_markup=order_actions_kb(order_id),
        disable_web_page_preview=True,
    )


@router.callback_query(F.data.startswith("status:"))
async def cb_status(callback: CallbackQuery, db_user: dict):
    order_id = int(callback.data.split(":")[1])
    order = await get_order_by_id(order_id)

    if not order or order["user_id"] != db_user["id"]:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    await callback.message.edit_text(
        format_order(order),
        parse_mode="HTML",
        reply_markup=order_actions_kb(order_id),
        disable_web_page_preview=True,
    )
    await callback.answer("Обновлено")
