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
db = Database()

PRIORITY_EMOJIS = {
    5: "🔴‼️",
    4: "🟠",
    3: "🟡",
    2: "🟢",
    1: "🔵",
    0: "⚪"
}

def send_daily_reminders():
    users = db.get_all_users()
    for user_id in users:
        reminders = db.get_today_reminders(user_id)
        if reminders:
            message = "📅 *Ваши задачи на сегодня:*\n\n"
            for reminder in reminders:
                for reminder in reminders:
                    id_, text, priority = reminder
                    emoji = PRIORITY_EMOJIS.get(priority, "")
                    message += f"{emoji} *{text}* (Приоритет: {priority}/5)\n\n"
            
            try:
                bot.send_message(user_id, message, parse_mode="Markdown")
            except Exception as e:
                print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
                
                
def scheduler():
    schedule.every().day.at("08:00").do(send_daily_reminders)
    # schedule.every().day.at("00:00").do(db.delete_old_reminders)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

threading.Thread(target=scheduler, daemon=True).start()

@bot.message_handler(commands=['start'])
def start(message):
    user = message.from_user
    
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton('➕ Добавить напоминание')
    button2 = types.KeyboardButton('📋 Мои напоминания')
    button3 = types.KeyboardButton('❌ Удалить напоминание')
    button4 = types.KeyboardButton('🗑️ История удаленных')
    markup.add(button1, button2, button3, button4)
    
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
    bot.register_next_step_handler(msg, add_reminder_step3, text)
    
    
def add_reminder_step3(message, text):
    try:
        priority = int(message.text)
        if (priority < 0) or (priority > 5):
            raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введи число от 0 до 5")
        return
    
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for i in range(1, 8):
        markup.add(types.KeyboardButton(str(i)))
    
    
    msg = bot.send_message(
         message.chat.id,
         "На сколько дней установить напоминание (1-7)?",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, add_reminder_step4, text, priority)


def add_reminder_step4(message, text, priority):
    try:
        days = int(message.text)
        if (priority < 1) or (priority > 7):
            raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введи насколько дней недели сохранить напоминание 1 до 7")
        return
    
    reminder_id = db.add_reminder(message.chat.id, text, priority, days)
    bot.send_message(
        message.chat.id,
        f"✅ Напоминание добавлено!\n"
        f"Текст: {text}\n"
        f"Приоритет: {priority}\n"
        f"Активно до: {(datetime.now()+ timedelta(days=days)).strftime('%d.%m.%Y')}",
        reply_markup=types.ReplyKeyboardRemove()
    )


@bot.message_handler(func=lambda message: message.text == '📋 Мои напоминания')
def show_reminders(message):
    reminders = db.get_today_reminders(message.chat.id)
    if not reminders:
        bot.send_message(message.chat.id, "У вас нет активностей на сегодня. валяем дурака")
        return
    
    
    message_text = "📋 *Ваши активные напоминания:*\n\n"
    for reminder in reminders:
        text, priority = reminder
        emoji = PRIORITY_EMOJIS.get(priority, "")
        message_text += f" {emoji} *{text}* (Приоритет: {priority}/5)\n\n"
    
    
    bot.send_message(
        message.chat.id,
        message_text,
        parse_mode="Markdown"
    )


# @bot.message_handler(func=lambda message: message.text == '❌ Удалить напоминание')


# @bot.message_handler(func=lambda message: message.text.startswith('Удалить #'))


# @bot.message_handler(commands=['history'])

if __name__ == '__main__':
    print("Bot is cooking!")
    bot.infinity_polling()