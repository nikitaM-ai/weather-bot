from telebot import types

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton("🌦 Погода сейчас"),
        types.KeyboardButton("⏰ Уведомления"),
        types.KeyboardButton("ℹ️ Помощь")
    ]
    markup.add(*buttons)
    return markup

def notifications_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton("➕ Добавить уведомление"),
        types.KeyboardButton("❌ Удалить уведомление"),
        types.KeyboardButton("📋 Мои уведомления"),
        types.KeyboardButton("🔙 Главное меню")
    ]
    markup.add(*buttons)
    return markup

def city_quick_reply():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    cities = ["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург"]
    buttons = [types.KeyboardButton(city) for city in cities]
    markup.add(*buttons)
    return markup