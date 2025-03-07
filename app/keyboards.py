# import from libraries
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# buttons to confirm send message
keyboard_send_mess = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Отправить', callback_data='send'),
     InlineKeyboardButton(text='Отменить', callback_data='cancel')],

])

keys_for_create_project = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Сохранить', callback_data='save_prj'),
     InlineKeyboardButton(text='Отменить', callback_data='cancel_prj')],

])

cancel_key_prj = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Отменить', callback_data='cancel_prj')],
])
