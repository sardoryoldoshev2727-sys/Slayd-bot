import asyncio
import io
import json
import logging
import os
import random
import re
import sqlite3

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (BufferedInputFile, CallbackQuery,
                            InlineKeyboardButton, InlineKeyboardMarkup,
                            Message)
from groq import Groq
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

# === SOZLAMALAR ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

# === NARXLAR ===
PAKETLAR = {
    "p2000":  {"nomi": "🥉 Standart", "narx": 2000,  "soni": 1},
    "p3000":  {"nomi": "🥈 Silver",   "narx": 3000,  "soni": 2},
    "p5000":  {"nomi": "🥇 Gold",     "narx": 5000,  "soni": 4},
    "p8000":  {"nomi": "💎 Premium",  "narx": 8000,  "soni": 8},
    "p10000": {"nomi": "👑 VIP",      "narx": 10000, "soni": 15},
}

# === 20 TA SHABLON ===
SHABLONLAR = {
    "s1":  {"nomi": "💼 Biznes Pro",   "bg": (15,32,67),    "title": (255,215,0),   "text": (255,255,255), "accent": (255,215,0)},
    "s2":  {"nomi": "🌟 Zamonaviy",   "bg": (10,10,30),    "title": (0,255,200),   "text": (255,255,255), "accent": (0,255,200)},
    "s3":  {"nomi": "✨ Minimal Oq",  "bg": (255,255,255), "title": (30,30,90),    "text": (50,50,80),    "accent": (41,128,185)},
    "s4":  {"nomi": "🌿 Tabiat",      "bg": (20,55,35),    "title": (100,220,100), "text": (255,255,255), "accent": (46,204,113)},
    "s5":  {"nomi": "🚀 Kosmik",      "bg": (5,5,25),      "title": (180,100,255), "text": (255,255,255), "accent": (155,89,182)},
    "s6":  {"nomi": "🔴 Qizil Kuch",  "bg": (80,10,10),    "title": (255,80,80),   "text": (255,255,255), "accent": (255,80,80)},
    "s7":  {"nomi": "🌊 Okean",       "bg": (5,30,70),     "title": (100,200,255), "text": (255,255,255), "accent": (52,152,219)},
    "s8":  {"nomi": "🎨 San'at",      "bg": (40,10,60),    "title": (255,150,255), "text": (255,255,255), "accent": (200,100,255)},
    "s9":  {"nomi": "🏆 Sport",       "bg": (20,20,20),    "title": (255,150,0),   "text": (255,255,255), "accent": (255,150,0)},
    "s10": {"nomi": "🏥 Tibbiyot",    "bg": (240,248,255), "title": (0,100,150),   "text": (30,30,80),    "accent": (0,180,150)},
    "s11": {"nomi": "📚 Ilmiy",       "bg": (245,245,250), "title": (20,60,120),   "text": (40,40,80),    "accent": (41,128,185)},
    "s12": {"nomi": "🌸 Bahor",       "bg": (255,240,245), "title": (180,50,100),  "text": (80,20,50),    "accent": (220,80,130)},
    "s13": {"nomi": "🌅 Quyosh",      "bg": (255,250,220), "title": (180,100,0),   "text": (80,50,0),     "accent": (230,150,0)},
    "s14": {"nomi": "🗿 Tarixiy",     "bg": (60,40,20),    "title": (220,180,100), "text": (255,235,180), "accent": (200,160,80)},
    "s15": {"nomi": "💻 Texno",       "bg": (5,15,5),      "title": (0,255,50),    "text": (200,255,200), "accent": (0,200,50)},
    "s16": {"nomi": "🎭 Teatr",       "bg": (30,0,30),     "title": (255,200,0),   "text": (255,240,200), "accent": (200,150,0)},
    "s17": {"nomi": "❄️ Muzli",       "bg": (220,240,255), "title": (0,80,160),    "text": (20,60,120),   "accent": (100,180,255)},
    "s18": {"nomi": "🔥 Olov",        "bg": (30,5,0),      "title": (255,120,0),   "text": (255,220,180), "accent": (255,80,0)},
    "s19": {"nomi": "🌙 Tungi",       "bg": (10,10,40),    "title": (200,200,255), "text": (180,180,240), "accent": (150,150,255)},
    "s20": {"nomi": "🎓 Ta'lim",      "bg": (250,250,255), "title": (0,50,150),    "text": (30,30,100),   "accent": (0,100,200)},
}

