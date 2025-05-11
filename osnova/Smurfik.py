import os
import time
import threading
import logging
from datetime import datetime, time as dt_time, timedelta
from dotenv import load_dotenv
import telebot
from telebot import types
from json_database import JSONDatabase
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_errors.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(os.getenv('TOKEN'))
db = JSONDatabase('reminders_data.json')

PRIORITY_EMOJIS = {
    5: "🔴‼️",
    4: "🟠",
    3: "🟡",
    2: "🟢",
    1: "🔵",
    0: "⚪️"
}

def send_daily_reminders():
    """Отправляет напоминания всем пользователям с обработкой ошибок"""
    try:
        users = db.get_all_users()
        if not users:
            logger.info("Нет пользователей для рассылки")
            return

        for user_id in users:
            try:
                reminders = db.get_today_reminders(user_id)
                if not reminders:
                    continue
                    
                message = "📅 *Ваши задачи на сегодня:*\n\n"
                for reminder in reminders:
                    id_ = reminder['id']
                    text = reminder['text']
                    priority = reminder['priority']
                    emoji = PRIORITY_EMOJIS.get(priority, "")
                    message += f"{emoji} *{text}* (Приоритет: {priority}/5)\nID: {id_}\n\n"
                
                try:
                    bot.send_message(user_id, message, parse_mode="Markdown")
                except telebot.apihelper.ApiException as e:
                    logger.error(f"Ошибка Telegram API при отправке пользователю {user_id}: {e}")
                except Exception as e:
                    logger.error(f"Неизвестная ошибка при отправке пользователю {user_id}: {e}")

            except Exception as e:
                logger.error(f"Ошибка обработки пользователя {user_id}: {e}")

    except Exception as e:
        logger.error(f"Критическая ошибка в send_daily_reminders: {e}")

def check_scheduled_tasks():
    """Проверяет и выполняет scheduled задачи"""
    while True:
        now = datetime.now()
        current_time = now.time()
        
        # Ежедневная рассылка в 8:00
        if current_time.hour == 8 and current_time.minute == 0:
            send_daily_reminders()
            time.sleep(60)
        
        if current_time.hour == 0 and current_time.minute == 0:
            db.delete_old_reminders()
            time.sleep(60)
        
        time.sleep(30)

threading.Thread(target=check_scheduled_tasks, daemon=True).start()

