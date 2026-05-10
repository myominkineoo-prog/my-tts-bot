import os
import asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import edge_tts

# --- Render အတွက် Web Server အပိုင်း ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()
# ----------------------------------

# Bot Token နဲ့ API Keys
TOKEN = os.environ.get('BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("မင်္ဂလာပါတူလေး! အန်တီ့ရဲ့ TTS Bot က အဆင်သင့်ပါပဲ။")

async def text_to_speech(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    output_file = "output.mp3"
    
    # TTS ပြောင်းလဲခြင်း
    communicate = edge_tts.Communicate(text, "my-MM-ThihaNeural")
    await communicate.save(output_file)
    
    # အသံဖိုင် ပေးပို့ခြင်း
    with open(output_file, 'rb') as audio:
        await update.message.reply_audio(audio)
    os.remove(output_file)

if __name__ == '__main__':
    keep_alive() # Web Server ကို အရင်ဖွင့်မယ်
    app_bot = ApplicationBuilder().token(TOKEN).build()
    
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), text_to_speech))
    
    print("Bot is starting...")
    app_bot.run_polling()