import telebot
import threading
import time
import logging
from datetime import datetime
from config import BOT_TOKEN, POLLING_TIMEOUT
from weather_api import get_weather
from database import NotificationDB
from keyboards import main_menu, notifications_menu, city_quick_reply

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='bot.log'
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)
db = NotificationDB()

def format_weather(weather: dict, title: str = "🌦 Погода сейчас") -> str:
    return (
        f"{title}\n\n"
        f"🌆 <b>{weather['city']}</b>\n"
        f"🌡 Температура: <b>{weather['temp']}°C</b>\n"
        f"💨 Ощущается: <b>{weather['feels_like']}°C</b>\n"
        f"☁ Состояние: <b>{weather['description'].capitalize()}</b>\n"
        f"💧 Влажность: <b>{weather['humidity']}%</b>\n"
        f"🌬 Ветер: <b>{weather['wind']} м/с</b>"
    )

def notification_worker():
    logger.info("Запущен worker уведомлений")
    while True:
        try:
            now = datetime.now().strftime("%H:%M")
            notifications = db.get_all_notifications()
            
            for chat_id, data in notifications.items():
                try:
                    if not isinstance(data, dict):
                        continue
                    if 'city' not in data or 'time' not in data:
                        continue
                        
                    if now == data['time']:
                        weather = get_weather(data['city'])
                        if 'error' not in weather:
                            bot.send_message(
                                chat_id,
                                format_weather(weather, "⏰ Ежедневный прогноз"),
                                parse_mode='HTML'
                            )
                            logger.info(f"Отправлено уведомление для {chat_id}")
                except Exception as e:
                    logger.error(f"Ошибка обработки уведомления для {chat_id}: {str(e)}")
                    
            time.sleep(POLLING_TIMEOUT)
        except Exception as e:
            logger.error(f"Ошибка в worker: {str(e)}")
            time.sleep(60)

def is_private_or_addressed_or_button(message):
    if message.chat.type == 'private':
        return True
    
    try:
        bot_username = f'@{bot.get_me().username}'
        if message.text and (bot_username in message.text or message.text.startswith('/')):
            return True
    except Exception as e:
        logger.error(f"Ошибка получения username бота: {str(e)}")
        return False
    
    menu_buttons = [
        "🌦 Погода сейчас", "ℹ️ Помощь", "⏰ Уведомления",
        "➕ Добавить уведомление", "❌ Удалить уведомление",
        "📋 Мои уведомления", "🔙 Главное меню"
    ]
    if message.text in menu_buttons:
        return True
    
    return False

