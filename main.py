# -- coding: utf-8 --
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask, request
import os, json
import asyncio

# ---------------- إعدادات ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")  # خليه من Environment Variables
CHANNEL_USERNAME = "@baher1ramzi"
DATA_FILE = "data.json"

bot = Bot(BOT_TOKEN)
application = ApplicationBuilder().token(BOT_TOKEN).build()

# ---------------- تحميل البيانات ----------------
INITIAL_DATA = {   # نفس الداتا متاعك بالتمام
    ...  # 🔥 خليه كما هو بالضبط (نفس اللي بعثته)
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

# ---------------- القوائم ----------------
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

# ---------------- التعامل مع الأزرار ----------------
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

    if section == "sheets" and len(data) == 2:
        rows = [
            [InlineKeyboardButton("📄 شيتات المنهج", callback_data=f"{mat}|sheets|manhaj")],
            [InlineKeyboardButton("📁 شيتات أكاديميا", callback_data=f"{mat}|sheets|academia")],
            [InlineKeyboardButton("⬅️ رجوع", callback_data=mat)]
        ]
        await query.message.reply_text("اختر نوع الشيتات:", reply_markup=InlineKeyboardMarkup(rows))
        return

    if section == "sheets" and len(data) == 3:
        group = data[2]
        await query.message.reply_text("اختر الباب:", reply_markup=InlineKeyboardMarkup(make_babs_buttons(mat, f"sheets|{group}")))
        return

    if section == "sheets" and len(data) == 4:
        group, bab = data[2], data[3]
        content = DATA.get(mat, {}).get("sheets", {}).get(group, {}).get(bab, [])
        rows = [[InlineKeyboardButton(item["title"], url=item["url"])] for item in content] if content else [[InlineKeyboardButton("⚠️ المحتوى غير متوفر", callback_data="noop")]]
        rows.append([InlineKeyboardButton("⬅️ رجوع", callback_data=f"{mat}|sheets")])
        await query.message.reply_text("اختر الملف:", reply_markup=InlineKeyboardMarkup(rows))
        return

    if len(data) == 2 and section in ["shoroh", "exams"]:
        await query.message.reply_text("اختر الباب:", reply_markup=InlineKeyboardMarkup(make_babs_buttons(mat, section)))
        return

    if len(data) == 3 and section in ["shoroh", "exams"]:
        bab = data[2]
        content = DATA.get(mat, {}).get(section, {}).get(bab, [])
        rows = [[InlineKeyboardButton(item["title"], url=item["url"])] for item in content] if content else [[InlineKeyboardButton("⚠️ المحتوى غير متوفر", callback_data="noop")]]
        rows.append([InlineKeyboardButton("⬅️ رجوع", callback_data=f"{mat}|{section}")])
        await query.message.reply_text("اختر الملف:", reply_markup=InlineKeyboardMarkup(rows))
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
