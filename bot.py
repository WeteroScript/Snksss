# bot.py - ИСПРАВЛЕННАЯ ВЕРСИЯ (ССЫЛКА НА СООБЩЕНИЕ)

import os
import asyncio
import logging
import smtplib
import random
import time
import re
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

# ===== ГЕНЕРАТОР ССЫЛКИ НА СООБЩЕНИЕ =====

def generate_message_link(update):
    """Генерирует ссылку на пересланное сообщение"""
    try:
        # Если переслано из канала/чата
        if hasattr(update.message, 'forward_from_chat') and update.message.forward_from_chat:
            chat_id = update.message.forward_from_chat.id
            message_id = update.message.forward_from_message_id
            
            # Для публичных каналов
            if str(chat_id).startswith('-100'):
                chat_username = f"c/{str(chat_id)[4:]}"
            else:
                chat_username = str(chat_id)
            
            return f"https://t.me/{chat_username}/{message_id}"
        
        # Если переслано от пользователя (нельзя сделать ссылку)
        elif hasattr(update.message, 'forward_from') and update.message.forward_from:
            return "Message forwarded from a user (link not available for private chats)"
        
        # Если переслано через forward_origin
        elif hasattr(update.message, 'forward_origin') and update.message.forward_origin:
            return "Message forwarded (link not available)"
        
        else:
            return "No link available"
            
    except Exception as e:
        logger.error(f"Ошибка генерации ссылки: {e}")
        return "Link could not be generated"

# ===== ГЕНЕРАТОР НАТУРАЛЬНЫХ ТЕКСТОВ =====

