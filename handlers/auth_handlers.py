import html
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
)
from database import (
    authenticate_user, set_session, get_session_user, 
    clear_session, get_visit_stats, get_user_by_username
)
from utils.keyboards import get_main_menu_keyboard

# States for Login Conversation
ASK_USERNAME, ASK_PASSWORD = range(2)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_session_user(chat_id)
    
    if user:
        is_admin = (user['role'] == 'admin')
        stats = get_visit_stats(user['id'] if not is_admin else None)
        
        name_esc = html.escape(user['full_name'])
        role_esc = html.escape(user['role'].upper())
        greeting = (
            f"👋 <b>Welcome back, {name_esc}!</b>\n\n"
            f"🏢 <b>Company:</b> Xartech Client Management\n"
            f"👤 <b>Role:</b> <code>{role_esc}</code>\n"
            f"📊 <b>Today's Visits:</b> <code>{stats.get('today', 0)}</code>\n"
            f"📈 <b>Total Visits Logged:</b> <code>{stats.get('total', 0)}</code>\n\n"
            "Use the buttons below to log a new client visit or manage options:"
        )
        await update.message.reply_text(
            greeting,
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard(is_admin)
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "🔒 <b>XARTECH CLIENT VISIT BOT</b>\n\n"
            "Welcome! Please login to your <b>Agent / Admin Account</b> to continue.\n\n"
            "👉 Please enter your <b>Username</b>:",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )
        return ASK_USERNAME

async def process_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip().lower()
    
    # Check if username exists in database
    user_record = get_user_by_username(username)
    
    if not user_record:
        await update.message.reply_text(
            f"❌ <b>Username '<code>{html.escape(username)}</code>' does not exist!</b>\n\n"
            "Please check your spelling or contact your Admin to create an account for you.\n\n"
            "👉 Please enter a valid <b>Username</b> (or type /cancel):",
            parse_mode="HTML"
        )
        return ASK_USERNAME
        
    if user_record.get('is_active') == 0:
        await update.message.reply_text(
            f"⛔ <b>Account Deactivated!</b>\n\n"
            f"The account '<code>{html.escape(username)}</code>' is currently disabled by Admin.\n"
            "Please contact Admin for assistance.",
            parse_mode="HTML"
        )
        return ASK_USERNAME
        
    context.user_data['login_username'] = username
    
    await update.message.reply_text(
        f"👤 Username: <code>{html.escape(username)}</code> (Found ✅)\n\n"
        "🔑 Now enter your <b>Password</b>:",
        parse_mode="HTML"
    )
    return ASK_PASSWORD

async def process_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text.strip()
    username = context.user_data.get('login_username')
    chat_id = update.effective_chat.id
    
    user = authenticate_user(username, password)
    
    if user:
        set_session(chat_id, user['id'])
        is_admin = (user['role'] == 'admin')
        context.user_data.clear()
        
        name_esc = html.escape(user['full_name'])
        role_esc = html.escape(user['role'].capitalize())
        await update.message.reply_text(
            f"🎉 <b>Login Successful!</b>\n\n"
            f"Welcome <b>{name_esc}</b> ({role_esc}).\n"
            "You can now log client visits and upload photos.",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard(is_admin)
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "❌ <b>Invalid Username or Password!</b>\n\n"
            "Please try again.\n"
            "Enter your <b>Username</b> (or type /cancel):",
            parse_mode="HTML"
        )
        return ASK_USERNAME

