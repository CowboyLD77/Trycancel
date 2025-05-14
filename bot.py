from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os
import asyncio
from quart import Quart

app = Quart(__name__)
cancellation_flags = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send /scan or /cancel")

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cancellation_flags[chat_id] = False
    
    await update.message.reply_text("🔄 Scan started... (10s)")
    
    for i in range(1, 11):
        if cancellation_flags.get(chat_id, False):
            await update.message.reply_text("❌ Cancelled!")
            del cancellation_flags[chat_id]
            return
        
        await asyncio.sleep(1)
        await update.message.reply_text(f"Progress: {i}/10")
    
    del cancellation_flags[chat_id]
    await update.message.reply_text("✅ Scan complete!")

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in cancellation_flags:
        cancellation_flags[chat_id] = True
        await update.message.reply_text("⏳ Cancelling...")
    else:
        await update.message.reply_text("⚠️ Nothing to cancel")

@app.route('/healthz')
async def health_check():
    return 'OK', 200

async def main():
    # Initialize application properly
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    webhook_url = f"{os.getenv('RENDER_WEBHOOK_URL')}/telegram"
    
    application = Application.builder().token(telegram_token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("scan", scan_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # Set webhook before starting
    await application.bot.set_webhook(webhook_url)
    
    # Start Quart server
    await app.run_task(host='0.0.0.0', port=int(os.getenv("PORT", 8000)))

if __name__ == "__main__":
    asyncio.run(main())