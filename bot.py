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

# ================== COMMAND HANDLERS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    await update.message.reply_text("🚀 Bot Started\nUse /scan to begin or /cancel to stop")

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle scan command with cancellation support"""
    chat_id = update.effective_chat.id
    cancellation_flags[chat_id] = False
    logger.info(f"Scan started for chat {chat_id}")
    
    try:
        await update.message.reply_text("🔄 Scan started... (10s)")
        
        for i in range(1, 11):
            # Check cancellation before each iteration
            if cancellation_flags.get(chat_id, False):
                await update.message.reply_text("❌ Scan cancelled!")
                return
                
            await update.message.reply_text(f"Progress: {i}/10")
            
            # Split sleep into smaller intervals with checks
            for _ in range(10):  # Check every 0.1 seconds
                if cancellation_flags.get(chat_id, False):
                    await update.message.reply_text("❌ Scan cancelled!")
                    return
                await asyncio.sleep(0.1)
        
        await update.message.reply_text("✅ Scan complete!")
        
    except Exception as e:
        logger.error(f"Scan error: {str(e)}")
        await update.message.reply_text("⚠️ Scan failed!")
    finally:
        cancellation_flags.pop(chat_id, None)

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancellation requests"""
    chat_id = update.effective_chat.id
    logger.info(f"Cancellation request from {chat_id}")
    
    if chat_id in cancellation_flags:
        cancellation_flags[chat_id] = True
        await update.message.reply_text("⏳ Stopping scan...")
    else:
        await update.message.reply_text("⚠️ No active scan to cancel")

# ================== WEBHOOK ENDPOINTS ==================
@app.route('/healthz')
async def health_check():
    return 'OK', 200

@app.route('/telegram', methods=['POST'])
async def telegram_webhook():
    """Handle incoming Telegram updates"""
    if request.method == "POST":
        json_data = await request.get_json()
        update = Update.de_json(json_data, application.bot)
        await application.process_update(update)
    return jsonify({"status": "ok"}), 200

# ================== MAIN APPLICATION ==================
async def main():
    """Initialize and start the application"""
    global application
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    webhook_url = f"{os.getenv('RENDER_WEBHOOK_URL')}/telegram"
    
    # Create PTB application
    application = Application.builder().token(telegram_token).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("scan", scan_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # Configure webhook
    await application.bot.set_webhook(
        url=webhook_url,
        drop_pending_updates=True
    )
    logger.info(f"Webhook configured: {webhook_url}")
    
    # Start application with proper async context
    async with application:
        await application.start()
        await app.run_task(host='0.0.0.0', port=int(os.getenv("PORT", 8000)))
        await application.stop()

if __name__ == "__main__":
    asyncio.run(main())