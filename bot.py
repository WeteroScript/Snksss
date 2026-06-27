# bot.py - ИСПРАВЛЕННАЯ ВЕРСИЯ

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

# ===== ТВОИ ПОЧТЫ =====
EMAIL_ACCOUNTS = [
    {
        "email": "allllkssso1@gmail.com",
        "password": "eller228",
        "smtp": "smtp.gmail.com",
        "port": 587
    },
]

# Отключаем webhook
try:
    requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")
except:
    pass

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

user_data = {}

# ===== ФУНКЦИЯ ОТПРАВКИ EMAIL =====

def send_complaint_via_email(sender_email, sender_password, target_email, subject, body):
    """Реально отправляет письмо с твоей почты"""
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = target_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        if 'gmail.com' in sender_email:
            smtp_server = "smtp.gmail.com"
            port = 587
        elif 'mail.ru' in sender_email:
            smtp_server = "smtp.mail.ru"
            port = 587
        elif 'yandex.ru' in sender_email:
            smtp_server = "smtp.yandex.ru"
            port = 587
        elif 'outlook.com' in sender_email or 'hotmail.com' in sender_email:
            smtp_server = "smtp-mail.outlook.com"
            port = 587
        else:
            smtp_server = "smtp.gmail.com"
            port = 587
        
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")
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

Данный пользователь нарушает правила сообщества.

Прошу принять меры:
- Заблокировать аккаунт @{target}
- Провести проверку

Номер обращения: TG-{random.randint(100000, 999999)}
Дата: {time.strftime('%Y-%m-%d %H:%M:%S')}

С уважением,
Пользователь Telegram
"""

def generate_subject(target):
    subjects = [
        f"URGENT: Complaint Against @{target}",
        f"VIOLATION REPORT: User @{target}",
        f"FORMAL COMPLAINT: @{target} Violates Rules",
    ]
    return random.choice(subjects)

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

# ===== ОСНОВНОЙ ОБРАБОТЧИК ВСЕХ СООБЩЕНИЙ =====
async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ЕДИНЫЙ обработчик для всех текстовых сообщений"""
    user_id = update.message.from_user.id
    text = update.message.text
    
    logger.info(f"Сообщение от {user_id}: {text[:50]}... Шаг: {user_data.get(user_id, {}).get('step', 'нет')}")
    
    # Если пользователь не в процессе
    if user_id not in user_data:
        await update.message.reply_text("Нажмите /start для начала")
        return
    
    step = user_data[user_id].get("step")
    
    # ===== ШАГ 1: ВВОД ЦЕЛИ =====
    if step == "waiting_target":
        user_data[user_id]["target"] = text
        user_data[user_id]["step"] = "waiting_message"
        await update.message.reply_text(
            f"✅ Цель: {text}\n"
            "Теперь ПЕРЕШЛИТЕ сообщение, на которое нужно отправить жалобу"
        )
        return
    
    # ===== ШАГ 2: ПЕРЕСЫЛКА СООБЩЕНИЯ =====
    if step == "waiting_message":
        # Проверяем, переслано ли сообщение
        is_forwarded = False
        forwarded_text = ""
        
        if hasattr(update.message, 'forward_from') and update.message.forward_from is not None:
            is_forwarded = True
            forwarded_text = update.message.text or "Медиа-сообщение"
        elif hasattr(update.message, 'forward_from_chat') and update.message.forward_from_chat is not None:
            is_forwarded = True
            forwarded_text = update.message.text or "Медиа-сообщение"
        elif hasattr(update.message, 'forward_origin') and update.message.forward_origin is not None:
            is_forwarded = True
            forwarded_text = update.message.text or "Медиа-сообщение"
        
        if is_forwarded:
            user_data[user_id]["message"] = forwarded_text
            user_data[user_id]["step"] = "waiting_reason"
            await update.message.reply_text(
                "✅ Сообщение получено!\n"
                "📝 Теперь напишите ПРИЧИНУ жалобы\n"
                "(Например: Оскорбление в чате)"
            )
        else:
            await update.message.reply_text(
                "❌ Это НЕ пересланное сообщение!\n\n"
                "Как правильно переслать:\n"
                "1. Нажмите на сообщение\n"
                "2. Выберите 'Переслать'\n"
                "3. Выберите этого бота"
            )
        return
    
    # ===== ШАГ 3: ВВОД ПРИЧИНЫ =====
    if step == "waiting_reason":
        # ЭТОТ БЛОК ТЕПЕРЬ ВЫПОЛНЯЕТСЯ!
        logger.info(f"ПОЛУЧЕНА ПРИЧИНА: {text}")
        
        data = user_data[user_id]
        target = data.get("target")
        message = data.get("message")
        
        if not target or not message:
            await update.message.reply_text("❌ Ошибка: данные потеряны. Начните заново /start")
            del user_data[user_id]
            return
        
        # Генерируем текст жалобы
        complaint_text = generate_complaint(target, message, text)
        subject = generate_subject(target)
        
        await update.message.reply_text(
            f"⏳ Отправляю жалобу...\n"
            f"📝 Причина: {text}\n"
            f"🎯 Цель: @{target}"
        )
        
        # Отправляем жалобу
        success = send_complaint_via_email(
            sender_email=EMAIL_ACCOUNTS[0]['email'],
            sender_password=EMAIL_ACCOUNTS[0]['password'],
            target_email="abuse@telegram.org",
            subject=subject,
            body=complaint_text
        )
        
        if success:
            await update.message.reply_text(
                f"✅ ЖАЛОБА ОТПРАВЛЕНА!\n"
                f"📧 С: {EMAIL_ACCOUNTS[0]['email']}\n"
                f"📨 Кому: abuse@telegram.org\n"
                f"🎯 Цель: @{target}\n"
                f"📝 Причина: {text}\n\n"
                f"Проверь папку 'Отправленные' в Gmail!"
            )
        else:
            await update.message.reply_text(
                "❌ ОШИБКА ОТПРАВКИ!\n\n"
                "Проверь:\n"
                "1. Пароль от почты\n"
                "2. Доступ для ненадежных приложений\n"
                "https://myaccount.google.com/lesssecureapps"
            )
        
        del user_data[user_id]
        return
    
    # Если шаг неизвестен
    await update.message.reply_text("❌ Неизвестный шаг. Нажмите /start заново")
    del user_data[user_id]

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in user_data:
        del user_data[user_id]
        await update.message.reply_text("❌ Процесс отменен")
    else:
        await update.message.reply_text("Нет активного процесса")

# ===== ЗАПУСК =====

def main():
    application = Application.builder().token(TOKEN).build()
    
    # Регистрируем ТОЛЬКО ОДИН обработчик для всех текстовых сообщений
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))
    
    print("="*60)
    print("🤖 БОТ ДЛЯ ЖАЛОБ ЧЕРЕЗ EMAIL")
    print("="*60)
    print(f"📧 Email: {EMAIL_ACCOUNTS[0]['email']}")
    print(f"📨 Кому: abuse@telegram.org")
    print("="*60)
    print("📩 Используй /start")
    print("="*60)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
