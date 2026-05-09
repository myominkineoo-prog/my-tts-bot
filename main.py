import os
import requests
import edge_tts
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Settings ---
GEMINI_API_KEY = "AIzaSyB34qbepGTRalPufOAIA4eCsO2UioWOfl4"
TELEGRAM_BOT_TOKEN = "8629308104:AAF3_J53Ze6kwym86_sznHzxd0PQ2yg6KsE"

user_data = {}

def get_gemini_fix(text, mood):
    if len(text) > 600: return text 
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        prompt = f"အောက်ပါစာသားကို {mood} ပုံစံပေါက်အောင် မြန်မာစကားပြော ပြင်ပေးပါ။ စာသားသက်သက်ပဲ ပြန်ဖြေပါ: {text}"
        response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        data = response.json()
        return data['candidates'][0]['content']['parts'][0]['text'] if 'candidates' in data else text
    except: return text

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text
    if chat_id not in user_data: user_data[chat_id] = {'voice': 'my-MM-NilarNeural', 'mood': 'ပုံမှန်'}

    settings_map = {
        'Nilar': ('voice', 'my-MM-NilarNeural'), 'Thiha': ('voice', 'my-MM-ThihaNeural'),
        'ပျော်ရွှင်': ('mood', 'ပျော်ရွှင်တက်ကြွတဲ့'), 'ဝမ်းနည်း': ('mood', 'ဝမ်းနည်းကြေကွဲနေတဲ့'),
        'ဒေါသ': ('mood', 'ဒေါသထွက်နေတဲ့'), 'လူကြီး': ('mood', 'တည်ငြိမ်ရင့်ကျက်တဲ့ လူကြီး'),
        'ကလေး': ('mood', 'ချစ်စရာကောင်းတဲ့ ကလေးငယ်'), 'ပုံမှန်': ('mood', 'ပုံမှန်')
    }

    if len(text) < 30:
        for key, (category, val) in settings_map.items():
            if key in text:
                user_data[chat_id][category] = val
                return await update.message.reply_text(f"✅ {text} သို့ ပြောင်းလိုက်ပါပြီ။")

    await context.bot.send_chat_action(chat_id=chat_id, action="record_voice")
    filename = f"voice_{chat_id}.mp3"

    try:
        fixed_text = get_gemini_fix(text, user_data[chat_id]['mood'])
        communicate = edge_tts.Communicate(fixed_text, user_data[chat_id]['voice'])
        await communicate.save(filename)

        with open(filename, 'rb') as audio:
            await update.message.reply_voice(voice=audio)
            audio.seek(0)
            await context.bot.send_audio(
                chat_id=chat_id,
                audio=audio,
                title="TTS Recording",
                filename="save_this_audio.mp3",
                caption="📥 ဖုန်းထဲသိမ်းရန် အစက် ၃ စက်ကိုနှိပ်ပြီး Save to Music လုပ်ပါဗျာ။"
            )
        os.remove(filename)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['👩 Nilar', '👨 Thiha'], ['😊 ပျော်ရွှင်', '😢 ဝမ်းနည်း'], ['😡 ဒေါသ', '👴 လူကြီး'], ['👶 ကလေး', '😐 ပုံမှန်']]
    await update.message.reply_text("TTS Bot အဆင်သင့်ဖြစ်ပါပြီ။", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__': main()
