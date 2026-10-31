import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, MenuButtonWebApp, WebAppInfo

from bot.config import settings
from bot.handlers import main_router
from bot.middlewares.auth import AuthMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


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

    logger.info("Bot started (long polling)")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
