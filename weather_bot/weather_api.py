import requests
import time
from datetime import datetime
from config import WEATHER_API_KEY, REQUEST_TIMEOUT, CACHE_TIME
import logging

logger = logging.getLogger(__name__)

weather_cache = {}

def get_weather(city: str) -> dict:
    if not city or len(city.strip()) < 2:
        return {'error': 'Название города слишком короткое'}

    # Проверка кэша
    cached = weather_cache.get(city)
    if cached and (time.time() - cached['timestamp']) < CACHE_TIME:
        logger.debug(f"Используем кэш для города {city}")
        return cached['data']

    try:
        url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': city,
            'appid': WEATHER_API_KEY,
            'units': 'metric',
            'lang': 'ru'
        }
        
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        weather_data = {
            'city': data['name'],
            'temp': round(data['main']['temp']),
            'feels_like': round(data['main']['feels_like']),
            'description': data['weather'][0]['description'],
            'humidity': data['main']['humidity'],
            'wind': round(data['wind']['speed'], 1)  # Округляем скорость ветра
        }

        # Обновляем кэш
        weather_cache[city] = {
            'data': weather_data,
            'timestamp': time.time()
        }

        return weather_data

    except requests.exceptions.HTTPError as e:
        error_msg = 'Город не найден' if e.response.status_code == 404 else f'Ошибка API: {str(e)}'
        logger.error(f"HTTP error for {city}: {error_msg}")
        return {'error': error_msg}
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error for {city}: {str(e)}")
        return {'error': f'Ошибка соединения: {str(e)}'}
    except (KeyError, ValueError) as e:
        logger.error(f"Data parsing error for {city}: {str(e)}")
        return {'error': 'Неверный формат данных от сервера'}