# import libraries
import asyncio
import logging

# import from libraries
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# import from modules
from app.handlers import router
from app.adminpanel import adm_r
from config.config import get_tokens, get_id_chat_root, logger
from app.database.models import async_main


async def start() -> Bot:
    bot_token = await get_tokens('TOKEN')
    bot_class = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    return bot_class


async def main(bot) -> None:
    """
    load token from .env
    register decorators with Dispatcher()
    create database
    delete updates from telegram servers
    start bot with token
    :return: None
    """
    dp = Dispatcher()
    dp.include_routers(adm_r, router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await bot.delete_webhook(drop_pending_updates=True)  # Пропускаем накопленные сообщения
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


async def on_startup(dispatcher) -> None:
    root_user_id = await get_id_chat_root()
    try:
        await async_main()
        logger.info('Start database')
    except Exception:
        logger.error('Проблема с базой данных')
        await bot.send_message(chat_id=int(root_user_id), text="Проблема с базой данны")

    await bot.send_message(chat_id=int(root_user_id), text="Бот запущен")


async def on_shutdown(dispatcher) -> None:
    root_user_id = await get_id_chat_root()
    await bot.send_message(chat_id=int(root_user_id), text="Бот останавливается")


# Run tg_bot and start log
if __name__ == '__main__':
    FORMAT = '[%(asctime)s]  %(levelname)s: —— %(message)s'
    logging.basicConfig(level=logging.INFO,
                        datefmt="%Y-%m-%d %H:%M:%S",
                        format=FORMAT)
    try:
        bot = asyncio.run(start())
        asyncio.run(main(bot))
    except KeyboardInterrupt:
        logger.warning('Произошел KeyboardInterrupt')
