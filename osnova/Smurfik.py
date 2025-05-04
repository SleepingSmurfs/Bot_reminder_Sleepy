import os
import time
import schedule
import threading
import telebot

from telebot import types
from datetime import datetime, timedelta
from database import Database
from dotenv import load_dotenv

load_dotenv()

bot = telebot.TeleBot(os.getenv('TOKEN'))

#def send_daily_reminders()
#def scheduler()

@bot.message_handler(commands=['start'])
def start(message):
    user = message.from_user
    
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton('➕ Добавить напоминание')
    button2 = types.KeyboardButton('📋 Мои напоминания')
    
    bot.send_message(
        message.chat.id, f"Привет, {user.first_name}! Я бот Sleepy_smurf для напоминаний заданий на день ну и всю неделю.\n"
        "Я буду присылать тебе список дел каждый день в 8:00.",
        reply_markup=markup
    )
    
@bot.message_handler(func=lambda message: message.text == '➕ Добавить напоминание')
def add_reminder_step1(message):
    msg = bot.send_message(message.chat.id, "Напиши текст напоминания:")
    bot.register_next_step_handler(msg, add_reminder_step2)
    
    
def add_reminder_step2(message):
    text = message.text
    if len(text) > 500:
        bot.send_message(message.chat.id, "Текст слишком длинный (макс. 500 символов)")
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for i in range(6):
        markup.add(types.KeyboardButton(str(i)))
    
    msg = bot.send_message(
         message.chat.id,
        "Выбери приоритет (0-5), где 0 - низкий, 5 - очень высокий:",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, add_reminder_step3)
    
def add_reminder_step3(message):
def add_reminder_step4(message):


@bot.message_handler(func=lambda message: message.text == '📋 Мои напоминания')
def show_reminders(message):

if __name__ == '__main__':
    print("Bot is cooking!")
    bot.infinity_polling()