from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os
import asyncio
from quart import Quart, request, jsonify
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Quart(__name__)
cancellation_flags = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send /scan or /cancel")

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cancellation_flags[chat_id] = False
    try:
        await update.message.reply_text("🔄 Scan started... (10s)")
        for i in range(1, 11):
            if cancellation_flags.get(chat_id, False):
                await update.message.reply_text("❌ Cancelled!")
                return
            await asyncio.sleep(1)
            await update.message.reply_text(f"Progress: {i}/10")
        await update.message.reply_text("✅ Scan complete!")
    finally:
        cancellation_flags.pop(chat_id, None)

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cancellation_flags[chat_id] = False
    try:
        await update.message.reply_text("🔄 Scan started... (10s)")
        
        for i in range(1, 11):
            # First check before sleep
            if cancellation_flags.get(chat_id, False):
                await update.message.reply_text("❌ Cancelled!")
                return
            
            await update.message.reply_text(f"Progress: {i}/10")
            
            # Split sleep into smaller intervals with checks
            for _ in range(10):  # Check every 0.1 seconds
                if cancellation_flags.get(chat_id, False):
                    await update.message.reply_text("❌ Cancelled!")
                    return
                await asyncio.sleep(0.1)
                
        await update.message.reply_text("✅ Scan complete!")
        
    finally:
        cancellation_flags.pop(chat_id, None)

@app.route('/healthz')
async def health_check():
    return 'OK', 200

@app.route('/telegram', methods=['POST'])
async def telegram_webhook():
    if request.method == "POST":
        update = Update.de_json(await request.get_json(), application.bot)
        await application.process_update(update)
    return jsonify({"status": "ok"}), 200

async def main():
    global application
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    webhook_url = f"{os.getenv('RENDER_WEBHOOK_URL')}/telegram"
    
    # Initialize application properly
    application = Application.builder().token(telegram_token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("scan", scan_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # Set up webhook
    await application.bot.set_webhook(webhook_url, drop_pending_updates=True)
    
    # Start servers with proper async context
    async with application:
        await application.start()
        await app.run_task(host='0.0.0.0', port=int(os.getenv("PORT", 8000)))
        await application.stop()

if __name__ == "__main__":
    asyncio.run(main())