import asyncio

# ================= PYROGRAM ASYNCIO FIX (FOR NEWER PYTHON VERSIONS) =================
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())
# ====================================================================================

import datetime
import random
import html
import time
import re
from pyrogram import Client, filters, idle
from pyrogram.types import Message, CallbackQuery, ChatJoinRequest, BotCommand, ChatPermissions
from pyrogram.enums import ParseMode
from motor.motor_asyncio import AsyncIOMotorClient
import aiohttp
import dns.resolver
from aiohttp import web
import os

# ================= PYDROID 3 / ANDROID DNS FIX =================
dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8', '8.8.4.4']

# ================= CONFIGURATION =================
BOT_TOKEN = "9102679894:AAGSBkanKV8nmTEmWgNL6Aht-LvpdOBAC1U"
API_ID = 35831190  
API_HASH = "f625657330797a7f149855cbdfcf9dae"
MONGO_URI = "mongodb+srv://Cricket_231:Rohit1616%40@zolmdho.mongodb.net/?appName=Cluster0" 
OWNER_ID = 7691071175 
TRACK_GROUP_ID = -1003946482336  
REQUIRED_USERNAME_TAG = "@redcube"
FSUB_CHANNEL = "@redcube_en"  
GROUP_INVITE_LINK = "https://t.me/+rdKCTKOlxUE1Mjc8"
BANNED_PROMOS = ["@dices", "@raika", "@booplay", "@Axoms", "@giftsggapp", "@royaldices"]

# ================= HTTP SESSION (For Fast API Calls) =================
HTTP_SESSION: aiohttp.ClientSession | None = None

async def get_session() -> aiohttp.ClientSession:
    global HTTP_SESSION
    if HTTP_SESSION is None or HTTP_SESSION.closed:
        connector = aiohttp.TCPConnector(limit=150, ttl_dns_cache=300)
        timeout = aiohttp.ClientTimeout(total=20, connect=8)
        HTTP_SESSION = aiohttp.ClientSession(connector=connector, timeout=timeout)
    return HTTP_SESSION

# Raw API Caller like bot_native.py (Prevents Pyrogram Stuck Issues)
async def tg(method: str, retries: int = 2, **params):
    clean = {k: v for k, v in params.items() if v is not None}
    base = f"https://api.telegram.org/bot{BOT_TOKEN}/"
    req_timeout = 12
    for attempt in range(retries + 1):
        try:
            s = await get_session()
            async with s.post(base + method, json=clean, timeout=req_timeout) as r:
                res = await r.json()
            if res.get("ok"): return res["result"]
            retry_after = res.get("parameters", {}).get("retry_after")
            if retry_after and attempt < retries:
                await asyncio.sleep(min(float(retry_after), 5.0))
                continue
            raise RuntimeError(res.get("description", str(res)))
        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            if attempt < retries:
                await asyncio.sleep(0.4)
                continue
            raise RuntimeError(f"Network timeout on {method}: {e}")

# ================= PREMIUM EMOJIS DATA =================
PREMIUM_EMOJIS = {
    "✅": "5123248930124989216", "❌": "5893197207493939355", "⚠️": "5420323339723881652",
    "💰": "5893473283696759404", "⛓️": "6021344879689341042", "📊": "5895444149699612825",
    "👥": "6021690418398239007", "🤖": "5931415565955503486", "💡": "6023897907034330805",
    "🎟": "6021617983774791539", "👨‍💻": "5444965061749644170", "🔐": "6019568309417023812",
    "🎉": "6023579259115674297", "⏱": "6034973034257848185", "🎁": "6023826881160157558",
    "🏆": "6021644067111180663", "📅": "6023880246128810031", "🛡": "6019328362479097179",
    "👑": "6021428854889913572", "📈": "5938539885907415367", "✏️": "5879841310902324730",
    "🏦": "5332455502917949981", "📍": "6023989024765516223", "🆕": "5886306834410640699",
    "👋": "5247133031235329609", "🌐": "6019205852831947754", "➡️": "5807462045288766810",
    "🇬🇧": "5395560546865013953", "🇷🇺": "5267224089382116952", "🇮🇳": "6129782715035163979",
    "💎": "5298988357538328017", "🏠": "5258503720928288433", "📢": "5938589252328624108",
    "🔙": "5255703720078879038", "💧": "5334757303667232230", "🌧": "5393512611968995988",
    "⛈": "5224257782013769471", "🌩": "5089144476023128742", "🌨": "5839380464116175529",
    "🌦": "5258362837411045098", "☔": "5348289410955754971", "💬": "5895713430584690466"
}

def pe(emoji_char: str) -> str:
    eid = PREMIUM_EMOJIS.get(emoji_char)
    if eid: return f'<tg-emoji emoji-id="{eid}">{emoji_char}</tg-emoji>'
    return emoji_char

# ================= BUTTON & KEYBOARD GENERATORS =================
def btn(text: str, data: str = None, style: str = None, url: str = None, icon: str = None) -> dict:
    b = {"text": str(text)} 
    if url: b["url"] = str(url)
    else: b["callback_data"] = str(data) if data else "noop"
    if style: b["style"] = style
    if icon and icon in PREMIUM_EMOJIS: b["icon_custom_emoji_id"] = PREMIUM_EMOJIS[icon]
    return b

def kb(*rows) -> dict:
    board = []
    for row in rows:
        r = []
        for item in row:
            if isinstance(item, dict): r.append(item)
            elif len(item) >= 4: r.append(btn(item[0], item[1], style=item[2], icon=item[3]))
            elif len(item) == 3: r.append(btn(item[0], item[1], style=item[2]))
            elif len(item) == 2: r.append(btn(item[0], item[1]))
            elif len(item) == 1: r.append(btn(item[0], item[0]))
        if r: board.append(r)
    return {"inline_keyboard": board}

async def send_msg(chat_id: int, text: str, markup=None, parse_mode="HTML", reply_to: int = None, disable_web_page_preview=True):
    try:
        return await tg("sendMessage", chat_id=chat_id, text=text, reply_markup=markup, parse_mode=parse_mode, reply_to_message_id=reply_to, disable_web_page_preview=disable_web_page_preview)
    except Exception:
        pass

async def edit_msg(chat_id: int, message_id: int, text: str, markup=None, parse_mode="HTML", disable_web_page_preview=True):
    try:
        return await tg("editMessageText", chat_id=chat_id, message_id=message_id, text=text, reply_markup=markup, parse_mode=parse_mode, disable_web_page_preview=disable_web_page_preview)
    except Exception as e:
        if "not modified" in str(e).lower():
            return None # Ignore silent errors when clicking the same active button
        return await send_msg(chat_id, text, markup=markup, parse_mode=parse_mode, disable_web_page_preview=disable_web_page_preview)