# === 5 XIL SHRIFT ===
SHRIFTLAR = {
    "f1": "Calibri",
    "f2": "Arial",
    "f3": "Times New Roman",
    "f4": "Verdana",
    "f5": "Georgia",
}

# === DATABASE ===
def init_db():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY,
        username TEXT,
        free_slides INTEGER DEFAULT 2,
        total_orders INTEGER DEFAULT 0,
        referral_by INTEGER DEFAULT 0
    )""")
    conn.commit()
    conn.close()

def get_user(tid):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE telegram_id=?", (tid,))
    u = c.fetchone()
    conn.close()
    return u

def add_user(tid, username, referral_by=0):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (telegram_id,username,referral_by) VALUES (?,?,?)",
              (tid, username, referral_by))
    conn.commit()
    conn.close()

def update_free(tid, n):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("UPDATE users SET free_slides=free_slides+? WHERE telegram_id=?", (n, tid))
    conn.commit()
    conn.close()

def use_free(tid):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("UPDATE users SET free_slides=free_slides-1 WHERE telegram_id=?", (tid,))
    conn.commit()
    conn.close()

def add_order(tid):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("UPDATE users SET total_orders=total_orders+1 WHERE telegram_id=?", (tid,))
    conn.commit()
    conn.close()

# === GROQ AI ===
def generate_content(mavzu, soni, bet):
    client = Groq(api_key=GROQ_API_KEY)
    prompt = f"""Sen professional taqdimot mutaxassisisiz.
"{mavzu}" mavzusida {soni} ta slayd uchun kontent yarat.
Har slaydda {bet} ta bullet point bo'lsin (har biri 1-2 gap, batafsil).

FAQAT JSON qaytar:
{{
  "slides": [
    {{"title": "Sarlavha", "subtitle": "Kichik izoh"}},
    {{"title": "Sarlavha 2", "bullets": ["Nuqta 1", "Nuqta 2", "Nuqta 3"]}},
    ...
  ]
}}

O'zbek tilida yoz. Birinchi slayd title slide bo'lsin. Professional va batafsil bo'lsin."""

    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4000
    )
    text = r.choices[0].message.content
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        return json.loads(m.group())["slides"]
    return None

# === SLAYD YARATISH ===
def make_pptx(mavzu, slides, shablon_key, shrift_key, bet):
    sh = SHABLONLAR[shablon_key]
    font = SHRIFTLAR.get(shrift_key, "Calibri")
    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)

    def rgb(t): return RGBColor(*t)

    for i, info in enumerate(slides):
        sl = prs.slides.add_slide(prs.slide_layouts[6])

        bg = sl.background.fill
        bg.solid()
        bg.fore_color.rgb = rgb(sh["bg"])

        bar = sl.shapes.add_shape(1, Inches(0), Inches(0), Inches(0.12), Inches(7.5))
        bar.fill.solid()
        bar.fill.fore_color.rgb = rgb(sh["accent"])
        bar.line.fill.background()

        bbar = sl.shapes.add_shape(1, Inches(0), Inches(7.2), Inches(13.33), Inches(0.08))
        bbar.fill.solid()
        bbar.fill.fore_color.rgb = rgb(sh["accent"])
        bbar.line.fill.background()

        if i == 0:
            tf = sl.shapes.add_textbox(Inches(1.2), Inches(2), Inches(11), Inches(1.8))
            p = tf.text_frame.add_paragraph()
            p.text = info.get("title", mavzu)
            p.font.size = Pt(48)
            p.font.bold = True
            p.font.name = font
            p.font.color.rgb = rgb(sh["title"])
            p.alignment = PP_ALIGN.CENTER

            tf2 = sl.shapes.add_textbox(Inches(1.2), Inches(4), Inches(11), Inches(1))
            p2 = tf2.text_frame.add_paragraph()
            p2.text = info.get("subtitle", "")
            p2.font.size = Pt(24)
            p2.font.name = font
            p2.font.color.rgb = rgb(sh["text"])
            p2.alignment = PP_ALIGN.CENTER
        else:
            tf = sl.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(12.5), Inches(1))
            p = tf.text_frame.add_paragraph()
            p.text = info.get("title", "")
            p.font.size = Pt(34)
            p.font.bold = True
            p.font.name = font
            p.font.color.rgb = rgb(sh["title"])

            line = sl.shapes.add_shape(1, Inches(0.5), Inches(1.35), Inches(12), Inches(0.05))
            line.fill.solid()
            line.fill.fore_color.rgb = rgb(sh["accent"])
            line.line.fill.background()

            tf2 = sl.shapes.add_textbox(Inches(0.7), Inches(1.5), Inches(12), Inches(5.5))
            tf2.text_frame.word_wrap = True
            first = True
            for bullet in info.get("bullets", [])[:bet]:
                if first:
                    p2 = tf2.text_frame.paragraphs[0]
                    first = False
                else:
                    p2 = tf2.text_frame.add_paragraph()
                p2.text = f"▸  {bullet}"
                p2.font.size = Pt(19)
                p2.font.name = font
                p2.font.color.rgb = rgb(sh["text"])
                p2.space_after = Pt(10)

        wm = sl.shapes.add_textbox(Inches(9), Inches(7.05), Inches(4), Inches(0.4))
        wp = wm.text_frame.add_paragraph()
        wp.text = "💧 @suvtekin_slayd_bot"
        wp.font.size = Pt(9)
        wp.font.name = font
        wp.font.color.rgb = rgb(sh["accent"])
        wp.alignment = PP_ALIGN.RIGHT

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf

