import asyncio
import random
import requests
from datetime import datetime
import pytz
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telegram.constants import ParseMode

# --- [Configuration] ---
TOKEN = '8344556214:AAEHn6O5R6D-CsnuSUacbTDYIpv-xRo884k'
ADMIN_ID = 6342470463 

# State constants
GET_GAME_ID, GET_SERVER_ID, CONFIRM_PAID, GET_RECEIPT = range(4)
GET_TRANS_ID, GET_TRANS_AMT = range(4, 6)

user_db = {} 

# --- [Helpers] ---
def get_mlbb_name(user_id, zone_id):
    try:
        url = f"https://api.isan.eu.org/nickname/ml?id={user_id}&zone={zone_id}"
        r = requests.get(url, timeout=10)
        return r.json().get("name")
    except: return None

def generate_order_id():
    return f"ORD{datetime.now(pytz.timezone('Asia/Yangon')).strftime('%y%m%d%H%M%S')}"

async def safe_delete(context, cid, mid):
    """Bot ရဲ့ စာကိုပဲ သီးသန့်ဖျက်ဖို့ Helper"""
    if mid:
        try: await context.bot.delete_message(chat_id=cid, message_id=mid)
        except: pass

def get_udata(uid, uobj=None):
    if uid not in user_db:
        user_db[uid] = {'coins': 0, 'history': [], 'name': uobj.first_name if uobj else "User"}
    return user_db[uid]

# --- [Main Menus] ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    udata = get_udata(uid, update.effective_user)
    text = (
        "💎 <b>WELCOME TO SHYO DIAMONDS SHOP</b> 💎\n"
        "-------------------------------\n"
        "🎮 Shyo Diamond Shop မှ ကြိုဆိုလိုက်ပါတယ်။\n"
        "အောက်က Menu မှ ရွေးချယ်ဝယ်ယူပါ။\n\n"
        f"💰 Your Coins: <b>{udata['coins']}</b>\n\n"
        "စျေးနှုန်းအမှန်နှင့် အမြန်ဆန်ဆုံး ဝန်ဆောင်မှု။"
    )
    kb = [
        [InlineKeyboardButton("📦 ဝယ်ယူရန်", callback_data='menu_buy')],
        [InlineKeyboardButton("👥 Invite Friend", callback_data='menu_inv'), 
         InlineKeyboardButton("💰 My Coins", callback_data='menu_coin')],
        [InlineKeyboardButton("📝 Order ပြန်ကြည့်ရန်", callback_data='menu_his')],
        [InlineKeyboardButton("💸 Coin အချင်းချင်းလွှဲရန်", callback_data='menu_trans')],
        [InlineKeyboardButton("📞 ဆက်သွယ်ရန် ↗️", url='https://t.me/Shyo29'), 
         InlineKeyboardButton("📖 လမ်းညွှန်", callback_data='menu_guide')]
    ]
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
    else:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