def generate_complaint(target, message, reason, message_link):
    if target.startswith('@@'):
        target = target[1:]
    elif target.startswith('@'):
        target = target
    
    templates = [
        f"""
Hi Telegram Team,

I need to report a user who's been causing problems. The username is @{target}.

They sent me this message:
{message}

This is clearly {reason}. I've seen them do this to other people too.

Here's the direct link to the message:
{message_link}

I'd appreciate it if you could check their account and take action. This kind of behavior ruins the experience for everyone.

Thanks for looking into this.
""",
        
        f"""
Hello Support,

I'm writing to complain about @{target}. I received an inappropriate message from them.

The content:
{message}

I'm reporting this because {reason}. I believe this violates Telegram's rules.

Link to the message:
{message_link}

Please investigate this account. I've already blocked them but they might be doing this to others.

Regards.
""",
        
        f"""
Dear Telegram,

I've been dealing with harassment from @{target}. They sent me a message that made me uncomfortable.

Here's what they said:
{message}

The reason I'm reporting this: {reason}.

You can see the message here:
{message_link}

I'm not sure if they've done this before, but this is not okay. Please take a look at their account.

Thank you.
""",
        
        f"""
To the Support Team,

I want to report @{target} for sending inappropriate content.

The message in question:
{message}

This is a clear case of {reason}. I'm attaching the link to the exact message.

Link:
{message_link}

I hope you can take appropriate action against this user. Nobody should have to deal with this kind of behavior.

Sincerely.
""",
        
        f"""
Hi there,

I've got a complaint about @{target}. They've been sending messages that go against Telegram's guidelines.

Here's the message:
{message}

Why I'm reporting this: {reason}.

You can see it here:
{message_link}

Could you please look into this? I think other users might be affected too.

Thanks for your help.
""",
        
        f"""
Hello,

@{target} sent me something that I think breaks the rules.

The message:
{message}

I'm reporting this because {reason}. It's not the first time either.

Direct link:
{message_link}

I'd really appreciate it if you could review their account and take action if necessary.

Best.
""",
        
        f"""
Telegram Support,

I'd like to report @{target} for inappropriate behavior.

They sent this:
{message}

This is {reason} and it violates your policies.

Evidence link:
{message_link}

I've been using Telegram for a while and this is the first time I've had to report someone. Please handle this properly.

Thanks.
""",
        
        f"""
Hi,

I'm contacting you about @{target}. They've been sending messages that are not acceptable.

Content of the message:
{message}

The issue is {reason}. I think this needs to be addressed.

Here's the message link:
{message_link}

Please take the necessary steps. I'm counting on your support team to handle this.

Regards.
""",
        
        f"""
Dear Support,

I need to report a user named @{target}. They sent me a message that made me uncomfortable.

What they wrote:
{message}

The reason for this report: {reason}.

You can check the message yourself:
{message_link}

I've already blocked this person but I'm reporting them so others don't have to deal with the same thing.

Thank you for your time.
""",
        
        f"""
Hello Telegram Team,

@{target} has been sending messages that I believe violate your terms of service.

The message:
{message}

This is {reason}. I'm providing the link to the original message.

Link:
{message_link}

I hope you can take action against this account. Everyone deserves to use Telegram without dealing with this kind of stuff.

Best regards.
""",
        
        f"""
To whom it may concern,

I'm writing to report @{target} for inappropriate messaging.

The message I received:
{message}

I'm reporting this because {reason}. This goes against what Telegram stands for.

Direct link:
{message_link}

I'd like to request that you review this user's activity and take appropriate measures.

Sincerely.
""",
        
        f"""
Hi Support Team,

I have a complaint about @{target}. They've been sending messages that are not okay.

Here's what they sent:
{message}

Why I'm reporting: {reason}.

You can see the message here:
{message_link}

I'm not the only one who's been affected by this user. Please check their account.

Thanks.
""",
        
        f"""
Hello,

I need to report @{target} for sending harassing messages.

The message:
{message}

This is {reason}. I've attached the link to the exact message.

Link:
{message_link}

I hope you can take action against this user. It's important to keep Telegram safe for everyone.

Regards.
""",
        
        f"""
Dear Telegram,

I'm reporting @{target} for violating your community guidelines.

They sent me this:
{message}

The violation is {reason}. Here's the link:

{message_link}

Please look into this. I've been using Telegram for years and I want to help keep the platform clean.

Thank you.
""",
        
        f"""
Hi,

@{target} sent me a message that I think crosses the line.

The content:
{message}

I'm reporting this because {reason}. This is not acceptable.

Message link:
{message_link}

I'd appreciate it if you could review their account and take the necessary steps.

Best.
""",
        
        f"""
Telegram Support,

I've received a message from @{target} that I'd like to report.

Here's the message:
{message}

This is clearly {reason}. I'm providing the link:

{message_link}

I hope you can take action. Thanks for reading this.

Sincerely.
""",
        
        f"""
Hello,

I want to report @{target} for sending messages that violate Telegram's policies.

The message:
{message}

Reason: {reason}.

Direct link:
{message_link}

Please take a look at this user's account and decide what action is needed.

Regards.
""",
        
        f"""
Dear Support Team,

@{target} has been bothering me with inappropriate messages.

Here's what they sent:
{message}

I'm reporting this because {reason}. You can verify it here:

{message_link}

I'd really appreciate your help with this. Thanks.

Best.
""",
        
        f"""
Hi,

I've got a report about @{target}. They sent a message that I think is against the rules.

The message:
{message}

The problem is {reason}. Here's the link:

{message_link}

Please check it out and take action if necessary. Thank you.

Regards.
""",
        
        f"""
Telegram Team,

I need to file a complaint against @{target}.

They sent me this:
{message}

This is {reason}. I've included the link to the message.

{message_link}

Please investigate this user. I've had enough of this behavior.

Sincerely.
""",
        
        f"""
Hello Support,

I'm reporting @{target} for abusive behavior.

Message they sent:
{message}

Why it's a problem: {reason}.

Evidence:
{message_link}

I'd appreciate it if you could take action against this account. Thanks.

Best regards.
"""
    ]
    
    return random.choice(templates)

