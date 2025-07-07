from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes
)

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
    user_data[user_id] = {"answers": [], "current_q": 0}
    await send_question(update, context)

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    current_q = user_data[user_id]["current_q"]
    if current_q < len(questions):
        q = questions[current_q]
        buttons = [[InlineKeyboardButton(opt, callback_data=opt)] for opt in q["options"]]
        reply_markup = InlineKeyboardMarkup(buttons)
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
    user_data[user_id]["answers"].append(query.data)
    user_data[user_id]["current_q"] += 1
    await send_question(update, context)

async def send_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    answers = user_data[user_id]["answers"]
    summary = "\n".join(
        f"Q{i+1}: {questions[i]['text']}\nYour answer: {ans}"
        for i, ans in enumerate(answers)
    )
    await update.callback_query.message.reply_text(
        f"📊 *Your Summary Report:*\n\n{summary}",
        parse_mode='Markdown'
    )

def main():
    app = ApplicationBuilder().token("7998832352:AAENC5rlDMjQbLylmLsCHbzX5eZLV5mJoWs").build()


    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
#git init
# git add .
# git commit -m "Initial commit"
# git branch -M main
# git remote add origin https://github.com/YOUR_USERNAME/telegram-bot.git
# git push -u origin main
