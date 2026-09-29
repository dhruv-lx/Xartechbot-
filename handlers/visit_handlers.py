import os
import html
import urllib.parse
from datetime import datetime
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, 
    MessageHandler, CallbackQueryHandler, filters
)
from database import get_session_user, save_visit, get_visits, get_active_admins
from config import PHOTOS_DIR
from utils.keyboards import (
    get_main_menu_keyboard, get_cancel_keyboard, 
    get_skip_keyboard, get_location_keyboard, get_confirm_visit_keyboard
)

# States for Visit Conversation
(
    VISIT_SHOP_NAME,
    VISIT_OWNER_NAME,
    VISIT_PHONE,
    VISIT_SHOP_PHOTO,
    VISIT_CARD_PHOTO,
    VISIT_LOCATION,
    VISIT_REMARKS,
    VISIT_CONFIRM
) = range(8)

async def start_visit_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_session_user(chat_id)
    
    if not user:
        await update.message.reply_text(
            "🔒 Please login first! Type /start",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
        
    context.user_data.clear()
    context.user_data['visit_user_id'] = user['id']
    context.user_data['visit_agent_name'] = user['full_name']
    
    await update.message.reply_text(
        "🏪 <b>LOG NEW CLIENT VISIT</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<b>Step 1/7:</b> Please enter the <b>Shop / Business Name</b>:\n\n"
        "<i>(You can tap '❌ Cancel Visit' anytime to cancel)</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    return VISIT_SHOP_NAME

async def handle_shop_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "❌ Cancel Visit":
        return await cancel_visit_flow(update, context)
        
    context.user_data['shop_name'] = text
    
    await update.message.reply_text(
        f"✅ Shop Name: <b>{html.escape(text)}</b>\n\n"
        "<b>Step 2/7:</b> Enter <b>Shop Owner / Contact Person Name</b>:\n"
        "<i>(Or tap '⏩ Skip This Step' if not available)</i>",
        parse_mode="HTML",
        reply_markup=get_skip_keyboard()
    )
    return VISIT_OWNER_NAME

async def handle_owner_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "❌ Cancel Visit":
        return await cancel_visit_flow(update, context)
    elif text != "⏩ Skip This Step":
        context.user_data['owner_name'] = text
    else:
        context.user_data['owner_name'] = None
        
    await update.message.reply_text(
        "<b>Step 3/7:</b> Enter Shop Owner / Contact <b>Mobile Number</b>:\n"
        "<i>(e.g. 9876543210)</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    return VISIT_PHONE

async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "❌ Cancel Visit":
        return await cancel_visit_flow(update, context)
        
    phone_clean = "".join(c for c in text if c.isdigit() or c == '+')
    if len(phone_clean) < 6:
        await update.message.reply_text(
            "⚠️ Please enter a valid phone number (at least 6-10 digits):",
            reply_markup=get_cancel_keyboard()
        )
        return VISIT_PHONE
        
    context.user_data['phone_number'] = phone_clean
    
    await update.message.reply_text(
        "📸 <b>Step 4/7:</b> Please send a <b>Shop Front Photo</b> (Upload / Take Photo):",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    return VISIT_SHOP_PHOTO

async def handle_shop_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Cancel Visit":
        return await cancel_visit_flow(update, context)
        
    if not update.message.photo:
        await update.message.reply_text(
            "⚠️ Please send an image photo of the shop:",
            reply_markup=get_cancel_keyboard()
        )
        return VISIT_SHOP_PHOTO
        
    photo = update.message.photo[-1]
    photo_file = await context.bot.get_file(photo.file_id)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    user_id = context.user_data.get('visit_user_id', '0')
    filename = f"shop_{user_id}_{timestamp}.jpg"
    filepath = PHOTOS_DIR / filename
    
    await photo_file.download_to_drive(custom_path=filepath)
    context.user_data['shop_photo_path'] = str(filepath)
    
    await update.message.reply_text(
        "✅ Shop Photo received!\n\n"
        "🪪 <b>Step 5/7:</b> Please send <b>Visiting Card Photo</b>:\n"
        "<i>(Or tap '⏩ Skip This Step' if card is not available)</i>",
        parse_mode="HTML",
        reply_markup=get_skip_keyboard()
    )
    return VISIT_CARD_PHOTO

async def handle_card_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Cancel Visit":
        return await cancel_visit_flow(update, context)
    elif update.message.text == "⏩ Skip This Step":
        context.user_data['card_photo_path'] = None
    elif update.message.photo:
        photo = update.message.photo[-1]
        photo_file = await context.bot.get_file(photo.file_id)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        user_id = context.user_data.get('visit_user_id', '0')
        filename = f"card_{user_id}_{timestamp}.jpg"
        filepath = PHOTOS_DIR / filename
        await photo_file.download_to_drive(custom_path=filepath)
        context.user_data['card_photo_path'] = str(filepath)
    else:
        await update.message.reply_text(
            "⚠️ Please send a visiting card photo or tap '⏩ Skip This Step':",
            reply_markup=get_skip_keyboard()
        )
        return VISIT_CARD_PHOTO

    await update.message.reply_text(
        "📍 <b>Step 6/7:</b> Share <b>Shop Location / Address</b>:\n"
        "Tap the button below to share GPS location or type the address text:",
        parse_mode="HTML",
        reply_markup=get_location_keyboard()
    )
    return VISIT_LOCATION

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Cancel Visit":
        return await cancel_visit_flow(update, context)
        
    if update.message.location:
        lat = update.message.location.latitude
        lon = update.message.location.longitude
        context.user_data['latitude'] = lat
        context.user_data['longitude'] = lon
        context.user_data['address'] = f"GPS: {lat:.6f}, {lon:.6f}"
    elif update.message.text and update.message.text != "⏩ Skip / Type Address Below":
        context.user_data['address'] = update.message.text.strip()
        context.user_data['latitude'] = None
        context.user_data['longitude'] = None
    else:
        context.user_data['address'] = None
        context.user_data['latitude'] = None
        context.user_data['longitude'] = None

    await update.message.reply_text(
        "📝 <b>Step 7/7:</b> Enter <b>Remarks / Client Requirements / Notes</b>:\n"
        "<i>(e.g. 'Interested in website/app', 'Follow-up next Monday', etc.)</i>\n"
        "Or tap '⏩ Skip This Step':",
        parse_mode="HTML",
        reply_markup=get_skip_keyboard()
    )
    return VISIT_REMARKS

async def handle_remarks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Cancel Visit":
        return await cancel_visit_flow(update, context)
    elif update.message.text != "⏩ Skip This Step":
        context.user_data['remarks'] = update.message.text.strip()
    else:
        context.user_data['remarks'] = None

    # Prepare Confirmation Summary
    d = context.user_data
    shop_name_esc = html.escape(d.get('shop_name', 'N/A'))
    owner_esc = html.escape(d.get('owner_name') or 'N/A')
    phone_esc = html.escape(d.get('phone_number', 'N/A'))
    addr_esc = html.escape(d.get('address') or 'N/A')
    rem_esc = html.escape(d.get('remarks') or 'None')

    summary = (
        "📋 <b>VISIT DATA SUMMARY REVIEW</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🏬 <b>Shop Name:</b> {shop_name_esc}\n"
        f"👤 <b>Contact Person:</b> {owner_esc}\n"
        f"📞 <b>Phone Number:</b> <code>{phone_esc}</code>\n"
        f"📸 <b>Shop Photo:</b> {'Attached ✅' if d.get('shop_photo_path') else 'Missing ❌'}\n"
        f"🪪 <b>Visiting Card:</b> {'Attached ✅' if d.get('card_photo_path') else 'None'}\n"
        f"📍 <b>Location:</b> {addr_esc}\n"
        f"📝 <b>Remarks:</b> {rem_esc}\n\n"
        "Are all details correct? Tap <b>Confirm & Save (OK)</b> below or type 'ok' to save on the server:"
    )

    await update.message.reply_text(
        summary,
        parse_mode="HTML",
        reply_markup=get_confirm_visit_keyboard()
    )
    return VISIT_CONFIRM

async def handle_text_ok_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text in ["ok", "save", "done", "confirm", "yes", "ha", "haan"]:
        return await save_visit_record(update, context, is_callback=False)
    elif text == "❌ Cancel Visit" or "cancel" in text:
        return await cancel_visit_flow(update, context)
    else:
        await update.message.reply_text(
            "Please type <b>'OK'</b> or tap the button below to save:",
            parse_mode="HTML",
            reply_markup=get_confirm_visit_keyboard()
        )
        return VISIT_CONFIRM

async def handle_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "confirm_save_visit":
        return await save_visit_record(update, context, is_callback=True)
    elif query.data == "cancel_save_visit":
        context.user_data.clear()
        chat_id = update.effective_chat.id
        user = get_session_user(chat_id)
        is_admin = user and (user['role'] == 'admin')
        
        await query.edit_message_text("❌ Visit entry cancelled.")
        await context.bot.send_message(
            chat_id=chat_id,
            text="Returned to Main Menu:",
            reply_markup=get_main_menu_keyboard(is_admin)
        )
        return ConversationHandler.END

def get_maps_url(latitude, longitude, address=None):
    if latitude and longitude:
        return f"https://www.google.com/maps?q={latitude},{longitude}"
    elif address and address != "GPS Recorded":
        encoded = urllib.parse.quote(address)
        return f"https://www.google.com/maps/search/?api=1&query={encoded}"
    return None

async def save_visit_record(update: Update, context: ContextTypes.DEFAULT_TYPE, is_callback=False):
    d = context.user_data
    chat_id = update.effective_chat.id
    user = get_session_user(chat_id)
    
    if not user:
        msg = "Session expired. Please type /start to login again."
        if is_callback:
            await update.callback_query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
        return ConversationHandler.END

    lat = d.get('latitude')
    lon = d.get('longitude')
    addr = d.get('address')
    shop_photo_path = d.get('shop_photo_path', '')
    card_photo_path = d.get('card_photo_path')
    
    # Save to SQLite Database
    visit_id = save_visit(
        user_id=user['id'],
        shop_name=d.get('shop_name', 'Unknown Shop'),
        owner_name=d.get('owner_name'),
        phone_number=d.get('phone_number', ''),
        address=addr,
        latitude=lat,
        longitude=lon,
        shop_photo_path=shop_photo_path,
        card_photo_path=card_photo_path,
        remarks=d.get('remarks')
    )
    
    # Create Google Maps Link
    maps_url = get_maps_url(lat, lon, addr)
    maps_text = f' <a href="{maps_url}">[📍 Open in Google Maps]</a>' if maps_url else ""
    
    context.user_data.clear()
    is_admin = (user['role'] == 'admin')
    
    shop_esc = html.escape(d.get('shop_name', ''))
    agent_esc = html.escape(user['full_name'])
    phone_esc = html.escape(d.get('phone_number', ''))
    remarks_esc = html.escape(d.get('remarks') or 'None')
    addr_esc = html.escape(addr or 'Location Saved')
    time_str = datetime.now().strftime('%I:%M %p, %d-%m-%Y')
    
    success_msg = (
        "🎉 <b>VISIT SUCCESSFULLY SAVED ON SERVER!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>Visit Reference ID:</b> <code>#{visit_id}</code>\n"
        f"🏬 <b>Shop Name:</b> {shop_esc}\n"
        f"👤 <b>Logged By:</b> {agent_esc}\n"
        f"📞 <b>Phone:</b> <code>{phone_esc}</code>\n"
        f"📍 <b>Location:</b> {addr_esc}{maps_text}\n"
        f"📝 <b>Remarks:</b> {remarks_esc}\n"
        f"🕒 <b>Recorded At:</b> {time_str}\n\n"
        "When you arrive at the next shop, simply tap <b>'🏪 New Shop Visit'</b> to log it!"
    )
    
    if is_callback:
        await update.callback_query.edit_message_text(success_msg, parse_mode="HTML")
        await context.bot.send_message(
            chat_id=chat_id,
            text="Menu Options:",
            reply_markup=get_main_menu_keyboard(is_admin)
        )
    else:
        await update.message.reply_text(
            success_msg,
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard(is_admin)
        )
        
    # --- REAL-TIME ADMIN NOTIFICATION (LEAD ALERT) ---
    try:
        active_admins = get_active_admins()
        alert_msg = (
            "🔔 <b>NEW CLIENT VISIT ALERT!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 <b>Visit ID:</b> <code>#{visit_id}</code>\n"
            f"🏬 <b>Shop:</b> {shop_esc}\n"
            f"👤 <b>Field Agent:</b> {agent_esc} (@{html.escape(user['username'])})\n"
            f"📞 <b>Contact:</b> <code>{phone_esc}</code>\n"
            f"📍 <b>Location:</b> {addr_esc}{maps_text}\n"
            f"📝 <b>Remarks:</b> {remarks_esc}\n"
            f"🕒 <b>Time:</b> {time_str}"
        )
        
        for admin in active_admins:
            # Don't duplicate if admin is the one who logged it
            if admin['telegram_chat_id'] == chat_id:
                continue
            try:
                if shop_photo_path and os.path.exists(shop_photo_path):
                    with open(shop_photo_path, "rb") as p_file:
                        await context.bot.send_photo(
                            chat_id=admin['telegram_chat_id'],
                            photo=p_file,
                            caption=alert_msg,
                            parse_mode="HTML"
                        )
                else:
                    await context.bot.send_message(
                        chat_id=admin['telegram_chat_id'],
                        text=alert_msg,
                        parse_mode="HTML"
                    )
            except Exception as admin_err:
                print(f"Could not notify admin {admin['id']}: {admin_err}")
    except Exception as e:
        print(f"Error during admin broadcast: {e}")
        
    return ConversationHandler.END

async def cancel_visit_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    chat_id = update.effective_chat.id
    user = get_session_user(chat_id)
    is_admin = user and (user['role'] == 'admin')
    
    await update.message.reply_text(
        "❌ Visit logging cancelled.",
        reply_markup=get_main_menu_keyboard(is_admin)
    )
    return ConversationHandler.END

async def my_visits_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = get_session_user(chat_id)
    
    if not user:
        await update.message.reply_text("Please type /start to login first.")
        return
        
    visits = get_visits(user_id=user['id'], date_filter='today')
    
    if not visits:
        await update.message.reply_text(
            "ℹ️ You have not logged any visits today.\n"
            "Tap '🏪 New Shop Visit' to start logging."
        )
        return
        
    msg = f"📋 <b>TODAY'S VISITS BY YOU ({len(visits)})</b>\n━━━━━━━━━━━━━━━━━━━━\n"
    for idx, v in enumerate(visits, 1):
        s_name = html.escape(v['shop_name'])
        o_name = html.escape(v.get('owner_name') or 'N/A')
        addr = html.escape(v.get('address') or 'Location Saved')
        msg += (
            f"<b>{idx}. {s_name}</b> (ID: <code>#{v['id']}</code>)\n"
            f"   📞 {html.escape(v['phone_number'])} | 👤 {o_name}\n"
            f"   📍 {addr}\n\n"
        )
        
    await update.message.reply_text(msg, parse_mode="HTML")

def get_visit_conversation_handler():
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🏪 New Shop Visit$"), start_visit_flow),
            CommandHandler("new_visit", start_visit_flow)
        ],
        states={
            VISIT_SHOP_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_shop_name)
            ],
            VISIT_OWNER_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_owner_name)
            ],
            VISIT_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)
            ],
            VISIT_SHOP_PHOTO: [
                MessageHandler(filters.PHOTO | (filters.TEXT & ~filters.COMMAND), handle_shop_photo)
            ],
            VISIT_CARD_PHOTO: [
                MessageHandler(filters.PHOTO | (filters.TEXT & ~filters.COMMAND), handle_card_photo)
            ],
            VISIT_LOCATION: [
                MessageHandler(filters.LOCATION | (filters.TEXT & ~filters.COMMAND), handle_location)
            ],
            VISIT_REMARKS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_remarks)
            ],
            VISIT_CONFIRM: [
                CallbackQueryHandler(handle_confirm_callback),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_ok_confirm)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_visit_flow),
            MessageHandler(filters.Regex("^❌ Cancel Visit$"), cancel_visit_flow)
        ],
        allow_reentry=True,
        per_message=False
    )
