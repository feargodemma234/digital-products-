import os
import sqlite3
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
WALLET = os.getenv("WALLET")
PRICE = float(os.getenv("PRICE", 10))
PRODUCT_NAME = "WhatsApp Growth Guide"
FILE_PATH = "WhatsApp_Growth_Guide.pdf" # put your pdf here

DB = "txids.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS txids (txid TEXT PRIMARY KEY)")
    conn.commit()
    conn.close()

def txid_used(txid):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT 1 FROM txids WHERE txid=?", (txid,))
    res = c.fetchone()
    conn.close()
    return res is not None

def save_txid(txid):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO txids (txid) VALUES (?)", (txid,))
    conn.commit()
    conn.close()

def verify_trx(txid):
    url = f"https://api.trongrid.io/v1/transactions/{txid}"
    r = requests.get(url, timeout=10)
    if r.status_code!= 200: return False
    data = r.json().get("data", [{}])[0]
    return data.get("to_address") == WALLET and data.get("contractData",{}).get("amount",0)/1000000 >= PRICE

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"🔥 *{PRODUCT_NAME}*\n\nPrice: *${PRICE} USDT TRC20*\n\nSend ${PRICE} to:\n`{WALLET}`\n\nThen send me your TXID here"
    await update.message.reply_text(text, parse_mode="Markdown")

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txid = update.message.text.strip()
    if txid_used(txid):
        return await update.message.reply_text("❌ This TXID has already been used")

    await update.message.reply_text("⏳ Verifying payment on Tron...")

    if verify_trx(txid):
        save_txid(txid)
        await update.message.reply_document(document=open(FILE_PATH, "rb"), caption="✅ Payment confirmed! Here is your file.")
    else:
        await update.message.reply_text("❌ Invalid TXID or wrong amount. Try again")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
init_db()
app.run_polling()