import json
import logging
from aiogram import Router, F
from aiogram.types import Message

from bot.services.supabase import create_order
from bot.keyboards.inline import order_actions_kb

router = Router(name="webapp")
logger = logging.getLogger(__name__)


def parse_accounts(raw: str) -> list[dict]:
    accounts = []
    for line in raw.strip().splitlines():
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
    return accounts


@router.message(F.web_app_data)
async def on_webapp_data(message: Message, db_user: dict = None):
    logger.info("=" * 70)
    logger.info(">>> WEBAPP DATA RECEIVED <<<")
    logger.info("from_user.id   = %s", message.from_user.id if message.from_user else None)
    logger.info("from_user.username = %s", message.from_user.username if message.from_user else None)
    logger.info("chat.id        = %s", message.chat.id if message.chat else None)
    logger.info("raw web_app_data.data = %s", getattr(message.web_app_data, "data", None))
    logger.info("db_user        = %s", db_user)

    try:
        payload = json.loads(message.web_app_data.data)
        logger.info("parsed payload = %s", payload)
    except Exception as e:
        logger.exception("JSON parse error: %s", e)
        await message.answer("❌ Не удалось прочитать данные из WebApp.")
        return

    accounts = []

    if payload.get("type") == "single":
        login = (payload.get("login") or "").strip()
        password = (payload.get("password") or "").strip()
        logger.info("single mode: login=%s password_len=%s", login, len(password) if password else 0)
        if login and password:
            accounts = [{"login": login, "password": password}]

    elif payload.get("type") == "list":
        text = payload.get("text") or ""
        logger.info("list mode: text_len=%s", len(text))
        accounts = parse_accounts(text)

    else:
        logger.warning("unknown payload type: %s", payload.get("type"))

    logger.info("parsed accounts count = %s", len(accounts))

    if not accounts:
        await message.answer("❌ Не найдено ни одного валидного аккаунта.")
        return

    if len(accounts) > 50:
        await message.answer("❌ Максимум 50 аккаунтов за один заказ.")
        return

    user_id = (db_user or {}).get("id")
    if not user_id:
        logger.error("db_user without id! db_user=%s", db_user)
        await message.answer("❌ Ошибка авторизации. Нажми /start и повтори.")
        return

    logger.info("calling create_order user_id=%s accounts=%s", user_id, len(accounts))

    try:
        order = await create_order(
            user_id=user_id,
            order_type="single" if len(accounts) == 1 else "bulk",
            accounts=accounts,
            status_message="Заказ принят, ожидает проверки",
            estimated_minutes=15,
        )
        logger.info("create_order SUCCESS order_id=%s", order.get("id"))
    except Exception as e:
        logger.exception("create_order FAILED: %s", e)
        await message.answer(f"❌ Ошибка при сохранении заказа: {e}")
        return

    order_id = order["id"]

    text = (
        f"✅ <b>Заказ принят</b>\n\n"
        f"Номер: <b>#{order_id}</b>\n"
        f"Аккаунтов: <b>{len(accounts)}</b>\n\n"
        f"Я сообщу, когда проверка будет готова."
    )

    try:
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=order_actions_kb(order_id),
        )
        logger.info("reply sent successfully for order #%s", order_id)
    except Exception as e:
        logger.exception("failed to send reply: %s", e)

    logger.info("=" * 70)
