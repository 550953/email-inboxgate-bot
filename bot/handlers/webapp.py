import json
from aiogram import Router, F
from aiogram.types import Message

from bot.services.supabase import create_order
from bot.keyboards.inline import order_actions_kb

router = Router(name="webapp")


def parse_accounts(raw: str) -> list[dict]:
    """
    Парсит текст вида:
    user1@gmail.com:pass1
    user2@gmail.com;pass2
    """
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
async def on_webapp_data(message: Message, db_user: dict):
    """
    WebApp отправил данные через Telegram.WebApp.sendData()
    """
    try:
        payload = json.loads(message.web_app_data.data)
    except Exception:
        await message.answer("❌ Не удалось прочитать данные из WebApp.")
        return

    accounts = []

    if payload.get("type") == "single":
        login = (payload.get("login") or "").strip()
        password = (payload.get("password") or "").strip()
        if login and password:
            accounts = [{"login": login, "password": password}]

    elif payload.get("type") == "list":
        accounts = parse_accounts(payload.get("text") or "")

    if not accounts:
        await message.answer("❌ Не найдено ни одного валидного аккаунта.")
        return

    if len(accounts) > 50:
        await message.answer("❌ Максимум 50 аккаунтов за один заказ.")
        return

    # db_user может быть заглушкой, если middleware упал
    user_id = db_user.get("id")
    if not user_id:
        await message.answer("❌ Ошибка авторизации. Попробуй /start и повтори.")
        return

    try:
        order = await create_order(
            user_id=user_id,
            order_type="single" if len(accounts) == 1 else "bulk",
            accounts=accounts,
            status_message="Заказ принят, ожидает проверки",
            estimated_minutes=15,
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при сохранении заказа: {e}")
        return

    order_id = order["id"]

    text = (
        f"✅ <b>Заказ принят</b>\n\n"
        f"Номер: <b>#{order_id}</b>\n"
        f"Аккаунтов: <b>{len(accounts)}</b>\n\n"
        f"Я сообщу, когда проверка будет готова."
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=order_actions_kb(order_id),
    )