def generate_subject(target):
    if target.startswith('@@'):
        target = target[1:]
    elif target.startswith('@'):
        target = target
    
    subjects = [
        f"Complaint about @{target}",
        f"Report: User @{target}",
        f"@{target} - Policy Violation",
        f"User Report: @{target}",
        f"Abuse report: @{target}",
        f"Message violation by @{target}",
        f"Harassment from @{target}",
        f"@{target} - Rule Breach",
        f"Violation report: @{target}",
        f"Complaint: @{target} sent inappropriate content"
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
    await query.edit_message_text("🎯 Enter the username (e.g. @username)")

async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    
    if user_id not in user_data:
        await update.message.reply_text("Press /start to begin")
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
            f"✅ Target set: {clean_target}\n"
            "Now FORWARD the message you want to report"
        )
        return
    
    # ШАГ 2: ПЕРЕСЫЛКА
    if step == "waiting_message":
        is_forwarded = False
        forwarded_text = ""
        
        # Проверяем, переслано ли сообщение
        if hasattr(update.message, 'forward_from') and update.message.forward_from:
            is_forwarded = True
            forwarded_text = update.message.text or "Media message"
            user_data[user_id]["forward_type"] = "user"
            
        elif hasattr(update.message, 'forward_from_chat') and update.message.forward_from_chat:
            is_forwarded = True
            forwarded_text = update.message.text or "Media message"
            user_data[user_id]["forward_type"] = "chat"
            user_data[user_id]["forward_chat_id"] = update.message.forward_from_chat.id
            user_data[user_id]["forward_message_id"] = update.message.forward_from_message_id
            
        elif hasattr(update.message, 'forward_origin') and update.message.forward_origin:
            is_forwarded = True
            forwarded_text = update.message.text or "Media message"
            user_data[user_id]["forward_type"] = "origin"
        
        if is_forwarded:
            user_data[user_id]["message"] = forwarded_text
            user_data[user_id]["step"] = "waiting_reason"
            await update.message.reply_text(
                "✅ Message received!\n"
                "📝 Now write the REASON for the complaint"
            )
        else:
            await update.message.reply_text(
                "❌ That's not a forwarded message!\n"
                "Tap and hold → 'Forward' → choose this bot"
            )
        return
    
    # ШАГ 3: ПРИЧИНА → ОТПРАВКА
    if step == "waiting_reason":
        data = user_data[user_id]
        target = data.get("target")
        message = data.get("message")
        forward_type = data.get("forward_type", "unknown")
        
        if not target or not message:
            await update.message.reply_text("❌ Error. Press /start again")
            del user_data[user_id]
            return
        
        # Генерируем ссылку
        message_link = "Link not available for this type of forward"
        
        if forward_type == "chat":
            chat_id = data.get("forward_chat_id")
            msg_id = data.get("forward_message_id")
            if chat_id and msg_id:
                if str(chat_id).startswith('-100'):
                    chat_username = f"c/{str(chat_id)[4:]}"
                else:
                    chat_username = str(chat_id)
                message_link = f"https://t.me/{chat_username}/{msg_id}"
        elif forward_type == "user":
            message_link = "Message forwarded from a user (link not available for private chats)"
        else:
            message_link = "Link could not be generated"
        
        clean_target = target
        if clean_target.startswith('@@'):
            clean_target = clean_target[1:]
        
        complaint = generate_complaint(clean_target, message, text, message_link)
        subject = generate_subject(clean_target)
        
        await update.message.reply_text(
            f"⏳ Sending complaint for @{clean_target}..."
        )
        
        success = send_complaint_via_email(
            sender_email=EMAIL_ACCOUNTS[0]['email'],
            sender_password=EMAIL_ACCOUNTS[0]['password'],
            target_email="abuse@telegram.org",
            subject=subject,
            body=complaint
        )
        
        if success:
            await update.message.reply_text(
                f"✅ COMPLAINT SENT!\n"
                f"📧 From: {EMAIL_ACCOUNTS[0]['email']}\n"
                f"📨 To: abuse@telegram.org\n"
                f"🎯 Target: @{clean_target}\n\n"
                f"📬 Check your Gmail 'Sent' folder!"
            )
        else:
            await update.message.reply_text(
                "❌ SEND FAILED!\n"
                "Check the console logs."
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

# ===== ЗАПУСК =====

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))
    
    print("="*60)
    print("🤖 COMPLAINT BOT")
    print("="*60)
    print(f"📧 Email: {EMAIL_ACCOUNTS[0]['email']}")
    print(f"📨 To: abuse@telegram.org")
    print("="*60)
    print("📩 Use /start")
    print("="*60)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
