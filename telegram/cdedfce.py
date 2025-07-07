from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from datetime import datetime

questions = [
    {
        "text": "Is the EV charging working?",
        "options": ["Yes", "No"]
    },
    {
        "text": "Is the CARE entry Andon Board Working?",
        "options": ["Yes", "No"]
    },
    {
        "text": "Flags Performance Overview Screen working?",
        "options": ["Yes", "No"]
    },
    {
        "text": "Cluster Andon Screen Working?",
        "options": ["Yes", "No"]
    }
]

user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {
        "name": None,
        "answers": [],
        "remarks": [],
        "current_q": 0,
        "awaiting_name": True,
        "awaiting_remark": False
    }
    await update.message.reply_text("👋 Hello! What is your *name*?", parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = user_data.get(user_id)

    if not data:
        await update.message.reply_text("Please start the bot using /start.")
        return

    if data.get("awaiting_name"):
        data["name"] = update.message.text.strip()
        data["awaiting_name"] = False
        await send_question(update, context)
    elif data.get("awaiting_remark"):
        data["remarks"].append(update.message.text.strip())
        data["awaiting_remark"] = False
        data["current_q"] += 1
        await send_question(update, context)

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    current_q = user_data[user_id]["current_q"]

    if current_q < len(questions):
        q = questions[current_q]
        buttons = [[InlineKeyboardButton(opt, callback_data=opt)] for opt in q["options"]]
        reply_markup = InlineKeyboardMarkup(buttons)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Q{current_q + 1}: {q['text']}",
            reply_markup=reply_markup
        )
    else:
        await send_summary(update, context)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = user_data[user_id]
    answer = query.data

    data["answers"].append(answer)

    if answer == "No":
        data["awaiting_remark"] = True
        await query.message.reply_text("⚠️ Please provide a *remark* for this issue:", parse_mode='Markdown')
    else:
        data["remarks"].append("N/A")
        data["current_q"] += 1
        await send_question(update, context)

async def send_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = user_data[user_id]
    name = data["name"]
    now = datetime.now().strftime("%d-%m-%Y %H:%M")

    summary_lines = [
        f"*📄 Today's Report - {name}*",
        f"*🕒 Date & Time:* {now}",
        ""
    ]

    for i, q in enumerate(questions):
        ans = data["answers"][i]
        remark = data["remarks"][i]
        summary_lines.append(f"*Q{i+1}:* {q['text']}\nAnswer: {ans}\nRemark: {remark}\n")

    summary = "\n".join(summary_lines)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=summary,
        parse_mode='Markdown'
    )

def main():
    app = ApplicationBuilder().token("YOUR_BOT_TOKEN_HERE").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()