# --- [Callback Logic] ---
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; data = query.data; uid = query.from_user.id
    udata = get_udata(uid)
    await query.answer()

    if data == 'menu_coin':
        await query.edit_message_text(f"💰 <b>သင့်ရဲ့ လက်ရှိ Coins ပမာဏ</b>\n\nTotal: <b>{udata['coins']} Coins</b>", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='home')]]), parse_mode=ParseMode.HTML)
    
    elif data == 'menu_inv':
        bot_me = await context.bot.get_me()
        inv_link = f"https://t.me/{bot_me.username}?start=INVITE{uid}"
        text = (
            f"👥 <b>Invite Friend</b>\n\n"
            f"🔗 <code>{inv_link}</code>\n\n"
            f"📌 လင့်ခ်ကို သူငယ်ချင်းများသို့ မျှဝေပါ။"
        )
        kb = [[InlineKeyboardButton("🚀 Share Link", url=f"https://t.me/share/url?url={inv_link}&text=MLBB စိန်ကိုစျေးသက်သက်သာသာနဲ့ Shyo Shop မှာဝယ်ယူလိုက်ပါ!")],
              [InlineKeyboardButton("🔙 နောက်သို့", callback_data='home')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif data == 'menu_his':
        history = udata['history']
        h_text = "📝 <b>သင်၏ မှာယူမှုမှတ်တမ်း</b>\n\n"
        if not history: h_text += "မှတ်တမ်းမရှိသေးပါ။"
        else:
            for h in history[-5:]: h_text += f"✅ {h}\n"
        await query.edit_message_text(h_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='home')]]), parse_mode=ParseMode.HTML)

    elif data == 'menu_guide':
        guide = "📖 <b>လမ်းညွှန်ချက်</b>\n\n1. ဝယ်ယူရန်နှိပ်ပြီး Package ရွေးပါ။\n2. Game ID ပို့ပါ။\n3. ငွေလွှဲပြီး ပြေစာ (Screenshot) ပို့ပေးပါ။\n4. Admin မှ စစ်ဆေးပြီး ၁ မိနစ်အတွင်း စိန်ထည့်ပေးပါမည်။"
        await query.edit_message_text(guide, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='home')]]), parse_mode=ParseMode.HTML)

    elif data == 'home': await start(update, context)

    # --- Buy Categories ---
    elif data == 'menu_buy':
        kb = [[InlineKeyboardButton("📅 Weekly Diamond Pass", callback_data='cat_w')],
              [InlineKeyboardButton("⚡ Double Diamond", callback_data='cat_d')],
              [InlineKeyboardButton("💎 Normal Diamonds", callback_data='cat_n')],
              [InlineKeyboardButton("📦 Big Diamonds", callback_data='cat_b')],
              [InlineKeyboardButton("🔙 Back", callback_data='home')]]
        await query.edit_message_text("📦 Package အမျိုးအစား ရွေးချယ်ပါ-", reply_markup=InlineKeyboardMarkup(kb))

    elif data == 'cat_w':
        btns = [[InlineKeyboardButton("📆 Weekly (x1) - 5,850", callback_data='buy_Weekly Pass_5850')],
                [InlineKeyboardButton("📆 Weekly (x2) - 11,700", callback_data='buy_Weekly Pass(x2)_11700')],
                [InlineKeyboardButton("🔙 Back", callback_data='menu_buy')]]
        await query.edit_message_text("📅 Weekly Pass စျေးနှုန်းများ", reply_markup=InlineKeyboardMarkup(btns))

    elif data == 'cat_d':
        btns = [[InlineKeyboardButton("⚡ 50+50D - 4,500", callback_data='buy_50+50 Double_4500')],
                [InlineKeyboardButton("⚡ 150+150D - 12,000", callback_data='buy_150+150 Double_12000')],
                [InlineKeyboardButton("⚡ 250+250D - 16,200", callback_data='buy_250+250 Double_16200')],
                [InlineKeyboardButton("⚡ 500+500D - 32,500", callback_data='buy_500+500 Double_32500')],
                [InlineKeyboardButton("🔙 Back", callback_data='menu_buy')]]
        await query.edit_message_text("⚡ Double Diamond စျေးနှုန်းများ", reply_markup=InlineKeyboardMarkup(btns))

    elif data == 'cat_n':
        btns = [[InlineKeyboardButton("💎 11💎 - 1,000", callback_data='buy_11💎_1000')],
                [InlineKeyboardButton("💎 22💎 - 2,000", callback_data='buy_22💎_2000')],
                [InlineKeyboardButton("💎 56💎 - 4,500", callback_data='buy_56💎_4500')],
                [InlineKeyboardButton("💎 86💎 - 5,000", callback_data='buy_86💎_5000')],
                [InlineKeyboardButton("💎 172💎 - 10,000", callback_data='buy_172💎_10000')],
                [InlineKeyboardButton("💎 257💎 - 15,500", callback_data='buy_257💎_15500')],
                [InlineKeyboardButton("🔙 Back", callback_data='menu_buy')]]
        await query.edit_message_text("💎 Normal Diamond (၆ မျိုး)", reply_markup=InlineKeyboardMarkup(btns))

    elif data == 'cat_b':
        btns = [[InlineKeyboardButton("📦 344💎 - 20,500", callback_data='buy_344💎_20500')],
                [InlineKeyboardButton("📦 429💎 - 25,500", callback_data='buy_429💎_25500')],
                [InlineKeyboardButton("📦 514💎 - 30,500", callback_data='buy_514💎_30500')],
                [InlineKeyboardButton("📦 600💎 - 35,500", callback_data='buy_600💎_35500')],
                [InlineKeyboardButton("📦 706💎 - 39,100", callback_data='buy_706💎_39100')],
                [InlineKeyboardButton("📦 9288💎 - 450,000", callback_data='buy_9288💎_450000')],
                [InlineKeyboardButton("🔙 Back", callback_data='menu_buy')]]
        await query.edit_message_text("📦 Big Diamond (၆ မျိုး)", reply_markup=InlineKeyboardMarkup(btns))

    # --- Admin Logic ---
    elif data.startswith('adm_'):
        _, action, target_uid, order_id = data.split('_')
        target_uid = int(target_uid)
        if action == "approve":
            user_db[target_uid]['coins'] += 25
            await context.bot.send_message(target_uid, "✅ <b>Order အောင်မြင်ပါသည်!</b>\n\nစိန်ထည့်သွင်းခြင်း ပြီးမြောက်ပါပြီ။\nBonus အဖြစ် <b>25 Coins</b> ထည့်ပေးလိုက်ပါတယ်။", parse_mode=ParseMode.HTML)
            await query.edit_message_caption(caption=query.message.caption + "\n\n✅ အတည်ပြုပြီး", reply_markup=None)
        elif action == "reject":
            await context.bot.send_message(target_uid, "❌ <b>Order ငြင်းပယ်ခံရသည်!</b>\n\nအချက်အလက်များကို ပြန်လည်စစ်ဆေးပါ။", parse_mode=ParseMode.HTML)
            await query.edit_message_caption(caption=query.message.caption + "\n\n❌ ငြင်းပယ်ပြီး", reply_markup=None)

