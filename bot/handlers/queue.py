from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from bot.services.supabase import get_queue_stats
from bot.keyboards.inline import back_to_menu_kb

router = Router(name="queue")


@router.message(Command("queue"))
async def cmd_queue(message: Message):
    stats = await get_queue_stats()
    pending = stats["pending_count"]
    processing = stats["processing_count"]

    status_line = (
        "🔄 Сейчас сервер проверяет заказ"
        if processing
        else "✅ Сервер свободен"
    )

    text = (
        f"📊 <b>Состояние очереди</b>\n\n"
        f"{status_line}\n\n"
        f"В очереди: <b>{pending}</b>\n"
        f"В обработке: <b>{processing}</b>\n\n"
        f"Примерное время ожидания зависит от размера заказов."
    )
    await message.answer(text, parse_mode="HTML", reply_markup=back_to_menu_kb())


@router.callback_query(F.data == "queue")
async def cb_queue(callback: CallbackQuery):
    stats = await get_queue_stats()
    pending = stats["pending_count"]
    processing = stats["processing_count"]

    status_line = (
        "🔄 Сейчас сервер проверяет заказ"
        if processing
        else "✅ Сервер свободен"
    )

    text = (
        f"📊 <b>Состояние очереди</b>\n\n"
        f"{status_line}\n\n"
        f"В очереди: <b>{pending}</b>\n"
        f"В обработке: <b>{processing}</b>"
    )
    await callback.message.edit_text(
        text, parse_mode="HTML", reply_markup=back_to_menu_kb()
    )
    await callback.answer()