@bot.message_handler(commands=['start', 'help'], func=is_private_or_addressed_or_button)
def send_welcome(message):
    try:
        help_text = (
            "🌟 <b>Помощь по боту</b> 🌟\n\n"
            "Я могу показать текущую погоду в любом городе мира!\n\n"
            "📌 <b>Основные команды:</b>\n"
            "/start - Начать работу с ботом\n"
            "/help - Показать это сообщение\n"
            "/alert - Настроить уведомления\n\n"
            "🌦 <b>Как узнать погоду:</b>\n"
            "1. Нажмите кнопку \"🌦 Погода сейчас\"\n"
            "2. Выберите город из списка или введите свой\n\n"
            "⏰ <b>Уведомления:</b>\n"
            "Можно настроить ежедневные уведомления о погоде\n\n"
            "🔍 <b>Примеры запросов:</b>\n"
            "<code>Москва</code>\n"
            "<code>London</code>\n"
            "<code>Нью-Йорк</code>"
        )
        bot.send_message(
            message.chat.id,
            help_text,
            parse_mode='HTML',
            reply_markup=main_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка в send_welcome: {str(e)}")

@bot.message_handler(func=lambda m: m.text == "🌦 Погода сейчас" and is_private_or_addressed_or_button(m))
def ask_city(message):
    try:
        bot.send_message(
            message.chat.id,
            "Выберите город или введите свой:",
            reply_markup=city_quick_reply()
        )
    except Exception as e:
        logger.error(f"Ошибка в ask_city: {str(e)}")

@bot.message_handler(func=lambda m: m.text in ["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург"])
def handle_city_button(message):
    try:
        weather = get_weather(message.text)
        if 'error' in weather:
            bot.send_message(
                message.chat.id,
                f"❌ {weather['error']}",
                reply_markup=city_quick_reply()
            )
        else:
            bot.send_message(
                message.chat.id,
                format_weather(weather),
                parse_mode='HTML',
                reply_markup=main_menu()
            )
    except Exception as e:
        logger.error(f"Ошибка в handle_city_button: {str(e)}")
        bot.send_message(
            message.chat.id,
            "❌ Произошла ошибка при получении погоды",
            reply_markup=main_menu()
        )

@bot.message_handler(func=lambda m: m.text == "ℹ️ Помощь" and is_private_or_addressed_or_button(m))
def show_help(message):
    send_welcome(message)

@bot.message_handler(func=lambda m: m.text == "⏰ Уведомления" and is_private_or_addressed_or_button(m))
def show_notifications_menu(message):
    try:
        bot.send_message(
            message.chat.id,
            "🔔 Управление уведомлениями:",
            reply_markup=notifications_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка в show_notifications_menu: {str(e)}")

@bot.message_handler(func=lambda m: m.text == "➕ Добавить уведомление" and is_private_or_addressed_or_button(m))
def add_notification(message):
    try:
        msg = bot.send_message(
            message.chat.id,
            "Введите город и время в формате:\n"
            "<b>Город ЧЧ:ММ</b>\n"
            "Пример: <i>Москва 08:30</i>",
            parse_mode='HTML'
        )
        bot.register_next_step_handler(msg, process_notification)
    except Exception as e:
        logger.error(f"Ошибка в add_notification: {str(e)}")

def process_notification(message):
    try:
        parts = message.text.strip().rsplit(' ', 1)
        if len(parts) != 2:
            raise ValueError("Неверный формат")
            
        city, time_str = parts
        datetime.strptime(time_str, "%H:%M")
        
        if db.save_notification(message.chat.id, city, time_str):
            bot.send_message(
                message.chat.id,
                f"✅ Уведомление установлено на {time_str} для {city}",
                reply_markup=notifications_menu()
            )
            logger.info(f"Добавлено уведомление для {message.chat.id}: {city} в {time_str}")
        else:
            raise Exception("Ошибка сохранения")
    except ValueError:
        bot.send_message(
            message.chat.id,
            "❌ Неверный формат. Используйте: Город ЧЧ:ММ\nПример: Москва 08:30",
            reply_markup=notifications_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка в process_notification: {str(e)}")
        bot.send_message(
            message.chat.id,
            "❌ Не удалось сохранить уведомление",
            reply_markup=notifications_menu()
        )

@bot.message_handler(func=lambda m: m.text == "📋 Мои уведомления" and is_private_or_addressed_or_button(m))
def show_notifications(message):
    try:
        notification = db.get_notification(message.chat.id)
        if notification:
            bot.send_message(
                message.chat.id,
                f"🔔 Ваше уведомление:\nГород: {notification['city']}\nВремя: {notification['time']}",
                reply_markup=notifications_menu()
            )
        else:
            bot.send_message(
                message.chat.id,
                "ℹ️ У вас нет активных уведомлений",
                reply_markup=notifications_menu()
            )
    except Exception as e:
        logger.error(f"Ошибка в show_notifications: {str(e)}")

@bot.message_handler(func=lambda m: m.text == "❌ Удалить уведомление" and is_private_or_addressed_or_button(m))
def delete_notification(message):
    try:
        if db.delete_notification(message.chat.id):
            bot.send_message(
                message.chat.id,
                "✅ Уведомление удалено",
                reply_markup=notifications_menu()
            )
            logger.info(f"Удалено уведомление для {message.chat.id}")
        else:
            bot.send_message(
                message.chat.id,
                "ℹ️ Нечего удалять - у вас нет активных уведомлений",
                reply_markup=notifications_menu()
            )
    except Exception as e:
        logger.error(f"Ошибка в delete_notification: {str(e)}")

@bot.message_handler(func=lambda m: m.text == "🔙 Главное меню" and is_private_or_addressed_or_button(m))
def back_to_main(message):
    try:
        bot.send_message(
            message.chat.id,
            "Главное меню:",
            reply_markup=main_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка в back_to_main: {str(e)}")

@bot.message_handler(commands=['alert'], func=is_private_or_addressed_or_button)
def handle_alert_command(message):
    show_notifications_menu(message)

@bot.message_handler(func=lambda m: is_private_or_addressed_or_button(m))
def handle_message(message):
    try:
        ignore_texts = [
            "ℹ️ Помощь", "⏰ Уведомления", "🌦 Погода сейчас",
            "➕ Добавить уведомление", "❌ Удалить уведомление",
            "📋 Мои уведомления", "🔙 Главное меню"
        ]
        if message.text in ignore_texts:
            return
            
        text = message.text.replace(f'@{bot.get_me().username}', '').strip()
        weather = get_weather(text)
        
        if 'error' in weather:
            bot.send_message(
                message.chat.id,
                f"❌ {weather['error']}",
                reply_markup=main_menu()
            )
        else:
            bot.send_message(
                message.chat.id,
                format_weather(weather),
                parse_mode='HTML',
                reply_markup=main_menu()
            )
    except Exception as e:
        logger.error(f"Ошибка в handle_message: {str(e)}")

if __name__ == '__main__':
    logger.info("Запуск бота...")
    try:
        threading.Thread(target=notification_worker, daemon=True).start()
        bot.infinity_polling()
    except Exception as e:
        logger.critical(f"Фатальная ошибка: {str(e)}")
        raise