# --- [Diamond Buying Conversation] ---
async def start_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, name, price = query.data.split('_')
    context.user_data['p_name'] = name
    context.user_data['p_price'] = price
    
    await query.message.delete()
    text = (f"🛒 <b>{name}</b>\n💰 <b>{price} Ks</b>\n\n"
            f"🎮 <b>Game ID ပို့ပါ။</b>\n"
            f"ဥပမာ: 12345678")
    msg = await context.bot.send_message(query.message.chat_id, text, parse_mode=ParseMode.HTML)
    context.user_data['bot_mid'] = msg.message_id
    return GET_GAME_ID

async def get_game_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['u_id'] = update.message.text
    # Bot ရဲ့ စာပဲ ဖျက်မယ်
    await safe_delete(context, update.effective_chat.id, context.user_data.get('bot_mid'))
    
    text = ("✅ <b>Game ID ရရှိပါသည်။</b>\n\n"
            "🌐 <b>Server ID ကို ရိုက်ထည့်ပါ။</b>\n"
            "ဥပမာ: 2033")
    msg = await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    context.user_data['bot_mid'] = msg.message_id
    return GET_SERVER_ID

async def get_server_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    z_id = update.message.text
    u_id = context.user_data['u_id']
    context.user_data['z_id'] = z_id
    
    await safe_delete(context, update.effective_chat.id, context.user_data.get('bot_mid'))
    load_msg = await update.message.reply_text("🔍 <b>နာမည်ရှာဖွေနေပါသည်... ခဏစောင့်ပါ။</b>", parse_mode=ParseMode.HTML)
    
    nick = get_mlbb_name(u_id, z_id)
    await load_msg.delete()
    
    if nick:
        context.user_data['nick'] = nick
        confirm_text = (
            f"✅ <b>နာမည်တွေ့ရှိသည်။</b>\n\n"
            f"👤 Game Name: <b>{nick}</b>\n"
            f"🆔 Game ID: <b>{u_id}</b>\n\n"
            f"🌐 Server ID: <b>{z_id}</b>\n\n"
            f"📦 Package: <b>{context.user_data['p_name']}</b>\n"
            f"💎 Diamonds: 0\n"
            f"💰 ကျသင့်ငွေ: <b>{context.user_data['p_price']} Ks</b>\n"
            f"👤 Name: <b>Shin Thant Kyi</b>\n\n"
            f"🏦 KBZPay: <code>09403384964</code>\n"
            f"🏦 WavePay: <code>09403384964</code>\n\n"
            f"📌 ငွေလွဲပြီးပါက အောက်ပါခလုတ်ကိုနှိပ်၍ Screenshot ပို့ပေးပါ။"
        )
        msg = await update.message.reply_text(confirm_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💸 လွှဲပြီးပြီ", callback_data='paid')]]), parse_mode=ParseMode.HTML)
        context.user_data['bot_mid'] = msg.message_id
        return CONFIRM_PAID
    else:
        msg = await update.message.reply_text("❌ <b>ID မတွေ့ပါ။ ID ပြန်ပို့ပေးပါ။</b>")
        context.user_data['bot_mid'] = msg.message_id
        return GET_GAME_ID

async def ask_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await safe_delete(context, query.message.chat_id, context.user_data.get('bot_mid'))
    
    msg = await context.bot.send_message(query.message.chat_id, "📤 <b>ငွေလွှဲပြေစာ ပို့ပါ</b>\n\nScreenshot ပို့ပါ။", parse_mode=ParseMode.HTML)
    context.user_data['bot_mid'] = msg.message_id
    return GET_RECEIPT

async def get_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    oid = generate_order_id()
    uid = update.effective_user.id
    
    await safe_delete(context, update.effective_chat.id, context.user_data.get('bot_mid'))
    
    admin_text = (
        f"🆕 <b>မှာယူမှုအသစ်</b>\n\n👤 Game Name: {context.user_data['nick']}\n"
        f"🆔 ID: {context.user_data['u_id']} | Server: {context.user_data['z_id']}\n"
        f"📦 Package: {context.user_data['p_name']}\n💰 Price: {context.user_data['p_price']} Ks\n"
        f"🆔 Order ID: {oid}\n\n⌛ စစ်ဆေးဆဲ"
    )
    kb = [[InlineKeyboardButton("✅ အတည်ပြု", callback_data=f"adm_approve_{uid}_{oid}"), 
           InlineKeyboardButton("❌ ငြင်းပယ်", callback_data=f"adm_reject_{uid}_{oid}")]]
    
    await context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, caption=admin_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
    
    # User Response
    await update.message.reply_text(f"⏳ <b>Admin စစ်ဆေးနေပါသည်။ ခဏစောင့်ပါ။</b>\n\nOrder ID: <code>{oid}</code>", parse_mode=ParseMode.HTML)
    return ConversationHandler.END

# --- [Coin Transfer] ---
async def start_trans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    msg = await query.edit_message_text("💸 <b>Coin လွှဲပြောင်းရန်</b>\n\nလွှဲပေးလိုသော User ၏ Telegram ID ကို ပို့ပေးပါ။")
    context.user_data['bot_mid'] = msg.message_id
    return GET_TRANS_ID

async def get_trans_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['target_id'] = int(update.message.text)
    await safe_delete(context, update.effective_chat.id, context.user_data.get('bot_mid'))
    msg = await update.message.reply_text("🔢 လွှဲမည့် <b>Coin ပမာဏ</b> ကို ရိုက်ထည့်ပါ။")
    context.user_data['bot_mid'] = msg.message_id
    return GET_TRANS_AMT

async def get_trans_amt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amount = int(update.message.text)
    sender_id = update.effective_user.id
    target_id = context.user_data['target_id']
    await safe_delete(context, update.effective_chat.id, context.user_data.get('bot_mid'))
    
    if user_db.get(sender_id, {}).get('coins', 0) >= amount:
        user_db[sender_id]['coins'] -= amount
        if target_id not in user_db: user_db[target_id] = {'coins': 0, 'history': [], 'name': "User"}
        user_db[target_id]['coins'] += amount
        await update.message.reply_text(f"✅ ID: {target_id} ဆီသို့ {amount} Coins လွှဲပြောင်းမှု အောင်မြင်ပါသည်။")
    else:
        await update.message.reply_text("❌ သင့်မှာ Coin မလုံလောက်ပါ။")
    return ConversationHandler.END

# --- [Main Initialization] ---
def main():
    app = Application.builder().token(TOKEN).build()
    
    buy_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_buy, pattern='^buy_')],
        states={
            GET_GAME_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_game_id)],
            GET_SERVER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_server_id)],
            CONFIRM_PAID: [CallbackQueryHandler(ask_receipt, pattern='^paid$')],
            GET_RECEIPT: [MessageHandler(filters.PHOTO, get_receipt)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
        allow_reentry=True
    )

    trans_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_trans, pattern='^menu_trans$')],
        states={
            GET_TRANS_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_trans_id)],
            GET_TRANS_AMT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_trans_amt)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
        allow_reentry=True
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(buy_conv)
    app.add_handler(trans_conv)
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    app.run_polling()

if __name__ == '__main__': main()