# === STATE ===
class Order(StatesGroup):
    bet = State()
    shrift = State()
    mavzu = State()
    shablon = State()

# === BOT ===
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

def main_kb(free):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🆓 Bepul ({free} ta)", callback_data="bepul")],
        [InlineKeyboardButton(text="🥉 2,000 so'm — 1 ta", callback_data="p2000"),
         InlineKeyboardButton(text="🥈 3,000 so'm — 2 ta", callback_data="p3000")],
        [InlineKeyboardButton(text="🥇 5,000 so'm — 4 ta", callback_data="p5000"),
         InlineKeyboardButton(text="💎 8,000 so'm — 8 ta", callback_data="p8000")],
        [InlineKeyboardButton(text="👑 10,000 so'm — 15 ta", callback_data="p10000")],
        [InlineKeyboardButton(text="👥 Do'st taklif", callback_data="referral"),
         InlineKeyboardButton(text="👤 Kabinet", callback_data="kabinet")],
    ])

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    args = message.text.split()
    referral_by = int(args[1]) if len(args) > 1 and args[1].isdigit() else 0

    add_user(user.id, user.username or user.first_name, referral_by)

    if referral_by and referral_by != user.id:
        update_free(referral_by, 1)
        update_free(user.id, 1)
        try:
            await bot.send_message(referral_by, "🎁 Do'stingiz kirdi! +1 bepul slayd!")
        except: pass

    db = get_user(user.id)
    free = db[2] if db else 2

    await message.answer(
        f"💧 <b>Suv Tekin Slayd Bot</b>\n\n"
        f"Salom, {user.first_name}! 👋\n\n"
        f"🎁 Bepul slayd: <b>{free} ta</b>\n\n"
        f"📦 <b>Paketlar:</b>\n"
        f"• 2,000 → 1 ta slayd\n"
        f"• 3,000 → 2 ta slayd\n"
        f"• 5,000 → 4 ta slayd\n"
        f"• 8,000 → 8 ta slayd\n"
        f"• 10,000 → 15 ta slayd\n\n"
        f"Har buyurtmada <b>3 xil dizayn</b> chiqadi! 🎨\n\n"
        f"👇 Tanlang:",
        parse_mode="HTML",
        reply_markup=main_kb(free)
    )

