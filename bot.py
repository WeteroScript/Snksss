# ===== БОТ С ТВОИМИ ПОЧТАМИ =====

import os
import asyncio
import logging
import smtplib
import random
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import requests

# ===== ТВОИ ПОЧТЫ =====
EMAIL_ACCOUNTS = [
    {
        "email": "allllkssso1@gmail.com",
        "password": "eller228",  # ТВОЙ ПАРОЛЬ
        "smtp": "smtp.gmail.com",
        "port": 587
    },
    # Если есть еще почты - добавляй сюда
]

# ===== КОНФИГ =====
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ Ошибка: TELEGRAM_BOT_TOKEN не установлена!")

# Отключаем webhook
try:
    requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")
except:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_data = {}

# ===== ФУНКЦИЯ ОТПРАВКИ ЖАЛОБЫ =====

def send_complaint_via_email(sender_email, sender_password, target_email, subject, body):
    """Реально отправляет письмо с твоей почты"""
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = target_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Подключаемся к Gmail SMTP
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)  # ВХОДИМ В ТВОЮ ПОЧТУ
        server.send_message(msg)  # ОТПРАВЛЯЕМ
        server.quit()
        
        return True
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return False

# ===== ГЕНЕРАТОР ТЕКСТА ЖАЛОБЫ =====

def generate_complaint(target, message, reason):
    return f"""
🚨 СРОЧНАЯ ЖАЛОБА НА ПОЛЬЗОВАТЕЛЯ @{target}

Уважаемая служба поддержки Telegram!

Я вынужден обратиться к вам с официальной жалобой на пользователя @{target},
который систематически нарушает правила платформы.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
НАРУШЕНИЕ:
{reason}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

СООБЩЕНИЕ-ДОКАЗАТЕЛЬСТВО:
{message}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Данный пользователь:
1. Распространяет оскорбительный контент
2. Нарушает правила сообщества
3. Создает угрозу для других пользователей

Прошу принять меры:
- Заблокировать аккаунт @{target}
- Провести проверку
- Удалить все нарушающие сообщения

Номер обращения: TG-{random.randint(100000, 999999)}
Дата: {time.strftime('%Y-%m-%d %H:%M:%S')}

С уважением,
Пользователь Telegram
"""

# ===== ОБРАБОТЧИКИ БОТА =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚀 Старт", callback_data="start_action")],
        [InlineKeyboardButton("🎯 Выбрать цель", callback_data="target_action")]
    ]
    await update.message.reply_text(
        "Добро пожаловать! Выберите кнопку:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "start_action":
        user_data[user_id] = {"step": "waiting_target"}
        await query.edit_message_text("🎯 Введите username цели (например: @username)")
    
    elif query.data == "target_action":
        user_data[user_id] = {"step": "waiting_target"}
        await query.edit_message_text("🎯 Введите username цели (например: @username)")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    
    if user_id not in user_data:
        await update.message.reply_text("Нажмите /start")
        return
    
    step = user_data[user_id].get("step")
    
    if step == "waiting_target":
        user_data[user_id]["target"] = text
        user_data[user_id]["step"] = "waiting_message"
        await update.message.reply_text(
            f"✅ Цель: {text}\n"
            "Теперь ПЕРЕШЛИТЕ сообщение, на которое нужно отправить жалобу"
        )
    
    elif step == "waiting_message":
        if update.message.forward_from or update.message.forward_from_chat:
            forwarded_text = update.message.text or "Медиа-сообщение (скриншот прикреплен)"
            user_data[user_id]["message"] = forwarded_text
            user_data[user_id]["step"] = "waiting_reason"
            await update.message.reply_text("📝 Напишите причину жалобы")
        else:
            await update.message.reply_text("❌ ПЕРЕШЛИТЕ сообщение, не копируйте!")

async def handle_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    reason = update.message.text
    
    if user_id not in user_data or user_data[user_id].get("step") != "waiting_reason":
        return
    
    data = user_data[user_id]
    target = data["target"]
    message = data["message"]
    
    # Генерируем текст жалобы
    complaint_text = generate_complaint(target, message, reason)
    
    await update.message.reply_text("⏳ Отправляю жалобу с твоей почты...")
    
    # ОТПРАВЛЯЕМ РЕАЛЬНУЮ ЖАЛОБУ
    success = send_complaint_via_email(
        sender_email="allllkssso1@gmail.com",
        sender_password="eller228",
        target_email="abuse@telegram.org",
        subject=f"URGENT: Complaint Against @{target}",
        body=complaint_text
    )
    
    if success:
        await update.message.reply_text(
            f"✅ ЖАЛОБА ОТПРАВЛЕНА!\n"
            f"📧 С: allllkssso1@gmail.com\n"
            f"📨 Кому: abuse@telegram.org\n"
            f"🎯 Цель: @{target}\n\n"
            f"Проверь папку 'Отправленные' в Gmail!"
        )
    else:
        await update.message.reply_text(
            "❌ ОШИБКА ОТПРАВКИ!\n"
            "Возможные причины:\n"
            "1. Неправильный пароль\n"
            "2. Нужно включить 'Доступ для ненадежных приложений'\n"
            "3. Не подтвержден вход\n\n"
            "Инструкция в следующем сообщении"
        )
    
    del user_data[user_id]

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in user_data:
        del user_data[user_id]
        await update.message.reply_text("❌ Отменено")

# ===== ЗАПУСК =====

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reason))
    
    print("="*50)
    print("🤖 БОТ С ТВОЕЙ ПОЧТОЙ")
    print("="*50)
    print(f"📧 Email: allllkssso1@gmail.com")
    print(f"🔑 Пароль: eller228")
    print(f"📨 Кому: abuse@telegram.org")
    print("="*50)
    print("📩 Используй /start")
    print("="*50)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
