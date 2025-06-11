import os
from dotenv import load_dotenv

load_dotenv()  # Загружает переменные из .env файла

BOT_TOKEN = os.getenv('BOT_TOKEN', '7674753483:AAEsU3-zUyTA7JyPWmS7uv96fQUU9tIC9aE')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', '71c4f361538787e6ced47aa25b24e4ef')
POLLING_TIMEOUT = 30
REQUEST_TIMEOUT = 10
CACHE_TIME = 600  # 10 минут в секундах