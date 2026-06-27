# bot.py - ПОЛНАЯ ВЕРСИЯ С ИСПРАВЛЕНИЕМ

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
    # Добавляй сюда другие почты
]

# Отключаем webhook
try:
    requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")
except:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
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
        
        # Определяем SMTP сервер по домену
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
    templates = [
        f"""
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
""",
        f"""
⚠️ COMPLAINT AGAINST @{target}

Telegram Support Team,

I am reporting user @{target} for violating Telegram's Terms of Service.

VIOLATION: {reason}

EVIDENCE:
{message}

This user has been engaging in:
- Harassment
- Spam
- Violation of community guidelines

Requested action:
- Account suspension
- Investigation
- Removal of content

Case ID: #{random.randint(1000, 9999)}
Date: {time.strftime('%Y-%m-%d %H:%M:%S')}

Sincerely,
Telegram User
"""
    ]
    return random.choice(templates)

def generate_subject(target):
    subjects = [
        f"URGENT: Complaint Against @{target}",
        f"VIOLATION REPORT: User @{target}",
        f"FORMAL COMPLAINT: @{target} Violates Rules",
        f"🚨 EMERGENCY: Report @{target}",
        f"Telegram Abuse Report: @{target}"
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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка всех сообщений"""
    user_id = update.message.from_user.id
    
    # Если пользователь не в процессе - игнорируем
    if user_id not in user_data:
        await update.message.reply_text("Нажмите /start для начала")
        return
    
    text = update.message.text
    step = user_data[user_id].get("step")
    
    if step == "waiting_target":
        # Сохраняем цель
        user_data[user_id]["target"] = text
        user_data[user_id]["step"] = "waiting_message"
        await update.message.reply_text(
            f"✅ Цель: {text}\n"
            "Теперь ПЕРЕШЛИТЕ сообщение, на которое нужно отправить жалобу"
        )
    
    elif step == "waiting_message":
        # ===== ИСПРАВЛЕННАЯ ПРОВЕРКА ПЕРЕСЛАННОГО СООБЩЕНИЯ =====
        
        # Проверяем, является ли сообщение пересланным
        is_forwarded = False
        forwarded_text = ""
        
        # Способ 1: Проверяем forward_from (если переслано от пользователя)
        if hasattr(update.message, 'forward_from') and update.message.forward_from is not None:
            is_forwarded = True
            forwarded_text = update.message.text or "Медиа-сообщение"
        
        # Способ 2: Проверяем forward_from_chat (если переслано из чата/канала)
        elif hasattr(update.message, 'forward_from_chat') and update.message.forward_from_chat is not None:
            is_forwarded = True
            forwarded_text = update.message.text or "Медиа-сообщение"
        
        # Способ 3: Проверяем forward_origin (новый API)
        elif hasattr(update.message, 'forward_origin') and update.message.forward_origin is not None:
            is_forwarded = True
            forwarded_text = update.message.text or "Медиа-сообщение"
        
        # Способ 4: Проверяем наличие подписи "Forwarded from"
        elif update.message.text and "Forwarded from" in update.message.text:
            is_forwarded = True
            forwarded_text = update.message.text
        
        # Если сообщение переслано
        if is_forwarded:
            user_data[user_id]["message"] = forwarded_text
            user_data[user_id]["step"] = "waiting_reason"
            await update.message.reply_text(
                "✅ Сообщение получено!\n"
                "📝 Теперь напишите причину жалобы"
            )
        else:
            await update.message.reply_text(
                "❌ Это НЕ пересланное сообщение!\n\n"
                "Как правильно переслать:\n"
                "1. Нажмите на сообщение\n"
                "2. Выберите 'Переслать'\n"
                "3. Выберите этого бота\n"
                "4. Отправьте"
            )

async def handle_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка причины и отправка жалобы"""
    user_id = update.message.from_user.id
    reason = update.message.text
    
    if user_id not in user_data:
        await update.message.reply_text("Нажмите /start")
        return
    
    if user_data[user_id].get("step") != "waiting_reason":
        return
    
    data = user_data[user_id]
    target = data.get("target")
    message = data.get("message")
    
    if not target or not message:
        await update.message.reply_text("❌ Ошибка: данные потеряны. Начните заново /start")
        del user_data[user_id]
        return
    
    # Генерируем текст жалобы
    complaint_text = generate_complaint(target, message, reason)
    subject = generate_subject(target)
    
    await update.message.reply_text(
        "⏳ Отправляю жалобу с твоей почты...\n"
        "Это может занять несколько секунд"
    )
    
    # Отправляем с каждого email аккаунта
    success_count = 0
    total_accounts = len(EMAIL_ACCOUNTS)
    
    for account in EMAIL_ACCOUNTS:
        success = send_complaint_via_email(
            sender_email=account['email'],
            sender_password=account['password'],
            target_email="abuse@telegram.org",
            subject=subject,
            body=complaint_text
        )
        
        if success:
            success_count += 1
            await update.message.reply_text(
                f"✅ Жалоба отправлена с {account['email']}"
            )
        else:
            await update.message.reply_text(
                f"❌ Ошибка с {account['email']}"
            )
        
        # Пауза между отправками
        if len(EMAIL_ACCOUNTS) > 1:
            await asyncio.sleep(5)
    
    # Итог
    if success_count > 0:
        await update.message.reply_text(
            f"✅ ГОТОВО!\n"
            f"📨 Отправлено жалоб: {success_count} из {total_accounts}\n"
            f"📧 С почт: {', '.join([a['email'] for a in EMAIL_ACCOUNTS[:success_count]])}\n"
            f"📨 Кому: abuse@telegram.org\n"
            f"🎯 Цель: @{target}\n\n"
            f"Проверь папку 'Отправленные' в Gmail!"
        )
    else:
        await update.message.reply_text(
            "❌ НИ ОДНА ЖАЛОБА НЕ ОТПРАВЛЕНА!\n\n"
            "Возможные причины:\n"
            "1. Неправильный пароль\n"
            "2. Нужно включить 'Доступ для ненадежных приложений'\n"
            "3. Не подтвержден вход в Google\n\n"
            "Инструкция:\n"
            "1. Зайди в Gmail\n"
            "2. Настройки → Безопасность\n"
            "3. Включи 'Доступ для ненадежных приложений'\n"
            "4. Или создай пароль приложения"
        )
    
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
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reason))
    
    print("="*60)
    print("🤖 БОТ ДЛЯ ЖАЛОБ ЧЕРЕЗ EMAIL")
    print("="*60)
    print(f"📧 Email аккаунтов: {len(EMAIL_ACCOUNTS)}")
    for acc in EMAIL_ACCOUNTS:
        print(f"   - {acc['email']}")
    print(f"📨 Кому: abuse@telegram.org")
    print("="*60)
    print("📩 Используй /start")
    print("="*60)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
