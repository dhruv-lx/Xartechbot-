import logging
import sys
import os
import io

# Set UTF-8 output encoding for Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters, ContextTypes
)
from config import BOT_TOKEN
from database import init_db
from handlers.auth_handlers import (
    get_auth_conversation_handler, logout_command, 
    profile_command, get_change_password_conversation_handler
)
from handlers.visit_handlers import (
    get_visit_conversation_handler, my_visits_today
)
from handlers.admin_handlers import (
    admin_panel_command, admin_callback_handler, 
    get_add_agent_conversation_handler
)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Log the error
    logger.error("Exception while handling an update: %s", context.error)
    if isinstance(context.error, Exception):
        err_str = str(context.error)
        if "Conflict: terminated by other getUpdates" in err_str:
            logger.warning("Another instance of the bot is running! Please make sure only one terminal is running bot.py.")
            return

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(b"<h1>Xartech Telegram Bot is Running Live 24/7!</h1>")
        
    def log_message(self, format, *args):
        pass  # Silence web server access logs

def start_health_server():
    port = int(os.environ.get("PORT", 8080))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthHandler)
        server.serve_forever()
    except Exception as e:
        logger.warning("Health server warning: %s", e)

def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("\n" + "="*60)
        print("⚠️  WARNING: BOT_TOKEN is not set in .env file!")
        print("Please edit .env file and paste your Telegram Bot Token from @BotFather.")
        print("="*60 + "\n")
        
    # Initialize SQLite Database & Default Admin
    init_db()
    print("✅ Database initialized successfully.")

    # Start Health Check Server for Render Free Web Service
    threading.Thread(target=start_health_server, daemon=True).start()
    print("🌐 Health check server started.")

    # Create Telegram Application
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_error_handler(error_handler)

    # Add Add-Agent Conversation Handler (Priority for callbacks)
    app.add_handler(get_add_agent_conversation_handler())

    # Add Change Password Conversation Handler
    app.add_handler(get_change_password_conversation_handler())

    # Add Visit Logging Conversation Handler
    app.add_handler(get_visit_conversation_handler())

    # Add Authentication (Login/Start) Conversation Handler
    app.add_handler(get_auth_conversation_handler())

    # Add Admin Panel Handlers
    app.add_handler(CommandHandler("admin", admin_panel_command))
    app.add_handler(MessageHandler(filters.Regex("^⚡ Admin Control Panel$"), admin_panel_command))
    app.add_handler(CallbackQueryHandler(admin_callback_handler))

    # Add General & Shortcut Handlers
    app.add_handler(CommandHandler("logout", logout_command))
    app.add_handler(MessageHandler(filters.Regex("^🚪 Logout$"), logout_command))
    
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(MessageHandler(filters.Regex("^👤 My Profile$"), profile_command))
    
    app.add_handler(CommandHandler("my_visits", my_visits_today))
    app.add_handler(MessageHandler(filters.Regex("^📋 My Visits Today$"), my_visits_today))

    print("\n🚀 [Xartech Bot] Starting Telegram Bot polling...")
    print("Default Admin Credentials:")
    print("  • Username: admin")
    print("  • Password: xartech@123")
    print("="*60 + "\n")
    
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
