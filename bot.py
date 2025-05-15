from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
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

# Initialize PTB application properly
telegram_token = os.getenv("TELEGRAM_TOKEN")
application = Application.builder().token(telegram_token).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Received /start command")
    await update.message.reply_text("Send /scan or /cancel")

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logger.info(f"Scan started for chat {chat_id}")
    
    cancellation_flags[chat_id] = False
    await update.message.reply_text("🔄 Scan started... (10s)")
    
    try:
        for i in range(1, 11):
            if cancellation_flags.get(chat_id, False):
                await update.message.reply_text("❌ Cancelled!")
                return
            
            await asyncio.sleep(1)
            await update.message.reply_text(f"Progress: {i}/10")
            logger.info(f"Scan progress {i}/10 for {chat_id}")
        
        await update.message.reply_text("✅ Scan complete!")
    finally:
        cancellation_flags.pop(chat_id, None)

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logger.info(f"Cancellation request for {chat_id}")
    
    if chat_id in cancellation_flags:
        cancellation_flags[chat_id] = True
        await update.message.reply_text("⏳ Cancelling...")
    else:
        await update.message.reply_text("⚠️ Nothing to cancel")

@app.route('/healthz')
async def health_check():
    return 'OK', 200

@app.route('/telegram', methods=['POST'])
async def telegram_webhook():
    """Main webhook endpoint"""
    if request.method == "POST":
        update = Update.de_json(await request.get_json(), application.bot)
        await application.process_update(update)
    return jsonify({"status": "ok"}), 200

async def main():
    webhook_url = f"{os.getenv('RENDER_WEBHOOK_URL')}/telegram"
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("scan", scan_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # Set webhook
    await application.bot.set_webhook(
        url=webhook_url,
        drop_pending_updates=True
    )
    logger.info(f"Webhook set to: {webhook_url}")
    
    # Start servers
    runner = app.run_task(host='0.0.0.0', port=int(os.getenv("PORT", 8000)))
    await application.start()
    await runner
    await application.stop()

if __name__ == "__main__":
    asyncio.run(main())