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
    
@bot.message_handler()
def add_reminder_step1()
def add_reminder_step2()
def add_reminder_step3()
def add_reminder_step4()

@bot.message_handler()
def show_reminders()

if __name__ == '__main__':
    print("Bot is cooking!")
    bot.infinity_polling()