@dp.callback_query(F.data == "bepul")
async def cb_bepul(call: CallbackQuery, state: FSMContext):
    db = get_user(call.from_user.id)
    if not db or db[2] <= 0:
        await call.answer("❌ Bepul slayd tugagan!", show_alert=True)
        return
    await state.update_data(paket="bepul", soni=1)
    rows = [[InlineKeyboardButton(text=str(i), callback_data=f"bet_{i}") for i in range(5, 11)]]
    await call.message.edit_text(
        "🆓 <b>Bepul paket</b>\n\n📄 Nechta bet? (5-10)",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )

@dp.callback_query(F.data.in_(set(PAKETLAR.keys())))
async def cb_paket(call: CallbackQuery, state: FSMContext):
    p = PAKETLAR[call.data]
    await state.update_data(paket=call.data, soni=p["soni"])
    rows = []
    row = []
    for i in range(5, 31):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"bet_{i}"))
        if len(row) == 5:
            rows.append(row)
            row = []
    if row: rows.append(row)
    await call.message.edit_text(
        f"{p['nomi']} — <b>{p['narx']:,} so'm</b>\n"
        f"📊 Slayd: <b>{p['soni']} ta</b>\n\n"
        f"📄 <b>Nechta bet?</b> (5-30)",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )

@dp.callback_query(F.data.startswith("bet_"))
async def cb_bet(call: CallbackQuery, state: FSMContext):
    bet = int(call.data.split("_")[1])
    await state.update_data(bet=bet)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Calibri", callback_data="font_f1"),
         InlineKeyboardButton(text="Arial", callback_data="font_f2")],
        [InlineKeyboardButton(text="Times New Roman", callback_data="font_f3")],
        [InlineKeyboardButton(text="Verdana", callback_data="font_f4"),
         InlineKeyboardButton(text="Georgia", callback_data="font_f5")],
    ])
    await call.message.edit_text(
        f"✅ Bet: <b>{bet} ta</b>\n\n🔤 <b>Shrift tanlang:</b>",
        parse_mode="HTML",
        reply_markup=kb
    )

@dp.callback_query(F.data.startswith("font_"))
async def cb_font(call: CallbackQuery, state: FSMContext):
    shrift = call.data.replace("font_", "")
    await state.update_data(shrift=shrift)
    data = await state.get_data()

    if data.get("paket") == "bepul":
        await state.set_state(Order.mavzu)
        await call.message.edit_text(
            "📝 <b>Mavzuni yozing:</b>\n<i>(Masalan: O'zbekiston tarixi)</i>",
            parse_mode="HTML"
        )
    else:
        p = PAKETLAR[data["paket"]]
        await call.message.edit_text(
            f"💳 <b>To'lov</b>\n\n"
            f"📦 {p['nomi']}: <b>{p['narx']:,} so'm</b>\n\n"
            f"📱 Payme/Click: <b>+998 XX XXX XX XX</b>\n"
            f"<i>(Izohga Telegram ID: {call.from_user.id})</i>\n\n"
            f"To'lovdan so'ng admin tasdiqlaydi!",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ To'lov qildim", callback_data="tolov_qildim")]
            ])
        )

