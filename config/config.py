import os
from dotenv import load_dotenv

# Подгружаем из директории .env
async def get_tokens(name):
    dotenv_path = os.path.join(os.path.dirname(__file__),'.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        TOKEN = os.getenv(name)
        return TOKEN
    else:
        print("No .env file found")

