# bot.py
import os
import sqlite3
from datetime import datetime
import telebot
from telebot import types
from dotenv import load_dotenv

# ====== CONFIG ======

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
DB_FILE = os.getenv("DB_FILE", "data.db")
ADMIN_IDS = []

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ====== MESSAGE DICTIONARY (EN / TR / RU) ======
MESSAGES = {
    "choose_language_prompt": {
        "en": "🌐 Choose your language:",
        "tr": "🌐 Dilinizi seçin:",
        "ru": "🌐 Выберите язык:"
    },
    "lang_set_confirm": {
        "en": "✅ Language set!",
        "tr": "✅ Dil seçildi!",
        "ru": "✅ Язык выбран!"
    },
    "start_welcome": {
        "en": ("👋 Welcome — CantaOrtak prototype!\n\n"
               "You can post orders or trips.\n\n"
               "Commands:\n"
               "/post_order - Post an order\n"
               "/post_trip - Post a trip\n"
               "/list - See active listings\n"
               "/profile - Your profile"),
        "tr": ("👋 Hoş geldiniz — CantaOrtak prototipi!\n\n"
               "Sipariş verebilir veya yolculuk ilanı ekleyebilirsiniz.\n\n"
               "Komutlar:\n"
               "/post_order - Sipariş ekle\n"
               "/post_trip - Yolculuk ekle\n"
               "/list - İlanları gör\n"
               "/profile - Profiliniz"),
        "ru": ("👋 Добро пожаловать — прототип CantaOrtak!\n\n"
               "Вы можете разместить заказ или поездку.\n\n"
               "Команды:\n"
               "/post_order - Разместить заказ\n"
               "/post_trip - Разместить поездку\n"
               "/list - Активные объявления\n"
               "/profile - Ваш профиль")
    },
    "profile_not_found": {
        "en": "Profile not found. Use /start to register.",
        "tr": "Profil bulunamadı. Kayıt için /start kullanın.",
        "ru": "Профиль не найден. Для регистрации используйте /start."
    },
    "ask_product": {
        "en": "📦 Enter product name (e.g. iPhone cable):",
        "tr": "📦 Ürün adını yazın (örn: iPhone kablo):",
        "ru": "📦 Введите название товара (например: кабель iPhone):"
    },
    "ask_weight": {
        "en": "⚖️ Enter approximate weight in kg (e.g. 0.3):",
        "tr": "⚖️ Yaklaşık ağırlığı (kg) yazın (örn: 0.3):",
        "ru": "⚖️ Введите приблизительный вес (кг), напр. 0.3:"
    },
    "ask_from": {
        "en": "📍 From which city (e.g. Istanbul):",
        "tr": "📍 Hangi şehirden (örn: İstanbul):",
        "ru": "📍 Из какого города (например: Стамбул):"
    },
    "ask_to": {
        "en": "🏠 To which city (e.g. Lefkoşa):",
        "tr": "🏠 Hangi şehire (örn: Lefkoşa):",
        "ru": "🏠 В какой город (например: Лефкоша):"
    },
    "ask_price": {
        "en": "💰 Enter your offered price (e.g. 10€):",
        "tr": "💰 Teklif ettiğiniz ücreti yazın (örn: 10€):",
        "ru": "💰 Введите вашу цену (например: 10€):"
    },
    "order_posted": {
        "en": "✅ Your order has been posted! Use /list to view.",
        "tr": "✅ Siparişiniz yayınlandı! Görmek için /list kullanın.",
        "ru": "✅ Ваш заказ опубликован! Для просмотра используйте /list."
    },
    "ask_trip_from": {
        "en": "📍 Which city are you departing from?",
        "tr": "📍 Hangi şehirden gidiyorsunuz?",
        "ru": "📍 Из какого города вы отправляетесь?"
    },
    "ask_trip_to": {
        "en": "📍 Which city are you going to?",
        "tr": "📍 Hangi şehire gidiyorsunuz?",
        "ru": "📍 В какой город вы направляетесь?"
    },
    "ask_trip_date": {
        "en": "📅 Enter date (YYYY-MM-DD) or human text (e.g. 2025-10-15):",
        "tr": "📅 Tarih girin (YYYY-AA-GG) veya (örn: 2025-10-15):",
        "ru": "📅 Введите дату (ГГГГ-ММ-ДД), например: 2025-10-15:"
    },
    "ask_trip_capacity": {
        "en": "⚖️ Enter available capacity (kg):",
        "tr": "⚖️ Boş kapasite (kg) yazın:",
        "ru": "⚖️ Введите доступную вместимость (кг):"
    },
    "ask_trip_price": {
        "en": "💵 Enter price (e.g. 2€/kg):",
        "tr": "💵 Fiyat yazın (örn: 2€/kg):",
        "ru": "💵 Укажите цену (напр.: 2€/кг):"
    },
    "trip_posted": {
        "en": "✅ Trip published! Use /list to view.",
        "tr": "✅ Yolculuk ilanınız yayınlandı! /list ile görebilirsiniz.",
        "ru": "✅ Поездка опубликована! Используйте /list для просмотра."
    },
    "list_no_active": {
        "en": "There are no active listings right now.",
        "tr": "Şu anda aktif ilan yok.",
        "ru": "Сейчас активных объявлений нет."
    },
    "list_header": {
        "en": "🔎 Recent listings:",
        "tr": "🔎 Son ilanlar:",
        "ru": "🔎 Последние объявления:"
    },
    "contact_sent_success": {
        "en": "✅ Contact request sent to the owner. They will reply if interested.",
        "tr": "✅ İletişim isteği ilan sahibine gönderildi. Cevap verirse haber alacaksınız.",
        "ru": "✅ Запрос на контакт отправлен владельцу. Если заинтересован — ответит."
    },
    "contact_sent_failed": {
        "en": "❗ Cannot send message to the owner (they might be blocked/offline).",
        "tr": "❗ Sahibine mesaj gönderilemedi (bloklama veya offline olabilir).",
        "ru": "❗ Не удалось отправить сообщение владельцу (возможно, заблокирован/офлайн)."
    }
}

