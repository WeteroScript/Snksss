# bot.py - БЕЗ ПАУЗЫ + ССЫЛКА НА СООБЩЕНИЕ

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

EMAIL_ACCOUNTS = [
    {
        "email": "allllkssso1@gmail.com",
        "password": "hrzaxqferrgdfsbr",
        "smtp": "smtp.gmail.com",
        "port": 587
    },
]

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
        
        logger.info(f"✅ Письмо отправлено с {sender_email} на {target_email}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return False

# ===== ГЕНЕРАТОР ССЫЛКИ НА СООБЩЕНИЕ (РАБОТАЕТ ВСЕГДА) =====

def get_message_link(update):
    """Универсальная генерация ссылки на пересланное сообщение"""
    try:
        # 1. Если переслано из канала/чата (есть forward_from_chat)
        if hasattr(update.message, 'forward_from_chat') and update.message.forward_from_chat:
            chat = update.message.forward_from_chat
            msg_id = update.message.forward_from_message_id
            
            if chat.username:
                return f"https://t.me/{chat.username}/{msg_id}"
            elif str(chat.id).startswith('-100'):
                return f"https://t.me/c/{str(chat.id)[4:]}/{msg_id}"
            else:
                return f"https://t.me/c/{chat.id}/{msg_id}"
        
        # 2. Если переслано от пользователя (forward_from)
        elif hasattr(update.message, 'forward_from') and update.message.forward_from:
            user = update.message.forward_from
            if user.username:
                return f"https://t.me/{user.username}"
            else:
                return f"Forwarded from user (no public link available)"
        
        # 3. Если есть forward_origin (новый API)
        elif hasattr(update.message, 'forward_origin') and update.message.forward_origin:
            origin = update.message.forward_origin
            if hasattr(origin, 'chat') and origin.chat:
                chat = origin.chat
                if chat.username:
                    return f"https://t.me/{chat.username}"
                else:
                    return f"https://t.me/c/{chat.id}"
            return "Forwarded (link not available)"
        
        else:
            return "Not a forwarded message"
            
    except Exception as e:
        logger.error(f"Ошибка генерации ссылки: {e}")
        return "Link could not be generated"

# ===== ГЕНЕРАТОР ТЕКСТОВ =====

def generate_complaint(target, message, reason, message_link):
    if target.startswith('@@'):
        target = target[1:]
    
    templates = [
        f"""
Hi Telegram Team,

I need to report @{target}. They sent me a message that violates your policies.

The message:
{message}

Reason: {reason}

Link to the message: {message_link}

Please investigate this account. Thank you.
""",
        f"""
Hello Support,

I'm writing to complain about @{target}. Here's what they sent:

{message}

Why it's a problem: {reason}

Evidence: {message_link}

Please take action against this user. Thanks.
""",
        f"""
Dear Telegram,

@{target} has been sending inappropriate messages. Here's one of them:

{message}

This is {reason}. You can check it here: {message_link}

Please review their account. Regards.
""",
        f"""
To Telegram Support,

I want to report @{target} for the following message:

{message}

Reason: {reason}

Direct link: {message_link}

I hope you can take appropriate action. Sincerely.
""",
        f"""
Hi Support Team,

@{target} sent me this message:

{message}

I'm reporting because {reason}. Here's the link: {message_link}

Please look into this. Thanks.
""",
        f"""
Hello,

I've received an inappropriate message from @{target}:

{message}

This is {reason}. Evidence: {message_link}

Please check their account and take action. Best.
""",
        f"""
Telegram Team,

I'd like to report @{target} for violating rules. They sent:

{message}

Reason: {reason}

Link: {message_link}

Please investigate. Thank you.
""",
        f"""
Hi,

@{target} is sending messages that break Telegram's guidelines. Example:

{message}

Why it's wrong: {reason}

Here's where you can see it: {message_link}

Please take action. Regards.
""",
        f"""
Dear Support,

I'm reporting @{target} for the following:

{message}

Reason: {reason}

Link: {message_link}

Please review this user's activity. Thanks.
""",
        f"""
Hello Support,

@{target} sent an inappropriate message:

{message}

This is {reason}. You can verify here: {message_link}

Please take necessary action. Sincerely.
""",
        f"""
Hi,

I want to report @{target}. They've been bothering me. Last message:

{message}

Why it's a problem: {reason}

Proof: {message_link}

Please do something about this. Thanks.
""",
        f"""
Telegram Support,

I've had enough of @{target}. They sent:

{message}

Reason: {reason}

Link: {message_link}

Please suspend this account. Regards.
""",
        f"""
Hello Team,

@{target} keeps sending messages like this:

{message}

This is {reason}. Here's the link: {message_link}

Please investigate. Thank you.
""",
        f"""
Dear Support Team,

I'm filing a complaint about @{target}. They sent:

{message}

Violation: {reason}

Evidence: {message_link}

Please take action. Best.
""",
        f"""
Hi,

@{target} is violating Telegram's rules. Message:

{message}

Reason: {reason}

Link: {message_link}

Please check their account. Thanks.
""",
        f"""
Hello Support,

I need to report @{target} for sending abusive content:

{message}

This is {reason}. You can see it here: {message_link}

Please review. Regards.
""",
        f"""
Telegram Team,

@{target} sent me this:

{message}

Reason: {reason}

Link: {message_link}

I'd appreciate it if you could take action. Thanks.
""",
        f"""
Hi Support,

I've been receiving messages from @{target}. Last one:

{message}

Why it's a problem: {reason}

Proof: {message_link}

Please do something. Sincerely.
""",
        f"""
Dear Telegram,

@{target} has been harassing me. They sent:

{message}

Reason: {reason}

Link to message: {message_link}

Please investigate. Thank you.
""",
        f"""
Hello Team,

@{target} is sending inappropriate content. Example:

{message}

Reason: {reason}

Evidence: {message_link}

Please take appropriate action. Thanks.
"""
    ]
    
    return random.choice(templates)

def generate_subject(target):
    if target.startswith('@@'):
        target = target[1:]
    
    subjects = [
        f"Complaint about @{target}",
        f"Report: User @{target}",
        f"@{target} - Policy Violation",
        f"User Report: @{target}",
        f"Abuse report: @{target}",
        f"Harassment from @{target}",
        f"Violation by @{target}",
        f"@{target} - Rule Breach",
        f"Complaint: @{target}",
        f"Report: @{target} inappropriate content"
    ]
    return random.choice(subjects)

# ===== ОБРАБОТЧИКИ =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚀 Start", callback_data="start_action")],
        [InlineKeyboardButton("🎯 Set target", callback_data="target_action")]
    ]
    await update.message.reply_text(
        "Welcome! Choose an option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_data[user_id] = {"step": "waiting_target"}
    await query.edit_message_text("🎯 Enter username (e.g. @username)")

async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    
    if user_id not in user_data:
        await update.message.reply_text("Press /start")
        return
    
    step = user_data[user_id].get("step")
    
    # ШАГ 1: ЦЕЛЬ
    if step == "waiting_target":
        clean_target = text
        if clean_target.startswith('@@'):
            clean_target = clean_target[1:]
        user_data[user_id]["target"] = clean_target
        user_data[user_id]["step"] = "waiting_message"
        await update.message.reply_text(
            f"✅ Target: {clean_target}\n"
            "Now FORWARD the message"
        )
        return
    
    # ШАГ 2: ПЕРЕСЫЛКА
    if step == "waiting_message":
        is_forwarded = False
        forwarded_text = ""
        
        if hasattr(update.message, 'forward_from') and update.message.forward_from:
            is_forwarded = True
            forwarded_text = update.message.text or "Media message"
        elif hasattr(update.message, 'forward_from_chat') and update.message.forward_from_chat:
            is_forwarded = True
            forwarded_text = update.message.text or "Media message"
        elif hasattr(update.message, 'forward_origin') and update.message.forward_origin:
            is_forwarded = True
            forwarded_text = update.message.text or "Media message"
        
        if is_forwarded:
            user_data[user_id]["message"] = forwarded_text
            # Сохраняем update для генерации ссылки позже
            user_data[user_id]["update"] = update
            user_data[user_id]["step"] = "waiting_reason"
            await update.message.reply_text(
                "✅ Message received!\n"
                "📝 Write the REASON"
            )
        else:
            await update.message.reply_text(
                "❌ Forward the message!\n"
                "Tap → Forward → choose this bot"
            )
        return
    
    # ШАГ 3: ПРИЧИНА → ОТПРАВКА
    if step == "waiting_reason":
        data = user_data[user_id]
        target = data.get("target")
        message = data.get("message")
        saved_update = data.get("update")
        
        if not target or not message:
            await update.message.reply_text("❌ Error. Press /start")
            del user_data[user_id]
            return
        
        # Генерируем ссылку
        if saved_update:
            message_link = get_message_link(saved_update)
        else:
            message_link = "Link not available"
        
        clean_target = target
        if clean_target.startswith('@@'):
            clean_target = clean_target[1:]
        
        # Генерируем текст
        complaint = generate_complaint(clean_target, message, text, message_link)
        subject = generate_subject(clean_target)
        
        await update.message.reply_text(
            f"⏳ Sending complaint for @{clean_target}..."
        )
        
        # ОТПРАВЛЯЕМ (без паузы, 5 раз подряд)
        success_count = 0
        for i in range(5):
            success = send_complaint_via_email(
                sender_email=EMAIL_ACCOUNTS[0]['email'],
                sender_password=EMAIL_ACCOUNTS[0]['password'],
                target_email="abuse@telegram.org",
                subject=subject + f" #{i+1}",
                body=complaint + f"\n\n---\nThis is complaint #{i+1} of 5"
            )
            
            if success:
                success_count += 1
                await update.message.reply_text(f"✅ Complaint #{i+1} sent")
            else:
                await update.message.reply_text(f"❌ Complaint #{i+1} failed")
                break
        
        # Итог
        await update.message.reply_text(
            f"✅ COMPLETED!\n"
            f"📨 Sent: {success_count}/5\n"
            f"📧 From: {EMAIL_ACCOUNTS[0]['email']}\n"
            f"🎯 Target: @{clean_target}\n"
            f"🔗 Link: {message_link}\n\n"
            f"📬 Check your Gmail 'Sent' folder!"
        )
        
        del user_data[user_id]
        return
    
    await update.message.reply_text("❌ Error. Press /start")
    del user_data[user_id]

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in user_data:
        del user_data[user_id]
        await update.message.reply_text("❌ Cancelled")
    else:
        await update.message.reply_text("No active process")

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))
    
    print("="*60)
    print("🤖 COMPLAINT BOT (NO PAUSE)")
    print("="*60)
    print(f"📧 Email: {EMAIL_ACCOUNTS[0]['email']}")
    print(f"📨 To: abuse@telegram.org")
    print(f"📤 Sends: 5 complaints instantly")
    print("="*60)
    print("📩 Use /start")
    print("="*60)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
