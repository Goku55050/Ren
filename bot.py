import os
import requests
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

# ==========================
# LOAD ENV VARIABLES
# ==========================
load_dotenv()  # loads BOT_TOKEN, ADMIN_ID from .env

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# API LINKS
API = "https://veerulookup.onrender.com/search_phone?number="
TRACE_API = "https://calltracerinfoapi.vercel.app/api?number="
VEHICLE_API = "https://veerulookup.onrender.com/search_vehicle?rc="
UPI_API = "https://veerulookup.onrender.com/search_upi?upi="

# USER CREDIT DATA
user_credits = {}  # {user_id: credits}

# ==========================
# TELEGRAM COMMANDS
# ==========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_credits:
        user_credits[user_id] = 5
    await update.message.reply_text(
        f"👑 WELCOME TO ARES INFO BOT - PREMIUM 👑\n"
        f"Use /help to get details.\n"
        f"💰 Credits: {'∞' if user_id == ADMIN_ID else user_credits[user_id]}"
    )

async def lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID and user_credits.get(user_id, 5) <= 0:
        await update.message.reply_text("❌ No credits left. Contact admin.")
        return
    if not context.args:
        await update.message.reply_text("❌ Provide a phone number. Example: /lookup +919876543210")
        return
    number = context.args[0]
    await update.message.reply_text("🔍 Searching, please wait...")
    try:
        r = requests.get(f"{API}{number}", timeout=15)
        if r.ok:
            data = r.json()
            if 'credit' in data and data['credit'].lower() == 'anshapi':
                data['credit'] = 'Ares'
            results = data.get("result", [])
            msg = f"💎 **ARES INFO BOT - RESULT** 💎\n\n"
            msg += f"Credit: {data.get('credit','Ares')}\nSuccess: {data.get('success', True)}\n\n"
            if not results:
                msg += "❌ No results found."
            else:
                for idx, entry in enumerate(results, 1):
                    msg += (
                        f"🔹 Result {idx} 🔹\n"
                        f"Name: {entry.get('name','N/A')}\n"
                        f"Mobile: {entry.get('mobile','N/A')}\n"
                        f"Alt Mobile: {entry.get('alt_mobile','N/A')}\n"
                        f"Father Name: {entry.get('father_name','N/A')}\n"
                        f"Address: {entry.get('address','N/A')}\n"
                        f"Circle: {entry.get('circle','N/A')}\n"
                        f"Email: {entry.get('email','N/A')}\n"
                        + "-"*30 + "\n"
                    )
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("❌ API not responding.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error connecting to API: {e}")
    if user_id != ADMIN_ID:
        user_credits[user_id] = user_credits.get(user_id, 5) - 1
        await update.message.reply_text(f"💰 Credits used: 1 | Remaining: {user_credits[user_id]}")

# ---------------------------
# Other commands (trace, vehicle, upi, credit, add_credit, help)
# can be implemented similarly as lookup for brevity
# ---------------------------

# ==========================
# FLASK APP FOR 24/7 KEEP ALIVE
# ==========================
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "✅ Ares Premium Bot is Running!"

def run_flask():
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

# ==========================
# TELEGRAM BOT
# ==========================
def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("lookup", lookup))
    # Add other handlers here...
    print("✅ Telegram Bot started...")
    app.run_polling()

# ==========================
# MAIN
# ==========================
if __name__ == "__main__":
    # Run Flask in a thread for Render keep-alive
    Thread(target=run_flask).start()
    # Run Telegram bot
    run_bot()
