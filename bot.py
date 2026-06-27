# bot.py - ПОЛНАЯ ВЕРСИЯ С ПРОВЕРКОЙ ПАРОЛЯ

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

# ===== ТВОЙ ПАРОЛЬ ПРИЛОЖЕНИЯ =====
EMAIL = "allllkssso1@gmail.com"
PASSWORD = "irosxfskteabviic"  # ЕСЛИ НЕ РАБОТАЕТ - СОЗДАЙ НОВЫЙ!

# ===== ПРОВЕРКА ПАРОЛЯ ПРИ ЗАПУСКЕ =====
def check_email():
    """Проверяет, работает ли пароль приложения"""
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.quit()
        print("✅ ПАРОЛЬ ПРИЛОЖЕНИЯ РАБОТАЕТ!")
        return True
    except Exception as e:
        print(f"❌ ПАРОЛЬ НЕ РАБОТАЕТ: {e}")
        print("\n🔧 СОЗДАЙ НОВЫЙ ПАРОЛЬ ПРИЛОЖЕНИЯ:")
        print("1. https://myaccount.google.com/security")
        print("2. 2-факторная аутентификация → ВКЛЮЧИТЬ")
        print("3. Пароли приложений → СОЗДАТЬ")
        print("4. Название: 'Telegram Bot'")
        print("5. СКОПИРУЙ 16-ЗНАЧНЫЙ ПАРОЛЬ")
        print("6. ВСТАВЬ В КОД ВМЕСТО irosxfskteabviic")
        return False

# Проверяем почту при запуске
if not check_email():
    print("⚠️ БОТ НЕ ЗАПУСТИТСЯ, ПОКА НЕ ИСПРАВИШЬ ПАРОЛЬ!")
    exit(1)

# Отключаем webhook
try:
    requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")
except:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

user_data = {}

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
        return True
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return False

# ===== ГЕНЕРАТОР ЖАЛОБЫ =====

def generate_complaint(target, message, reason):
    # Чистим @
    if target.startswith('@@'):
        target = target[1:]
    
    return f"""
🚨 ЖАЛОБА НА @{target}

Уважаемая поддержка Telegram!

Жалуюсь на пользователя @{target}.

ПРИЧИНА: {reason}

ДОКАЗАТЕЛЬСТВО:
{message}

Прошу заблокировать аккаунт.

Номер: TG-{random.randint(100000, 999999)}
Дата: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""

def generate_subject(target):
    if target.startswith('@@'):
        target = target[1:]
    return f"Complaint Against @{target}"

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
    user_data[user_id] = {"step": "waiting_target"}
    await query.edit_message_text("🎯 Введите username цели (например: @username)")

async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    
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
    
    # ШАГ 2: ПЕРЕСЛАННОЕ СООБЩЕНИЕ
    if step == "waiting_message":
        is_forwarded = False
        forwarded_text = ""
        
        if hasattr(update.message, 'forward_from') and update.message.forward_from:
            is_forwarded = True
            forwarded_text = update.message.text or "Медиа-сообщение"
        elif hasattr(update.message, 'forward_from_chat') and update.message.forward_from_chat:
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
            await update.message.reply_text("❌ ПЕРЕШЛИТЕ сообщение, не копируйте!")
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
        clean_target = target if not target.startswith('@@') else target[1:]
        
        # Генерируем жалобу
        complaint = generate_complaint(clean_target, message, text)
        subject = generate_subject(clean_target)
        
        await update.message.reply_text(
            f"⏳ Отправляю жалобу на @{clean_target}..."
        )
        
        # ОТПРАВЛЯЕМ
        success = send_complaint_via_email(
            sender_email=EMAIL,
            sender_password=PASSWORD,
            target_email="abuse@telegram.org",
            subject=subject,
            body=complaint
        )
        
        if success:
            await update.message.reply_text(
                f"✅ ЖАЛОБА ОТПРАВЛЕНА!\n"
                f"📧 С: {EMAIL}\n"
                f"📨 Кому: abuse@telegram.org\n"
                f"🎯 Цель: @{clean_target}\n\n"
                f"Проверь папку 'Отправленные' в Gmail!"
            )
        else:
            await update.message.reply_text(
                "❌ ОШИБКА ОТПРАВКИ!\n\n"
                "🔧 СДЕЛАЙ ЭТО:\n"
                "1. Зайди в аккаунт Google\n"
                "2. https://myaccount.google.com/security\n"
                "3. 2-факторная аутентификация → ВКЛЮЧИТЬ\n"
                "4. Пароли приложений → СОЗДАТЬ НОВЫЙ\n"
                "5. Название: 'Telegram Bot'\n"
                "6. Скопируй НОВЫЙ пароль\n"
                "7. Вставь в код вместо irosxfskteabviic\n"
                "8. Перезапусти бота"
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
    print(f"📧 Почта: {EMAIL}")
    print(f"🔑 Пароль приложения: {'*' * 16}")
    print(f"📨 Кому: abuse@telegram.org")
    print("="*60)
    print("📩 Используй /start")
    print("="*60)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
