import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests

# === Настройки ===
TELEGRAM_TOKEN = 'ВАШ_ТОКЕН_ОТ_BOTFATHER'
LM_STUDIO_URL = 'http://localhost:1234/v1/chat/completions'

user_contexts = {}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def query_lm_studio(messages: list) -> str:
    payload = {
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": -1,
        "stream": False
    }
    try:
        response = requests.post(LM_STUDIO_URL, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        logging.error(f"Ошибка при запросе к LM Studio: {e}")
        return "Извините, произошла ошибка при генерации ответа."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот с локальной LLM. Отправляй сообщения, и я буду отвечать с учётом контекста. "
        "Используй /clear, чтобы сбросить историю."
    )

# Обработчик команды /clear
async def clear_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_contexts.pop(user_id, None)  # Удаляем контекст, если есть
    await update.message.reply_text("Контекст очищен. Начнём с чистого листа!")

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    if user_id not in user_contexts:
        user_contexts[user_id] = []

    user_contexts[user_id].append({"role": "user", "content": user_message})

    bot_reply = query_lm_studio(user_contexts[user_id])

    user_contexts[user_id].append({"role": "assistant", "content": bot_reply})

    await update.message.reply_text(bot_reply)

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("clear", clear_context))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()