async def logout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    clear_session(chat_id)
    context.user_data.clear()
    
    await update.message.reply_text(
        "👋 <b>You have logged out successfully.</b>\n\n"
        "Type /start anytime to login again.",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_session_user(chat_id)
    
    if not user:
        await update.message.reply_text("Please type /start to login first.")
        return
        
    is_admin = (user['role'] == 'admin')
    stats = get_visit_stats(user['id'] if not is_admin else None)
    
    name_esc = html.escape(user['full_name'])
    user_esc = html.escape(user['username'])
    role_esc = html.escape(user['role'].upper())
    
    msg = (
        "👤 <b>PROFILE DETAILS</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ <b>Name:</b> {name_esc}\n"
        f"🆔 <b>Username:</b> <code>{user_esc}</code>\n"
        f"🛡️ <b>Role:</b> <code>{role_esc}</code>\n"
        f"📅 <b>Joined:</b> {user.get('created_at', 'N/A')}\n\n"
        "📊 <b>VISIT STATISTICS</b>\n"
        f"• Today's Visits: <b>{stats.get('today', 0)}</b>\n"
        f"• Total Visits: <b>{stats.get('total', 0)}</b>\n"
    )
    if is_admin:
        msg += f"• Active Team Agents: <b>{stats.get('active_agents', 0)}</b>\n"
        
    msg += "\n💡 <i>To change your password, type /change_password</i>"
        
    await update.message.reply_text(
        msg,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(is_admin)
    )

async def cancel_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Login cancelled. Type /start to login.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def get_auth_conversation_handler():
    return ConversationHandler(
        entry_points=[
            CommandHandler("start", start_command),
            CommandHandler("login", start_command)
        ],
        states={
            ASK_USERNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_username)
            ],
            ASK_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_password)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_login)],
        allow_reentry=True,
        per_message=False
    )

# --- CHANGE PASSWORD CONVERSATION ---
OLD_PWD, NEW_PWD = range(2)

async def start_change_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_session_user(chat_id)
    
    if not user:
        await update.message.reply_text("Please login first using /start.")
        return ConversationHandler.END
        
    context.user_data['cp_user_id'] = user['id']
    context.user_data['cp_username'] = user['username']
    
    await update.message.reply_text(
        "🔑 <b>CHANGE PASSWORD</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<b>Step 1/2:</b> Please enter your <b>Current (Old) Password</b>:\n\n"
        "<i>(Type /cancel anytime to cancel)</i>",
        parse_mode="HTML"
    )
    return OLD_PWD

async def handle_old_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    old_pass = update.message.text.strip()
    username = context.user_data.get('cp_username')
    
    user = authenticate_user(username, old_pass)
    if not user:
        await update.message.reply_text(
            "❌ <b>Incorrect Old Password!</b>\n\n"
            "Please enter your correct <b>Current Password</b> (or type /cancel):",
            parse_mode="HTML"
        )
        return OLD_PWD
        
    await update.message.reply_text(
        "✅ Old Password verified!\n\n"
        "<b>Step 2/2:</b> Now enter your <b>New Password</b> (at least 4 characters):",
        parse_mode="HTML"
    )
    return NEW_PWD

async def handle_new_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_pass = update.message.text.strip()
    user_id = context.user_data.get('cp_user_id')
    chat_id = update.effective_chat.id
    user = get_session_user(chat_id)
    is_admin = user and (user['role'] == 'admin')
    
    if len(new_pass) < 4:
        await update.message.reply_text(
            "⚠️ Password must be at least 4 characters long. Enter a stronger password:",
            parse_mode="HTML"
        )
        return NEW_PWD
        
    from database import update_user_password
    update_user_password(user_id, new_pass)
    context.user_data.clear()
    
    await update.message.reply_text(
        "🎉 <b>Password Updated Successfully!</b>\n\n"
        "You can now use your new password for future logins.",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(is_admin)
    )
    return ConversationHandler.END

async def cancel_change_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    chat_id = update.effective_chat.id
    user = get_session_user(chat_id)
    is_admin = user and (user['role'] == 'admin')
    
    await update.message.reply_text(
        "Password change cancelled.",
        reply_markup=get_main_menu_keyboard(is_admin)
    )
    return ConversationHandler.END

def get_change_password_conversation_handler():
    return ConversationHandler(
        entry_points=[
            CommandHandler("change_password", start_change_password),
            MessageHandler(filters.Regex("^🔑 Change Password$"), start_change_password)
        ],
        states={
            OLD_PWD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_old_password)
            ],
            NEW_PWD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_password)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel_change_password)],
        allow_reentry=True,
        per_message=False
    )
