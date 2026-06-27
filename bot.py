# bot.py - ПАРСИТ ССЫЛКУ ИЗ ТВОЕГО СООБЩЕНИЯ

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

# ===== ФУНКЦИЯ ДЛЯ ПОИСКА ССЫЛКИ =====

def extract_telegram_link(text):
    """Находит ссылку на Telegram в тексте"""
    patterns = [
        r'https?://t\.me/[^\s]+',       # https://t.me/...
        r'https?://telegram\.me/[^\s]+', # https://telegram.me/...
        r't\.me/[^\s]+',                # t.me/...
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    
    return None

# ===== ГЕНЕРАТОР ТЕКСТОВ =====

def generate_complaint(target, message, reason, message_link):
    if target.startswith('@@'):
        target = target[1:]
    
    templates = [
        f"""
Hi Telegram Team,

I'm writing to report @{target}. This user suddenly became aggressive towards me for no reason.

Here's what they sent:
{message}

This is clearly {reason}. This person started attacking me out of nowhere and it's making me uncomfortable.

Link to the message: {message_link}

I've been using Telegram for a while and I've never experienced anything like this. Please look into this account.

Thanks.
""",
        
        f"""
Hello Support,

I need to report @{target}. This user started being aggressive towards me in a conversation. I didn't provoke them or anything.

The message:
{message}

Why I'm reporting: {reason}.

Direct link: {message_link}

This kind of behavior shouldn't be allowed on Telegram. Please take action.

Regards.
""",
        
        f"""
Dear Telegram Team,

I'm filing a complaint about @{target}. They started acting aggressively towards me for absolutely no reason. I was just minding my own business.

What they said:
{message}

This is {reason}. They came at me out of nowhere and I don't appreciate it.

You can see it here: {message_link}

I hope you can review this user's account and take the necessary steps. Nobody should have to deal with this.

Sincerely.
""",
        
        f"""
Hi Support Team,

I want to report @{target}. This user started becoming aggressive towards me for no reason at all.

The message they sent:
{message}

This is {reason}. I didn't even know this person and they just started attacking me.

Link: {message_link}

Please investigate this account. This isn't okay.

Thanks.
""",
        
        f"""
Hello Telegram,

@{target} started being aggressive towards me out of nowhere. I've never interacted with them before and they just sent me this.

The message:
{message}

Reason: {reason}.

You can check it here: {message_link}

I'd really appreciate it if you could take a look at their account and decide what action is needed.

Regards.
""",
        
        f"""
To the Support Team,

I'm reporting @{target} because they started being aggressive towards me for no reason. I didn't say anything to them first.

What they sent:
{message}

Why this is wrong: {reason}.

Evidence: {message_link}

Please take a look at this. I don't want other users to go through the same thing.

Sincerely.
""",
        
        f"""
Hi,

@{target} started acting aggressive towards me out of nowhere. I was just having a normal day and this person decided to attack me.

The message:
{message}

This is {reason}. They had no reason to act like this.

Link: {message_link}

Please investigate this user. I'm not the only one they're doing this to.

Thanks.
""",
        
        f"""
Hello Support,

I need to report @{target}. They've been aggressive towards me for no reason. I didn't even know them before this.

Here's what they sent:
{message}

Why it's a problem: {reason}.

You can see it here: {message_link}

I hope you can take appropriate action. This kind of behavior ruins the experience for everyone.

Regards.
""",
        
        f"""
Dear Telegram Team,

@{target} started being aggressive towards me for absolutely no reason. I didn't say or do anything to provoke them.

The message:
{message}

This is {reason}. They just came at me out of nowhere.

Proof: {message_link}

Please check this user's account and take action if necessary. This is not acceptable.

Thank you.
""",
        
        f"""
Hi Support,

I'm writing to complain about @{target}. This user became aggressive towards me for no reason at all.

The message they sent:
{message}

Reason: {reason}.

Link: {message_link}

I've been using Telegram for years and this is the first time I've had to report someone. Please handle this.

Thanks.
"""
    ]
    
    return random.choice(templates)

def generate_subject(target):
    if target.startswith('@@'):
        target = target[1:]
    
    subjects = [
        f"Complaint about @{target}",
        f"Report: User @{target}",
        f"@{target} - Aggressive Behavior",
        f"User Report: @{target}",
        f"Abuse report: @{target}",
        f"Harassment from @{target}",
        f"@{target} - Policy Violation",
        f"Violation by @{target}",
        f"Complaint: @{target}",
        f"Report: @{target} aggressive behavior"
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
            user_data[user_id]["step"] = "waiting_reason"
            await update.message.reply_text(
                "✅ Message received!\n"
                "📝 Write the REASON and paste the link to the message\n"
                "Example: Оскорбление в чате https://t.me/chattarakanovtelefone/162402"
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
        
        if not target or not message:
            await update.message.reply_text("❌ Error. Press /start")
            del user_data[user_id]
            return
        
        # ИЩЕМ ССЫЛКУ В ТЕКСТЕ
        message_link = extract_telegram_link(text)
        
        if not message_link:
            await update.message.reply_text(
                "❌ No link found! Please include the link to the message.\n"
                "Example: Оскорбление в чате https://t.me/chattarakanovtelefone/162402"
            )
            return
        
        # Убираем ссылку из причины
        reason = re.sub(r'https?://[^\s]+', '', text).strip()
        if not reason:
            reason = "Inappropriate behavior"
        
        clean_target = target
        if clean_target.startswith('@@'):
            clean_target = clean_target[1:]
        
        await update.message.reply_text(
            f"⏳ Sending 3 complaints for @{clean_target}...\n"
            f"⏰ Wait 30 minutes between each"
        )
        
        # ===== ОТПРАВЛЯЕМ 3 ЖАЛОБЫ С ПАУЗОЙ 30 МИНУТ =====
        success_count = 0
        
        for i in range(3):
            complaint = generate_complaint(clean_target, message, reason, message_link)
            subject = generate_subject(clean_target)
            
            success = send_complaint_via_email(
                sender_email=EMAIL_ACCOUNTS[0]['email'],
                sender_password=EMAIL_ACCOUNTS[0]['password'],
                target_email="abuse@telegram.org",
                subject=subject,
                body=complaint
            )
            
            if success:
                success_count += 1
                await update.message.reply_text(
                    f"✅ Complaint #{i+1} sent successfully!\n"
                    f"📧 From: {EMAIL_ACCOUNTS[0]['email']}\n"
                    f"🎯 Target: @{clean_target}"
                )
            else:
                await update.message.reply_text(
                    f"❌ Complaint #{i+1} failed!"
                )
                break
            
            if i < 2:
                await update.message.reply_text(
                    f"⏳ Waiting 30 minutes before next complaint...\n"
                    f"⏰ Next at: {time.strftime('%H:%M:%S', time.localtime(time.time() + 1800))}"
                )
                await asyncio.sleep(1800)
        
        # Итог
        if success_count == 3:
            await update.message.reply_text(
                f"✅ ALL 3 COMPLAINTS SENT!\n"
                f"📧 From: {EMAIL_ACCOUNTS[0]['email']}\n"
                f"📨 To: abuse@telegram.org\n"
                f"🎯 Target: @{clean_target}\n"
                f"🔗 Link: {message_link}\n\n"
                f"📬 Check your Gmail 'Sent' folder!"
            )
        else:
            await update.message.reply_text(
                f"⚠️ Only {success_count}/3 complaints sent successfully."
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
    print("🤖 COMPLAINT BOT")
    print("="*60)
    print(f"📧 Email: {EMAIL_ACCOUNTS[0]['email']}")
    print(f"📨 To: abuse@telegram.org")
    print(f"📤 Sends: 3 complaints (30 min pause between each)")
    print(f"🔗 Links: Paste link in reason message")
    print("="*60)
    print("📩 Use /start")
    print("="*60)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
