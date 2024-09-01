"""
this module load environment and read .env file
"""


import os
from dotenv import load_dotenv
import asyncio


# Load token from .env
async def get_tokens(name_of_token: str) -> str:
    """
    function accept name as str
    load .env file
    find token {name}

    :param name_of_token:
    :return: token as str
    """
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        return os.getenv(name_of_token)
    else:
        print("No .env file found")


async def get_id_chat_root() -> str:
    """
    :return: id of root-chat as str
    """
    return await get_tokens("ROOT_CHAT")


async def test_get_tokens() -> None:
    """
    the test of the get_tokens function
    """
    names_massive = ['TOKEN', 'PostSQL_host', 'ROOT', 'ROOT_CHAT']

    for i in names_massive:
        result = await get_tokens(i)
        print(f'{i = } -- {result= }')
        print(type(result))


if __name__ == '__main__':
    """
    start test
    """
    asyncio.run(test_get_tokens())