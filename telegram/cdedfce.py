from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters,
    ContextTypes
)

questions = [
    {"text": "Is the EV charging working?", "options": ["Yes", "No"]},
    {"text": "Is the CARE entry Andon Board Working?", "options": ["Yes", "No"]},
    {"text": "Flags Performance Overview Screen working?", "options": ["Yes", "No"]},
    {"text": "Cluster Andon Screen Working?", "options": ["Yes", "No"]}
]

user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {
        "answers": [],
        "current_q": 0,
        "awaiting_remark": False
    }
    await send_question(update, context)

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    current_q = user_data[user_id]["current_q"]
    
    if current_q < len(questions):
        q = questions[current_q]
        buttons = [[InlineKeyboardButton(opt, callback_data=opt)] for opt in q["options"]]
        reply_markup = InlineKeyboardMarkup(buttons)

        # Decide where to send the next question (message vs callback query)
        if update.message:
            await update.message.reply_text(q["text"], reply_markup=reply_markup)
        else:
            await update.callback_query.message.reply_text(q["text"], reply_markup=reply_markup)
    else:
        await send_summary(update, context)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    choice = query.data

    if choice == "No":
        user_data[user_id]["answers"].append({"answer": "No", "remark": None})
        user_data[user_id]["awaiting_remark"] = True
        await query.message.reply_text("❗ Please provide a remark for your 'No' answer.")
    else:
        user_data[user_id]["answers"].append({"answer": "Yes", "remark": None})
        user_data[user_id]["current_q"] += 1
        await send_question(update, context)

async def handle_remark(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in user_data and user_data[user_id].get("awaiting_remark"):
        remark = update.message.text
        # Save remark to last answer
        user_data[user_id]["answers"][-1]["remark"] = remark
        user_data[user_id]["awaiting_remark"] = False
        user_data[user_id]["current_q"] += 1
        await send_question(update, context)

async def send_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    answers = user_data[user_id]["answers"]

    summary = ""
    for i, entry in enumerate(answers):
        q_text = questions[i]["text"]
        ans = entry["answer"]
        remark = f"\nRemark: {entry['remark']}" if entry["remark"] else ""
        summary += f"Q{i+1}: {q_text}\nYour answer: {ans}{remark}\n\n"

    await update.callback_query.message.reply_text(
        f"📊 *Your Summary Report:*\n\n{summary}",
        parse_mode='Markdown'
    )

def main():
    app = ApplicationBuilder().token("7998832352:AAENC5rlDMjQbLylmLsCHbzX5eZLV5mJoWs").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_remark))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()