# ================= INITIALIZATION =================
app = Client("my_advanc9768e6d_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

client = AsyncIOMotorClient(MONGO_URI, maxPoolSize=50)
db = client['Advanced56BotDB']
users_db = db['users']
admins_db = db['admins']
config_db = db['config']
activity_db = db['activity']
auth_groups_db = db['authorized_groups'] 
rain_db = db['rain_events']

user_states = {}
active_tickets = {}   
pending_tickets = {}  
user_langs = {}  

# Admin Notification Tracking
admin_ticket_msgs = {}
admin_withdraw_msgs = {} 

# DOUBLE MESSAGE PREVENTER & SPAM TRACKER
processed_msgs = {}
spam_tracker = {}
ldb_cache = {} 
ADMIN_CACHE = {"data": [], "time": 0}
CONFIG_CACHE = {"data": None, "time": 0}

# ================= LANGUAGE DICTIONARY =================
TR = {
    "en": {
        "welcome_head": f"Welcome <b>{{name}}</b>! {pe('👋')}\n\n",
        "welcome": f"{pe('✅')} <b>Welcome to the Tracker Bot!</b>\n\nTo verify your account:\n1. Add <code>{{tag}}</code> to your Telegram Name.\n2. Add this link to your Bio: {{link}}\n\nUse the buttons below to navigate.",
        "lang_set": f"{pe('✅')} Language set to English.",
        "verify_ok": f"{pe('✅')} <b>Verification Successful!</b> Your name and bio are now being tracked.",
        "verify_fail": f"{pe('❌')} <b>Verification Failed:</b>\nPlease ensure your name contains <code>{{tag}}</code> and your bio has the tracking link.",
        "help": f"{pe('✏️')} <b>Available Commands:</b>\n/start - Open Menu\n/lang - Change Language\n/verify - Verify profile\n/affiliate - Get referral link\n/leaderboard - View Activity\n/rank - View your daily rank\n/balance - Check balance\n/support - Contact support\n/close - Close active ticket",
        "affiliate_link": f"{pe('⛓️')} <b>Your Personal Affiliate Link:</b>\n{{link}}\n\nShare this to invite users. We automatically track valid invites.",
        "affiliate_stats": f"{pe('📊')} <b>Affiliate Stats:</b>\n{pe('👥')} Real Invites: {{real}}\n{pe('❌')} Left Members: {{left}}\n{pe('🤖')} Fake/Filtered: {{fake}}\n\n{pe('💡')} You get ${{reward}} for every {{req}} valid members.",
        "affiliate_disabled": f"{pe('⚠️')} <b>Affiliate system is currently disabled by admins.</b>",
        "sup_ask": f"{pe('✏️')} Please describe your issue in a single message. (Reason for support):",
        "sup_sent": f"{pe('✅')} Your request has been sent to the admins. Ticket Number: <b>{{tkt}}</b>\nPlease wait for an admin to accept it.",
        "sup_pending": f"{pe('⚠️')} You already have a pending or active support ticket. Please wait until it is resolved.",
        "tkt_joined": f"{pe('👨‍💻')} <b>An admin has joined the chat!</b>\nYou can now talk directly to them.",
        "tkt_closed": f"{pe('🔐')} <b>Your ticket has been closed.</b>",
        "tkt_rejected": f"{pe('❌')} <b>Your ticket ({{tkt}}) has been rejected by an admin.</b>",
        "draw_none": "No draw results available yet.",
        "draw_res": f"{pe('🎉')} <b>DAILY DRAW RESULTS</b> {pe('🎉')}\n\n{pe('⏱')} <b>Time:</b> {{time}}\n{pe('👥')} <b>Total Participants:</b> {{total}}\n{pe('🎁')} <b>Prize:</b> ${{amt}} each\n\n{pe('🏆')} <b>Winners:</b>\n{{winners}}",
        "wd_addr": f"{pe('📍')} Please send your {pe('💎')} TON withdrawal address:\n\n<b>Example:</b> <code>UQ...</code>",
        "wd_rej": f"{pe('❌')} <b>Withdrawal Rejected!</b>\nAmount: ${{amount}}\nReason: {{reason}}\nFunds refunded.",
        "btn_verify": "Verify",
        "btn_affiliate": "Affiliate",
        "btn_leaderboard": "Leaderboard",
        "btn_draw": "Draw",
        "btn_support": "Support",
        "btn_language": "Language",
        "btn_daily": "Daily",
        "btn_weekly": "Weekly",
        "btn_monthly": "Monthly",
        "btn_back": "Back"
    },
    "ru": {
        "welcome_head": f"Добро пожаловать <b>{{name}}</b>! {pe('👋')}\n\n",
        "welcome": f"{pe('✅')} <b>Добро пожаловать в Tracker Bot!</b>\n\nДля верификации аккаунта:\n1. Добавьте <code>{{tag}}</code> в ваше имя.\n2. Добавьте эту ссылку в Bio: {{link}}\n\nИспользуйте кнопки ниже.",
        "lang_set": f"{pe('✅')} Язык изменен на Русский.",
        "verify_ok": f"{pe('✅')} <b>Верификация пройдена!</b> Ваше имя и Bio отслеживаются.",
        "verify_fail": f"{pe('❌')} <b>Ошибка верификации:</b>\nУбедитесь, что ваше имя содержит <code>{{tag}}</code>, а в Bio есть ссылка.",
        "help": f"{pe('✏️')} <b>Команды:</b>\n/start - Меню\n/lang - Сменить язык\n/verify - Верификация\n/affiliate - Реферальная ссылка\n/leaderboard - Таблица лидеров\n/rank - Узнать свой ранг\n/balance - Баланс\n/support - Поддержка\n/close - Закрыть тикет",
        "affiliate_link": f"{pe('⛓️')} <b>Ваша реферальная ссылка:</b>\n{{link}}\n\nПоделитесь ею для приглашения. Мы automatically учитываем валидных пользователей.",
        "affiliate_stats": f"{pe('📊')} <b>Статистика:</b>\n{pe('👥')} Реальные: {{real}}\n{pe('❌')} Покинули: {{left}}\n{pe('🤖')} Фейки: {{fake}}\n\n{pe('💡')} Вы получаете ${{reward}} за каждых {{req}} пользователей.",
        "affiliate_disabled": f"{pe('⚠️')} <b>Партнерская система в настоящее время отключена администраторами.</b>",
        "sup_ask": f"{pe('✏️')} Пожалуйста, опишите вашу проблему в одном сообщении (Причина обращения):",
        "sup_sent": f"{pe('✅')} Ваш запрос отправлен. Номер тикета: <b>{{tkt}}</b>\nПожалуйста, подождите ответа.",
        "sup_pending": f"{pe('⚠️')} У вас already есть активный тикет. Дождитесь его закрытия.",
        "tkt_joined": f"{pe('👨‍💻')} <b>Администратор подключился!</b>\nТеперь вы можете общаться с ним.",
        "tkt_closed": f"{pe('🔐')} <b>Ваш тикет закрыт.</b>",
        "tkt_rejected": f"{pe('❌')} <b>Ваш тикет ({{tkt}}) был отклонен администратором.</b>",
        "draw_none": "Результаты розыгрыша пока недоступны.",
        "draw_res": f"{pe('🎉')} <b>РЕЗУЛЬТАТЫ РОЗЫГРЫША</b> {pe('🎉')}\n\n{pe('⏱')} <b>Время:</b> {{time}}\n{pe('👥')} <b>Участников:</b> {{total}}\n{pe('🎁')} <b>Приз:</b> ${{amt}} каждому\n\n{pe('🏆')} <b>Победители:</b>\n{{winners}}",
        "wd_addr": f"{pe('📍')} Пожалуйста, отправьте ваш адрес {pe('💎')} TON:\n\n<b>Пример:</b> <code>UQ...</code>",
        "wd_rej": f"{pe('❌')} <b>Вывод отклонен!</b>\nСумма: ${{amount}}\nПричина: {{reason}}\nСредства возвращены.",
        "btn_verify": "Проверить",
        "btn_affiliate": "Реферал",
        "btn_leaderboard": "Таблица",
        "btn_draw": "Розыгрыш",
        "btn_support": "Поддержка",
        "btn_language": "Язык",
        "btn_daily": "День",
        "btn_weekly": "Неделя",
        "btn_monthly": "Месяц",
        "btn_back": "Назад"
    },
    "hi": {
        "welcome_head": f"स्वागत है <b>{{name}}</b>! {pe('👋')}\n\n",
        "welcome": f"{pe('✅')} <b>ट्रैकर बॉट में आपका स्वागत है!</b>\n\nअपने अकाउंट को वेरीफाई करने के लिए:\n1. अपने टेलीग्राम नाम में <code>{{tag}}</code> जोड़ें।\n2. अपने Bio में यह लिंक जोड़ें: {{link}}\n\nनेविगेट करने के लिए नीचे दिए गए बटन्स का उपयोग करें।",
        "lang_set": f"{pe('✅')} भाषा हिंदी में सेट हो गई है।",
        "verify_ok": f"{pe('✅')} <b>सत्यापन सफल!</b> आपका नाम और बायो अब ट्रैक किया जा रहा है।",
        "verify_fail": f"{pe('❌')} <b>सत्यापन विफल:</b>\nकृपया सुनिश्चित करें कि आपके नाम में <code>{{tag}}</code> है और आपके बायो में ट्रैकिंग लिंक है।",
        "help": f"{pe('✏️')} <b>उपलब्ध कमांड्स:</b>\n/start - मेन्यू खोलें\n/lang - भाषा बदलें\n/verify - प्रोफाइल वेरीफाई करें\n/affiliate - रेफरल लिंक प्राप्त करें\n/leaderboard - लीडरबोर्ड देखें\n/rank - अपनी दैनिक रैंक देखें\n/balance - बैलेंस देखें\n/support - सहायता प्राप्त करें\n/close - सक्रिय टिकट बंद करें",
        "affiliate_link": f"{pe('⛓️')} <b>आपका पर्सनल एफिलिएट लिंक:</b>\n{{link}}\n\nयूजर्स को इनवाइट करने के लिए इसे शेयर करें।",
        "affiliate_stats": f"{pe('📊')} <b>एफिलिएट आँकड़े:</b>\n{pe('👥')} असली इनवाइट: {{real}}\n{pe('❌')} छोड़ दिया: {{left}}\n{pe('🤖')} फेक/फ़िल्टर: {{fake}}\n\n{pe('💡')} हर {{req}} मेंबर्स पर आपको ${{reward}} मिलेंगे।",
        "affiliate_disabled": f"{pe('⚠️')} <b>एफिलिएट सिस्टम वर्तमान में एडमिन द्वारा बंद कर दिया गया है।</b>",
        "sup_ask": f"{pe('✏️')} कृपया अपनी समस्या एक मैसेज में लिखें (सहायता का कारण):",
        "sup_sent": f"{pe('✅')} आपका अनुरोध एडमिन को भेज दिया गया है। टिकट नंबर: <b>{{tkt}}</b>\nकृपया प्रतीक्षा करें।",
        "sup_pending": f"{pe('⚠️')} आपके पास पहले से ही एक सक्रिय टिकट है। कृपया इसके समाधान की प्रतीक्षा करें।",
        "tkt_joined": f"{pe('👨‍💻')} <b>एक एडमिन चैट में शामिल हो गया है!</b>\nअब आप सीधे उनसे बात कर सकते हैं।",
        "tkt_closed": f"{pe('🔐')} <b>आपका टिकट बंद कर दिया गया है।</b>",
        "tkt_rejected": f"{pe('❌')} <b>आपका टिकट ({{tkt}}) एडमिन द्वारा अस्वीकार कर दिया गया है।</b>",
        "draw_none": "अभी तक कोई ड्रा रिज़ल्ट उपलब्ध नहीं है।",
        "draw_res": f"{pe('🎉')} <b>डेली ड्रा रिज़ल्ट</b> {pe('🎉')}\n\n{pe('⏱')} <b>समय:</b> {{time}}\n{pe('👥')} <b>कुल प्रतिभागी:</b> {{total}}\n{pe('🎁')} <b>इनाम:</b> ${{amt}} प्रत्येक\n\n{pe('🏆')} <b>विजेता:</b>\n{{winners}}",
        "wd_addr": f"{pe('📍')} कृपया अपना {pe('💎')} TON निकासी पता भेजें:\n\n<b>उदाहरण:</b> <code>UQ...</code>",
        "wd_rej": f"{pe('❌')} <b>निकासी अस्वीकृत!</b>\nरकम: ${{amount}}\nकारण: {{reason}}\nफंड्स वापस कर दिए गए हैं।",
        "btn_verify": "सत्यापन",
        "btn_affiliate": "रेफरल",
        "btn_leaderboard": "लीडरबोर्ड",
        "btn_draw": "ड्रा",
        "btn_support": "सहायता",
        "btn_language": "भाषा",
        "btn_daily": "दैनिक",
        "btn_weekly": "साप्ताहिक",
        "btn_monthly": "मासिक",
        "btn_back": "पीछे"
    }
}

# ================= HELPER FUNCTIONS =================
async def check_double_msg(user_id: int) -> bool:
    now = time.time()
    if user_id in processed_msgs and now - processed_msgs[user_id] < 1.5:
        return True 
    processed_msgs[user_id] = now
    return False

async def is_admin(user_id):
    if user_id == OWNER_ID: return True
    now = time.time()
    if now - ADMIN_CACHE["time"] > 300: 
        admins = await admins_db.find().to_list(100)
        ADMIN_CACHE["data"] = [a["user_id"] for a in admins]
        ADMIN_CACHE["time"] = now
    return user_id in ADMIN_CACHE["data"]

async def is_group_authorized(chat_id: int) -> bool:
    if chat_id > 0: return True 
    if chat_id == TRACK_GROUP_ID: return True
    return bool(await auth_groups_db.find_one({"chat_id": chat_id}))

async def get_lang(user_id):
    if user_id in user_langs: return user_langs[user_id]
    user = await users_db.find_one({"user_id": user_id})
    l = user.get("lang", "en") if user else "en"
    user_langs[user_id] = l
    return l

async def get_config():
    now = time.time()
    if CONFIG_CACHE["data"] and now - CONFIG_CACHE["time"] < 60: 
        return CONFIG_CACHE["data"]
        
    conf = await config_db.find_one({"_id": "settings"})
    if not conf:
        conf = {
            "affiliate_reward": 3.0, 
            "affiliate_req": 100,
            "draw_winners_count": 10,
            "draw_amount": 2.0,
            "draw_enabled": True,
            "withdrawal_enabled": True,
            "affiliate_enabled": True,
            "min_withdrawal": 20.0
        }
        await config_db.insert_one({"_id": "settings", **conf})
        
    CONFIG_CACHE["data"] = conf
    CONFIG_CACHE["time"] = now
    return conf

async def get_or_create_user(user_id, user_obj=None):
    user = await users_db.find_one({"user_id": user_id})
    name = "User"
    if user_obj:
        name = user_obj.first_name or "User"
        if user_obj.last_name: name += f" {user_obj.last_name}"
        
    if not user:
        user = {
            "user_id": user_id, "balance": 0.0, "bio_link": None, 
            "verified": False, "affiliates": [], "fake_affiliates": [], "left_affiliates": [],
            "lang": "en", "won_draw": False, "name": name,
            "ever_joined_group": False, "warnings": 0
        }
        await users_db.insert_one(user)
    elif user_obj and (user.get("name") != name or user.get("name") == "User"):
        await users_db.update_one({"user_id": user_id}, {"$set": {"name": name}})
        user["name"] = name
    return user

async def fetch_real_name(user_id, db_name):
    if db_name and db_name != "User":
        return db_name
    try:
        u = await app.get_users(user_id)
        name = u.first_name or "User"
        if u.last_name: name += f" {u.last_name}"
        await users_db.update_one({"user_id": user_id}, {"$set": {"name": name}})
        return name
    except:
        return "User"

def get_main_menu(lang: str):
    tr = TR.get(lang, TR["en"])
    return kb(
        [(tr["btn_verify"], "menu_verify", "primary", "✅"), (tr["btn_affiliate"], "menu_affiliate", "success", "⛓️")],
        [(tr["btn_leaderboard"], "menu_leaderboard", "primary", "🏆"), (tr["btn_draw"], "menu_draw", "primary", "🎉")],
        [(tr["btn_support"], "menu_support", "danger", "🎟"), (tr["btn_language"], "menu_lang", "primary", "🌐")]
    )

async def generate_leaderboard_text(period, page, group_id):
    today = datetime.date.today()
    if period == "daily":
        match_date = {"$gte": str(today)}
        title = "DAILY ACTIVITY RANKING"
    elif period == "weekly":
        match_date = {"$gte": str(today - datetime.timedelta(days=7))}
        title = "WEEKLY ACTIVITY RANKING"
    else: 
        match_date = {"$gte": str(today - datetime.timedelta(days=30))}
        title = "MONTHLY ACTIVITY RANKING"

    now = datetime.datetime.now().timestamp()
    cache_key = f"{period}_{page}_{group_id}"
    
    if cache_key in ldb_cache and (now - ldb_cache[cache_key]["time"] < 60):
        return ldb_cache[cache_key]["text"], ldb_cache[cache_key]["max_pages"]
    
    match_query = {"date": match_date, "group_id": group_id}
        
    pipeline = [
        {"$match": match_query},
        {"$group": {"_id": "$user_id", "total": {"$sum": "$message_count"}}},
        {"$sort": {"total": -1}},
        {"$skip": page * 10},
        {"$limit": 10},
        {"$lookup": {
            "from": "users",
            "localField": "_id",
            "foreignField": "user_id",
            "as": "user_info"
        }}
    ]
    
    results = await activity_db.aggregate(pipeline).to_list(length=10)
    unique_users_list = await activity_db.distinct("user_id", match_query)
    total_users_period = len(unique_users_list)
    max_pages = max(0, (total_users_period - 1) // 10)
    
    text = f"{pe('🏆')} <b>{title}</b>\n\n"
    if not results:
        text += f"<i>No activity recorded yet.</i> {pe('⚠️')}"
    else:
        for i, res in enumerate(results, start=(page*10)+1):
            user_info = res.get('user_info', [])
            db_name = user_info[0].get("name") if user_info else None
            name = await fetch_real_name(res['_id'], db_name)
            safe_name = html.escape(name)
            text += f"<b>{i}.</b> {safe_name} - {res['total']} msgs {pe('💬')}\n"
            
    ldb_cache[cache_key] = {"text": text, "max_pages": max_pages, "time": now}
    return text, max_pages

# ================= SAFE FORCE SUBSCRIBE LOGIC =================
async def is_user_subscribed(client: Client, user_id: int) -> bool:
    if await is_admin(user_id):
        return True
    
    async def check_chat(chat_identifier):
        try:
            m = await client.get_chat_member(chat_identifier, user_id)
            status = str(m.status).lower()
            if any(x in status for x in ["member", "admin", "creator", "owner", "restricted"]):
                return True
        except Exception:
            pass
        
        try:
            res = await tg("getChatMember", chat_id=chat_identifier, user_id=user_id)
            status = res.get("status", "").lower()
            if status in ["member", "administrator", "creator", "restricted"]:
                return True
        except Exception:
            pass
            
        return False

    in_channel = await check_chat(FSUB_CHANNEL)
    if not in_channel: 
        return False
        
    in_group = await check_chat(TRACK_GROUP_ID)
    return in_group

def get_fsub_keyboard():
    channel_url = f"https://t.me/{FSUB_CHANNEL.replace('@', '')}"
    return {
        "inline_keyboard": [
            [btn("Join Channel", url=channel_url, style="primary", icon="📢")],
            [btn("Join Group", url=GROUP_INVITE_LINK, style="primary", icon="👥")],
            [btn("Check", data="check_fsub", style="success", icon="✅")]
        ]
    }

async def pass_fsub(client: Client, message_or_call):
    user_id = message_or_call.from_user.id
    if await is_user_subscribed(client, user_id):
        return True
    
    text = f"{pe('⚠️')} <b>Please join our official channel and group to use this bot!</b>\n\nClick the buttons below to join, then click <b>Check {pe('✅')}</b>."
    markup = get_fsub_keyboard()
    
    if isinstance(message_or_call, Message):
        await send_msg(message_or_call.chat.id, text, markup=markup)
    elif isinstance(message_or_call, CallbackQuery):
        if getattr(message_or_call, "message", None):
            await edit_msg(message_or_call.message.chat.id, message_or_call.message.id, text, markup=markup)
        else:
            await send_msg(user_id, text, markup=markup)
    return False
# ==============================================================

# ================= BACKGROUND TIMERS =================
async def rain_timer_task(chat_id, message_id, event_id, end_time, total_amt, win_count, min_msgs):
    while True:
        now = time.time()
        if now >= end_time:
            break
            
        rem = int(end_time - now)
        mins, secs = divmod(rem, 60)
        hrs, mins = divmod(mins, 60)
        time_str = f"{hrs}h {mins}m {secs}s" if hrs > 0 else f"{mins}m {secs}s"
        
        event = await rain_db.find_one({"_id": event_id})
        if not event: break
        
        parts_count = len(event.get("participants", []))
        
        text = f"{pe('🌧')} <b>RAIN EVENT!</b> {pe('⛈')}\n\n{pe('🌩')} <b>Total Prize:</b> ${total_amt}\n{pe('🏆')} <b>Winners:</b> {win_count}\n{pe('✏️')} <b>Required Activity:</b> {min_msgs} messages today.\n\n{pe('👥')} <b>Participants:</b> {parts_count}\n{pe('⏱')} <b>Ends In:</b> {time_str}"
        markup = kb([("Participate", f"rain_join_{event_id}", "success", "☔")])
        
        try:
            await tg("editMessageText", chat_id=chat_id, message_id=message_id, text=text, reply_markup=markup, parse_mode="HTML")
        except Exception:
            pass 
            
        await asyncio.sleep(10)
        
    # Rain Ended - Select Winners
    event = await rain_db.find_one({"_id": event_id})
    if not event: return
    
    participants = event.get("participants", [])
    winners_list = []
    
    if participants:
        # Fetch names for redcube weight boost & daily messages
        p_docs = await users_db.find({"user_id": {"$in": participants}}).to_list(length=None)
        p_dict = {d["user_id"]: d.get("name", "").lower() for d in p_docs}
        
        today_date = str(datetime.date.today())
        act_docs = await activity_db.aggregate([
            {"$match": {"user_id": {"$in": participants}, "date": today_date}},
            {"$group": {"_id": "$user_id", "total": {"$sum": "$message_count"}}}
        ]).to_list(length=None)
        daily_msgs_dict = {d["_id"]: d["total"] for d in act_docs}
        
        population = []
        weights = []
        for p in participants:
            population.append(p)
            name = p_dict.get(p, "")
            
            # Base weight based on name tag
            base_weight = 5 if "redcube" in name else 1
            # Add today's message count to their weight (higher daily msgs = higher chance)
            daily_weight = daily_msgs_dict.get(p, 0)
            
            weights.append(base_weight + daily_weight)
                
        # Draw winners without replacement
        win_count_actual = min(win_count, len(population))
        for _ in range(win_count_actual):
            if not population: break
            winner_choice = random.choices(population, weights=weights, k=1)[0]
            idx = population.index(winner_choice)
            winners_list.append(winner_choice)
            population.pop(idx)
            weights.pop(idx)
        
    win_amount_each = total_amt / win_count if win_count > 0 else 0
    
    mentions = []
    for wid in winners_list:
        await users_db.update_one({"user_id": wid}, {"$inc": {"balance": win_amount_each}}, upsert=True)
        u_info = await get_or_create_user(wid)
        mentions.append(f"<a href='tg://user?id={wid}'>{html.escape(u_info['name'])}</a>")
        try: await send_msg(wid, f"{pe('🎉')} <b>Congratulations!</b> You won ${round(win_amount_each, 2)} in the Rain Event!")
        except: pass
        
    if not mentions:
        final_text = f"{pe('🌧')} <b>RAIN EVENT ENDED!</b> {pe('⛈')}\n\n{pe('❌')} <b>No eligible participants joined in time!</b>"
    else:
        final_text = f"{pe('🌧')} <b>RAIN EVENT ENDED!</b> {pe('⛈')}\n\n{pe('🌩')} <b>Total Dropped:</b> ${total_amt}\n{pe('🎁')} <b>Prize Each:</b> ${round(win_amount_each, 2)}\n\n{pe('🏆')} <b>Winners:</b>\n"
        for i, m in enumerate(mentions, 1):
            final_text += f"<blockquote>{i}. {m}</blockquote>\n"
            
    try:
        await tg("editMessageText", chat_id=chat_id, message_id=message_id, text=final_text, reply_markup=None, parse_mode="HTML")
    except: pass
    await rain_db.delete_one({"_id": event_id})

async def background_verification_check():
    while True:
        try:
            verified_users = await users_db.find({"verified": True}).to_list(length=None)
            for u in verified_users:
                try:
                    chat_info = await app.get_chat(u["user_id"])
                    full_name = f"{chat_info.first_name or ''} {chat_info.last_name or ''}".lower()
                    name_ok = REQUIRED_USERNAME_TAG.lower() in full_name
                    bio_ok = u.get("bio_link") in (chat_info.bio or "")
                    
                    if not (name_ok and bio_ok):
                        await users_db.update_one({"user_id": u["user_id"]}, {"$set": {"verified": False}})
                        lang = await get_lang(u["user_id"])
                        msg = f"{pe('⚠️')} <b>Warning:</b> You have removed the required name tag or bio link! Your verification is revoked and you are disqualified from upcoming draws. Please add them back and send /verify."
                        if lang == "ru":
                            msg = f"{pe('⚠️')} <b>Внимание:</b> Вы удалили тег из имени или ссылку из Bio! Ваша верификация аннулирована. Пожалуйста, верните их и отправьте /verify."
                        elif lang == "hi":
                            msg = f"{pe('⚠️')} <b>चेतावनी:</b> आपने नाम से टैग या बायो से लिंक हटा दिया है! आपका सत्यापन रद्द कर दिया गया है। कृपया उन्हें वापस जोड़ें और /verify भेजें।"
                        try: await send_msg(u["user_id"], msg)
                        except: pass
                except: pass
                await asyncio.sleep(2) 
        except: pass
        await asyncio.sleep(120)

# ================= USER COMMANDS =================
@app.on_message(filters.command("lang") & filters.private)
async def lang_cmd(client: Client, message: Message):
    if await check_double_msg(message.from_user.id): return
    if not await pass_fsub(client, message): return 
    btns = kb(
        [("English", "lang_en", "primary", "🇬🇧"), ("Русский", "lang_ru", "danger", "🇷🇺")],
        [("हिंदी (Hindi)", "lang_hi", "success", "🇮🇳")]
    )
    await send_msg(message.chat.id, "Select your language / Выберите язык / भाषा चुनें:", markup=btns)

@app.on_message(filters.command("access"))
async def access_cmd(client: Client, message: Message):
    if not await is_admin(message.from_user.id): return
    try:
        target_chat = int(message.command[1]) if len(message.command) > 1 else message.chat.id
        if target_chat > 0:
            return await send_msg(message.chat.id, f"{pe('⚠️')} Use this command inside a group, or provide a Group ID (-100xxxx).")
            
        await auth_groups_db.update_one({"chat_id": target_chat}, {"$set": {"chat_id": target_chat}}, upsert=True)
        await send_msg(message.chat.id, f"{pe('✅')} Group <code>{target_chat}</code> authorized successfully! Activity tracking and leaderboards will now work here.")
    except Exception as e:
        await send_msg(message.chat.id, "Usage: /access [group_id] or use in group.")

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    if await check_double_msg(message.from_user.id): return
    if not await pass_fsub(client, message): return 
    
    if message.from_user.id in user_states:
        del user_states[message.from_user.id]
        
    user = await get_or_create_user(message.from_user.id, message.from_user)
    lang = await get_lang(message.from_user.id)
    
    if not user.get("bio_link"):
        try:
            invite = await app.create_chat_invite_link(TRACK_GROUP_ID, name=f"Bio_{message.from_user.id}", creates_join_request=True)
            await users_db.update_one({"user_id": message.from_user.id}, {"$set": {"bio_link": invite.invite_link}})
            user["bio_link"] = invite.invite_link
        except:
            pass 
            
    welcome_head = TR[lang]["welcome_head"].format(name=html.escape(user['name']))
    await send_msg(message.chat.id, welcome_head, disable_web_page_preview=True)
    
    welcome_body = TR[lang]["welcome"].format(tag=REQUIRED_USERNAME_TAG, link=user.get('bio_link', 'No Link Generated'))
    await send_msg(message.chat.id, welcome_body, markup=get_main_menu(lang), disable_web_page_preview=True)
    
    if await is_admin(message.from_user.id):
        await send_msg(message.chat.id, f"{pe('🛡')} <b>Admin Access Recognized!</b> Send /adminhelp to see your commands.")

@app.on_message(filters.command("help") & filters.private)
async def help_cmd(client: Client, message: Message):
    if await check_double_msg(message.from_user.id): return
    if not await pass_fsub(client, message): return 
    lang = await get_lang(message.from_user.id)
    await send_msg(message.chat.id, TR[lang]["help"])

@app.on_message(filters.command("verify") & filters.private)
async def verify_cmd(client: Client, message: Message):
    if await check_double_msg(message.from_user.id): return
    if not await pass_fsub(client, message): return 
    user_id = message.from_user.id
    user_data = await get_or_create_user(user_id, message.from_user)
    lang = await get_lang(user_id)
    
    chat_info = await app.get_chat(user_id)
    full_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".lower()
    
    name_ok = REQUIRED_USERNAME_TAG.lower() in full_name
    bio_ok = user_data.get("bio_link") in (chat_info.bio or "")

    if name_ok and bio_ok:
        await users_db.update_one({"user_id": user_id}, {"$set": {"verified": True}})
        await send_msg(message.chat.id, TR[lang]["verify_ok"])
    else:
        await send_msg(message.chat.id, TR[lang]["verify_fail"].format(tag=REQUIRED_USERNAME_TAG))

@app.on_message(filters.command("affiliate") & filters.private)
async def affiliate_cmd(client: Client, message: Message):
    if await check_double_msg(message.from_user.id): return
    if not await pass_fsub(client, message): return 
    user = await get_or_create_user(message.from_user.id, message.from_user)
    lang = await get_lang(message.from_user.id)
    conf = await get_config()

    if not conf.get("affiliate_enabled", True):
        return await send_msg(message.chat.id, TR[lang]["affiliate_disabled"])

    # Generating link unconditionally due to revoke compatibility
    invite_link = user.get("affiliate_link")
    if not invite_link:
        try:
            invite = await app.create_chat_invite_link(TRACK_GROUP_ID, name=f"Affiliate_{message.from_user.id}", creates_join_request=True)
            invite_link = invite.invite_link
            await users_db.update_one({"user_id": message.from_user.id}, {"$set": {"affiliate_link": invite_link}})
        except:
            return await send_msg(message.chat.id, f"{pe('❌')} Error creating link. Ensure bot is admin in the tracking group.")

    markup = kb(
        [("Affiliate Status", "menu_aff_stats", "primary", "📊")],
        [(TR[lang]["btn_back"], "menu_main", "danger", "🔙")]
    )
    await send_msg(message.chat.id, TR[lang]["affiliate_link"].format(link=invite_link), markup=markup)

@app.on_message(filters.command(["rank", "myrank"]))
async def rank_cmd(client: Client, message: Message):
    if await check_double_msg(message.from_user.id): return
    
    is_private = message.chat.id > 0
    if is_private:
        if not await pass_fsub(client, message): return 
        group_id = TRACK_GROUP_ID
    else:
        if not await is_group_authorized(message.chat.id): return
        group_id = message.chat.id
        
    user_id = message.from_user.id
    today = str(datetime.date.today())

    # Get user's today messages for specific group
    user_act = await activity_db.aggregate([
        {"$match": {"user_id": user_id, "date": today, "group_id": group_id}},
        {"$group": {"_id": None, "total": {"$sum": "$message_count"}}}
    ]).to_list(1)
    user_msgs = user_act[0]["total"] if user_act else 0

    # Get user rank for today in specific group
    higher_users = await activity_db.aggregate([
        {"$match": {"date": today, "group_id": group_id}},
        {"$group": {"_id": "$user_id", "total": {"$sum": "$message_count"}}},
        {"$match": {"total": {"$gt": user_msgs}}},
        {"$count": "count"}
    ]).to_list(1)
    
    rank = higher_users[0]["count"] + 1 if higher_users else 1
    
    name = message.from_user.first_name or "User"
    safe_name = html.escape(name)
    
    text = f"{pe('🏆')} <b>Rank Info for {safe_name}</b>\n\n"
    text += f"{pe('📊')} <b>Daily Rank:</b> #{rank}\n"
    text += f"{pe('💬')} <b>Messages Today:</b> {user_msgs}"
    
    await send_msg(message.chat.id, text)

@app.on_message(filters.command("draw") & filters.private)
async def show_draw_cmd(client: Client, message: Message):
    if await check_double_msg(message.from_user.id): return
    if not await pass_fsub(client, message): return 
    lang = await get_lang(message.from_user.id)
    conf = await get_config()
    
    if not conf.get("draw_enabled", True):
        return await send_msg(message.chat.id, f"{pe('⚠️')} <b>Draw now disabled, soon coming.</b>")

    draw_data = await config_db.find_one({"_id": "latest_draw"})
    
    if not draw_data or not draw_data.get("winners"):
        return await send_msg(message.chat.id, TR[lang]["draw_none"])
        
    winners_text = ""
    for i, wid in enumerate(draw_data["winners"], 1):
        u_doc = await users_db.find_one({"user_id": wid})
        db_name = u_doc.get("name") if u_doc else None
        name = await fetch_real_name(wid, db_name)
        winners_text += f"{i}. {html.escape(name)}\n"
        
    text = TR[lang]["draw_res"].format(
        time=draw_data["time"], total=draw_data["total"], 
        amt=draw_data.get("amount", 2.0), winners=winners_text
    )
    await send_msg(message.chat.id, text, disable_web_page_preview=True)

@app.on_message(filters.command(["daily", "weekly", "monthly", "leaderboard"]))
async def leaderboard_cmd(client: Client, message: Message):
    if await check_double_msg(message.from_user.id): return
    
    is_private = message.chat.id > 0
    if is_private:
        if not await pass_fsub(client, message): return 
        group_id = TRACK_GROUP_ID
    else:
        if not await is_group_authorized(message.chat.id): return
        group_id = message.chat.id
        
    cmd = message.command[0].lower()
    period = cmd if cmd in ["daily", "weekly", "monthly"] else "weekly"
    lang = await get_lang(message.from_user.id)
    tr = TR.get(lang, TR["en"])
    
    text, max_pages = await generate_leaderboard_text(period, 0, group_id)
    
    d_style = "success" if period == "daily" else "primary"
    w_style = "success" if period == "weekly" else "primary"
    m_style = "success" if period == "monthly" else "primary"
    
    if is_private:
        # Private: Always show buttons + Back button
        btns = kb(
            [(tr["btn_daily"], "ldb_daily_0", d_style, "📅"), 
             (tr["btn_weekly"], "ldb_weekly_0", w_style, "📅"), 
             (tr["btn_monthly"], "ldb_monthly_0", m_style, "📅")],
            [(tr["btn_back"], "menu_main", "danger", "🔙")]
        )
        await send_msg(message.chat.id, text, markup=btns, disable_web_page_preview=True)
    else:
        # Group: Only show buttons if the exact command was /leaderboard
        if cmd == "leaderboard":
            btn_rows = [
                [(tr["btn_daily"], "ldb_daily_0", d_style, "📅"), 
                 (tr["btn_weekly"], "ldb_weekly_0", w_style, "📅"), 
                 (tr["btn_monthly"], "ldb_monthly_0", m_style, "📅")]
            ]
            if max_pages > 0:
                btn_rows.append([("Next ➡️", f"ldb_{period}_1", "primary", "➡️")])
                
            btns = kb(*btn_rows)
            await send_msg(message.chat.id, text, markup=btns, disable_web_page_preview=True)
        else:
            # If they just typed /daily, /weekly, /monthly in a group -> No Buttons
            await send_msg(message.chat.id, text, disable_web_page_preview=True)


@app.on_message(filters.command(["balance", "bal"]) & filters.private)
async def balance_cmd(client: Client, message: Message):
    if await check_double_msg(message.from_user.id): return
    if not await pass_fsub(client, message): return
    user = await get_or_create_user(message.from_user.id, message.from_user)
    await send_msg(message.chat.id, f"{pe('💰')} <b>Your Current Balance:</b> ${round(user.get('balance', 0.0), 2)}")

@app.on_message(filters.command("support") & filters.private)
async def support_cmd(client: Client, message: Message):
    if await check_double_msg(message.from_user.id): return
    if not await pass_fsub(client, message): return 
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    
    if user_id in active_tickets or user_id in pending_tickets:
        return await send_msg(message.chat.id, TR[lang]["sup_pending"])
        
    user_states[user_id] = {"state": "wait_for_support"}
    await send_msg(message.chat.id, TR[lang]["sup_ask"])

@app.on_message(filters.command("withdraw") & filters.private)
async def withdraw_cmd(client: Client, message: Message):
    if await check_double_msg(message.from_user.id): return
    if not await pass_fsub(client, message): return 
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    conf = await get_config()
    
    if not conf.get("withdrawal_enabled", True): 
        return await send_msg(message.chat.id, f"{pe('⚠️')} Withdrawals are disabled.")
        
    user = await get_or_create_user(user_id, message.from_user)
    min_wd = conf.get("min_withdrawal", 20.0)
    
    if user["balance"] < min_wd: 
        return await send_msg(message.chat.id, f"{pe('❌')} Your wallet balance is ${round(user['balance'], 2)}. Minimum withdrawal is ${min_wd}.")
        
    user_states[user_id] = {"state": "wait_for_method", "amount": user["balance"]}
    
    markup = kb(
        [("Redcube Wallet", "wd_method_redcube", "success", "🏦")], 
        [(TR[lang]["btn_back"], "menu_main", "danger", "🔙")]
    )
    await send_msg(message.chat.id, f"{pe('💰')} <b>Balance:</b> ${user['balance']}\n\nPlease select the withdrawal method:", markup=markup)

@app.on_message(filters.command("close") & filters.private)
async def close_cmd(client: Client, message: Message):
    if not await pass_fsub(client, message): return 
    user_id = message.from_user.id
    
    if user_id not in active_tickets: 
        return await send_msg(message.chat.id, f"No active ticket. {pe('⚠️')}")
        
    target_id = active_tickets[user_id]
    
    del active_tickets[user_id]
    if target_id in active_tickets: 
        del active_tickets[target_id]
        
    await send_msg(message.chat.id, f"{pe('✅')} Ticket closed.")
    
    try: 
        t_lang = await get_lang(target_id)
        await send_msg(target_id, TR[t_lang]["tkt_closed"])
    except: pass
        
# ================= BACKGROUND TRACKERS =================
@app.on_chat_join_request()
async def handle_join_request(client: Client, request: ChatJoinRequest):
    user_id = request.from_user.id
    chat_id = request.chat.id
    
    # Fake Account Auto Reject Logic
    user = request.from_user
    if user.is_bot or getattr(user, 'is_fake', False) or getattr(user, 'is_scam', False) or getattr(user, 'is_restricted', False):
        try:
            await client.decline_chat_join_request(chat_id, user_id)
        except: pass
        return
        
    conf = await get_config()
    
    # Stop auto-approval for group if affiliate is disabled, EXCEPT for admins
    if chat_id == TRACK_GROUP_ID and not conf.get("affiliate_enabled", True):
        if not await is_admin(user_id):
            return  # Leave request pending

    # Auto-approve for channels or allowed group requests
    try:
        await client.approve_chat_join_request(chat_id, user_id)
    except Exception: pass
    
    # Affiliate tracking only happens in the main tracking group
    if chat_id == TRACK_GROUP_ID:
        joining_user = await get_or_create_user(user_id, request.from_user)

        # Check if they have EVER joined before (Global exploit fix)
        if not joining_user.get("ever_joined_group", False):
            # Mark them as joined so they can never be counted again
            await users_db.update_one({"user_id": user_id}, {"$set": {"ever_joined_group": True}})

            if request.invite_link and request.invite_link.name and request.invite_link.name.startswith("Affiliate_"):
                # Double check config in case it changed mid-flight
                if not conf.get("affiliate_enabled", True):
                    return # Skip affiliate processing if system is toggled off

                inviter_id = int(request.invite_link.name.split("_")[1])
                inviter_data = await get_or_create_user(inviter_id)
                
                if user_id not in inviter_data.get("affiliates", []) and user_id not in inviter_data.get("left_affiliates", []):
                    await users_db.update_one({"user_id": inviter_id}, {"$addToSet": {"affiliates": user_id}})
                    
                    new_count = len(inviter_data.get("affiliates", [])) + 1
                    
                    if new_count % conf["affiliate_req"] == 0:
                        reward = conf["affiliate_reward"]
                        await users_db.update_one({"user_id": inviter_id}, {"$inc": {"balance": reward}})
                        lang = await get_lang(inviter_id)
                        msg = f"{pe('🎉')} <b>Congratulations!</b> You reached {conf['affiliate_req']} members. ${reward} added!"
                        if lang == "ru": msg = f"{pe('🎉')} <b>Поздравляем!</b> Вы пригласили {conf['affiliate_req']} участников. Вам начислено ${reward}!"
                        if lang == "hi": msg = f"{pe('🎉')} <b>बधाई हो!</b> आपने {conf['affiliate_req']} मेंबर्स जोड़ लिए हैं। आपके वॉलेट में ${reward} जुड़ गए हैं!"
                        try: await send_msg(inviter_id, msg)
                        except: pass

@app.on_message(filters.left_chat_member & filters.chat(TRACK_GROUP_ID))
async def handle_member_leave(client: Client, message: Message):
    left_user_id = message.left_chat_member.id
    
    # Updates immediately when someone leaves (Works even if affiliate is toggled off)
    inviter = await users_db.find_one({"affiliates": left_user_id})
    if inviter:
        inviter_id = inviter["user_id"]
        await users_db.update_one(
            {"user_id": inviter_id}, 
            {
                "$pull": {"affiliates": left_user_id},
                "$addToSet": {"left_affiliates": left_user_id},
                "$inc": {"balance": -0.03} 
            }
        )

def contains_russian(text: str) -> bool:
    if not text: return False
    return bool(re.search(r'[А-яЁё]', text))

@app.on_message(filters.group, group=1)
async def group_activity_tracker(client: Client, message: Message):
    if not message.from_user: return
    if not await is_group_authorized(message.chat.id): return

    user_id = message.from_user.id
    full_name = message.from_user.first_name or "User"
    if message.from_user.last_name:
        full_name += f" {message.from_user.last_name}"
        
    # --- ANTI-SPAM SYSTEM ---
    if not await is_admin(user_id):
        now = time.time()
        user_times = spam_tracker.get(user_id, [])
        # Strictly keep messages from the last 5 seconds
        user_times = [t for t in user_times if now - t <= 5.0]
        user_times.append(now)
        spam_tracker[user_id] = user_times

        if len(user_times) >= 5: # Sent 5+ msgs within 5 seconds
            spam_tracker[user_id] = [] # Reset local tracker for this incident to prevent instant re-trigger
            
            # Increment warning count in DB
            user_doc = await users_db.find_one_and_update(
                {"user_id": user_id},
                {"$inc": {"warnings": 1}},
                return_document=True,
                upsert=True
            )
            warns = user_doc.get("warnings", 1)
            
            if warns >= 5:
                # MUTE THE USER
                try:
                    await client.restrict_chat_member(message.chat.id, user_id, ChatPermissions(can_send_messages=False))
                    await message.reply_text(f"{pe('⚠️')} <a href='tg://user?id={user_id}'>{html.escape(full_name)}</a> has been muted for spamming. (5/5 warnings)", parse_mode=ParseMode.HTML)
                except: pass
            else:
                # SEND WARNING
                try:
                    await message.reply_text(f"{pe('⚠️')} <a href='tg://user?id={user_id}'>{html.escape(full_name)}</a>, Please don't spam! Warning ({warns}/5)", parse_mode=ParseMode.HTML)
                except: pass
            return # Block message from being counted in activity
    # ------------------------
        
    # 1. Russian Ban Check
    if contains_russian(message.text or message.caption):
        try:
            await message.delete()
            await client.ban_chat_member(message.chat.id, user_id)
        except: pass
        return
        
    # 2. Strict Promo/Username Warning Check (Ignore REQUIRED_USERNAME_TAG)
    name_lower = full_name.lower()
    
    # Remove the required tag from the check string so it doesn't trigger the "@" detection
    check_name = name_lower.replace(REQUIRED_USERNAME_TAG.lower(), "")
    
    has_promo = "@" in check_name or any(promo.lower() in check_name for promo in BANNED_PROMOS)
    
    if has_promo:
        try:
            await message.delete()
            warning = await message.reply_text(f"{pe('⚠️')} <a href='tg://user?id={user_id}'>{html.escape(full_name)}</a>, please remove the <b>@ username</b> or promo from your profile name to send messages here. {pe('🛡')}", parse_mode=ParseMode.HTML)
            await asyncio.sleep(5)
            await warning.delete()
        except: pass
        return

    today = str(datetime.date.today())
    await users_db.update_one({"user_id": user_id}, {"$set": {"name": full_name}}, upsert=True)
    await activity_db.update_one(
        {"user_id": user_id, "group_id": message.chat.id, "date": today},
        {"$inc": {"message_count": 1}}, upsert=True
    )

# ================= ADMIN COMMANDS =================
@app.on_message(filters.command("rain") & filters.group)
async def rain_cmd(client: Client, message: Message):
    if not await is_admin(message.from_user.id): return
    
    try:
        parts = message.text.split()
        if len(parts) != 5: raise Exception()
        
        winners_count = int(parts[1])
        total_amount = float(parts[2])
        min_msgs = int(parts[3])
        time_str = parts[4].lower()
        
        duration_secs = 0
        if "h" in time_str:
            duration_secs = float(time_str.replace("h", "")) * 3600
        elif "m" in time_str:
            duration_secs = float(time_str.replace("m", "")) * 60
        else:
            duration_secs = float(time_str) * 60 
            
        end_time = time.time() + duration_secs
        event_id = str(random.randint(100000, 999999))
        
        await rain_db.insert_one({
            "_id": event_id,
            "chat_id": message.chat.id,
            "winners_count": winners_count,
            "total_amount": total_amount,
            "min_msgs": min_msgs,
            "end_time": end_time,
            "participants": []
        })
        
        text = f"{pe('🌧')} <b>RAIN EVENT!</b> {pe('⛈')}\n\n{pe('🌩')} <b>Total Prize:</b> ${total_amount}\n{pe('🏆')} <b>Winners:</b> {winners_count}\n{pe('✏️')} <b>Required Activity:</b> {min_msgs} messages today.\n\n{pe('👥')} <b>Participants:</b> 0\n{pe('⏱')} <b>Starting timer...</b>"
        markup = kb([("Participate", f"rain_join_{event_id}", "success", "☔")])
        
        sent = await send_msg(message.chat.id, text, markup=markup, reply_to=message.id)
        if not sent: return 
        
        asyncio.create_task(rain_timer_task(message.chat.id, sent["message_id"], event_id, end_time, total_amount, winners_count, min_msgs))
        
    except Exception as e:
        await message.reply_text(f"Usage: /rain [winners] [total_amount] [min_msgs_today] [time(h/m)]\nExample: `/rain 10 2 100 4h` {pe('⚠️')}")

@app.on_message(filters.command("adminhelp") & filters.private)
async def adminhelp_cmd(client: Client, message: Message):
    if not await is_admin(message.from_user.id): return
    text = (
        f"{pe('🛡')} <b>ADMIN COMMANDS MENU</b>\n\n"
        f"🔸 `/redraw` - Draw daily winners (Activity weighted)\n"
        f"🔸 `/toggledraw` - Enable/Disable Draw feature\n"
        f"🔸 `/drawsettings [count] [amount]` - Set daily winners and prize amount\n"
        f"🔸 `/addadmin [user_id]` - Add new admin\n"
        f"🔸 `/removeadmin [user_id]` - Remove admin\n"
        f"🔸 `/adminlist` - View all admins\n"
        f"🔸 `/setprice [members] [amount]` - Update affiliate referral price\n"
        f"🔸 `/togglewithdraw` - Turn withdrawals ON/OFF\n"
        f"🔸 `/toggleaffiliate` - Turn affiliate system ON/OFF\n"
        f"🔸 `/revokeall` - Clear existing affiliate links for all users\n"
        f"🔸 `/withdrawupdate [amount]` - Set minimum withdrawal limit\n"
        f"🔸 `/broadcast` - Reply to any msg to send to all users\n"
        f"🔸 `/check [username/id]` - Check specific user's activity\n"
        f"🔸 `/affiliatecheck [username/id]` - Check user affiliate details\n"
        f"🔸 `/rain [wins] [amt] [msgs_today] [time]` - Start group rain\n"
        f"🔸 `/warnreset [username/id]` - Reset a user's warnings and unmute them\n"
        f"🔸 `/access` (in a group) - Authorize group for Leaderboard commands\n"
    )
    await send_msg(message.chat.id, text)

@app.on_message(filters.command("warnreset"))
async def warnreset_cmd(client: Client, message: Message):
    if not await is_admin(message.from_user.id): return
    
    target_id = None
    safe_name = "User"
    
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
        safe_name = html.escape(message.reply_to_message.from_user.first_name or "User")
    elif len(message.command) > 1:
        target_input = message.command[1]
        try:
            user_info = await app.get_users(target_input)
            target_id = user_info.id
            safe_name = html.escape(user_info.first_name or "User")
        except:
            try:
                target_id = int(target_input)
            except:
                return await send_msg(message.chat.id, f"{pe('⚠️')} Invalid User ID or Username.")
    else:
        return await send_msg(message.chat.id, f"{pe('⚠️')} Usage: Reply to user or use /warnreset [username/id]")
        
    if not target_id: return
    
    # Reset warnings in DB
    await users_db.update_one({"user_id": target_id}, {"$set": {"warnings": 0}})
    
    # Try to unrestrict them if command is used in group
    if message.chat.id < 0:
        try:
            await client.restrict_chat_member(message.chat.id, target_id, ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            ))
        except: pass
        
    await send_msg(message.chat.id, f"{pe('✅')} Warnings for <a href='tg://user?id={target_id}'>{safe_name}</a> have been reset to 0, and they have been unmuted.")

@app.on_message(filters.command("revokeall"))
async def revokeall_cmd(client: Client, message: Message):
    if not await is_admin(message.from_user.id): return
    
    # Remove 'affiliate_link' field from all users in the DB
    result = await users_db.update_many(
        {"affiliate_link": {"$exists": True}},
        {"$unset": {"affiliate_link": ""}}
    )
    
    await send_msg(message.chat.id, f"{pe('✅')} <b>All affiliate links revoked!</b>\n{result.modified_count} users will get a fresh link next time they use /affiliate.")

@app.on_message(filters.command("toggleaffiliate"))
async def toggleaffiliate_cmd(client: Client, message: Message):
    if not await is_admin(message.from_user.id): return
    conf = await get_config()
    new_state = not conf.get("affiliate_enabled", True)
    await config_db.update_one({"_id": "settings"}, {"$set": {"affiliate_enabled": new_state}}, upsert=True)
    
    global CONFIG_CACHE
    CONFIG_CACHE["time"] = 0 
    
    await send_msg(message.chat.id, f"{pe('✏️')} Affiliate System is now <b>{'ENABLED' if new_state else 'DISABLED'}</b>.")

@app.on_message(filters.command("withdrawupdate"))
async def withdrawupdate_cmd(client: Client, message: Message):
    if not await is_admin(message.from_user.id): return
    try:
        parts = message.text.split()
        new_min = float(parts[1])
        await config_db.update_one({"_id": "settings"}, {"$set": {"min_withdrawal": new_min}}, upsert=True)
        
        global CONFIG_CACHE
        CONFIG_CACHE["time"] = 0
        
        await send_msg(message.chat.id, f"{pe('✅')} Minimum withdrawal limit successfully updated to <b>${new_min}</b>.")
    except:
        await send_msg(message.chat.id, f"Usage: /withdrawupdate [amount]\nExample: `/withdrawupdate 10` {pe('⚠️')}")

@app.on_message(filters.command("toggledraw"))
async def toggledraw_cmd(client: Client, message: Message):
    if not await is_admin(message.from_user.id): return
    conf = await get_config()
    new_state = not conf.get("draw_enabled", True)
    await config_db.update_one({"_id": "settings"}, {"$set": {"draw_enabled": new_state}}, upsert=True)
    
    global CONFIG_CACHE
    CONFIG_CACHE["time"] = 0 
    
    await send_msg(message.chat.id, f"{pe('✅')} Draw is now <b>{'ENABLED' if new_state else 'DISABLED'}</b>.")

@app.on_message(filters.command("drawsettings"))
async def drawsettings_cmd(client: Client, message: Message):
    if not await is_admin(message.from_user.id): return
    try:
        parts = message.text.split()
        count = int(parts[1])
        amount = float(parts[2])
        await config_db.update_one({"_id": "settings"}, {"$set": {"draw_winners_count": count, "draw_amount": amount}}, upsert=True)
        await send_msg(message.chat.id, f"{pe('✅')} <b>Draw Settings Updated!</b>\nWinners per draw: {count}\nAmount per winner: ${amount}")
    except:
        await send_msg(message.chat.id, f"Usage: /drawsettings [number_of_winners] [amount_per_winner]\nExample: `/drawsettings 10 2.5` {pe('⚠️')}")

@app.on_message(filters.command("redraw"))
async def redraw_cmd(client: Client, message: Message):
    if not await is_admin(message.from_user.id): return
    
    conf = await get_config()
    win_count = conf.get("draw_winners_count", 10)
    win_amt = conf.get("draw_amount", 2.0)
    
    users = await users_db.find({"verified": True, "won_draw": {"$ne": True}}).to_list(length=None)
    
    if len(users) < win_count:
        await users_db.update_many({"verified": True}, {"$set": {"won_draw": False}})
        users = await users_db.find({"verified": True, "won_draw": {"$ne": True}}).to_list(length=None)
        
    if not users: return await send_msg(message.chat.id, f"{pe('❌')} No verified users available to draw.")

    today = str(datetime.date.today() - datetime.timedelta(days=7))
    activity = await activity_db.aggregate([
        {"$match": {"date": {"$gte": today}}},
        {"$group": {"_id": "$user_id", "total": {"$sum": "$message_count"}}}
    ]).to_list(length=None)
    
    act_dict = {a["_id"]: a["total"] for a in activity}
    
    population = []
    weights = []
    for u in users:
        population.append(u)
        w = 1 + act_dict.get(u["user_id"], 0)
        weights.append(w)
        
    valid_winners = []
    
    while len(valid_winners) < win_count and population:
        winner = random.choices(population, weights=weights, k=1)[0]
        idx = population.index(winner)
        population.pop(idx)
        weights.pop(idx)
        
        try:
            chat_info = await app.get_chat(winner['user_id'])
            full_name = f"{chat_info.first_name or ''} {chat_info.last_name or ''}".lower()
            name_ok = REQUIRED_USERNAME_TAG.lower() in full_name
            bio_ok = winner.get("bio_link") in (chat_info.bio or "")
            
            if name_ok and bio_ok:
                valid_winners.append(winner)
            else:
                await users_db.update_one({"user_id": winner['user_id']}, {"$set": {"verified": False}})
                lang = await get_lang(winner['user_id'])
                msg = f"{pe('⚠️')} <b>Draw Disqualified!</b> You removed the required name tag or bio link. Please /verify again."
                try: await send_msg(winner['user_id'], msg)
                except: pass
        except:
            pass
            
    if not valid_winners:
        return await send_msg(message.chat.id, f"{pe('❌')} No strictly verified users found (all removed their tags/bio!).")

    winner_ids = [w['user_id'] for w in valid_winners]
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_verified = await users_db.count_documents({"verified": True})
    
    for wid in winner_ids:
        await users_db.update_one({"user_id": wid}, {"$set": {"won_draw": True}, "$inc": {"balance": float(win_amt)}})
        lang = await get_lang(wid)
        msg = f"{pe('🎉')} <b>Congratulations!</b> You won ${win_amt} in today's draw based on your activity!" 
        try: await send_msg(wid, msg)
        except: pass

    await config_db.update_one(
        {"_id": "latest_draw"},
        {"$set": {"time": now, "total": total_verified, "winners": winner_ids, "amount": win_amt}}, upsert=True
    )
    await send_msg(message.chat.id, f"{pe('✅')} <b>Draw Completed!</b>\n{len(valid_winners)} strictly active winners selected and credited ${win_amt}.\nPublic list updated.")

@app.on_message(filters.command("addadmin"))
async def addadmin_cmd(client: Client, message: Message):
    if message.from_user.id != OWNER_ID: return
    try:
        target = int(message.text.split()[1])
        await admins_db.update_one({"user_id": target}, {"$set": {"user_id": target}}, upsert=True)
        await send_msg(message.chat.id, f"{pe('✅')} User <code>{target}</code> is now an Admin.")
    except: await send_msg(message.chat.id, f"Usage: /addadmin [user_id] {pe('⚠️')}")

@app.on_message(filters.command("removeadmin"))
async def removeadmin_cmd(client: Client, message: Message):
    if message.from_user.id != OWNER_ID: return
    try:
        target = int(message.text.split()[1])
        await admins_db.delete_one({"user_id": target})
        await send_msg(message.chat.id, f"{pe('✅')} Admin <code>{target}</code> removed.")
    except: await send_msg(message.chat.id, f"Usage: /removeadmin [user_id] {pe('⚠️')}")

@app.on_message(filters.command("adminlist"))
async def adminlist_cmd(client: Client, message: Message):
    if not await is_admin(message.from_user.id): return
    admins = await admins_db.find().to_list(length=100)
    text = f"{pe('👑')} <b>Owner:</b> <code>{OWNER_ID}</code>\n\n{pe('🛡')} <b>Admins:</b>\n"
    for a in admins: text += f"- <code>{a['user_id']}</code>\n"
    await send_msg(message.chat.id, text)

@app.on_message(filters.command("setprice"))
async def setprice_cmd(client: Client, message: Message):
    if not await is_admin(message.from_user.id): return
    try:
        parts = message.text.split()
        m_req = int(parts[1])
        rew = float(parts[2])
        await config_db.update_one({"_id": "settings"}, {"$set": {"affiliate_req": m_req, "affiliate_reward": rew}}, upsert=True)
        await send_msg(message.chat.id, f"{pe('✅')} Price updated: ${rew} per {m_req} members.")
    except: await send_msg(message.chat.id, f"Usage: /setprice [members] [reward amount] {pe('⚠️')}")

@app.on_message(filters.command("togglewithdraw"))
async def togglewd_cmd(client: Client, message: Message):
    if not await is_admin(message.from_user.id): return
    conf = await get_config()
    new_state = not conf.get("withdrawal_enabled", True)
    await config_db.update_one({"_id": "settings"}, {"$set": {"withdrawal_enabled": new_state}}, upsert=True)
    
    global CONFIG_CACHE
    CONFIG_CACHE["time"] = 0 
    
    await send_msg(message.chat.id, f"{pe('✏️')} Withdrawals are now <b>{'ENABLED' if new_state else 'DISABLED'}</b>.")

@app.on_message(filters.command("broadcast"))
async def broadcast_cmd(client: Client, message: Message):
    if not await is_admin(message.from_user.id): return
    if not message.reply_to_message: return await send_msg(message.chat.id, f"Reply to a message to broadcast. {pe('⚠️')}")
    users = await users_db.find().to_list(length=None)
    sent = 0
    for u in users:
        try:
            await message.reply_to_message.copy(u["user_id"])
            sent += 1
            await asyncio.sleep(0.05) 
        except: pass
    await send_msg(message.chat.id, f"{pe('✅')} Broadcast complete. Sent to {sent} users.")

@app.on_message(filters.command(["check", "checkactivity"]))
async def checkactivity_cmd(client: Client, message: Message):
    if not await is_admin(message.from_user.id): return
    
    target_id = None
    safe_name = "User"
    
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
        safe_name = html.escape(message.reply_to_message.from_user.first_name or "User")
    elif len(message.command) > 1:
        target_input = message.command[1]
        try:
            user_info = await app.get_users(target_input)
            target_id = user_info.id
            safe_name = html.escape(user_info.first_name or "User")
        except:
            try:
                target_id = int(target_input)
            except:
                return await send_msg(message.chat.id, f"{pe('⚠️')} Invalid User ID or Username.")
    else:
        return await send_msg(message.chat.id, f"{pe('⚠️')} Usage: Reply to user or use /check [username/id]")
        
    if not target_id: return
    
    try:
        today = datetime.date.today()
        week_ago = today - datetime.timedelta(days=7)
        month_ago = today - datetime.timedelta(days=30)
        
        pipeline = [
            {"$match": {"user_id": target_id}},
            {"$group": {
                "_id": "$date",
                "total": {"$sum": "$message_count"}
            }}
        ]
        records = await activity_db.aggregate(pipeline).to_list(length=None)
        
        d_count = 0
        w_count = 0
        m_count = 0
        
        for r in records:
            r_date_str = r["_id"]
            try:
                r_date = datetime.date.fromisoformat(r_date_str)
                if r_date == today:
                    d_count += r["total"]
                if r_date >= week_ago:
                    w_count += r["total"]
                if r_date >= month_ago:
                    m_count += r["total"]
            except:
                pass
        
        await send_msg(message.chat.id, f"{pe('📈')} <b>Activity Report for <a href='tg://user?id={target_id}'>{safe_name}</a> (<code>{target_id}</code>)</b>:\n\n{pe('📅')} <b>Today:</b> {d_count} msgs\n{pe('📅')} <b>This Week:</b> {w_count} msgs\n{pe('📅')} <b>This Month:</b> {m_count} msgs")
    except Exception as e: 
        await send_msg(message.chat.id, f"{pe('⚠️')} Error: {e}")

# Admin command for checking affiliate details
@app.on_message(filters.command("affiliatecheck"))
async def affiliatecheck_cmd(client: Client, message: Message):
    if not await is_admin(message.from_user.id): return
    
    target_id = None
    safe_name = "User"
    
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
        safe_name = html.escape(message.reply_to_message.from_user.first_name or "User")
    elif len(message.command) > 1:
        target_input = message.command[1]
        try:
            user_info = await app.get_users(target_input)
            target_id = user_info.id
            safe_name = html.escape(user_info.first_name or "User")
        except:
            try:
                target_id = int(target_input)
            except:
                return await send_msg(message.chat.id, f"{pe('⚠️')} Invalid User ID or Username.")
    else:
        return await send_msg(message.chat.id, f"{pe('⚠️')} Usage: Reply to user or use /affiliatecheck [username/id]")
        
    if not target_id: return
    
    u_doc = await users_db.find_one({"user_id": target_id})
    if not u_doc:
        return await send_msg(message.chat.id, f"{pe('❌')} User not found in database.")
        
    invites = len(u_doc.get("affiliates", []))
    left = len(u_doc.get("left_affiliates", []))
    bal = u_doc.get("balance", 0.0)
    
    text = f"{pe('📊')} <b>Affiliate Check for <a href='tg://user?id={target_id}'>{safe_name}</a></b>:\n\n{pe('👥')} Active Invites: {invites}\n{pe('❌')} Left Invites: {left}\n{pe('💰')} Wallet Balance: ${round(bal, 2)}"
    await send_msg(message.chat.id, text)

# ================= MAIN MENU & INLINE ROUTER =================
@app.on_callback_query(filters.regex("^menu_main$"))
async def cb_menu_main(client: Client, call: CallbackQuery):
    await call.answer()
    if not await pass_fsub(client, call): return 
    
    if call.from_user.id in user_states:
        del user_states[call.from_user.id]
        
    user = await get_or_create_user(call.from_user.id, call.from_user)
    lang = await get_lang(call.from_user.id)
    
    welcome_body = TR[lang]["welcome"].format(tag=REQUIRED_USERNAME_TAG, link=user.get('bio_link', 'No Link Generated'))
    await edit_msg(call.message.chat.id, call.message.id, welcome_body, markup=get_main_menu(lang))

@app.on_callback_query(filters.regex("^menu_verify$"))
async def cb_menu_verify(client: Client, call: CallbackQuery):
    await call.answer()
    if not await pass_fsub(client, call): return 
    user_id = call.from_user.id
    user_data = await get_or_create_user(user_id, call.from_user)
    lang = await get_lang(user_id)
    
    chat_info = await app.get_chat(user_id)
    full_name = f"{call.from_user.first_name or ''} {call.from_user.last_name or ''}".lower()
    name_ok = REQUIRED_USERNAME_TAG.lower() in full_name
    bio_ok = user_data.get("bio_link") in (chat_info.bio or "")

    markup = kb([(TR[lang]["btn_back"], "menu_main", "danger", "🔙")])
    if name_ok and bio_ok:
        await users_db.update_one({"user_id": user_id}, {"$set": {"verified": True}})
        await edit_msg(call.message.chat.id, call.message.id, TR[lang]["verify_ok"], markup=markup)
    else:
        await edit_msg(call.message.chat.id, call.message.id, TR[lang]["verify_fail"].format(tag=REQUIRED_USERNAME_TAG), markup=markup)

@app.on_callback_query(filters.regex("^menu_affiliate$"))
async def cb_menu_affiliate(client: Client, call: CallbackQuery):
    await call.answer()
    if not await pass_fsub(client, call): return 
    user_id = call.from_user.id
    user = await get_or_create_user(user_id, call.from_user)
    lang = await get_lang(user_id)
    conf = await get_config()

    if not conf.get("affiliate_enabled", True):
        markup = kb([(TR[lang]["btn_back"], "menu_main", "danger", "🔙")])
        return await edit_msg(call.message.chat.id, call.message.id, TR[lang]["affiliate_disabled"], markup=markup)
    
    invite_link = user.get("affiliate_link")
    if not invite_link:
        try:
            invite = await app.create_chat_invite_link(TRACK_GROUP_ID, name=f"Affiliate_{user_id}", creates_join_request=True)
            invite_link = invite.invite_link
            await users_db.update_one({"user_id": user_id}, {"$set": {"affiliate_link": invite_link}})
        except:
            return await send_msg(call.message.chat.id, f"Error creating link. Bot must be admin. {pe('❌')}")
            
    markup = kb(
        [("Affiliate Status", "menu_aff_stats", "primary", "📊")],
        [(TR[lang]["btn_back"], "menu_main", "danger", "🔙")]
    )
    await edit_msg(call.message.chat.id, call.message.id, TR[lang]["affiliate_link"].format(link=invite_link), markup=markup, disable_web_page_preview=True)

@app.on_callback_query(filters.regex("^menu_aff_stats$"))
async def cb_menu_aff_stats(client: Client, call: CallbackQuery):
    await call.answer()
    if not await pass_fsub(client, call): return 
    user_id = call.from_user.id
    user = await get_or_create_user(user_id, call.from_user)
    lang = await get_lang(user_id)
    conf = await get_config()
    
    markup = kb([(TR[lang]["btn_back"], "menu_affiliate", "danger", "🔙")])
    await edit_msg(call.message.chat.id, call.message.id, TR[lang]["affiliate_stats"].format(
        real=len(user.get("affiliates", [])), left=len(user.get("left_affiliates", [])), fake=len(user.get("fake_affiliates", [])), 
        reward=conf['affiliate_reward'], req=conf['affiliate_req']
    ), markup=markup)

@app.on_callback_query(filters.regex("^menu_support$"))
async def cb_menu_support(client: Client, call: CallbackQuery):
    await call.answer()
    if not await pass_fsub(client, call): return 
    user_id = call.from_user.id
    lang = await get_lang(user_id)
    
    if user_id in active_tickets or user_id in pending_tickets:
        return await send_msg(call.message.chat.id, f"You already have an active/pending ticket. {pe('⚠️')}")
        
    user_states[user_id] = {"state": "wait_for_support"}
    markup = kb([(TR[lang]["btn_back"], "menu_main", "danger", "🔙")])
    await edit_msg(call.message.chat.id, call.message.id, TR[lang]["sup_ask"], markup=markup)

@app.on_callback_query(filters.regex("^menu_draw$"))
async def cb_menu_draw(client: Client, call: CallbackQuery):
    await call.answer()
    if not await pass_fsub(client, call): return 
    user_id = call.from_user.id
    lang = await get_lang(user_id)
    conf = await get_config()
    
    markup = kb([(TR[lang]["btn_back"], "menu_main", "danger", "🔙")])
    
    if not conf.get("draw_enabled", True):
        return await edit_msg(call.message.chat.id, call.message.id, f"{pe('⚠️')} <b>Draw now disabled, soon coming.</b>", markup=markup)

    draw_data = await config_db.find_one({"_id": "latest_draw"})
    
    if not draw_data or not draw_data.get("winners"):
        return await edit_msg(call.message.chat.id, call.message.id, TR[lang]["draw_none"], markup=markup)
        
    winners_text = ""
    for i, wid in enumerate(draw_data["winners"], 1):
        u_doc = await users_db.find_one({"user_id": wid})
        db_name = u_doc.get("name") if u_doc else None
        name = await fetch_real_name(wid, db_name)
        winners_text += f"{i}. {html.escape(name)}\n"
        
    text = TR[lang]["draw_res"].format(
        time=draw_data["time"], total=draw_data["total"], 
        amt=draw_data.get("amount", 2.0), winners=winners_text
    )
    await edit_msg(call.message.chat.id, call.message.id, text, markup=markup, disable_web_page_preview=True)

@app.on_callback_query(filters.regex("^menu_lang$"))
async def cb_menu_lang(client: Client, call: CallbackQuery):
    await call.answer()
    if not await pass_fsub(client, call): return 
    lang = await get_lang(call.from_user.id)
    btns = kb(
        [("English", "lang_en", "primary", "🇬🇧"), ("Русский", "lang_ru", "danger", "🇷🇺")],
        [("हिंदी (Hindi)", "lang_hi", "success", "🇮🇳")],
        [(TR[lang]["btn_back"], "menu_main", "danger", "🔙")]
    )
    await edit_msg(call.message.chat.id, call.message.id, "Select your language / Выберите язык / भाषा चुनें:", markup=btns)

@app.on_callback_query(filters.regex("^lang_(en|ru|hi)$"))
async def cb_set_lang(client: Client, call: CallbackQuery):
    await call.answer()
    if not await pass_fsub(client, call): return 
    new_lang = call.data.split("_")[1]
    user_id = call.from_user.id
    
    await users_db.update_one({"user_id": user_id}, {"$set": {"lang": new_lang}})
    user_langs[user_id] = new_lang
    
    user = await get_or_create_user(user_id, call.from_user)
    
    welcome_body = TR[new_lang]["welcome"].format(tag=REQUIRED_USERNAME_TAG, link=user.get('bio_link', ''))
    text = TR[new_lang]["lang_set"] + "\n\n" + welcome_body
    
    await edit_msg(call.message.chat.id, call.message.id, text, markup=get_main_menu(new_lang))

@app.on_callback_query(filters.regex("^menu_leaderboard$"))
async def cb_menu_leaderboard(client: Client, call: CallbackQuery):
    await call.answer()
    
    is_private = call.message.chat.id > 0
    if is_private:
        if not await pass_fsub(client, call): return 
        group_id = TRACK_GROUP_ID
    else:
        if not await is_group_authorized(call.message.chat.id): return
        group_id = call.message.chat.id

    lang = await get_lang(call.from_user.id)
    tr = TR.get(lang, TR["en"])
    
    text, max_pages = await generate_leaderboard_text("weekly", 0, group_id)
    
    btn_rows = [
        [(tr["btn_daily"], "ldb_daily_0", "primary", "📅"), 
         (tr["btn_weekly"], "ldb_weekly_0", "success", "📅"), 
         (tr["btn_monthly"], "ldb_monthly_0", "primary", "📅")]
    ]
    
    if max_pages > 0:
        btn_rows.append([("Next ➡️", "ldb_weekly_1", "primary", "➡️")])
        
    if is_private:
        btn_rows.append([(tr["btn_back"], "menu_main", "danger", "🔙")])
        
    btns = kb(*btn_rows)
    await edit_msg(call.message.chat.id, call.message.id, text, markup=btns, disable_web_page_preview=True)

@app.on_callback_query(filters.regex(r"^ldb_(daily|weekly|monthly)_(\d+)$"))
async def cb_ldb_pagination(client: Client, call: CallbackQuery):
    match = re.match(r"^ldb_(daily|weekly|monthly)_(\d+)$", call.data)
    if not match: return await call.answer()
    
    period = match.group(1)
    page = int(match.group(2))
    
    is_private = call.message.chat.id > 0
    group_id = TRACK_GROUP_ID if is_private else call.message.chat.id
    
    lang = await get_lang(call.from_user.id)
    tr = TR.get(lang, TR["en"])
    
    text, max_pages = await generate_leaderboard_text(period, page, group_id)
    
    d_style = "success" if period == "daily" else "primary"
    w_style = "success" if period == "weekly" else "primary"
    m_style = "success" if period == "monthly" else "primary"
    
    btn_rows = [
        [(tr["btn_daily"], "ldb_daily_0", d_style, "📅"),
         (tr["btn_weekly"], "ldb_weekly_0", w_style, "📅"),
         (tr["btn_monthly"], "ldb_monthly_0", m_style, "📅")]
    ]
    
    nav_row = []
    if page > 0:
        nav_row.append(("⬅️ Prev", f"ldb_{period}_{page-1}", "primary", "🔙"))
    if page < max_pages:
        nav_row.append(("Next ➡️", f"ldb_{period}_{page+1}", "primary", "➡️"))
    if nav_row:
        btn_rows.append(nav_row)
        
    if is_private:
        btn_rows.append([(tr["btn_back"], "menu_main", "danger", "🔙")])
        
    markup = kb(*btn_rows)
    
    try:
        await edit_msg(call.message.chat.id, call.message.id, text, markup=markup, disable_web_page_preview=True)
    except Exception:
        pass
    await call.answer()

@app.on_callback_query(filters.regex("^menu_withdraw$"))
async def cb_menu_withdraw(client: Client, call: CallbackQuery):
    await call.answer()
    if not await pass_fsub(client, call): return 
    user_id = call.from_user.id
    lang = await get_lang(user_id)
    conf = await get_config()
    
    if not conf.get("withdrawal_enabled", True): 
        markup = kb([(TR[lang]["btn_back"], "menu_main", "danger", "🔙")])
        return await edit_msg(call.message.chat.id, call.message.id, f"{pe('⚠️')} Withdrawals are disabled.", markup=markup)
        
    user = await get_or_create_user(user_id, call.from_user)
    min_wd = conf.get("min_withdrawal", 20.0)
    
    if user["balance"] < min_wd: 
        markup = kb([(TR[lang]["btn_back"], "menu_main", "danger", "🔙")])
        return await edit_msg(call.message.chat.id, call.message.id, f"{pe('❌')} Your wallet balance is ${round(user['balance'], 2)}. Minimum withdrawal is ${min_wd}.", markup=markup)
        
    user_states[user_id] = {"state": "wait_for_method", "amount": user["balance"]}

    markup = kb(
        [("Redcube Wallet", "wd_method_redcube", "success", "🏦")], 
        [(TR[lang]["btn_back"], "menu_main", "danger", "🔙")]
    )
    await edit_msg(call.message.chat.id, call.message.id, f"{pe('💰')} <b>Balance:</b> ${user['balance']}\n\nPlease select the withdrawal method:", markup=markup)

@app.on_callback_query(filters.regex("^wd_method_redcube$"))
async def cb_wd_method_redcube(client: Client, call: CallbackQuery):
    await call.answer()
    if not await pass_fsub(client, call): return 
    user_id = call.from_user.id
    lang = await get_lang(user_id)
    state_info = user_states.get(user_id, {})
    
    if state_info.get("state") != "wait_for_method":
        return await send_msg(call.message.chat.id, f"Session expired. Please request withdrawal again. {pe('⚠️')}")
        
    amount = state_info["amount"]
    method = "Redcube Wallet"
    
    await users_db.update_one({"user_id": user_id}, {"$inc": {"balance": -float(amount)}})
    del user_states[user_id]
    
    name = call.from_user.first_name or "User"
    if call.from_user.last_name: name += f" {call.from_user.last_name}"
    safe_name = html.escape(name)
    
    btns = kb(
        [("Accept", f"wdone_{user_id}_{amount}", "success"), ("Reject", f"wrej_{user_id}_{amount}", "danger")]
    )
    
    admin_text = f"{pe('🆕')} <b>Withdrawal Request ({method})</b>\n{pe('👨‍💻')} User: <a href='tg://user?id={user_id}'>{safe_name}</a> (<code>{user_id}</code>)\n{pe('💰')} Amount: ${amount}"
    
    admins = await admins_db.find().to_list(100)
    admin_withdraw_msgs[user_id] = {}
    for aid in set([OWNER_ID] + [a["user_id"] for a in admins]):
        try: 
            msg = await send_msg(aid, admin_text, markup=btns)
            if msg: admin_withdraw_msgs[user_id][aid] = msg['message_id']
        except: pass
        
    markup = kb([(TR[lang]["btn_back"], "menu_main", "primary", "🔙")])
    await edit_msg(call.message.chat.id, call.message.id, f"{pe('✅')} Your {method} withdrawal request has been sent to admins.", markup=markup)

# ================= ADMIN BUTTON HANDLERS =================
@app.on_callback_query(filters.regex("^tktacc_"))
async def ticket_accept(client: Client, call: CallbackQuery):
    await call.answer()
    if not await is_admin(call.from_user.id): return
    target_id = int(call.data.split("_")[1])
    
    if target_id not in pending_tickets:
        return await send_msg(call.message.chat.id, f"This ticket is no longer pending or has been closed. {pe('⚠️')}")
        
    pending_tickets.pop(target_id, None) 
    active_tickets[target_id] = call.from_user.id
    active_tickets[call.from_user.id] = target_id
    
    admin_name = html.escape(call.from_user.first_name or "Admin")
    update_text = f"{pe('✅')} <b>Ticket Accepted & Resolved by <a href='tg://user?id={call.from_user.id}'>{admin_name}</a></b>"
    
    if target_id in admin_ticket_msgs:
        for aid, mid in admin_ticket_msgs[target_id].items():
            try: await edit_msg(aid, mid, update_text, markup=None)
            except: pass
        del admin_ticket_msgs[target_id]
    else:
        await edit_msg(call.message.chat.id, call.message.id, update_text, markup=None)
    
    t_lang = await get_lang(target_id)
    await send_msg(target_id, TR[t_lang]["tkt_joined"])
    await send_msg(call.from_user.id, f"{pe('✅')} Session Started with <code>{target_id}</code>.\nUse /close to end.")

@app.on_callback_query(filters.regex("^tktrej_"))
async def ticket_reject(client: Client, call: CallbackQuery):
    await call.answer()
    if not await is_admin(call.from_user.id): return
    target_id = int(call.data.split("_")[1])
    
    text = call.message.text or call.message.caption or ""
    match = re.search(r"#TKT\d+", text)
    ticket_id = match.group(0) if match else "#TKT_UNKNOWN"
    
    if target_id in pending_tickets:
        del pending_tickets[target_id]
    
    admin_name = html.escape(call.from_user.first_name or "Admin")
    update_text = f"{pe('❌')} <b>Ticket Rejected by <a href='tg://user?id={call.from_user.id}'>{admin_name}</a></b>"
    
    if target_id in admin_ticket_msgs:
        for aid, mid in admin_ticket_msgs[target_id].items():
            try: await edit_msg(aid, mid, update_text, markup=None)
            except: pass
        del admin_ticket_msgs[target_id]
    else:
        await edit_msg(call.message.chat.id, call.message.id, update_text, markup=None)
    
    t_lang = await get_lang(target_id)
    try: await send_msg(target_id, TR[t_lang]["tkt_rejected"].format(tkt=ticket_id))
    except: pass

@app.on_callback_query(filters.regex("^wdone_"))
async def wd_done(client: Client, call: CallbackQuery):
    await call.answer()
    if not await is_admin(call.from_user.id): return
    
    _, target_id, amount = call.data.split("_")
    target_id = int(target_id)
    
    user_states[call.from_user.id] = {"state": "wait_for_txlink", "target_id": target_id, "amount": amount}
    
    admin_name = html.escape(call.from_user.first_name or "Admin")
    update_text = f"{pe('✅')} <b>Withdrawal Processed by <a href='tg://user?id={call.from_user.id}'>{admin_name}</a></b>"
    
    if target_id in admin_withdraw_msgs:
        for aid, mid in admin_withdraw_msgs[target_id].items():
            try: await edit_msg(aid, mid, update_text, markup=None)
            except: pass
        del admin_withdraw_msgs[target_id]
    else:
        await edit_msg(call.message.chat.id, call.message.id, update_text, markup=None)
    
    await send_msg(call.message.chat.id, f"{pe('✏️')} <b>Please type the Transaction Link for this withdrawal:</b>")

@app.on_callback_query(filters.regex("^wrej_"))
async def wd_reject(client: Client, call: CallbackQuery):
    await call.answer()
    if not await is_admin(call.from_user.id): return
    
    _, target_id, amount = call.data.split("_")
    target_id = int(target_id)
    
    user_states[call.from_user.id] = {"state": "wait_for_reason", "target_id": target_id, "amount": amount}
    
    admin_name = html.escape(call.from_user.first_name or "Admin")
    update_text = f"{pe('❌')} <b>Withdrawal Rejected by <a href='tg://user?id={call.from_user.id}'>{admin_name}</a></b>"
    
    if target_id in admin_withdraw_msgs:
        for aid, mid in admin_withdraw_msgs[target_id].items():
            try: await edit_msg(aid, mid, update_text, markup=None)
            except: pass
        del admin_withdraw_msgs[target_id]
    else:
        await edit_msg(call.message.chat.id, call.message.id, update_text, markup=None)
    
    await send_msg(call.message.chat.id, f"{pe('✏️')} <b>Please type the reason for rejection:</b>")

# ================= RAIN BUTTON HANDLER =================
@app.on_callback_query(filters.regex("^rain_join_"))
async def cb_rain_join(client: Client, call: CallbackQuery):
    event_id = call.data.split("_")[2]
    user_id = call.from_user.id
    
    event = await rain_db.find_one({"_id": event_id})
    if not event:
        return await call.answer("This event has ended! ⚠️", show_alert=True)
        
    if user_id in event.get("participants", []):
        return await call.answer("You are already participating! ✅", show_alert=True)
        
    min_msgs = event.get("min_msgs", 0)
    today = str(datetime.date.today())
    
    # Strictly checking today's messages
    pipeline = [
        {"$match": {"user_id": user_id, "group_id": call.message.chat.id, "date": today}},
        {"$group": {"_id": None, "total": {"$sum": "$message_count"}}}
    ]
    activity = await activity_db.aggregate(pipeline).to_list(1)
    total_sent = activity[0]["total"] if activity else 0
    
    if total_sent < min_msgs:
        return await call.answer(f"You need at least {min_msgs} messages TODAY in this group to participate!\nYou currently have {total_sent} messages today. ⚠️", show_alert=True)
        
    await rain_db.update_one({"_id": event_id}, {"$addToSet": {"participants": user_id}})
    await call.answer("You have successfully joined the Rain Event! 💧", show_alert=True)

# ================= FSUB CHECK BUTTON HANDLER =================
@app.on_callback_query(filters.regex("^check_fsub$"))
async def cb_check_fsub(client: Client, call: CallbackQuery):
    if await is_user_subscribed(client, call.from_user.id):
        await call.answer("Joined successfully! ✅", show_alert=True)
        user = await get_or_create_user(call.from_user.id, call.from_user)
        lang = await get_lang(call.from_user.id)
        
        await call.message.delete()
        
        welcome_head = TR[lang]["welcome_head"].format(name=html.escape(user['name']))
        await send_msg(call.message.chat.id, welcome_head, disable_web_page_preview=True)
        
        welcome_body = TR[lang]["welcome"].format(tag=REQUIRED_USERNAME_TAG, link=user.get('bio_link', 'No Link Generated'))
        await send_msg(call.message.chat.id, welcome_body, markup=get_main_menu(lang), disable_web_page_preview=True)
    else:
        await call.answer("You haven't joined yet! Please join the channel first. ⚠️", show_alert=True)

@app.on_message(filters.private & filters.text & ~filters.regex(r"^/"))
async def message_handler(client: Client, message: Message):
    if await check_double_msg(message.from_user.id): return
    if not await pass_fsub(client, message): return 
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    state = user_states.get(user_id, {}).get("state")
    
    name = message.from_user.first_name or "User"
    if message.from_user.last_name: name += f" {message.from_user.last_name}"
    safe_name = html.escape(name)
    
    if state == "wait_for_support":
        reason = message.text
        del user_states[user_id]
        
        ticket_id = f"#TKT{random.randint(10000, 99999)}"
        pending_tickets[user_id] = ticket_id  
        
        btns = kb(
            [("Accept", f"tktacc_{user_id}", "success"), ("Reject", f"tktrej_{user_id}", "danger")]
        )
        admin_text = f"{pe('🎟')} <b>New Support Ticket ({ticket_id})</b>\n{pe('👥')} User: <a href='tg://user?id={user_id}'>{safe_name}</a> (<code>{user_id}</code>)\n{pe('✏️')} <b>Reason:</b> {html.escape(reason)}"
        
        admins = await admins_db.find().to_list(100)
        admin_ticket_msgs[user_id] = {}
        for aid in set([OWNER_ID] + [a["user_id"] for a in admins]):
            try: 
                msg = await send_msg(aid, admin_text, markup=btns)
                if msg: admin_ticket_msgs[user_id][aid] = msg['message_id']
            except: pass
            
        markup = kb([(TR[lang]["btn_back"], "menu_main", "primary", "🔙")])
        return await send_msg(message.chat.id, TR[lang]["sup_sent"].format(tkt=ticket_id), markup=markup)

    if state == "wait_for_address":
        address_info = message.text
        amount = user_states[user_id]["amount"]
        method = user_states[user_id].get("method", "TON")
        
        await users_db.update_one({"user_id": user_id}, {"$inc": {"balance": -float(amount)}})
        del user_states[user_id]
        
        btns = kb(
            [("Accept", f"wdone_{user_id}_{amount}", "success"), ("Reject", f"wrej_{user_id}_{amount}", "danger")]
        )
        
        admin_text = f"{pe('🆕')} <b>Withdrawal Request ({method})</b>\n{pe('👨‍💻')} User: <a href='tg://user?id={user_id}'>{safe_name}</a> (<code>{user_id}</code>)\n{pe('💰')} Amount: ${amount}\n{pe('📍')} Address: <code>{html.escape(address_info)}</code>"
        
        admins = await admins_db.find().to_list(100)
        admin_withdraw_msgs[user_id] = {}
        for aid in set([OWNER_ID] + [a["user_id"] for a in admins]):
            try: 
                msg = await send_msg(aid, admin_text, markup=btns)
                if msg: admin_withdraw_msgs[user_id][aid] = msg['message_id']
            except: pass
            
        markup = kb([(TR[lang]["btn_back"], "menu_main", "primary", "🔙")])
        return await send_msg(message.chat.id, f"{pe('✅')} Your {method} withdrawal request has been sent to admins.", markup=markup)

    if state == "wait_for_txlink":
        if not await is_admin(user_id): return
        target_id = user_states[user_id]["target_id"]
        amount = user_states[user_id]["amount"]
        tx_link = message.text
        
        del user_states[user_id]
        
        t_lang = await get_lang(target_id)
        try: await send_msg(target_id, f"{pe('✅')} <b>Your withdrawal of ${amount} has been successfully processed!</b>\n\n{pe('⛓️')} <b>Transaction Link:</b> {html.escape(tx_link)}", disable_web_page_preview=True)
        except: pass
        
        return await send_msg(message.chat.id, f"{pe('✅')} Withdrawal marked as Paid and transaction link sent to user.")

    if state == "wait_for_reason":
        if not await is_admin(user_id): return
        target_id = user_states[user_id]["target_id"]
        amount = user_states[user_id]["amount"]
        reason = message.text
        
        await users_db.update_one({"user_id": target_id}, {"$inc": {"balance": float(amount)}})
        del user_states[user_id]
        
        t_lang = await get_lang(target_id)
        try: await send_msg(target_id, TR[t_lang]["wd_rej"].format(amount=amount, reason=html.escape(reason)))
        except: pass
        return await send_msg(message.chat.id, f"{pe('✅')} Rejection reason sent and funds refunded to user.")

    if user_id in active_tickets:
        target_id = active_tickets[user_id]
        is_sender_admin = await is_admin(user_id)
        try: 
            if is_sender_admin:
                await message.copy(target_id)
            else:
                await message.forward(target_id)
        except: pass

# ================= SAFE DUMMY WEB SERVER (FOR RENDER) =================
async def web_server():
    async def handle(request):
        return web.Response(text="Bot is Alive and Running on Render! ✅")
    
    web_app = web.Application()
    web_app.router.add_get('/', handle)
    runner = web.AppRunner(web_app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8080))
    try:
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        print(f"Fake Web Server Started on port {port} 🌐")
    except Exception as e:
        print(f"Port {port} in use! (Render deploy overlapping). Avoiding crash. Error: {e}")

# ================= STARTUP =================
async def main():
    await app.start()
    
    asyncio.create_task(web_server())
    asyncio.create_task(background_verification_check())
    
    await app.set_bot_commands([
        BotCommand("start", "Start Menu"),
        BotCommand("lang", "Change Language"),
        BotCommand("rank", "View your daily rank"),
        BotCommand("help", "Commands list")
    ])
    print("Bot is successfully running! ✅ Blazing Fast Response & Pure Buttons Active.")
    await idle()
    await app.stop()

if __name__ == "__main__":
    app.run(main())
