# -- coding: utf-8 --
import os, json, asyncio
import nest_asyncio
nest_asyncio.apply()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask, request

# ---------------- إعدادات ------------ 
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@baher1ramzi"
DATA_FILE = "data.json"

bot = Bot(BOT_TOKEN)
application = ApplicationBuilder().token(BOT_TOKEN).build()

# ---------------- تحميل البيانات ----------------
INITIAL_DATA = {
    "math": {
        "shoroh": {
            "b1": [{"title": "المحددات 1", "url": "https://drive.google.com/file/d/1Nsy8PaWa7lzqo8Mi6epJ6m1wE8qwY2Ee/view?usp=drivesdk"}],
            "b2": [], "b3": [], "b4": [], "b5": [], "b6": [], "b7": []
        },
        "sheets": {
            "manhaj": {"b1": [{"title": "منهج الباب الأول", "url": "https://drive.google.com/file/d/1LbH9iWCa2Kk60WIy_TdJpWKK5dKCd3VY/view?usp=drivesdk"}]},
            "academia": {"b1": [{"title": "أكاديميا الباب الأول", "url": "https://drive.google.com/file/d/1-R6r5xjtaGX6nQHi3hfMpFI8eT_kunT6/view?usp=drivesdk"}]}
        },
        "exams": {"b1": [{"title": "أسئلة امتحانات الباب الأول", "url": "https://drive.google.com/file/d/17QCUX1OuMb1b-_1ZgFW0eWmSMk12be5g/view?usp=drivesdk"}]},
        "black": [{"title": "الكتاب الأسود", "url": "https://drive.google.com/file/d/1XsRtRcdo3T1Bw-q5sZCGZKOqp1hwcN4o/view?usp=drivesdk"}]
    },
    "stats": {
        "shoroh": {"b1": [{"title": "نظرية الاحتمالات", "url": "https://drive.google.com/file/d/1RJ7H2Lil1HxukuavyWuNibTPDYjCDRJa/view?usp=drivesdk"}]},
        "sheets": {
            "manhaj": {"b1": [{"title": "منهج الاحصاء الباب الأول", "url": "https://drive.google.com/file/d/1EQ8pvHbdwrnu-0TGNdDedrj_2MJuvKx1/view?usp=drivesdk"}]},
            "academia": {"b1": [{"title": "أكاديميا الاحصاء الباب الأول", "url": "https://drive.google.com/file/d/1j5rCPO79B-KjPE7my2HSb9FovPkDet0M/view?usp=drivesdk"}]}
        }
    }
}

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(INITIAL_DATA, f, ensure_ascii=False, indent=2)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

DATA = load_data()

# ---------------- التحقق من الاشتراك ----------------
async def check_membership(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ---------------- /start ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_membership(user_id, context):
        btn = InlineKeyboardButton("📢 انضم للقناة", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")
        await update.message.reply_text(
            "⚠️ يجب أن تكون مشتركًا في قناة م.باهر رمزي.\n\nبعد الاشتراك أرسل /start.",
            reply_markup=InlineKeyboardMarkup([[btn]])
        )
        return

    keyboard = [
        [InlineKeyboardButton("📘 رياضيات", callback_data="math")],
        [InlineKeyboardButton("📗 إحصاء", callback_data="stats")]
    ]
    await update.message.reply_text(
        "حياك الله في بوت م.باهر رمزي 👋، اختر المادة لبدء التحميل",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- التعامل مع الأزرار ----------------
def make_section_menu(mat):
    rows = [
        [InlineKeyboardButton("🎥 شروحات", callback_data=f"{mat}|shoroh")],
        [InlineKeyboardButton("📄 شيتات", callback_data=f"{mat}|sheets")]
    ]
    if mat == "math":
        rows.append([InlineKeyboardButton("📝 أسئلة امتحانات", callback_data=f"{mat}|exams")])
    rows.append([InlineKeyboardButton("📘 الكتاب الأسود", callback_data=f"{mat}|black")])
    rows.append([InlineKeyboardButton("🏠 رجوع", callback_data="home")])
    return rows

def make_babs_buttons(mat, section):
    bab_count = 7 if mat == "math" else 5
    rows = [
        [InlineKeyboardButton(f"📘 الباب {i}", callback_data=f"{mat}|{section}|b{i}") for i in range(1, bab_count + 1)]
    ]
    rows.append([InlineKeyboardButton("⬅️ رجوع", callback_data=mat)])
    return rows

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")

    if data[0] == "home":
        keyboard = [
            [InlineKeyboardButton("📘 رياضيات", callback_data="math")],
            [InlineKeyboardButton("📗 إحصاء", callback_data="stats")]
        ]
        await query.message.reply_text("اختر المادة:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if len(data) == 1 and data[0] in ["math", "stats"]:
        mat = data[0]
        await query.message.reply_text("اختر القسم:", reply_markup=InlineKeyboardMarkup(make_section_menu(mat)))
        return

    mat, section = data[0], data[1]

    if section == "black":
        file = DATA["math"]["black"][0]
        btn = InlineKeyboardButton("📘 اضغط للعرض", url=file["url"])
        await query.message.reply_text(
            f"📘 *{file['title']}*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[btn], [InlineKeyboardButton("⬅️ رجوع", callback_data="math")]])
        )
        return

# ---------------- Handlers ----------------
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button))

# ---------------- Flask Webhook ----------------
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Bot is running!", 200

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    asyncio.get_event_loop().create_task(application.process_update(update))
    return "ok", 200
