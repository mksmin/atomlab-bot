# import from libraries
from aiogram import Router, F
from aiogram.filters import CommandStart, ChatMemberUpdatedFilter, \
    KICKED, LEFT, MEMBER, RESTRICTED
from aiogram.types import Message, ChatMemberUpdated

# import from modules
import app.database.request as rq
from app.middlewares import CheckChatBot
from config.config import get_id_chat_root

router = Router()  # main handler


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """
    Start handler
    :return: none
    """
    from_user = message.from_user
    await rq.set_user(from_user.id, from_user.username)
    await message.answer(f'Привет, {from_user.first_name}!')


# Добавляем пользователя в бд после вступления в чат
@router.chat_member(ChatMemberUpdatedFilter(
    member_status_changed=
    (KICKED | LEFT | -RESTRICTED)
    >>
    (+RESTRICTED | MEMBER)
))
async def get_member(update: ChatMemberUpdated) -> None:
    """
    Add user's info to DB after he's joined to chat
    and check number of chats, where he's member
    :param update:
    :return: None
    """
    chat = update.chat
    from_user = update.new_chat_member.user

    await rq.set_user(from_user.id, from_user.username)

    count_chats = await rq.set_user_chat(from_user.id, chat.id)

    if from_user.username is None:
        username_ = f'{from_user.first_name}'
    else:
        username_ = f'{from_user.first_name} (@{from_user.username})'

    if count_chats < 2:
        message_text = f'Привет, {username_}!'
        await update.answer(message_text)
    else:
        message_text = (f'Привет, {username_}!'
                        f'\nУчиться можно только на одном направлении'
                        f'\n\nЯ отправил админу сообщение, он свяжется с тобой и удалит тебя из других чатов')
        await update.answer(message_text)

        root_id = await get_id_chat_root()
        chats_titles_list = await rq.get_chats(from_user.id)
        await update.bot.send_message(chat_id=int(root_id),
                                      text=f'{username_}'
                                           f'\nвступил в несколько чатов: '
                                           f'\n\n{chats_titles_list}'
                                           f'\n\nСвяжись с ним, чтобы обсудить детали')


# /-- karma start --/
# Функция увеличения репутации
@router.message(F.reply_to_message,
                F.text.lower().contains('+rep'),
                CheckChatBot(chat_type=["group", "supergroup"]))
async def add_rep_to_user(message: Message) -> None:
    id_recipient = message.reply_to_message.from_user.id
    id_sender = message.from_user.id

    if id_recipient == message.bot.id:
        await message.reply('Боту нельзя поднять репутацию, но спасибо, что ты ценишь его работу')
        return None
    if id_recipient == id_sender:
        await message.reply('Cебе нельзя поднять репутацию')
        return None

    result = await rq.check_karma(id_sender, id_recipient)
    dict_value = {
        'send': '',
        'recipient': '',
    }
    keys_of_dict = list(dict_value.keys())

    for ind in range(2):
        for i, v in result[ind]:
            dict_new = {
                'ID': i,
                'karma': v
            }

            dict_value.update({
                keys_of_dict[ind]: dict_new
            })

    sender_id, sender_karma = dict_value['send']['ID'], dict_value['send']['karma']
    recipient_id, recipient_karma = dict_value['recipient']['ID'], dict_value['recipient']['karma']

    if sender_karma <= 0:
        await message.reply(f'Упс! У тебя закончились очки репутации')
    else:
        sender_karma -= 1
        recipient_karma += 1
        recipient_username = message.reply_to_message.from_user.username

        await rq.update_karma(sender_id, sender_karma,
                              recipient_id, recipient_karma)
        await message.reply(f'Репутация @{recipient_username} повышена. '
                            f'У тебя осталось очков репутации - <b>{sender_karma}</b>')

# /-- karma end --/
