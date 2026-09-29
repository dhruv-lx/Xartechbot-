import html
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, 
    MessageHandler, CallbackQueryHandler, filters
)
from database import (
    get_session_user, create_user, get_all_agents, 
    toggle_user_status, get_visits, get_visit_stats, get_user_by_id
)
from utils.keyboards import (
    get_admin_menu_inline, get_export_format_inline, 
    get_export_filter_inline, get_main_menu_keyboard
)
from exporters.html_exporter import generate_html_report
from exporters.pdf_exporter import generate_pdf_report
from exporters.excel_exporter import generate_excel_report
from exporters.zip_exporter import generate_zip_package

# States for Add Agent Wizard
NEW_AGENT_USERNAME, NEW_AGENT_PASSWORD, NEW_AGENT_NAME = range(3)

async def admin_panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_session_user(chat_id)
    
    if not user or user['role'] != 'admin':
        await update.message.reply_text("⛔ Access Denied. Only authorized Admins can open this panel.")
        return
        
    stats = get_visit_stats()
    admin_name = html.escape(user['full_name'])
    msg = (
        "⚡ <b>XARTECH ADMIN CONTROL PANEL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 <b>Admin:</b> {admin_name}\n"
        f"📊 <b>Total Visits Logged:</b> <code>{stats.get('total', 0)}</code>\n"
        f"☀️ <b>Today's Visits:</b> <code>{stats.get('today', 0)}</code>\n"
        f"👥 <b>Active Agents:</b> <code>{stats.get('active_agents', 0)}</code>\n\n"
        "Please select an option below:"
    )
    await update.message.reply_text(
        msg,
        parse_mode="HTML",
        reply_markup=get_admin_menu_inline()
    )

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    chat_id = update.effective_chat.id
    user = get_session_user(chat_id)
    
    if not user or user['role'] != 'admin':
        await query.answer("Access Denied.", show_alert=True)
        return
        
    await query.answer()

    if data == "admin_stats":
        stats = get_visit_stats()
        agents = get_all_agents()
        agent_lines = []
        for a in agents:
            if a['role'] == 'agent':
                st = '✅ Active' if a['is_active'] else '❌ Inactive'
                agent_lines.append(f"• <b>{html.escape(a['full_name'])}</b> (<code>{html.escape(a['username'])}</code>) - {st}")
        
        agent_list_text = "\n".join(agent_lines)
        msg = (
            "📈 <b>TEAM & VISIT STATISTICS</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"🏬 <b>Total Client Visits:</b> <code>{stats.get('total', 0)}</code>\n"
            f"☀️ <b>Today's Visits:</b> <code>{stats.get('today', 0)}</code>\n"
            f"👥 <b>Total Team Members:</b> <code>{len(agents)}</code>\n\n"
            f"<b>Agents List:</b>\n{agent_list_text if agent_list_text else 'No agents created yet.'}"
        )
        await query.edit_message_text(
            msg,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_back")]])
        )

    elif data == "admin_list_agents":
        agents = get_all_agents()
        keyboard = []
        for a in agents:
            status_icon = "🟢" if a['is_active'] == 1 else "🔴"
            btn_text = f"{status_icon} {a['full_name']} (@{a['username']}) [{a['role'].upper()}]"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"agent_toggle_{a['id']}")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_back")])
        
        await query.edit_message_text(
            "👥 <b>AGENTS & USERS DIRECTORY</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Tap any agent below to toggle their status (Active / Inactive):",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("agent_toggle_"):
        agent_id = int(data.split("_")[2])
        success, new_status = toggle_user_status(agent_id)
        if success:
            status_str = "Active ✅" if new_status == 1 else "Deactivated ⛔"
            await query.answer(f"Agent #{agent_id} status changed to {status_str}", show_alert=True)
        # Refresh agent list
        agents = get_all_agents()
        keyboard = []
        for a in agents:
            status_icon = "🟢" if a['is_active'] == 1 else "🔴"
            btn_text = f"{status_icon} {a['full_name']} (@{a['username']}) [{a['role'].upper()}]"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"agent_toggle_{a['id']}")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_back")])
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "admin_export_menu":
        await query.edit_message_text(
            "📊 <b>SELECT EXPORT FORMAT</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Choose the report format you would like to download:",
            parse_mode="HTML",
            reply_markup=get_export_format_inline()
        )

    elif data in ["export_fmt_html", "export_fmt_pdf", "export_fmt_excel", "export_fmt_zip"]:
        fmt = data.replace("export_fmt_", "")
        context.user_data['selected_export_fmt'] = fmt
        fmt_names = {
            'html': '🌐 Interactive HTML Report',
            'pdf': '📑 Formatted PDF Report',
            'excel': '📊 Excel (.xlsx) with Photos',
            'zip': '🗂️ Complete ZIP Package'
        }
        await query.edit_message_text(
            f"Selected Format: <b>{fmt_names.get(fmt, fmt.upper())}</b>\n\n"
            "Select date range or agent filter:",
            parse_mode="HTML",
            reply_markup=get_export_filter_inline(fmt)
        )

    elif data.startswith("exp_"):
        parts = data.split("_")
        fmt = parts[1]
        filter_type = parts[2]
        
        if filter_type == "agent" and len(parts) > 3 and parts[3] == "sel":
            # Show agent picker
            agents = [a for a in get_all_agents() if a['role'] == 'agent']
            keyboard = []
            for a in agents:
                keyboard.append([InlineKeyboardButton(f"👤 {a['full_name']}", callback_data=f"exp_{fmt}_user_{a['id']}")])
            keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=f"export_fmt_{fmt}")])
            await query.edit_message_text(
                "👤 Select the Agent to export data for:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        # Handle Generation
        user_id_filter = None
        date_filter = None
        filter_name = "All Records"

        if filter_type == "all":
            date_filter = None
            filter_name = "All Time Visits"
        elif filter_type == "today":
            date_filter = 'today'
            filter_name = "Today's Visits"
        elif filter_type == "week":
            date_filter = 'week'
            filter_name = "Past 7 Days Visits"
        elif filter_type == "user":
            user_id_filter = int(parts[3])
            agent_obj = get_user_by_id(user_id_filter)
            filter_name = f"Agent: {agent_obj['full_name']}" if agent_obj else f"Agent #{user_id_filter}"

        await query.edit_message_text(f"⏳ Generating <b>{fmt.upper()}</b> report ({filter_name})... Please wait.", parse_mode="HTML")
        
        visits = get_visits(user_id=user_id_filter, date_filter=date_filter)
        
        if not visits:
            await query.edit_message_text(
                f"ℹ️ No visit records found for ({filter_name}).",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Export Menu", callback_data="admin_export_menu")]])
            )
            return

        try:
            file_to_send = None
            caption = f"📦 <b>Xartech Client Visits Report</b>\nFormat: <code>{fmt.upper()}</code> | Filter: <code>{html.escape(filter_name)}</code> | Total: <code>{len(visits)}</code> visits"
            
            if fmt == "html":
                file_to_send = generate_html_report(visits, filter_info=filter_name)
            elif fmt == "pdf":
                file_to_send = generate_pdf_report(visits, filter_info=filter_name)
            elif fmt == "excel":
                file_to_send = generate_excel_report(visits)
            elif fmt == "zip":
                file_to_send = generate_zip_package(visits)

            if file_to_send and file_to_send.exists():
                with open(file_to_send, "rb") as doc_file:
                    await context.bot.send_document(
                        chat_id=chat_id,
                        document=doc_file,
                        caption=caption,
                        parse_mode="HTML"
                    )
                await query.edit_message_text(
                    "✅ File generated and sent successfully! Select an option below:",
                    reply_markup=get_admin_menu_inline()
                )
            else:
                await query.edit_message_text(
                    "❌ Error generating report file.",
                    reply_markup=get_admin_menu_inline()
                )
        except Exception as e:
            print(f"Export error: {e}")
            await query.edit_message_text(
                f"❌ Export failed: {html.escape(str(e))}",
                reply_markup=get_admin_menu_inline()
            )

    elif data == "admin_back":
        stats = get_visit_stats()
        admin_name = html.escape(user['full_name'])
        msg = (
            "⚡ <b>XARTECH ADMIN CONTROL PANEL</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👑 <b>Admin:</b> {admin_name}\n"
            f"📊 <b>Total Visits Logged:</b> <code>{stats.get('total', 0)}</code>\n"
            f"☀️ <b>Today's Visits:</b> <code>{stats.get('today', 0)}</code>\n"
            f"👥 <b>Active Agents:</b> <code>{stats.get('active_agents', 0)}</code>\n\n"
            "Please select an option below:"
        )
        await query.edit_message_text(
            msg,
            parse_mode="HTML",
            reply_markup=get_admin_menu_inline()
        )

    elif data == "admin_close":
        await query.edit_message_text("Admin panel closed.")
        await context.bot.send_message(
            chat_id=chat_id,
            text="Main Menu:",
            reply_markup=get_main_menu_keyboard(is_admin=True)
        )

# Add Agent Conversation Handlers
async def start_add_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "➕ <b>CREATE NEW AGENT / INTERN ACCOUNT</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<b>Step 1/3:</b> Enter a <b>Username</b> for the agent:\n"
        "<i>(e.g. rahul, aman_sales, intern1)</i>\n\n"
        "Type /cancel anytime to cancel.",
        parse_mode="HTML"
    )
    return NEW_AGENT_USERNAME

