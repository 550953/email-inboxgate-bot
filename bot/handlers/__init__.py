from aiogram import Router

from bot.handlers.start import router as start_router
from bot.handlers.help import router as help_router
from bot.handlers.new import router as new_router
from bot.handlers.status import router as status_router
from bot.handlers.my_orders import router as my_orders_router
from bot.handlers.queue import router as queue_router
from bot.handlers.cancel import router as cancel_router

main_router = Router()
main_router.include_router(start_router)
main_router.include_router(help_router)
main_router.include_router(new_router)
main_router.include_router(status_router)
main_router.include_router(my_orders_router)
main_router.include_router(queue_router)
main_router.include_router(cancel_router)