# ====== DB HELPERS ======
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # create users with lang column (if not exists)
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        tg_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        registered_at TEXT,
        lang TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER,
        product TEXT,
        weight REAL,
        from_city TEXT,
        to_city TEXT,
        price TEXT,
        created_at TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS trips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER,
        from_city TEXT,
        to_city TEXT,
        date TEXT,
        capacity_kg REAL,
        price_per_kg TEXT,
        created_at TEXT
    )
    """)
    conn.commit()

    # Migration safety: if users table existed but lacked 'lang', add it
    c.execute("PRAGMA table_info(users)")
    cols = [r[1] for r in c.fetchall()]
    if 'lang' not in cols:
        c.execute("ALTER TABLE users ADD COLUMN lang TEXT")
        conn.commit()

    conn.close()

def db_execute(query, params=(), fetch=False, many=False):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if many:
        c.executemany(query, params)
        conn.commit()
        conn.close()
        return
    c.execute(query, params)
    if fetch:
        rows = c.fetchall()
        conn.close()
        return rows
    conn.commit()
    conn.close()

# ====== LANGUAGE HELPERS ======
def get_lang(user_id):
    row = db_execute("SELECT lang FROM users WHERE tg_id = ?", (user_id,), fetch=True)
    if row and row[0][0]:
        return row[0][0]
    # default language if none set
    return "tr"  # dəyişmək istəsən "en" edə bilərsən

def get_text(key, user_id):
    lang = get_lang(user_id)
    return MESSAGES.get(key, {}).get(lang, MESSAGES.get(key, {}).get("en", ""))

# ====== USER REGISTER ======
def register_user(message):
    tg_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""
    registered_at = datetime.utcnow().isoformat()
    exists = db_execute("SELECT 1 FROM users WHERE tg_id = ?", (tg_id,), fetch=True)
    if not exists:
        # default lang undefined until user chooses; we set default 'tr' here
        db_execute(
            "INSERT INTO users (tg_id, username, first_name, last_name, registered_at, lang) VALUES (?, ?, ?, ?, ?, ?)",
            (tg_id, username, first_name, last_name, registered_at, None)
        )
    else:
        db_execute(
            "UPDATE users SET username = ?, first_name = ?, last_name = ? WHERE tg_id = ?",
            (username, first_name, last_name, tg_id)
        )

# ====== UTIL FORMATTERS (orders/trips) ======
def format_order_row(row):
    oid, tg_id, product, weight, from_city, to_city, price, created_at = row
    text = f"📦 <b>Order #{oid}</b>\n"
    text += f"👤 Owner: <code>{tg_id}</code>\n"
    if from_city and to_city:
        text += f"📍 <b>{from_city}</b> → <b>{to_city}</b>\n"
    text += f"📝 Product: {product}\n⚖️ Weight: {weight} kg\n💰 Price: {price}\n🕒 {created_at.split('T')[0]}"
    return text

def format_trip_row(row):
    tid, tg_id, from_city, to_city, date, capacity_kg, price_per_kg, created_at = row
    text = f"🛄 <b>Trip #{tid}</b>\n"
    text += f"👤 Owner: <code>{tg_id}</code>\n"
    text += f"📍 <b>{from_city}</b> → <b>{to_city}</b>\n📅 Date: {date}\n⚖️ Free: {capacity_kg} kg\n💵 Price: {price_per_kg}\n🕒 {created_at.split('T')[0]}"
    return text

# ====== COMMANDS / HANDLERS ======
@bot.message_handler(commands=['start'])
def cmd_start(message):
    register_user(message)
    # show language selection (multi-language prompt so everyone understands)
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("English 🇬🇧", callback_data="setlang_en"),
        types.InlineKeyboardButton("Türkçe 🇹🇷", callback_data="setlang_tr")
    )
    markup.row(
        types.InlineKeyboardButton("Русский 🇷🇺", callback_data="setlang_ru")
    )
    # Multi-language prompt for first-time comprehension
    prompt = ("🌐 Choose / Dil seçin / Выберите язык:\n\n"
              "English 🇬🇧  — press English\n"
              "Türkçe 🇹🇷  — Türkçe'ye basın\n"
              "Русский 🇷🇺 — нажмите Русский")
    bot.send_message(message.chat.id, prompt, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("setlang_"))
def callback_setlang(call):
    lang = call.data.split("_")[1]
    db_execute("UPDATE users SET lang = ? WHERE tg_id = ?", (lang, call.from_user.id))
    bot.answer_callback_query(call.id, MESSAGES["lang_set_confirm"].get(lang, "✅ Language set!"))
    # send localized start/welcome
    bot.send_message(call.message.chat.id, get_text("start_welcome", call.from_user.id))

@bot.message_handler(commands=['profile'])
def cmd_profile(message):
    register_user(message)
    rows = db_execute("SELECT username, first_name, last_name, registered_at, lang FROM users WHERE tg_id = ?", (message.from_user.id,), fetch=True)
    if not rows:
        bot.reply_to(message, get_text("profile_not_found", message.from_user.id))
        return
    username, first_name, last_name, registered_at, lang = rows[0]
    text = f"👤 Profile:\nName: {first_name} {last_name}\nUsername: @{username if username else 'n/a'}\nRegistered: {registered_at.split('T')[0]}\nLanguage: {lang if lang else 'n/a'}"
    bot.send_message(message.chat.id, text)

# ---- POST ORDER flow ----
@bot.message_handler(commands=['post_order'])
def cmd_post_order(message):
    register_user(message)
    msg = bot.send_message(message.chat.id, get_text("ask_product", message.from_user.id))
    bot.register_next_step_handler(msg, post_order_product)

def post_order_product(message):
    product = message.text.strip()
    msg = bot.send_message(message.chat.id, get_text("ask_weight", message.from_user.id))
    bot.register_next_step_handler(msg, post_order_weight, product)

def post_order_weight(message, product):
    try:
        weight = float(message.text.strip())
    except Exception:
        weight = 0.0
    msg = bot.send_message(message.chat.id, get_text("ask_from", message.from_user.id))
    bot.register_next_step_handler(msg, post_order_from, product, weight)

def post_order_from(message, product, weight):
    from_city = message.text.strip()
    msg = bot.send_message(message.chat.id, get_text("ask_to", message.from_user.id))
    bot.register_next_step_handler(msg, post_order_to, product, weight, from_city)

def post_order_to(message, product, weight, from_city):
    to_city = message.text.strip()
    msg = bot.send_message(message.chat.id, get_text("ask_price", message.from_user.id))
    bot.register_next_step_handler(msg, post_order_price, product, weight, from_city, to_city)

def post_order_price(message, product, weight, from_city, to_city):
    price = message.text.strip()
    created_at = datetime.utcnow().isoformat()
    db_execute(
        "INSERT INTO orders (tg_id, product, weight, from_city, to_city, price, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (message.from_user.id, product, weight, from_city, to_city, price, created_at)
    )
    bot.send_message(message.chat.id, get_text("order_posted", message.from_user.id))

# ---- POST TRIP flow ----
@bot.message_handler(commands=['post_trip'])
def cmd_post_trip(message):
    register_user(message)
    msg = bot.send_message(message.chat.id, get_text("ask_trip_from", message.from_user.id))
    bot.register_next_step_handler(msg, post_trip_from)

def post_trip_from(message):
    from_city = message.text.strip()
    msg = bot.send_message(message.chat.id, get_text("ask_trip_to", message.from_user.id))
    bot.register_next_step_handler(msg, post_trip_to, from_city)

def post_trip_to(message, from_city):
    to_city = message.text.strip()
    msg = bot.send_message(message.chat.id, get_text("ask_trip_date", message.from_user.id))
    bot.register_next_step_handler(msg, post_trip_date, from_city, to_city)

def post_trip_date(message, from_city, to_city):
    date = message.text.strip()
    msg = bot.send_message(message.chat.id, get_text("ask_trip_capacity", message.from_user.id))
    bot.register_next_step_handler(msg, post_trip_capacity, from_city, to_city, date)

def post_trip_capacity(message, from_city, to_city, date):
    try:
        capacity = float(message.text.strip())
    except Exception:
        capacity = 0.0
    msg = bot.send_message(message.chat.id, get_text("ask_trip_price", message.from_user.id))
    bot.register_next_step_handler(msg, post_trip_price, from_city, to_city, date, capacity)

def post_trip_price(message, from_city, to_city, date, capacity):
    price_per_kg = message.text.strip()
    created_at = datetime.utcnow().isoformat()
    db_execute(
        "INSERT INTO trips (tg_id, from_city, to_city, date, capacity_kg, price_per_kg, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (message.from_user.id, from_city, to_city, date, capacity, price_per_kg, created_at)
    )
    bot.send_message(message.chat.id, get_text("trip_posted", message.from_user.id))

# ---- LIST ----
@bot.message_handler(commands=['list'])
def cmd_list(message):
    register_user(message)
    orders = db_execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 10", fetch=True) or []
    trips = db_execute("SELECT * FROM trips ORDER BY created_at DESC LIMIT 10", fetch=True) or []

    if not orders and not trips:
        bot.send_message(message.chat.id, get_text("list_no_active", message.from_user.id))
        return

    bot.send_message(message.chat.id, get_text("list_header", message.from_user.id))

    for row in orders:
        text = format_order_row(row)
        order_id = row[0]
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="📩 Contact owner", callback_data=f"contact_order_{order_id}"))
        bot.send_message(message.chat.id, text, reply_markup=markup)

    for row in trips:
        text = format_trip_row(row)
        trip_id = row[0]
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="📩 Contact owner", callback_data=f"contact_trip_{trip_id}"))
        bot.send_message(message.chat.id, text, reply_markup=markup)

# ---- CALLBACK contact handlers ----
@bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("contact_"))
def callback_contact(call):
    data = call.data
    parts = data.split("_")
    kind = parts[1]
    item_id = int(parts[2])

    requester = call.from_user
    requester_info = f"{requester.first_name or ''} {requester.last_name or ''}".strip()
    requester_username = requester.username or "(no username)"

    # determine user's language to send localized feedback
    user_lang = get_lang(call.from_user.id)

    if kind == "order":
        rows = db_execute("SELECT tg_id, product FROM orders WHERE id = ?", (item_id,), fetch=True)
        if not rows:
            bot.answer_callback_query(call.id, "Listing not found.")
            return
        owner_tg, product = rows[0]
        text_to_owner = (
            f"📩 Your <b>Order #{item_id}</b> has a contact request.\n\n"
            f"Requester: {requester_info}\nUsername: @{requester_username}\n\n"
            f"Product: {product}\n\nRespond if you want to proceed."
        )
        try:
            bot.send_message(owner_tg, text_to_owner)
            bot.answer_callback_query(call.id, MESSAGES["contact_sent_success"].get(user_lang))
            bot.send_message(call.message.chat.id, MESSAGES["contact_sent_success"].get(user_lang))
        except Exception:
            bot.answer_callback_query(call.id, MESSAGES["contact_sent_failed"].get(user_lang))
            bot.send_message(call.message.chat.id, MESSAGES["contact_sent_failed"].get(user_lang))
    elif kind == "trip":
        rows = db_execute("SELECT tg_id, from_city, to_city, date FROM trips WHERE id = ?", (item_id,), fetch=True)
        if not rows:
            bot.answer_callback_query(call.id, "Listing not found.")
            return
        owner_tg, from_city, to_city, date = rows[0]
        text_to_owner = (
            f"📩 Your <b>Trip #{item_id}</b> has a contact request.\n\n"
            f"Requester: {requester_info}\nUsername: @{requester_username}\n"
            f"Route: {from_city} → {to_city} (Date: {date})\n\nRespond if you want to proceed."
        )
        try:
            bot.send_message(owner_tg, text_to_owner)
            bot.answer_callback_query(call.id, MESSAGES["contact_sent_success"].get(user_lang))
            bot.send_message(call.message.chat.id, MESSAGES["contact_sent_success"].get(user_lang))
        except Exception:
            bot.answer_callback_query(call.id, MESSAGES["contact_sent_failed"].get(user_lang))
            bot.send_message(call.message.chat.id, MESSAGES["contact_sent_failed"].get(user_lang))
    else:
        bot.answer_callback_query(call.id, "Error.")

# ---- ADMIN (optional) ----
@bot.message_handler(commands=['all_orders'])
def cmd_all_orders(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "Not admin.")
        return
    rows = db_execute("SELECT * FROM orders ORDER BY created_at DESC", fetch=True) or []
    for row in rows:
        bot.send_message(message.chat.id, format_order_row(row))

@bot.message_handler(commands=['all_trips'])
def cmd_all_trips(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "Not admin.")
        return
    rows = db_execute("SELECT * FROM trips ORDER BY created_at DESC", fetch=True) or []
    for row in rows:
        bot.send_message(message.chat.id, format_trip_row(row))

# ====== START ======
if __name__ == "__main__":
    print("Initializing DB...")
    init_db()
    print("Bot started...")
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except KeyboardInterrupt:
        print("Bot stopped by user.")
