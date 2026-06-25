import os
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import time

# ===== КОНФИГ ИЗ ПЕРЕМЕННЫХ =====
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Токен бота
if not TOKEN:
    raise ValueError("❌ Ошибка: переменная TELEGRAM_BOT_TOKEN не установлена!")

# Дополнительные переменные (опционально)
TARGET_USERNAME = os.getenv("TARGET_USERNAME", "")  # Цель по умолчанию
ADMIN_ID = os.getenv("ADMIN_ID", "")  # ID админа для логов

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Хранилище данных пользователей
user_data = {}

# ===== ОБРАБОТЧИКИ =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветственное сообщение с кнопками"""
    keyboard = [
        [InlineKeyboardButton("🚀 Старт", callback_data="start_action")],
        [InlineKeyboardButton("🎯 Выбрать цель", callback_data="target_action")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Добро пожаловать, выберите кнопки снизу",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий кнопок"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "start_action":
        # Если есть цель по умолчанию
        if TARGET_USERNAME:
            user_data[user_id] = {
                "step": "waiting_message",
                "target": TARGET_USERNAME
            }
            await query.edit_message_text(
                f"🎯 Цель: {TARGET_USERNAME}\n"
                "📩 Перешлите сообщение для отправки жалобы.\n"
                "(После пересланного сообщения 👇)"
            )
        else:
            await query.edit_message_text(
                "⚠️ Сначала выберите цель через кнопку 'Выбрать цель'"
            )
    
    elif query.data == "target_action":
        await query.edit_message_text(
            "🎯 Введите username или ID цели (например: @username или 123456789)"
        )
        user_data[user_id] = {"step": "waiting_target"}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка всех текстовых сообщений"""
    user_id = update.message.from_user.id
    text = update.message.text
    
    # Если пользователь не в процессе - игнорируем
    if user_id not in user_data:
        await update.message.reply_text("Нажмите /start для начала")
        return
    
    step = user_data[user_id].get("step")
    
    if step == "waiting_target":
        # Сохраняем цель
        user_data[user_id]["target"] = text
        user_data[user_id]["step"] = "waiting_message"
        await update.message.reply_text(
            f"✅ Цель сохранена: {text}\n"
            "Теперь перешлите сообщение для отправки жалобы.\n"
            "(После пересланного сообщения 👇)"
        )
    
    elif step == "waiting_message":
        # Проверяем пересланное сообщение
        if update.message.forward_from or update.message.forward_from_chat:
            # Сохраняем пересланное сообщение
            user_data[user_id]["forwarded_message"] = update.message
            
            # Запрашиваем причину
            user_data[user_id]["step"] = "waiting_reason"
            await update.message.reply_text(
                "📝 Назовите причину для жалобы\n"
                "(После причины 👇)"
            )
        else:
            await update.message.reply_text(
                "❌ Пожалуйста, ПЕРЕШЛИТЕ сообщение (не копируйте текст).\n"
                "Нажмите на сообщение → 'Переслать' → выберите этого бота."
            )

async def handle_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка причины жалобы и запуск отправки"""
    user_id = update.message.from_user.id
    reason = update.message.text
    
    if user_id not in user_data:
        await update.message.reply_text("Нажмите /start для начала")
        return
    
    if user_data[user_id].get("step") != "waiting_reason":
        return
    
    # Сохраняем причину
    user_data[user_id]["reason"] = reason
    user_data[user_id]["step"] = "sending"
    
    await update.message.reply_text(
        "⏳ Начинаю отправку жалоб...\n"
        "Отправляется по 1 жалобе каждые 30 секунд.\n"
        "Не останавливайте бота!"
    )
    
    # Запускаем отправку жалоб
    await send_complaints(update, context)

async def send_complaints(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка жалоб в техподдержку"""
    user_id = update.message.from_user.id
    data = user_data[user_id]
    
    target = data.get("target")
    forwarded_msg = data.get("forwarded_message")
    reason = data.get("reason")
    
    # Формируем текст жалобы
    complaint_text = (
        f"🚨 ЖАЛОБА НА ПОЛЬЗОВАТЕЛЯ\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Цель: {target}\n"
        f"📝 Причина: {reason}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📩 Пересланное сообщение:\n"
        f"{forwarded_msg.text if forwarded_msg.text else '[Медиа-сообщение]'}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 Отправлено: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    # Отправляем в @notoscam (техподдержка Telegram)
    try:
        # Отправляем 5 жалоб с интервалом 30 секунд
        for i in range(1, 6):
            await context.bot.send_message(
                chat_id="@notoscam",  # Официальный бот техподдержки
                text=complaint_text
            )
            
            # Прогресс-сообщение пользователю
            await update.message.reply_text(
                f"✅ Жалоба #{i} отправлена. Осталось: {5 - i}"
            )
            
            if i < 5:
                await asyncio.sleep(30)  # Пауза 30 секунд
        
        await update.message.reply_text(
            "✅ ВСЕ ЖАЛОБЫ ОТПРАВЛЕНЫ!\n"
            "Всего отправлено: 5 жалоб\n"
            "Интервал: 30 секунд"
        )
        
        # Очищаем данные пользователя
        del user_data[user_id]
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка при отправке: {str(e)}\n"
            "Попробуйте позже."
        )
        logger.error(f"Error: {e}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена текущего процесса"""
    user_id = update.message.from_user.id
    if user_id in user_data:
        del user_data[user_id]
        await update.message.reply_text("❌ Процесс отменен. Нажмите /start для начала заново.")
    else:
        await update.message.reply_text("Нет активного процесса.")

def main():
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Отдельный обработчик для причины (после пересылки)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reason))
    
    # Запуск бота
    print("🤖 Бот запущен!")
    print(f"⚡ Токен: {TOKEN[:10]}...")
    print("📩 Используйте /start")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
