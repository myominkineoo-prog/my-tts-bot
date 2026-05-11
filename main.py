import os
import random
import logging
import asyncio
import edge_tts
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Render အတွက် Flask setup
app = Flask(__name__)

# Logging စနစ်
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- နှုတ်ဆက်စကားစာရင်း (မရိုးရအောင် အများကြီး ထည့်ပေးထားပါတယ်) ---
GREETINGS = [
    "မင်္ဂလာပါရှင်! စာသားများကို သာယာနာပျော်ဖွယ် အသံများအဖြစ် ပြောင်းလဲပေးဖို့ အသင့်ရှိနေပါပြီ။",
    "ကိုယ်စိတ်နှစ်ပါး ကျန်းမာချမ်းသာကြပါစေ။ ဒီနေ့အတွက် ဘယ်စာသားကို အသံပြောင်းပေးရမလဲရှင်။",
    "လာရောက်အသုံးပြုပေးလို့ ကျေးဇူးအထူးတင်ပါတယ်။ အကောင်းဆုံး အသံဖန်တီးမှုတွေကို စတင်လိုက်ရအောင်။",
    "ပျော်ရွှင်စရာ နေ့ရက်လေးတစ်ခု ဖြစ်ပါစေရှင်။ စာသားမှ အသံပြောင်းလဲခြင်း ဝန်ဆောင်မှုကို စတင်အသုံးပြုနိုင်ပါပြီ။",
    "ယနေ့မှစ၍ သင်၏စာသားများကို သက်ရှိထင်ရှား အသံများအဖြစ် ဖန်တီးပေးပါရစေ။",
    "ကြိုဆိုပါတယ်ရှင်! လူကြီးမင်း၏ အလုပ်များကို ပိုမိုလွယ်ကူစေဖို့ အသံလှလှလေးတွေနဲ့ ကူညီပေးပါရစေ။",
    "တစ်နေ့တာကို အသံချိုချိုလေးတွေနဲ့ စတင်လိုက်ရအောင်။ ဘာများ ကူညီပေးရမလဲရှင်။",
    "စာဖတ်ရတာ ပင်ပန်းနေပြီလား? စာသားများကို ပို့ပေးလိုက်ပါ၊ အသံအဖြစ် ပြောင်းပေးပါမယ်ရှင်။",
    "သင်၏ စိတ်ကူးများကို အသံအဖြစ် အသက်သွင်းပေးဖို့ ကျွန်မတို့ စောင့်ကြိုနေပါတယ်။",
    "မင်္ဂလာရှိသော နေ့လေးဖြစ်ပါစေ။ အသံဖိုင် ဖန်တီးဖို့ စာသားလေး ပို့ပေးရုံပါပဲရှင်။"
]

SUCCESS_MESSAGES = [
    "အသံဖိုင်လေး ဖန်တီးလို့ ပြီးပါပြီရှင်။ သိမ်းဆည်းဖို့ အစက်သုံးစက်ကို နှိပ်ပြီး 'Save to Music' (သို့မဟုတ်) 'Save to mp3' လုပ်ပေးပါနော်။",
    "အသံထွက်လေးက တကယ်ကို သာယာပါတယ်ရှင်။ သိမ်းဆည်းဖို့ မမေ့နဲ့ဦးနော်။",
    "လူကြီးမင်းအတွက် အကောင်းဆုံး ပြောင်းလဲပေးထားပါတယ်။ အဆင်ပြေမယ်လို့ မျှော်လင့်ပါတယ်ရှင်။",
    "အသံဖိုင်လေး ရပါပြီ။ သူငယ်ချင်းများကိုလည်း ပြန်လည်မျှဝေပေးနိုင်ပါတယ်ရှင်။",
    "အောင်မြင်စွာ ပြောင်းလဲပြီးပါပြီ။ နောက်ထပ်လည်း လိုအပ်တာရှိရင် အမြဲတမ်း စောင့်ကြိုနေမှာပါ။"
]

# --- Bot လုပ်ဆောင်ချက်များ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = random.choice(GREETINGS)
    keyboard = [
        [InlineKeyboardButton("မြန်မာအသံ (အမျိုးသား - သီဟ)", callback_data='my-MM-ThihaNeural')],
        [InlineKeyboardButton("မြန်မာအသံ (အမျိုးသမီး - နီလာ)", callback_data='my-MM-NilarNeural')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"🌟 {welcome_text}\n\nကျေးဇူးပြုပြီး အသုံးပြုလိုသော အသံအမျိုးအစားကို ရွေးချယ်ပေးပါရှင် -", 
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['text_to_convert'] = update.message.text
    keyboard = [
        [InlineKeyboardButton("မြန်မာအသံ (အမျိုးသား - သီဟ)", callback_data='my-MM-ThihaNeural')],
        [InlineKeyboardButton("မြန်မာအသံ (အမျိုးသမီး - နီလာ)", callback_data='my-MM-NilarNeural')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("အသံပြောင်းလဲရန် အသံအမျိုးအစားကို ရွေးချယ်ပေးပါရှင် -", reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    selected_voice = query.data
    text = context.user_data.get('text_to_convert')
    
    if not text:
        await query.edit_message_text("ကျေးဇူးပြုပြီး အရင်ဆုံး စာသားတစ်ခုခု ပို့ပေးပါရှင်။")
        return

    status_msg = await query.edit_message_text("⏳ ခဏစောင့်ပေးပါ... အသံဖိုင် ဖန်တီးနေပါတယ်ရှင်။")
    
    # အသံပြောင်းလဲခြင်း လုပ်ငန်းစဉ်
    output_file = f"voice_{query.from_user.id}.mp3"
    try:
        communicate = edge_tts.Communicate(text, selected_voice)
        await communicate.save(output_file)
        
        success_text = random.choice(SUCCESS_MESSAGES)
        with open(output_file, 'rb') as audio:
            await context.bot.send_audio(
                chat_id=query.message.chat_id, 
                audio=audio, 
                caption=f"✅ {success_text}\n\n#TTS_Bot #Myanmar"
            )
        
        await status_msg.delete()
    except Exception as e:
        await query.edit_message_text(f"တောင်းပန်ပါတယ်ရှင်။ အမှားတစ်ခု ဖြစ်သွားလို့ပါ - {str(e)}")
    finally:
        if os.path.exists(output_file):
            os.remove(output_file)

# --- Main စနစ် ---
def main():
    token = os.environ.get('BOT_TOKEN')
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))

    # Bot စတင်ပတ်ခြင်း
    print("Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()