@bot.message_handler(commands=['start'])
def start(message):
    try:
        user = message.from_user
        db.add_user(user.id, user.username, user.first_name, user.last_name)
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('➕ Добавить напоминание')
        btn2 = types.KeyboardButton('📋 Мои напоминания')
        btn3 = types.KeyboardButton('❌ Удалить напоминание')
        btn4 = types.KeyboardButton('🗑 История удаленных')
        markup.add(btn1, btn2, btn3, btn4)
        
        bot.send_message(
            message.chat.id,
            f"Привет, {user.first_name}! Я бот-напоминалка.\n"
            "Используйте кнопки ниже для управления напоминаниями.",
            reply_markup=markup
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике start: {e}")
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка. Попробуйте позже.")

@bot.message_handler(func=lambda message: message.text == '➕ Добавить напоминание')
def add_reminder_step1(message):
    try:
        msg = bot.send_message(
            message.chat.id, 
            "Напишите текст напоминания (макс. 500 символов):",
            reply_markup=types.ReplyKeyboardRemove()
        )
        bot.register_next_step_handler(msg, add_reminder_step2)
    except Exception as e:
        logger.error(f"Ошибка в add_reminder_step1: {e}")
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка. Попробуйте позже.")

def add_reminder_step2(message):
    try:
        if not message.text or len(message.text.strip()) == 0:
            bot.send_message(message.chat.id, "Текст напоминания не может быть пустым.")
            return
            
        text = message.text.strip()
        if len(text) > 500:
            bot.send_message(message.chat.id, "Текст слишком длинный (макс. 500 символов).")
            return
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for i in range(6):
            markup.add(types.KeyboardButton(str(i)))
        
        msg = bot.send_message(
            message.chat.id,
            "Выберите приоритет (0-5), где 0 - низкий, 5 - очень высокий:",
            reply_markup=markup
        )
        bot.register_next_step_handler(msg, add_reminder_step3, text)
    except Exception as e:
        logger.error(f"Ошибка в add_reminder_step2: {e}")
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка. Начните заново.")

def add_reminder_step3(message, text):
    try:
        priority = int(message.text)
        if priority < 0 or priority > 5:
            raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите число от 0 до 5")
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
        if days < 1 or days > 7:
            raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите число от 1 до 7")
        return
    
    try:
        reminder_id = db.add_reminder(message.chat.id, text, priority, days)
        if not reminder_id:
            raise Exception("Не удалось добавить напоминание")
            
        expires_date = (datetime.now() + timedelta(days=days)).strftime('%d.%m.%Y')
        bot.send_message(
            message.chat.id,
            f"✅ Напоминание добавлено!\n"
            f"ID: {reminder_id}\n"
            f"Текст: {text}\n"
            f"Приоритет: {priority}\n"
            f"Активно до: {expires_date}",
            reply_markup=types.ReplyKeyboardRemove()
        )
    except Exception as e:
        logger.error(f"Ошибка в add_reminder_step4: {e}")
        bot.send_message(
            message.chat.id,
            "⚠️ Не удалось добавить напоминание. Попробуйте позже.",
            reply_markup=types.ReplyKeyboardRemove()
        )

@bot.message_handler(func=lambda message: message.text == '📋 Мои напоминания')
def show_reminders(message):
    try:
        reminders = db.get_today_reminders(message.chat.id)
        if not reminders:
            bot.send_message(message.chat.id, "У вас нет активных напоминаний на сегодня.")
            return
        
        message_text = "📋 *Ваши активные напоминания:*\n\n"
        for reminder in reminders:
            id_ = reminder['id']
            text = reminder['text']
            priority = reminder['priority']
            emoji = PRIORITY_EMOJIS.get(priority, "")
            message_text += f"{emoji} *{text}* (Приоритет: {priority}/5)\nID: {id_}\n\n"
        
        bot.send_message(
            message.chat.id,
            message_text,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка в show_reminders: {e}")
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка. Попробуйте позже.")

@bot.message_handler(func=lambda message: message.text == '❌ Удалить напоминание')
def ask_reminder_to_delete(message):
    try:
        reminders = db.get_today_reminders(message.chat.id)
        if not reminders:
            bot.send_message(message.chat.id, "У вас нет активных напоминаний для удаления.")
            return
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for reminder in reminders:
            id_ = reminder['id']
            text = reminder['text']
            btn_text = f"❌ Удалить #{id_}: {text[:20]}..." if len(text) > 20 else f"❌ Удалить #{id_}: {text}"
            markup.add(types.KeyboardButton(btn_text))
        markup.add(types.KeyboardButton("Отмена"))
        
        bot.send_message(
            message.chat.id,
            "Выберите напоминание для удаления:",
            reply_markup=markup
        )
    except Exception as e:
        logger.error(f"Ошибка в ask_reminder_to_delete: {e}")
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка. Попробуйте позже.")

@bot.message_handler(func=lambda message: message.text.startswith('❌ Удалить #'))
def process_deletion(message):
    try:
        if message.text == "Отмена":
            bot.send_message(
                message.chat.id,
                "Удаление отменено.",
                reply_markup=types.ReplyKeyboardRemove()
            )
            return
            
        reminder_id = int(message.text.split('#')[1].split(':')[0])
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Да", callback_data=f"del_confirm_{reminder_id}"),
            types.InlineKeyboardButton("❌ Нет", callback_data="del_cancel")
        )
        
        bot.send_message(
            message.chat.id,
            "Вы уверены, что хотите удалить это напоминание?",
            reply_markup=markup
        )
    except Exception as e:
        logger.error(f"Ошибка в process_deletion: {e}")
        bot.send_message(
            message.chat.id,
            "⚠️ Не удалось обработать запрос. Попробуйте еще раз.",
            reply_markup=types.ReplyKeyboardRemove()
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith('del_confirm_'))
def confirm_deletion(call):
    try:
        reminder_id = int(call.data.split('_')[-1])
        if db.delete_reminder(reminder_id, call.message.chat.id):
            bot.edit_message_text(
                "Напоминание успешно удалено!",
                call.message.chat.id,
                call.message.message_id
            )
        else:
            bot.edit_message_text(
                "Не удалось найти напоминание для удаления",
                call.message.chat.id,
                call.message.message_id
            )
    except Exception as e:
        logger.error(f"Ошибка в confirm_deletion: {e}")
        bot.answer_callback_query(call.id, "⚠️ Ошибка при удалении")

@bot.callback_query_handler(func=lambda call: call.data == 'del_cancel')
def cancel_deletion(call):
    try:
        bot.edit_message_text(
            "Удаление отменено",
            call.message.chat.id,
            call.message.message_id
        )
    except Exception as e:
        logger.error(f"Ошибка в cancel_deletion: {e}")

@bot.message_handler(func=lambda message: message.text == '🗑 История удаленных')
@bot.message_handler(commands=['history'])
def show_deleted_history(message):
    try:
        deleted = db.get_deleted_reminders(message.chat.id)
        if not deleted:
            bot.send_message(message.chat.id, "У вас нет удаленных напоминаний.")
            return
        
        response = "🗑 *История удаленных напоминаний:*\n\n"
        for item in deleted:
            original_id = item['original_id']
            text = item['text']
            priority = item['priority']
            deleted_at = datetime.fromisoformat(item['deleted_at'])
            reason = item['reason']
            
            response += (
                f"🔹 *ID:* {original_id}\n"
                f"📝 *Текст:* {text}\n"
                f"🔢 *Приоритет:* {priority}\n"
                f"🗓 *Удалено:* {deleted_at.strftime('%d.%m.%Y %H:%M')}\n"
                f"ℹ️ *Причина:* {reason}\n\n"
            )
        
        bot.send_message(
            message.chat.id,
            response,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка в show_deleted_history: {e}")
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка при получении истории.")

def start_bot():
    while True:
        try:
            logger.info("Бот запущен...")
            bot.infinity_polling()
        except KeyboardInterrupt:
            logger.info("Бот остановлен пользователем")
            db.close()
            break
        except Exception as e:
            logger.error(f"Критическая ошибка в основном потоке: {e}")
            time.sleep(10)
            continue

if __name__ == '__main__':
    start_bot()