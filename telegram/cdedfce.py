import os
import logging
from datetime import datetime, timedelta, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ✅ Updated checklist questions
questions = [
    "Is ev charging machine in use",
    "Is the UDS cleaning person available",
    "CARE Entry Andon Board working",
    "L&I station equipments available (wireless charger, 12V charger, USB, Pendrive)",
    "All Flags system working",
    "Foot mat available on assigned station",
    "AC Sniffer machine working",
    "Foot Paper is being used",
    "Foot Paper stock available",
    "Traffic light at Underbody working",
    "Shower Entry AI Vision Camera working",
    "Shower Pressure (2.2 bar) maintained",
    "Sunroof opening/closing being checked at S&R"
]

# Store per-user data
user_data = {}

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name or "User"
    user_data[user_id] = {
        "name": first_name,
        "answers": [],
        "remarks": [],
        "current_q": 0,
        "awaiting_remark": False
    }
    await send_question(update, context)

# Handle text messages (for remarks)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = user_data.get(user_id)

    if not data:
        await update.message.reply_text("Please start the bot using /start.")
        return

    if data["awaiting_remark"]:
        data["remarks"].append(update.message.text.strip())
        data["awaiting_remark"] = False
        data["current_q"] += 1
        await send_question(update, context)

# Ask question
async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    current_q = user_data[user_id]["current_q"]

    if current_q < len(questions):
        q_text = questions[current_q]
        buttons = [
            [InlineKeyboardButton("Yes", callback_data="Yes")],
            [InlineKeyboardButton("No", callback_data="No")]
        ]
        markup = InlineKeyboardMarkup(buttons)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Q{current_q + 1}: {q_text}",
            reply_markup=markup
        )
    else:
        await send_summary(update, context)

# Handle button click
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = user_data[user_id]
    answer = query.data
    data["answers"].append(answer)
    data["awaiting_remark"] = True

    await query.message.reply_text("📝 Please provide a remark for this item (even if it's 'N/A').")

# Send summary
async def send_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = user_data[user_id]
    name = data.get("name") or update.effective_user.first_name or "Unknown User"

    IST = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(IST).strftime("%d-%m-%Y %H:%M")

    def escape_markdown(text):
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        return ''.join(f'\\{c}' if c in escape_chars else c for c in text)

    summary_lines = [
        f"*📄 Today's Report - {escape_markdown(now)}*",
        f"*👤 Inspected by:* {escape_markdown(name)}",
        ""
    ]

    for i, q_text in enumerate(questions):
        escaped_q = escape_markdown(q_text)
        escaped_ans = escape_markdown(data["answers"][i])
        escaped_remark = escape_markdown(data["remarks"][i])
        summary_lines.append(f"*Q{i+1}:* {escaped_q}\nAnswer: {escaped_ans}\nRemark: {escaped_remark}\n")

    summary_text = "\n".join(summary_lines)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=summary_text,
        parse_mode='Markdown'
    )

# Log errors
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error("Exception while handling update:", exc_info=context.error)

# Run the bot
from telegram.ext import Application

app = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_error_handler(error_handler)

# Webhook setup for Railway
app.run_webhook(
    listen="0.0.0.0",
    port=int(os.environ.get("PORT", 8080)),
    webhook_url="https://telegrambot-production-fa9e.up.railway.app"
)






