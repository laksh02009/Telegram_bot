import os
import logging
from datetime import datetime, timedelta, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Checklist questions
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

# Per-user session storage
user_data = {}

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {
        "name": update.effective_user.first_name or update.effective_user.username or "Unknown",
        "answers": [],
        "remarks": [],
        "current_q": 0,
        "awaiting_remark": False,
        "follow_up_for_yes": False
    }
    await send_question(update, context)

# Handle remarks and other messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = user_data.get(user_id)
    if not data:
        await update.message.reply_text("Please start with /start.")
        return

    if data["awaiting_remark"]:
        remark = update.message.text.strip()
        data["remarks"].append(remark)
        data["awaiting_remark"] = False
        data["follow_up_for_yes"] = False
        data["current_q"] += 1
        await send_question(update, context)

# Ask next question
async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    current_q = user_data[user_id]["current_q"]

    if current_q < len(questions):
        q_text = questions[current_q]
        buttons = [
            [InlineKeyboardButton("Yes ✅", callback_data="Yes")],
            [InlineKeyboardButton("No ❌", callback_data="No")]
        ]
        markup = InlineKeyboardMarkup(buttons)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Q{current_q + 1}: {q_text}",
            reply_markup=markup
        )
    else:
        await send_summary(update, context)

# Handle button selections
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = user_data[user_id]

    current_q = data["current_q"]
    answer = query.data

    if answer in ["Yes", "No"]:
        data["answers"].append(answer)
        if answer == "No":
            data["awaiting_remark"] = True
            await query.message.reply_text("⚠️ Please provide a *remark* for this issue:", parse_mode='Markdown')
        else:
            data["follow_up_for_yes"] = True
            buttons = [
                [InlineKeyboardButton("N/A", callback_data="N/A")],
                [InlineKeyboardButton("Add Remark", callback_data="AddRemark")]
            ]
            markup = InlineKeyboardMarkup(buttons)
            await query.message.reply_text("✅ Would you like to add a remark?", reply_markup=markup)
    elif answer == "N/A":
        data["remarks"].append("N/A")
        data["follow_up_for_yes"] = False
        data["current_q"] += 1
        await send_question(update, context)
    elif answer == "AddRemark":
        data["awaiting_remark"] = True
        await query.message.reply_text("📝 Please enter your remark:")

# Summary report
async def send_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = user_data[user_id]

    name = data["name"]
    IST = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(IST).strftime("%d-%m-%Y %H:%M")

    lines = [f"*📄 Today's Report - {now}*", f"*👤 Inspected by:* {name}", ""]

    for i, q_text in enumerate(questions):
        ans = data["answers"][i]
        remark = data["remarks"][i].strip()
    
        # ✅ Skip the question if remark is "N/A" and answer was "Yes"
        if ans == "Yes" and remark.upper() == "N/A":
            continue
    
        escaped_q = escape_markdown(q_text)
        escaped_ans = "✅ Yes" if ans == "Yes" else "❌ No"
        escaped_remark = escape_markdown(remark)
        summary_lines.append(f"*Q{i+1}:* {escaped_q} — *{escaped_ans}* — _{escaped_remark}_")


    summary = "\n".join(lines)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=summary, parse_mode='Markdown')

# Error logging
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error("Exception while handling update:", exc_info=context.error)

# Launch application
from telegram.ext import Application

app = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_error_handler(error_handler)

# For Railway or similar deployments
app.run_webhook(
    listen="0.0.0.0",
    port=int(os.environ.get("PORT", 8080)),
    webhook_url="https://telegrambot-production-fa9e.up.railway.app"
)
