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
from config.config import get_tokens
from app.database.models import async_main


async def main() -> None:
    """
    load token from .env
    register decorators with Dispatcher()
    create database
    delete updates from telegram servers
    start bot with token
    :return: None
    """
    bot_token = await get_tokens('TOKEN')
    bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_routers(adm_r, router)
    dp.startup.register(on_startup)
    await bot.delete_webhook(drop_pending_updates=True)  # Пропускаем накопленные сообщения
    await dp.start_polling(bot)


async def on_startup(dispatcher) -> None:
    await async_main()
    print('Started database')

# Run tg_bot and start log
if __name__ == '__main__':
    FORMAT = '%(asctime)s __ %(message)s'
    logging.basicConfig(level=logging.INFO,
                        format=FORMAT)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
