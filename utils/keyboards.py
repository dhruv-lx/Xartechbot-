from telegram import (
    ReplyKeyboardMarkup, KeyboardButton, 
    InlineKeyboardMarkup, InlineKeyboardButton
)

def get_main_menu_keyboard(is_admin=False):
    keyboard = [
        [KeyboardButton("🏪 New Shop Visit"), KeyboardButton("📋 My Visits Today")],
        [KeyboardButton("👤 My Profile"), KeyboardButton("🚪 Logout")]
    ]
    if is_admin:
        keyboard.insert(0, [KeyboardButton("⚡ Admin Control Panel")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_cancel_keyboard():
    return ReplyKeyboardMarkup([["❌ Cancel Visit"]], resize_keyboard=True)

def get_skip_keyboard():
    return ReplyKeyboardMarkup([["⏩ Skip This Step"], ["❌ Cancel Visit"]], resize_keyboard=True)

def get_location_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📍 Share Current GPS Location", request_location=True)],
        [KeyboardButton("⏩ Skip / Type Address Below")],
        [KeyboardButton("❌ Cancel Visit")]
    ], resize_keyboard=True)

def get_confirm_visit_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ OK - Confirm & Save", callback_data="confirm_save_visit"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_save_visit")
        ]
    ])

def get_admin_menu_inline():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add New Agent", callback_data="admin_add_agent"),
            InlineKeyboardButton("👥 List All Agents", callback_data="admin_list_agents")
        ],
        [
            InlineKeyboardButton("📊 Download Reports", callback_data="admin_export_menu"),
            InlineKeyboardButton("📈 Statistics", callback_data="admin_stats")
        ],
        [
            InlineKeyboardButton("🔙 Back to Main Menu", callback_data="admin_close")
        ]
    ])

def get_export_format_inline():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🌐 Interactive HTML (Photos inside)", callback_data="export_fmt_html"),
            InlineKeyboardButton("📑 PDF Report", callback_data="export_fmt_pdf")
        ],
        [
            InlineKeyboardButton("📊 Excel Sheet (Photos inside)", callback_data="export_fmt_excel"),
            InlineKeyboardButton("🗂️ Complete ZIP Package", callback_data="export_fmt_zip")
        ],
        [
            InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_back")
        ]
    ])

def get_export_filter_inline(export_fmt):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📅 All Time Records", callback_data=f"exp_{export_fmt}_all"),
            InlineKeyboardButton("☀️ Today's Records", callback_data=f"exp_{export_fmt}_today")
        ],
        [
            InlineKeyboardButton("📆 Past 7 Days", callback_data=f"exp_{export_fmt}_week"),
            InlineKeyboardButton("👤 Filter by Agent", callback_data=f"exp_{export_fmt}_agent_sel")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="admin_export_menu")
        ]
    ])
