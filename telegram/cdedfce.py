import os
import logging
from datetime import datetime, timedelta, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# IST Timezone
IST = timezone(timedelta(hours=5, minutes=30))

# New 13 questions
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

user_data = {}

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    user_data[user_id] = {
        "name": username,
        "answers": [],
        "remarks": [],
        "current_q": 0,
        "awaiting_remark": False,
        "last_answer": None
    }
    await send_question(update, context)

# Handle typed messages (remarks)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = user_data.get(user_id)

    if not data or not data["awaiting_remark"]:
        await update.message.reply_text("Please start the inspection using /start.")
        return

    data["remarks"].append(update.message.text.strip())
    data["awaiting_remark"] = False
    data["current_q"] += 1
    await send_question(update, context)

# Ask next question
async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    current_q = user_data[user_id]["current_q"]

    if current_q < len(questions):
        question = questions[current_q]
        buttons = [[InlineKeyboardButton("Yes", callback_data="Yes")],
                   [InlineKeyboardButton("No", callback_data="No")]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Q{current_q + 1}: {question}",
            reply_markup=reply_markup
        )
    else:
        await send_summary(update, context)

# Handle Yes/No button
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = user_data[user_id]
    answer = query.data

    data["answers"].append(answer)
    data["last_answer"] = answer
    data["awaiting_remark"] = True
    await query.message.reply_text("📝 Please provide a remark for this response:")

# Final summary
async def send_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = user_data[user_id]
    now = datetime.now(IST).strftime("%d-%m-%Y %H:%M")

    summary_lines = [
    f"<b>📄 Inspection Report - {now}</b>",
    f"<b>👤 Inspected by:</b> {data['name']}",
    ""
    ]
    summary_lines.append(f"<b>Q{i+1}:</b> {question}<br>Answer: {ans}<br>Remark: {remark}<br>")

    for i, question in enumerate(questions):
        ans = data["answers"][i]
        remark = data["remarks"][i]
        summary_lines.append(f"*Q{i+1}:* {question}\nAnswer: {ans}\nRemark: {remark}\n")

    summary_text = "\n".join(summary_lines)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=summary_text, parse_mode='HTML')

# Error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(msg="Exception while handling update:", exc_info=context.error)

# Start the bot
app = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_error_handler(error_handler)

# Webhook settings
app.run_webhook(
    listen="0.0.0.0",
    port=int(os.environ.get("PORT", 8080)),
    webhook_url="https://telegrambot-production-fa9e.up.railway.app"
)




