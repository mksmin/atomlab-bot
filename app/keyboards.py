# import from libraries
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# buttons to confirm send message
keyboard_send_mess = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Отправить', callback_data='send'),
     InlineKeyboardButton(text='Отменить', callback_data='cancel')],

])
