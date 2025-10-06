# bot.py
import os
import sqlite3
from datetime import datetime, timedelta
import telebot
from telebot import types
from dotenv import load_dotenv
import threading
import time

# ====== CONFIG ======

load_dotenv()

TOKEN = os.getenv("TOKEN") or os.getenv("BOT_TOKEN")
DB_FILE = os.getenv("DB_FILE", "data.db")
ADMIN_IDS = []
# Varsayılan ilan süresi (gün)
DEFAULT_LISTING_EXPIRY_DAYS = int(os.getenv("DEFAULT_LISTING_EXPIRY_DAYS", "7"))

if not TOKEN:
    raise Exception("TOKEN bulunamadı! Railway Variables kısmını kontrol et.")

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
               "/profile - Your profile\n"
               "/my_listings - Your active listings"),
        "tr": ("👋 Hoş geldiniz — CantaOrtak prototipi!\n\n"
               "Sipariş verebilir veya yolculuk ilanı ekleyebilirsiniz.\n\n"
               "Komutlar:\n"
               "/post_order - Sipariş ekle\n"
               "/post_trip - Yolculuk ekle\n"
               "/list - İlanları gör\n"
               "/profile - Profiliniz\n"
               "/my_listings - Aktif ilanlarınız"),
        "ru": ("👋 Добро пожаловать — прототип CantaOrtak!\n\n"
               "Вы можете разместить заказ или поездку.\n\n"
               "Команды:\n"
               "/post_order - Разместить заказ\n"
               "/post_trip - Разместить поездку\n"
               "/list - Активные объявления\n"
               "/profile - Ваш профиль\n"
               "/my_listings - Ваши активные объявления")
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
    "ask_order_expiry": {
        "en": "📅 Until when is this order valid? (YYYY-MM-DD, e.g. 2024-12-31) or number of days (e.g. 7):",
        "tr": "📅 Bu sipariş ne zamana kadar geçerli? (YYYY-AA-GG, örn: 2024-12-31) veya gün sayısı (örn: 7):",
        "ru": "📅 До какого числа действует этот заказ? (ГГГГ-ММ-ДД, напр. 2024-12-31) или количество дней (напр. 7):"
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
        "en": "📅 Enter trip date (YYYY-MM-DD) when you will travel (e.g. 2024-12-25):",
        "tr": "📅 Seyahat tarihini girin (YYYY-AA-GG) (örn: 2024-12-25):",
        "ru": "📅 Введите дату поездки (ГГГГ-ММ-ДД), когда вы будете путешествовать (напр. 2024-12-25):"
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
    },
    "command_intercepted": {
        "en": "⚠️ Command detected! If you want to answer the previous question, please send a normal message without '/'.",
        "tr": "⚠️ Komut algılandı! Önceki soruyu yanıtlamak istiyorsanız, lütfen '/' olmadan normal mesaj gönderin.",
        "ru": "⚠️ Обнаружена команда! Если хотите ответить на предыдущий вопрос, отправьте обычное сообщение без '/'."
    },
    "invalid_date": {
        "en": "❌ Invalid date format. Please use YYYY-MM-DD format or number of days.",
        "tr": "❌ Geçersiz tarih formatı. Lütfen YYYY-AA-GG formatında veya gün sayısı girin.",
        "ru": "❌ Неверный формат даты. Используйте формат ГГГГ-ММ-ДД или количество дней."
    },
    "date_in_past": {
        "en": "❌ Date cannot be in the past. Please enter a future date.",
        "tr": "❌ Tarih geçmişte olamaz. Lütfen gelecek bir tarih girin.",
        "ru": "❌ Дата не может быть в прошлом. Введите будущую дату."
    },
    "my_listings_header": {
        "en": "📋 Your active listings:",
        "tr": "📋 Aktif ilanlarınız:",
        "ru": "📋 Ваши активные объявления:"
    },
    "no_active_listings": {
        "en": "You have no active listings.",
        "tr": "Hiç aktif ilanınız yok.",
        "ru": "У вас нет активных объявлений."
    },
    "listing_deactivated": {
        "en": "✅ Listing has been deactivated.",
        "tr": "✅ İlan devre dışı bırakıldı.",
        "ru": "✅ Объявление деактивировано."
    },
    "not_listing_owner": {
        "en": "❌ You are not the owner of this listing.",
        "tr": "❌ Bu ilanın sahibi siz değilsiniz.",
        "ru": "❌ Вы не владелец этого объявления."
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
        created_at TEXT,
        expires_at TEXT,
        is_active BOOLEAN DEFAULT 1
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
        created_at TEXT,
        expires_at TEXT,
        is_active BOOLEAN DEFAULT 1
    )
    """)
    # User states için tablo (komut algılama için)
    c.execute("""
    CREATE TABLE IF NOT EXISTS user_states (
        user_id INTEGER PRIMARY KEY,
        state TEXT,
        data TEXT,
        updated_at TEXT
    )
    """)
    conn.commit()

    # Migration safety: if users table existed but lacked 'lang', add it
    c.execute("PRAGMA table_info(users)")
    cols = [r[1] for r in c.fetchall()]
    if 'lang' not in cols:
        c.execute("ALTER TABLE users ADD COLUMN lang TEXT")
        conn.commit()
    
    # Migration: orders ve trips tablolarına expires_at ve is_active ekle
    c.execute("PRAGMA table_info(orders)")
    cols = [r[1] for r in c.fetchall()]
    if 'expires_at' not in cols:
        c.execute("ALTER TABLE orders ADD COLUMN expires_at TEXT")
        c.execute("ALTER TABLE orders ADD COLUMN is_active BOOLEAN DEFAULT 1")
        # Mevcut kayıtlar için expires_at değeri ata
        c.execute("UPDATE orders SET expires_at = datetime(created_at, '+' || ? || ' days')", (DEFAULT_LISTING_EXPIRY_DAYS,))
        conn.commit()
    
    c.execute("PRAGMA table_info(trips)")
    cols = [r[1] for r in c.fetchall()]
    if 'expires_at' not in cols:
        c.execute("ALTER TABLE trips ADD COLUMN expires_at TEXT")
        c.execute("ALTER TABLE trips ADD COLUMN is_active BOOLEAN DEFAULT 1")
        # Mevcut kayıtlar için expires_at değeri ata
        c.execute("UPDATE trips SET expires_at = datetime(created_at, '+' || ? || ' days')", (DEFAULT_LISTING_EXPIRY_DAYS,))
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

# ====== DATE HELPER FUNCTIONS ======
def parse_date_input(date_input, user_lang="tr"):
    """Kullanıcının tarih girdisini parse eder"""
    try:
        # Eğer sayı ise (gün sayısı)
        if date_input.isdigit():
            days = int(date_input)
            if days <= 0:
                return None, MESSAGES["date_in_past"].get(user_lang)
            return datetime.utcnow() + timedelta(days=days), None
        
        # Tarih formatı ise (YYYY-MM-DD)
        date_obj = datetime.strptime(date_input, "%Y-%m-%d")
        if date_obj.date() < datetime.utcnow().date():
            return None, MESSAGES["date_in_past"].get(user_lang)
        return date_obj, None
        
    except ValueError:
        return None, MESSAGES["invalid_date"].get(user_lang)

def calculate_trip_expiry(trip_date_str):
    """Seyahat tarihine göre expiry hesaplar (seyahat tarihi + 1 gün)"""
    try:
        trip_date = datetime.strptime(trip_date_str, "%Y-%m-%d")
        # Seyahat tarihinden sonraki günün başlangıcı
        expiry_date = trip_date + timedelta(days=1)
        return expiry_date
    except ValueError:
        # Geçersiz tarih durumunda varsayılan süre
        return datetime.utcnow() + timedelta(days=DEFAULT_LISTING_EXPIRY_DAYS)

# ====== USER STATE MANAGEMENT ======
def set_user_state(user_id, state, data=None):
    """Kullanıcının mevcut durumunu kaydeder"""
    updated_at = datetime.utcnow().isoformat()
    db_execute(
        "INSERT OR REPLACE INTO user_states (user_id, state, data, updated_at) VALUES (?, ?, ?, ?)",
        (user_id, state, data, updated_at)
    )

def get_user_state(user_id):
    """Kullanıcının mevcut durumunu getirir"""
    row = db_execute("SELECT state, data FROM user_states WHERE user_id = ?", (user_id,), fetch=True)
    if row:
        return row[0][0], row[0][1]
    return None, None

def clear_user_state(user_id):
    """Kullanıcının durumunu temizler"""
    db_execute("DELETE FROM user_states WHERE user_id = ?", (user_id,))

# ====== EXPIRED LISTINGS CLEANUP ======
def cleanup_expired_listings():
    """Süresi dolmuş veya seyahat tarihi geçmiş ilanları temizler"""
    now = datetime.utcnow().isoformat()
    
    # Orders temizleme (expires_at geçmiş ve aktif olanlar)
    expired_orders = db_execute(
        "SELECT id FROM orders WHERE expires_at < ? AND is_active = 1", 
        (now,), 
        fetch=True
    )
    if expired_orders:
        db_execute("UPDATE orders SET is_active = 0 WHERE expires_at < ? AND is_active = 1", (now,))
        print(f"✅ Deactivated {len(expired_orders)} expired orders")
    
    # Trips temizleme (expires_at geçmiş ve aktif olanlar)
    expired_trips = db_execute(
        "SELECT id FROM trips WHERE expires_at < ? AND is_active = 1", 
        (now,), 
        fetch=True
    )
    if expired_trips:
        db_execute("UPDATE trips SET is_active = 0 WHERE expires_at < ? AND is_active = 1", (now,))
        print(f"✅ Deactivated {len(expired_trips)} expired trips")

def auto_cleanup_worker():
    """Her gün otomatik temizleme yapar"""
    while True:
        try:
            cleanup_expired_listings()
            # 24 saat bekle
            time.sleep(24 * 60 * 60)
        except Exception as e:
            print(f"❌ Cleanup error: {e}")
            time.sleep(60 * 60)  # 1 saat sonra tekrar dene

# ====== COMMAND DETECTION MIDDLEWARE ======
def is_command(message):
    """Mesajın komut olup olmadığını kontrol eder"""
    return (message.text and 
            (message.text.startswith('/') or 
             message.text in ['/start', '/post_order', '/post_trip', '/list', '/profile', '/all_orders', '/all_trips', '/my_listings']))

# ====== LANGUAGE HELPERS ======
def get_lang(user_id):
    row = db_execute("SELECT lang FROM users WHERE tg_id = ?", (user_id,), fetch=True)
    if row and row[0][0]:
        return row[0][0]
    return "tr"

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
def format_order_row(row, show_controls=False, user_id=None):
    oid, tg_id, product, weight, from_city, to_city, price, created_at, expires_at, is_active = row
    status = "✅ Active" if is_active else "❌ Inactive"
    text = f"📦 <b>Order #{oid}</b> - {status}\n"
    text += f"👤 Owner: <code>{tg_id}</code>\n"
    if from_city and to_city:
        text += f"📍 <b>{from_city}</b> → <b>{to_city}</b>\n"
    text += f"📝 Product: {product}\n⚖️ Weight: {weight} kg\n💰 Price: {price}\n🕒 Created: {created_at.split('T')[0]}\n⏰ Expires: {expires_at.split('T')[0]}"
    
    return text

def format_trip_row(row, show_controls=False, user_id=None):
    tid, tg_id, from_city, to_city, date, capacity_kg, price_per_kg, created_at, expires_at, is_active = row
    status = "✅ Active" if is_active else "❌ Inactive"
    text = f"🛄 <b>Trip #{tid}</b> - {status}\n"
    text += f"👤 Owner: <code>{tg_id}</code>\n"
    text += f"📍 <b>{from_city}</b> → <b>{to_city}</b>\n📅 Trip Date: {date}\n⚖️ Free: {capacity_kg} kg\n💵 Price: {price_per_kg}\n🕒 Created: {created_at.split('T')[0]}\n⏰ Expires: {expires_at.split('T')[0]}"
    
    return text

# ====== COMMANDS / HANDLERS ======
@bot.message_handler(commands=['start'])
def cmd_start(message):
    register_user(message)
    clear_user_state(message.from_user.id)
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("English 🇬🇧", callback_data="setlang_en"),
        types.InlineKeyboardButton("Türkçe 🇹🇷", callback_data="setlang_tr")
    )
    markup.row(
        types.InlineKeyboardButton("Русский 🇷🇺", callback_data="setlang_ru")
    )
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
    bot.send_message(call.message.chat.id, get_text("start_welcome", call.from_user.id))

# ---- POST ORDER flow ----
@bot.message_handler(commands=['post_order'])
def cmd_post_order(message):
    register_user(message)
    clear_user_state(message.from_user.id)
    set_user_state(message.from_user.id, "waiting_product")
    msg = bot.send_message(message.chat.id, get_text("ask_product", message.from_user.id))
    bot.register_next_step_handler(msg, post_order_product)

def post_order_product(message):
    if is_command(message):
        bot.send_message(message.chat.id, get_text("command_intercepted", message.from_user.id))
        clear_user_state(message.from_user.id)
        return
        
    product = message.text.strip()
    set_user_state(message.from_user.id, "waiting_weight", product)
    msg = bot.send_message(message.chat.id, get_text("ask_weight", message.from_user.id))
    bot.register_next_step_handler(msg, post_order_weight, product)

def post_order_weight(message, product):
    if is_command(message):
        bot.send_message(message.chat.id, get_text("command_intercepted", message.from_user.id))
        clear_user_state(message.from_user.id)
        return
        
    try:
        weight = float(message.text.strip())
    except Exception:
        weight = 0.0
    set_user_state(message.from_user.id, "waiting_from_city", f"{product}|{weight}")
    msg = bot.send_message(message.chat.id, get_text("ask_from", message.from_user.id))
    bot.register_next_step_handler(msg, post_order_from, product, weight)

def post_order_from(message, product, weight):
    if is_command(message):
        bot.send_message(message.chat.id, get_text("command_intercepted", message.from_user.id))
        clear_user_state(message.from_user.id)
        return
        
    from_city = message.text.strip()
    set_user_state(message.from_user.id, "waiting_to_city", f"{product}|{weight}|{from_city}")
    msg = bot.send_message(message.chat.id, get_text("ask_to", message.from_user.id))
    bot.register_next_step_handler(msg, post_order_to, product, weight, from_city)

def post_order_to(message, product, weight, from_city):
    if is_command(message):
        bot.send_message(message.chat.id, get_text("command_intercepted", message.from_user.id))
        clear_user_state(message.from_user.id)
        return
        
    to_city = message.text.strip()
    set_user_state(message.from_user.id, "waiting_price", f"{product}|{weight}|{from_city}|{to_city}")
    msg = bot.send_message(message.chat.id, get_text("ask_price", message.from_user.id))
    bot.register_next_step_handler(msg, post_order_price, product, weight, from_city, to_city)

def post_order_price(message, product, weight, from_city, to_city):
    if is_command(message):
        bot.send_message(message.chat.id, get_text("command_intercepted", message.from_user.id))
        clear_user_state(message.from_user.id)
        return
        
    price = message.text.strip()
    set_user_state(message.from_user.id, "waiting_order_expiry", f"{product}|{weight}|{from_city}|{to_city}|{price}")
    msg = bot.send_message(message.chat.id, get_text("ask_order_expiry", message.from_user.id))
    bot.register_next_step_handler(msg, post_order_expiry, product, weight, from_city, to_city, price)

def post_order_expiry(message, product, weight, from_city, to_city, price):
    if is_command(message):
        bot.send_message(message.chat.id, get_text("command_intercepted", message.from_user.id))
        clear_user_state(message.from_user.id)
        return
        
    expiry_input = message.text.strip()
    user_lang = get_lang(message.from_user.id)
    
    expiry_date, error = parse_date_input(expiry_input, user_lang)
    if error:
        msg = bot.send_message(message.chat.id, error)
        bot.register_next_step_handler(msg, post_order_expiry, product, weight, from_city, to_city, price)
        return
    
    created_at = datetime.utcnow().isoformat()
    expires_at = expiry_date.isoformat()
    
    db_execute(
        "INSERT INTO orders (tg_id, product, weight, from_city, to_city, price, created_at, expires_at, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (message.from_user.id, product, weight, from_city, to_city, price, created_at, expires_at, 1)
    )
    clear_user_state(message.from_user.id)
    bot.send_message(message.chat.id, get_text("order_posted", message.from_user.id))

# ---- POST TRIP flow ----
@bot.message_handler(commands=['post_trip'])
def cmd_post_trip(message):
    register_user(message)
    clear_user_state(message.from_user.id)
    set_user_state(message.from_user.id, "waiting_trip_from")
    msg = bot.send_message(message.chat.id, get_text("ask_trip_from", message.from_user.id))
    bot.register_next_step_handler(msg, post_trip_from)

def post_trip_from(message):
    if is_command(message):
        bot.send_message(message.chat.id, get_text("command_intercepted", message.from_user.id))
        clear_user_state(message.from_user.id)
        return
        
    from_city = message.text.strip()
    set_user_state(message.from_user.id, "waiting_trip_to", from_city)
    msg = bot.send_message(message.chat.id, get_text("ask_trip_to", message.from_user.id))
    bot.register_next_step_handler(msg, post_trip_to, from_city)

def post_trip_to(message, from_city):
    if is_command(message):
        bot.send_message(message.chat.id, get_text("command_intercepted", message.from_user.id))
        clear_user_state(message.from_user.id)
        return
        
    to_city = message.text.strip()
    set_user_state(message.from_user.id, "waiting_trip_date", f"{from_city}|{to_city}")
    msg = bot.send_message(message.chat.id, get_text("ask_trip_date", message.from_user.id))
    bot.register_next_step_handler(msg, post_trip_date, from_city, to_city)

def post_trip_date(message, from_city, to_city):
    if is_command(message):
        bot.send_message(message.chat.id, get_text("command_intercepted", message.from_user.id))
        clear_user_state(message.from_user.id)
        return
        
    trip_date_input = message.text.strip()
    user_lang = get_lang(message.from_user.id)
    
    try:
        trip_date = datetime.strptime(trip_date_input, "%Y-%m-%d")
        if trip_date.date() < datetime.utcnow().date():
            msg = bot.send_message(message.chat.id, MESSAGES["date_in_past"].get(user_lang))
            bot.register_next_step_handler(msg, post_trip_date, from_city, to_city)
            return
    except ValueError:
        msg = bot.send_message(message.chat.id, MESSAGES["invalid_date"].get(user_lang))
        bot.register_next_step_handler(msg, post_trip_date, from_city, to_city)
        return
    
    trip_date_str = trip_date_input
    set_user_state(message.from_user.id, "waiting_trip_capacity", f"{from_city}|{to_city}|{trip_date_str}")
    msg = bot.send_message(message.chat.id, get_text("ask_trip_capacity", message.from_user.id))
    bot.register_next_step_handler(msg, post_trip_capacity, from_city, to_city, trip_date_str)

def post_trip_capacity(message, from_city, to_city, trip_date):
    if is_command(message):
        bot.send_message(message.chat.id, get_text("command_intercepted", message.from_user.id))
        clear_user_state(message.from_user.id)
        return
        
    try:
        capacity = float(message.text.strip())
    except Exception:
        capacity = 0.0
    set_user_state(message.from_user.id, "waiting_trip_price", f"{from_city}|{to_city}|{trip_date}|{capacity}")
    msg = bot.send_message(message.chat.id, get_text("ask_trip_price", message.from_user.id))
    bot.register_next_step_handler(msg, post_trip_price, from_city, to_city, trip_date, capacity)

def post_trip_price(message, from_city, to_city, trip_date, capacity):
    if is_command(message):
        bot.send_message(message.chat.id, get_text("command_intercepted", message.from_user.id))
        clear_user_state(message.from_user.id)
        return
        
    price_per_kg = message.text.strip()
    created_at = datetime.utcnow().isoformat()
    # Seyahat tarihinden sonraki gün expire edilecek
    expires_at = calculate_trip_expiry(trip_date).isoformat()
    
    db_execute(
        "INSERT INTO trips (tg_id, from_city, to_city, date, capacity_kg, price_per_kg, created_at, expires_at, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (message.from_user.id, from_city, to_city, trip_date, capacity, price_per_kg, created_at, expires_at, 1)
    )
    clear_user_state(message.from_user.id)
    bot.send_message(message.chat.id, get_text("trip_posted", message.from_user.id))

# ---- LIST ----
@bot.message_handler(commands=['list'])
def cmd_list(message):
    register_user(message)
    clear_user_state(message.from_user.id)
    
    now = datetime.utcnow().isoformat()
    orders = db_execute(
        "SELECT * FROM orders WHERE expires_at > ? AND is_active = 1 ORDER BY created_at DESC LIMIT 10", 
        (now,), 
        fetch=True
    ) or []
    trips = db_execute(
        "SELECT * FROM trips WHERE expires_at > ? AND is_active = 1 ORDER BY created_at DESC LIMIT 10", 
        (now,), 
        fetch=True
    ) or []

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

# ---- MY LISTINGS ----
@bot.message_handler(commands=['my_listings'])
def cmd_my_listings(message):
    register_user(message)
    clear_user_state(message.from_user.id)
    
    user_id = message.from_user.id
    now = datetime.utcnow().isoformat()
    
    # Aktif order'lar
    orders = db_execute(
        "SELECT * FROM orders WHERE tg_id = ? AND expires_at > ? AND is_active = 1 ORDER BY created_at DESC", 
        (user_id, now), 
        fetch=True
    ) or []
    
    # Aktif trip'ler
    trips = db_execute(
        "SELECT * FROM trips WHERE tg_id = ? AND expires_at > ? AND is_active = 1 ORDER BY created_at DESC", 
        (user_id, now), 
        fetch=True
    ) or []

    if not orders and not trips:
        bot.send_message(message.chat.id, get_text("no_active_listings", user_id))
        return

    bot.send_message(message.chat.id, get_text("my_listings_header", user_id))

    # Order'ları göster
    for row in orders:
        text = format_order_row(row, show_controls=True, user_id=user_id)
        order_id = row[0]
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="❌ Deactivate", callback_data=f"deactivate_order_{order_id}"))
        bot.send_message(message.chat.id, text, reply_markup=markup)

    # Trip'leri göster
    for row in trips:
        text = format_trip_row(row, show_controls=True, user_id=user_id)
        trip_id = row[0]
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="❌ Deactivate", callback_data=f"deactivate_trip_{trip_id}"))
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

    user_lang = get_lang(call.from_user.id)

    if kind == "order":
        rows = db_execute("SELECT tg_id, product FROM orders WHERE id = ? AND is_active = 1", (item_id,), fetch=True)
        if not rows:
            bot.answer_callback_query(call.id, "Listing not found or inactive.")
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
        except Exception:
            bot.answer_callback_query(call.id, MESSAGES["contact_sent_failed"].get(user_lang))
    elif kind == "trip":
        rows = db_execute("SELECT tg_id, from_city, to_city, date FROM trips WHERE id = ? AND is_active = 1", (item_id,), fetch=True)
        if not rows:
            bot.answer_callback_query(call.id, "Listing not found or inactive.")
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
        except Exception:
            bot.answer_callback_query(call.id, MESSAGES["contact_sent_failed"].get(user_lang))
    else:
        bot.answer_callback_query(call.id, "Error.")

# ---- DEACTIVATE LISTING HANDLER ----
@bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("deactivate_"))
def callback_deactivate(call):
    data = call.data
    parts = data.split("_")
    kind = parts[1]
    item_id = int(parts[2])
    
    user_id = call.from_user.id
    user_lang = get_lang(user_id)
    
    if kind == "order":
        # İlan sahibi kontrolü
        rows = db_execute("SELECT tg_id FROM orders WHERE id = ?", (item_id,), fetch=True)
        if not rows:
            bot.answer_callback_query(call.id, "Listing not found.")
            return
        
        owner_id = rows[0][0]
        if owner_id != user_id:
            bot.answer_callback_query(call.id, MESSAGES["not_listing_owner"].get(user_lang))
            return
        
        # İlanı deaktive et
        db_execute("UPDATE orders SET is_active = 0 WHERE id = ?", (item_id,))
        bot.answer_callback_query(call.id, MESSAGES["listing_deactivated"].get(user_lang))
        # Mesajı güncelle
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            bot.send_message(call.message.chat.id, MESSAGES["listing_deactivated"].get(user_lang))
        except:
            pass
            
    elif kind == "trip":
        # İlan sahibi kontrolü
        rows = db_execute("SELECT tg_id FROM trips WHERE id = ?", (item_id,), fetch=True)
        if not rows:
            bot.answer_callback_query(call.id, "Listing not found.")
            return
        
        owner_id = rows[0][0]
        if owner_id != user_id:
            bot.answer_callback_query(call.id, MESSAGES["not_listing_owner"].get(user_lang))
            return
        
        # İlanı deaktive et
        db_execute("UPDATE trips SET is_active = 0 WHERE id = ?", (item_id,))
        bot.answer_callback_query(call.id, MESSAGES["listing_deactivated"].get(user_lang))
        # Mesajı güncelle
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            bot.send_message(call.message.chat.id, MESSAGES["listing_deactivated"].get(user_lang))
        except:
            pass

# ---- ADMIN COMMANDS ----
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

# ---- COMMAND INTERCEPTION HANDLER ----
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Tüm mesajları kontrol eder ve state varsa komutları yakalar"""
    user_id = message.from_user.id
    state, data = get_user_state(user_id)
    
    if state and is_command(message):
        bot.send_message(message.chat.id, get_text("command_intercepted", user_id))
        return
    
    if not state and not is_command(message):
        bot.reply_to(message, "❌ Unknown command. Use /start to see available commands.")

# ====== START ======
if __name__ == "__main__":
    print("Initializing DB...")
    init_db()
    
    print("Cleaning up expired listings...")
    cleanup_expired_listings()
    
    # Otomatik temizleme thread'ini başlat
    cleanup_thread = threading.Thread(target=auto_cleanup_worker, daemon=True)
    cleanup_thread.start()
    print("Auto-cleanup thread started...")
    
    print("Bot started...")
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except KeyboardInterrupt:
        print("Bot stopped by user.")