async def handle_new_agent_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip().lower()
    context.user_data['new_agent_username'] = username
    
    await update.message.reply_text(
        f"✅ Username: <code>{html.escape(username)}</code>\n\n"
        "<b>Step 2/3:</b> Set a <b>Password</b> for this agent:",
        parse_mode="HTML"
    )
    return NEW_AGENT_PASSWORD

async def handle_new_agent_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text.strip()
    context.user_data['new_agent_password'] = password
    
    await update.message.reply_text(
        "<b>Step 3/3:</b> Enter the Agent's <b>Full Name</b>:\n"
        "<i>(e.g. Rahul Sharma)</i>",
        parse_mode="HTML"
    )
    return NEW_AGENT_NAME

async def handle_new_agent_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    full_name = update.message.text.strip()
    username = context.user_data.get('new_agent_username')
    password = context.user_data.get('new_agent_password')
    
    success, user_id, msg = create_user(username, password, full_name, role='agent')
    context.user_data.clear()
    
    if success:
        card = (
            "🎉 <b>NEW AGENT ACCOUNT CREATED!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 <b>Agent ID:</b> <code>#{user_id}</code>\n"
            f"👤 <b>Full Name:</b> {html.escape(full_name)}\n"
            f"🏷️ <b>Username:</b> <code>{html.escape(username)}</code>\n"
            f"🔑 <b>Password:</b> <code>{html.escape(password)}</code>\n"
            f"🛡️ <b>Role:</b> Agent / Intern\n\n"
            "📌 <b>Share these login credentials with your Intern/Agent.</b> They can login by sending /start to the bot."
        )
        await update.message.reply_text(
            card,
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard(is_admin=True)
        )
    else:
        await update.message.reply_text(
            f"❌ <b>Failed to create agent:</b>\n{html.escape(msg)}\n\nYou can try again from the Admin Panel.",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard(is_admin=True)
        )
        
    return ConversationHandler.END

async def cancel_add_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Agent creation cancelled.",
        reply_markup=get_main_menu_keyboard(is_admin=True)
    )
    return ConversationHandler.END

def get_add_agent_conversation_handler():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_add_agent, pattern="^admin_add_agent$")
        ],
        states={
            NEW_AGENT_USERNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_agent_username)
            ],
            NEW_AGENT_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_agent_password)
            ],
            NEW_AGENT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_agent_name)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel_add_agent)],
        allow_reentry=True,
        per_message=False
    )
