from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser
from bot.services.supabase import get_or_create_user
import logging

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        tg_user: TgUser | None = data.get("event_from_user")

        if tg_user and not tg_user.is_bot:
            try:
                db_user = await get_or_create_user(
                    telegram_id=tg_user.id,
                    username=tg_user.username,
                    first_name=tg_user.first_name,
                    last_name=tg_user.last_name,
                    language_code=tg_user.language_code,
                    is_premium=bool(getattr(tg_user, "is_premium", False)),
                )
                data["db_user"] = db_user
            except Exception as e:
                logger.exception("AuthMiddleware error for user %s: %s", tg_user.id, e)
                # Заглушка, чтобы хендлеры не падали
                data["db_user"] = {
                    "id": None,
                    "telegram_id": tg_user.id,
                }

        return await handler(event, data)