@dp.callback_query(F.data == "tolov_qildim")
async def cb_tolov(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    p = PAKETLAR.get(data.get("paket"), {})
    if ADMIN_ID:
        await bot.send_message(
            ADMIN_ID,
            f"🆕 <b>Yangi buyurtma!</b>\n\n"
            f"👤 ID: <code>{call.from_user.id}</code>\n"
            f"👤 Ism: {call.from_user.first_name}\n"
            f"📦 Paket: {p.get('nomi')} — {p.get('narx',0):,} so'm\n\n"
            f"✅ Tasdiqlash: <code>/tolov {call.from_user.id} {data.get('paket')}</code>",
            parse_mode="HTML"
        )
    await state.set_state(Order.mavzu)
    await call.message.edit_text(
        "✅ <b>So'rov yuborildi!</b>\n\nAdmin tasdiqlashini kuting.\n\n📝 <b>Mavzuni yozing:</b>",
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "referral")
async def cb_referral(call: CallbackQuery):
    link = f"https://t.me/suvtekin_slayd_bot?start={call.from_user.id}"
    await call.message.edit_text(
        f"👥 <b>Do'st taklif</b>\n\n"
        f"Sizning link:\n<code>{link}</code>\n\n"
        f"🎁 Do'st kirsa — ikkalangizga +1 bepul slayd!",
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "kabinet")
async def cb_kabinet(call: CallbackQuery):
    db = get_user(call.from_user.id)
    free = db[2] if db else 0
    orders = db[3] if db else 0
    await call.message.edit_text(
        f"👤 <b>Kabinet</b>\n\n"
        f"🆔 ID: <code>{call.from_user.id}</code>\n"
        f"💧 Bepul: <b>{free} ta</b>\n"
        f"📦 Buyurtmalar: <b>{orders} ta</b>",
        parse_mode="HTML"
    )

@dp.message(Order.mavzu)
async def get_mavzu(message: Message, state: FSMContext):
    await state.update_data(mavzu=message.text)
    rows = []
    row = []
    for k, v in SHABLONLAR.items():
        row.append(InlineKeyboardButton(text=v["nomi"], callback_data=f"sh_{k}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row: rows.append(row)
    await message.answer(
        f"✅ Mavzu: <b>{message.text}</b>\n\n"
        f"🎨 <b>20 ta shablondan birini tanlang:</b>\n"
        f"<i>(Biz 3 xil dizayn yuboramiz!)</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )

@dp.callback_query(F.data.startswith("sh_"))
async def cb_shablon(call: CallbackQuery, state: FSMContext):
    shablon_key = call.data.replace("sh_", "")
    data = await state.get_data()
    mavzu = data.get("mavzu", "")
    soni = data.get("soni", 1)
    bet = data.get("bet", 5)
    shrift = data.get("shrift", "f1")

    await call.message.edit_text(
        f"⏳ <b>Slaydlar yaratilmoqda...</b>\n\n"
        f"📝 Mavzu: {mavzu}\n"
        f"📊 Slayd: {soni} ta | 📄 Bet: {bet} ta\n"
        f"🤖 AI kontent tayyorlamoqda...",
        parse_mode="HTML"
    )

    try:
        slides = generate_content(mavzu, soni, bet)
        if not slides:
            await bot.send_message(call.from_user.id, "❌ Xatolik! Qayta urinib ko'ring.")
            return

        keys = list(SHABLONLAR.keys())
        chosen = [shablon_key]
        other = [k for k in keys if k != shablon_key]
        chosen += random.sample(other, min(2, len(other)))

        for key in chosen:
            pptx = make_pptx(mavzu, slides, key, shrift, bet)
            sh_name = SHABLONLAR[key]["nomi"]
            await bot.send_document(
                call.from_user.id,
                document=BufferedInputFile(pptx.read(), filename=f"{mavzu[:15]}_{sh_name}.pptx"),
                caption=f"✅ <b>{mavzu}</b>\n🎨 {sh_name}\n📄 {len(slides)} slayd | {bet} bet\n\n💧 @suvtekin_slayd_bot",
                parse_mode="HTML"
            )

        if data.get("paket") == "bepul":
            use_free(call.from_user.id)
        add_order(call.from_user.id)
        await state.clear()

        db = get_user(call.from_user.id)
        free = db[2] if db else 0
        await bot.send_message(
            call.from_user.id,
            "🎉 <b>Tayyor!</b> Slaydlaringiz yuborildi!\n\n👇 Yana buyurtma:",
            parse_mode="HTML",
            reply_markup=main_kb(free)
        )

    except Exception as e:
        await bot.send_message(call.from_user.id, f"❌ Xatolik: {e}")

@dp.message(Command("tolov"))
async def cmd_tolov(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Format: /tolov <user_id> <paket>")
        return
    uid = int(parts[1])
    paket = parts[2]
    soni = PAKETLAR.get(paket, {}).get("soni", 0)
    update_free(uid, soni)
    await bot.send_message(
        uid,
        f"✅ <b>To'lovingiz tasdiqlandi!</b>\n\n"
        f"🎁 <b>{soni} ta slayd</b> qo'shildi!\n\n"
        f"📝 Mavzuni yozing:",
        parse_mode="HTML"
    )
    await message.answer(f"✅ {uid} ga {soni} ta slayd berildi!")

async def main():
    init_db()
    print("✅ SuvTekin Slayd Bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
