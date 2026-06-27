# bot.py - ФИНАЛЬНАЯ РАБОЧАЯ ВЕРСИЯ С НОВЫМ ПАРОЛЕМ

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

# ===== КОНФИГ =====
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ Ошибка: TELEGRAM_BOT_TOKEN не установлена!")

# ===== ТВОИ ДАННЫЕ (ОБНОВЛЕНО) =====
EMAIL_ACCOUNTS = [
    {
        "email": "allllkssso1@gmail.com",
        "password": "hrzaxqferrgdfsbr",  # НОВЫЙ ПАРОЛЬ ПРИЛОЖЕНИЯ
        "smtp": "smtp.gmail.com",
        "port": 587
    },
]

# Отключаем webhook
try:
    requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")
except:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

user_data = {}

# ===== ПРОВЕРКА ПАРОЛЯ ПРИ ЗАПУСКЕ =====
def check_email():
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_ACCOUNTS[0]['email'], EMAIL_ACCOUNTS[0]['password'])
        server.quit()
        print("✅ ПАРОЛЬ ПРИЛОЖЕНИЯ РАБОТАЕТ!")
        return True
    except Exception as e:
        print(f"❌ ПАРОЛЬ НЕ РАБОТАЕТ: {e}")
        return False

# Проверяем
if not check_email():
    print("⚠️ ПАРОЛЬ НЕ РАБОТАЕТ! ПРОВЕРЬ:")
    print(f"   Email: {EMAIL_ACCOUNTS[0]['email']}")
    print(f"   Пароль: {EMAIL_ACCOUNTS[0]['password']}")
    print("   Если не работает - создай новый пароль приложения")
    exit(1)

# ===== ФУНКЦИЯ ОТПРАВКИ =====

def send_complaint_via_email(sender_email, sender_password, target_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = target_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"✅ Письмо отправлено с {sender_email} на {target_email}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return False

# ===== ГЕНЕРАТОР ЖАЛОБЫ =====

def generate_complaint(target, message, reason):
    # Убираем лишний @
    if target.startswith('@@'):
        target = target[1:]
    elif target.startswith('@'):
        target = target
    
    return f"""
🚨 СРОЧНАЯ ЖАЛОБА НА ПОЛЬЗОВАТЕЛЯ @{target}

Уважаемая служба поддержки Telegram!

Я вынужден обратиться к вам с официальной жалобой на пользователя @{target},
который нарушает правила платформы.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
НАРУШЕНИЕ:
{reason}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

СООБЩЕНИЕ-ДОКАЗАТЕЛЬСТВО:
{message}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Прошу:
- Заблокировать аккаунт @{target}
- Провести проверку

Номер обращения: TG-{random.randint(100000, 999999)}
Дата: {time.strftime('%Y-%m-%d %H:%M:%S')}

С уважением,
Пользователь Telegram
"""

def generate_subject(target):
    if target.startswith('@@'):
        target = target[1:]
    subjects = [
        f"URGENT: Complaint Against @{target}",
        f"VIOLATION REPORT: @{target}",
        f"FORMAL COMPLAINT: @{target}",
    ]
    return random.choice(subjects)

# ===== ОБРАБОТЧИКИ =====

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
    user_data[user_id] = {"step": "waiting_target"}
    await query.edit_message_text("🎯 Введите username цели (например: @username)")

async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    
    logger.info(f"Сообщение от {user_id}: шаг {user_data.get(user_id, {}).get('step', 'нет')}")
    
    if user_id not in user_data:
        await update.message.reply_text("Нажмите /start")
        return
    
    step = user_data[user_id].get("step")
    
    # ШАГ 1: ЦЕЛЬ
    if step == "waiting_target":
        user_data[user_id]["target"] = text
        user_data[user_id]["step"] = "waiting_message"
        await update.message.reply_text(
            f"✅ Цель: {text}\n"
            "Теперь ПЕРЕШЛИТЕ сообщение для жалобы"
        )
        return
    
    # ШАГ 2: ПЕРЕСЫЛКА
    if step == "waiting_message":
        is_forwarded = False
        forwarded_text = ""
        
        if hasattr(update.message, 'forward_from') and update.message.forward_from:
            is_forwarded = True
            forwarded_text = update.message.text or "Медиа-сообщение"
        elif hasattr(update.message, 'forward_from_chat') and update.message.forward_from_chat:
            is_forwarded = True
            forwarded_text = update.message.text or "Медиа-сообщение"
        elif hasattr(update.message, 'forward_origin') and update.message.forward_origin:
            is_forwarded = True
            forwarded_text = update.message.text or "Медиа-сообщение"
        
        if is_forwarded:
            user_data[user_id]["message"] = forwarded_text
            user_data[user_id]["step"] = "waiting_reason"
            await update.message.reply_text(
                "✅ Сообщение получено!\n"
                "📝 Напишите ПРИЧИНУ жалобы"
            )
        else:
            await update.message.reply_text(
                "❌ Это НЕ пересланное сообщение!\n"
                "Нажмите на сообщение → 'Переслать' → выберите бота"
            )
        return
    
    # ШАГ 3: ПРИЧИНА → ОТПРАВКА
    if step == "waiting_reason":
        data = user_data[user_id]
        target = data.get("target")
        message = data.get("message")
        
        if not target or not message:
            await update.message.reply_text("❌ Ошибка. Начните /start заново")
            del user_data[user_id]
            return
        
        # Чистим цель
        clean_target = target
        if clean_target.startswith('@@'):
            clean_target = clean_target[1:]
        
        # Генерируем
        complaint = generate_complaint(clean_target, message, text)
        subject = generate_subject(clean_target)
        
        await update.message.reply_text(
            f"⏳ Отправляю жалобу на @{clean_target}..."
        )
        
        # ОТПРАВЛЯЕМ
        success = send_complaint_via_email(
            sender_email=EMAIL_ACCOUNTS[0]['email'],
            sender_password=EMAIL_ACCOUNTS[0]['password'],
            target_email="abuse@telegram.org",
            subject=subject,
            body=complaint
        )
        
        if success:
            await update.message.reply_text(
                f"✅ ЖАЛОБА ОТПРАВЛЕНА!\n"
                f"📧 С: {EMAIL_ACCOUNTS[0]['email']}\n"
                f"📨 Кому: abuse@telegram.org\n"
                f"🎯 Цель: @{clean_target}\n\n"
                f"📬 Проверь папку 'Отправленные' в Gmail!"
            )
        else:
            await update.message.reply_text(
                "❌ ОШИБКА ОТПРАВКИ!\n\n"
                "Проверь логи в консоли."
            )
        
        del user_data[user_id]
        return
    
    await update.message.reply_text("❌ Ошибка. Нажмите /start")
    del user_data[user_id]

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in user_data:
        del user_data[user_id]
        await update.message.reply_text("❌ Отменено")
    else:
        await update.message.reply_text("Нет активного процесса")

# ===== ЗАПУСК =====

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))
    
    print("="*60)
    print("🤖 БОТ ДЛЯ ЖАЛОБ")
    print("="*60)
    print(f"📧 Почта: {EMAIL_ACCOUNTS[0]['email']}")
    print(f"🔑 Пароль приложения: {'*' * 16}")
    print(f"📨 Кому: abuse@telegram.org")
    print("="*60)
    print("📩 Используй /start")
    print("="*60)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
