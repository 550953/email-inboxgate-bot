import asyncio
import logging
import os
import json
import hmac
import hashlib
from urllib.parse import parse_qsl

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, MenuButtonWebApp, WebAppInfo

from bot.config import settings
from bot.handlers import main_router
from bot.middlewares.auth import AuthMiddleware
from bot.services.supabase import get_or_create_user, create_order

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def validate_init_data(init_data: str, bot_token: str) -> dict | None:
    """
    Проверяет подпись Telegram WebApp initData.
    Возвращает parsed data или None если невалидно.
    """
    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = parsed.pop("hash", None)
        if not received_hash:
            return None

        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed.items())
        )

        secret_key = hmac.new(
            b"WebAppData", bot_token.encode(), hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(calculated_hash, received_hash):
            logger.warning("initData hash mismatch")
            return None

        return parsed
    except Exception as e:
        logger.exception("validate_init_data error: %s", e)
        return None


async def health_handler(request: web.Request) -> web.Response:
    return web.Response(text="OK", status=200)


async def create_order_handler(request: web.Request) -> web.Response:
    """
    POST /api/create-order
    Body: { "initData": "...", "type": "single"|"list", "login": "...", "password": "...", "text": "..." }
    """
    # CORS
    if request.method == "OPTIONS":
        return web.Response(
            status=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            },
        )

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Invalid JSON"}, status=400)

    init_data = body.get("initData") or ""
    logger.info("=== /api/create-order === initData_len=%s type=%s", len(init_data), body.get("type"))

    if not init_data:
        return web.json_response({"ok": False, "error": "initData required"}, status=400)

    parsed = validate_init_data(init_data, settings.telegram_bot_token)
    if not parsed:
        logger.warning("Invalid initData")
        return web.json_response({"ok": False, "error": "Invalid initData"}, status=403)

    # user из initData
    try:
        user_data = json.loads(parsed.get("user", "{}"))
        telegram_id = user_data.get("id")
        if not telegram_id:
            return web.json_response({"ok": False, "error": "No user in initData"}, status=400)
    except Exception as e:
        logger.exception("parse user error: %s", e)
        return web.json_response({"ok": False, "error": "Bad user data"}, status=400)

    logger.info("telegram_id from initData = %s", telegram_id)

    # создаём/получаем пользователя
    try:
        db_user = await get_or_create_user(
            telegram_id=telegram_id,
            username=user_data.get("username"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            language_code=user_data.get("language_code"),
            is_premium=bool(user_data.get("is_premium", False)),
        )
    except Exception as e:
        logger.exception("get_or_create_user failed: %s", e)
        return web.json_response({"ok": False, "error": f"User error: {e}"}, status=500)

    user_id = db_user.get("id")
    if not user_id:
        return web.json_response({"ok": False, "error": "No user id"}, status=500)

    # парсим аккаунты
    accounts = []
    order_type = body.get("type") or "single"

    if order_type == "single":
        login = (body.get("login") or "").strip()
        password = (body.get("password") or "").strip()
        if login and password:
            accounts = [{"login": login, "password": password}]
    elif order_type == "list":
        text = body.get("text") or ""
        for line in text.strip().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                login, password = line.split(":", 1)
            elif ";" in line:
                login, password = line.split(";", 1)
            else:
                continue
            login = login.strip()
            password = password.strip()
            if login and password:
                accounts.append({"login": login, "password": password})

    if not accounts:
        return web.json_response({"ok": False, "error": "No valid accounts"}, status=400)

    if len(accounts) > 50:
        return web.json_response({"ok": False, "error": "Max 50 accounts"}, status=400)

    logger.info("creating order for user_id=%s accounts=%s", user_id, len(accounts))

    try:
        order = await create_order(
            user_id=user_id,
            order_type="single" if len(accounts) == 1 else "bulk",
            accounts=accounts,
            status_message="Заказ принят, ожидает проверки",
            estimated_minutes=15,
        )
        order_id = order["id"]
        logger.info("ORDER CREATED #%s", order_id)
    except Exception as e:
        logger.exception("create_order failed: %s", e)
        return web.json_response({"ok": False, "error": f"DB error: {e}"}, status=500)

    # пробуем отправить сообщение в Telegram
    bot: Bot = request.app["bot"]
    try:
        text = (
            f"✅ <b>Заказ принят</b>\n\n"
            f"Номер: <b>#{order_id}</b>\n"
            f"Аккаунтов: <b>{len(accounts)}</b>\n\n"
            f"Я сообщу, когда проверка будет готова."
        )
        await bot.send_message(chat_id=telegram_id, text=text, parse_mode="HTML")
        logger.info("notification sent to %s", telegram_id)
    except Exception as e:
        logger.warning("could not send telegram message: %s", e)

    return web.json_response(
        {
            "ok": True,
            "order_id": order_id,
            "accounts_count": len(accounts),
        },
        headers={"Access-Control-Allow-Origin": "*"},
    )


async def set_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="new", description="Новая проверка"),
        BotCommand(command="status", description="Статус заказа по номеру"),
        BotCommand(command="my", description="Мои последние заказы"),
        BotCommand(command="queue", description="Состояние очереди сервера"),
        BotCommand(command="cancel", description="Отменить последний заказ"),
        BotCommand(command="help", description="Формат списка и лимиты"),
    ]
    await bot.set_my_commands(commands)


async def set_menu_button(bot: Bot) -> None:
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="Открыть",
                web_app=WebAppInfo(url=settings.webapp_url),
            )
        )
    except Exception as e:
        logger.warning("Не удалось установить Menu Button: %s", e)


async def main() -> None:
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.update.middleware(AuthMiddleware())
    dp.include_router(main_router)

    await set_commands(bot)
    await set_menu_button(bot)

    # --- HTTP сервер ---
    app = web.Application()
    app["bot"] = bot

    app.router.add_get("/", health_handler)
    app.router.add_get("/healthz", health_handler)
    app.router.add_route("OPTIONS", "/api/create-order", create_order_handler)
    app.router.add_post("/api/create-order", create_order_handler)

    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info("HTTP server started on 0.0.0.0:%s", port)

    try:
        logger.info("Bot started (long polling)")
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
