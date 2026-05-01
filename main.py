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
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '0'))
PORT = int(os.environ.get('PORT', '8080'))

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
    "s1":  {"nomi": "💼 Biznes Pro",     "bg": (16,24,39),    "title": (250,204,21),  "text": (243,244,246), "accent": (250,204,21)},
    "s2":  {"nomi": "🏢 Korporativ",     "bg": (255,255,255), "title": (17,24,39),    "text": (55,65,81),    "accent": (37,99,235)},
    "s3":  {"nomi": "📊 Startup",        "bg": (15,23,42),    "title": (56,189,248),  "text": (203,213,225), "accent": (14,165,233)},
    "s4":  {"nomi": "🎨 Kreativ",        "bg": (88,28,135),   "title": (251,191,36),  "text": (254,243,199), "accent": (236,72,153)},
    "s5":  {"nomi": "🎭 Teatr & Sanat",  "bg": (20,0,30),     "title": (255,200,50),  "text": (255,240,220), "accent": (255,100,150)},
    "s6":  {"nomi": "📸 Foto & Media",   "bg": (10,10,10),    "title": (255,255,255), "text": (200,200,200), "accent": (255,50,50)},
    "s7":  {"nomi": "🎓 Talim",          "bg": (254,252,232), "title": (146,64,14),   "text": (66,32,6),     "accent": (217,119,6)},
    "s8":  {"nomi": "🔬 Ilmiy",          "bg": (240,249,255), "title": (12,74,110),   "text": (8,47,73),     "accent": (2,132,199)},
    "s9":  {"nomi": "📚 Universitet",    "bg": (20,30,50),    "title": (180,160,100), "text": (220,215,195), "accent": (150,130,70)},
    "s10": {"nomi": "💻 Texno Dark",     "bg": (0,0,0),       "title": (0,255,136),   "text": (200,255,220), "accent": (0,200,100)},
    "s11": {"nomi": "🤖 AI & Data",      "bg": (15,15,35),    "title": (139,92,246),  "text": (221,214,254), "accent": (124,58,237)},
    "s12": {"nomi": "⚡ Elektronika",    "bg": (10,10,20),    "title": (0,255,255),   "text": (200,240,255), "accent": (0,200,255)},
    "s13": {"nomi": "🌿 Eko",            "bg": (20,83,45),    "title": (187,247,208), "text": (240,253,244), "accent": (74,222,128)},
    "s14": {"nomi": "🌊 Okean",          "bg": (12,74,110),   "title": (186,230,253), "text": (224,242,254), "accent": (14,165,233)},
    "s15": {"nomi": "🌅 Quyoshli",       "bg": (120,53,15),   "title": (254,243,199), "text": (255,251,235), "accent": (245,158,11)},
    "s16": {"nomi": "🏥 Tibbiyot",       "bg": (255,255,255), "title": (13,148,136),  "text": (17,24,39),    "accent": (20,184,166)},
    "s17": {"nomi": "❤️ Salomatlik",     "bg": (255,241,242), "title": (190,18,60),   "text": (68,10,30),    "accent": (244,63,94)},
    "s18": {"nomi": "🏆 Sport",          "bg": (20,20,20),    "title": (251,146,60),  "text": (255,237,213), "accent": (249,115,22)},
    "s19": {"nomi": "🔥 Energiya",       "bg": (69,10,10),    "title": (254,202,202), "text": (254,226,226), "accent": (239,68,68)},
    "s20": {"nomi": "💎 VIP Premium",    "bg": (10,10,15),    "title": (255,215,0),   "text": (230,230,210), "accent": (218,165,32)},
}

SHRIFTLAR = {
    "f1": "Calibri",
    "f2": "Arial",
    "f3": "Times New Roman",
    "f4": "Verdana",
    "f5": "Georgia",
}

# === DATABASE ===
def init_db():
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY,
        username TEXT,
        free_slides INTEGER DEFAULT 2,
        total_orders INTEGER DEFAULT 0,
        referral_by INTEGER DEFAULT 0
    )''')
    conn.commit()
    conn.close()

def get_user(tid):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE telegram_id=?', (tid,))
    u = c.fetchone()
    conn.close()
    return u

def add_user(tid, username, referral_by=0):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (telegram_id,username,referral_by) VALUES (?,?,?)',
              (tid, username, referral_by))
    conn.commit()
    conn.close()

def update_free(tid, n):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('UPDATE users SET free_slides=free_slides+? WHERE telegram_id=?', (n, tid))
    conn.commit()
    conn.close()

def use_free(tid):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('UPDATE users SET free_slides=free_slides-1 WHERE telegram_id=?', (tid,))
    conn.commit()
    conn.close()

def add_order(tid):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('UPDATE users SET total_orders=total_orders+1 WHERE telegram_id=?', (tid,))
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
    {{"title": "Sarlavha 2", "bullets": ["Nuqta 1", "Nuqta 2", "Nuqta 3"]}}
  ]
}}

O'zbek tilida yoz. Birinchi slayd title slide bo'lsin. Professional va batafsil bo'lsin."""

    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{'role': 'user', 'content': prompt}],
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
        bg.fore_color.rgb = rgb(sh['bg'])

        bar = sl.shapes.add_shape(1, Inches(0), Inches(0), Inches(0.12), Inches(7.5))
        bar.fill.solid()
        bar.fill.fore_color.rgb = rgb(sh['accent'])
        bar.line.fill.background()

        bbar = sl.shapes.add_shape(1, Inches(0), Inches(7.25), Inches(13.33), Inches(0.08))
        bbar.fill.solid()
        bbar.fill.fore_color.rgb = rgb(sh['accent'])
        bbar.line.fill.background()

        if i == 0:
            tf = sl.shapes.add_textbox(Inches(1.2), Inches(2.2), Inches(11), Inches(1.5))
            p = tf.text_frame.add_paragraph()
            p.text = info.get('title', mavzu)
            p.font.size = Pt(48)
            p.font.bold = True
            p.font.name = font
            p.font.color.rgb = rgb(sh['title'])
            p.alignment = PP_ALIGN.CENTER

            tf2 = sl.shapes.add_textbox(Inches(1.2), Inches(4), Inches(11), Inches(1))
            p2 = tf2.text_frame.add_paragraph()
            p2.text = info.get('subtitle', '')
            p2.font.size = Pt(24)
            p2.font.name = font
            p2.font.color.rgb = rgb(sh['text'])
            p2.alignment = PP_ALIGN.CENTER
        else:
            tf = sl.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(12.5), Inches(1))
            p = tf.text_frame.add_paragraph()
            p.text = info.get('title', '')
            p.font.size = Pt(34)
            p.font.bold = True
            p.font.name = font
            p.font.color.rgb = rgb(sh['title'])

            line = sl.shapes.add_shape(1, Inches(0.5), Inches(1.35), Inches(12), Inches(0.05))
            line.fill.solid()
            line.fill.fore_color.rgb = rgb(sh['accent'])
            line.line.fill.background()

            tf2 = sl.shapes.add_textbox(Inches(0.7), Inches(1.5), Inches(12), Inches(5.5))
            tf2.text_frame.word_wrap = True
            first = True
            for bullet in info.get('bullets', [])[:bet]:
                if first:
                    p2 = tf2.text_frame.paragraphs[0]
                    first = False
                else:
                    p2 = tf2.text_frame.add_paragraph()
                p2.text = f"▸  {bullet}"
                p2.font.size = Pt(19)
                p2.font.name = font
                p2.font.color.rgb = rgb(sh['text'])
                p2.space_after = Pt(10)

        wm = sl.shapes.add_textbox(Inches(9), Inches(7.05), Inches(4), Inches(0.4))
        wp = wm.text_frame.add_paragraph()
        wp.text = "💧 @suvtekin_slayd_bot"
        wp.font.size = Pt(9)
        wp.font.name = font
        wp.font.color.rgb = rgb(sh['accent'])
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
        [InlineKeyboardButton(text=f'🆓 Bepul ({free} ta)', callback_data='bepul')],
        [InlineKeyboardButton(text='🥉 2,000 so\'m — 1 ta', callback_data='p2000'),
         InlineKeyboardButton(text='🥈 3,000 so\'m — 2 ta', callback_data='p3000')],
        [InlineKeyboardButton(text='🥇 5,000 so\'m — 4 ta', callback_data='p5000'),
         InlineKeyboardButton(text='💎 8,000 so\'m — 8 ta', callback_data='p8000')],
        [InlineKeyboardButton(text='👑 10,000 so\'m — 15 ta', callback_data='p10000')],
        [InlineKeyboardButton(text='👥 Do\'st taklif', callback_data='referral'),
         InlineKeyboardButton(text='👤 Kabinet', callback_data='kabinet')],
    ])

@dp.message(Command('start'))
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
            await bot.send_message(referral_by, '🎁 Do\'stingiz kirdi! +1 bepul slayd!')
        except: pass

    db = get_user(user.id)
    free = db[2] if db else 2

    await message.answer(
        f'💧 <b>Suv Tekin Slayd Bot</b>\n\n'
        f'Salom, {user.first_name}! 👋\n\n'
        f'🎁 Bepul slayd: <b>{free} ta</b>\n\n'
        f'📦 <b>Paketlar:</b>\n'
        f'• 2,000 → 1 ta slayd\n'
        f'• 3,000 → 2 ta slayd\n'
        f'• 5,000 → 4 ta slayd\n'
        f'• 8,000 → 8 ta slayd\n'
        f'• 10,000 → 15 ta slayd\n\n'
        f'Har buyurtmada <b>3 xil dizayn</b> chiqadi! 🎨\n\n'
        f'👇 Tanlang:',
        parse_mode='HTML',
        reply_markup=main_kb(free)
    )

@dp.callback_query(F.data == 'bepul')
async def cb_bepul(call: CallbackQuery, state: FSMContext):
    db = get_user(call.from_user.id)
    if not db or db[2] <= 0:
        await call.answer('❌ Bepul slayd tugagan!', show_alert=True)
        return
    await state.update_data(paket='bepul', soni=1)
    rows = [[InlineKeyboardButton(text=str(i), callback_data=f'bet_{i}') for i in range(5, 11)]]
    await call.message.edit_text(
        '🆓 <b>Bepul paket</b>\n\n📄 Nechta bet? (5-10)',
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )

@dp.callback_query(F.data.in_(set(PAKETLAR.keys())))
async def cb_paket(call: CallbackQuery, state: FSMContext):
    p = PAKETLAR[call.data]
    await state.update_data(paket=call.data, soni=p['soni'])
    rows = []
    row = []
    for i in range(5, 31):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f'bet_{i}'))
        if len(row) == 5:
            rows.append(row)
            row = []
    if row: rows.append(row)
    await call.message.edit_text(
        f'{p["nomi"]} — <b>{p["narx"]:,} so\'m</b>\n'
        f'📊 Slayd: <b>{p["soni"]} ta</b>\n\n'
        f'📄 <b>Nechta bet?</b> (5-30)',
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )

@dp.callback_query(F.data.startswith('bet_'))
async def cb_bet(call: CallbackQuery, state: FSMContext):
    bet = int(call.data.split('_')[1])
    await state.update_data(bet=bet)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Calibri', callback_data='font_f1'),
         InlineKeyboardButton(text='Arial', callback_data='font_f2')],
        [InlineKeyboardButton(text='Times New Roman', callback_data='font_f3')],
        [InlineKeyboardButton(text='Verdana', callback_data='font_f4'),
         InlineKeyboardButton(text='Georgia', callback_data='font_f5')],
    ])
    await call.message.edit_text(
        f'✅ Bet: <b>{bet} ta</b>\n\n🔤 <b>Shrift tanlang:</b>',
        parse_mode='HTML',
        reply_markup=kb
    )

@dp.callback_query(F.data.startswith('font_'))
async def cb_font(call: CallbackQuery, state: FSMContext):
    shrift = call.data.replace('font_', '')
    await state.update_data(shrift=shrift)
    data = await state.get_data()

    if data.get('paket') == 'bepul':
        await state.set_state(Order.mavzu)
        await call.message.edit_text(
            '📝 <b>Mavzuni yozing:</b>\n<i>(Masalan: O\'zbekiston tarixi)</i>',
            parse_mode='HTML'
        )
    else:
        p = PAKETLAR[data['paket']]
        await call.message.edit_text(
            f'💳 <b>To\'lov</b>\n\n'
            f'📦 {p["nomi"]}: <b>{p["narx"]:,} so\'m</b>\n\n'
            f'📱 Payme/Click: <b>+998 XX XXX XX XX</b>\n'
            f'<i>(Izohga Telegram ID: {call.from_user.id})</i>\n\n'
            f'To\'lovdan so\'ng admin tasdiqlaydi!',
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='✅ To\'lov qildim', callback_data='tolov_qildim')]
            ])
        )

@dp.callback_query(F.data == 'tolov_qildim')
async def cb_tolov(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    p = PAKETLAR.get(data.get('paket'), {})
    if ADMIN_ID:
        await bot.send_message(
            ADMIN_ID,
            f'🆕 <b>Yangi buyurtma!</b>\n\n'
            f'👤 ID: <code>{call.from_user.id}</code>\n'
            f'👤 Ism: {call.from_user.first_name}\n'
            f'📦 Paket: {p.get("nomi")} — {p.get("narx",0):,} so\'m\n\n'
            f'✅ Tasdiqlash: <code>/tolov {call.from_user.id} {data.get("paket")}</code>',
            parse_mode='HTML'
        )
    await state.set_state(Order.mavzu)
    await call.message.edit_text(
        '✅ <b>So\'rov yuborildi!</b>\n\nAdmin tasdiqlashini kuting.\n\n📝 <b>Mavzuni yozing:</b>',
        parse_mode='HTML'
    )

@dp.callback_query(F.data == 'referral')
async def cb_referral(call: CallbackQuery):
    link = f'https://t.me/suvtekin_slayd_bot?start={call.from_user.id}'
    await call.message.edit_text(
        f'👥 <b>Do\'st taklif</b>\n\n'
        f'Sizning link:\n<code>{link}</code>\n\n'
        f'🎁 Do\'st kirsa — ikkalangizga +1 bepul slayd!',
        parse_mode='HTML'
    )

@dp.callback_query(F.data == 'kabinet')
async def cb_kabinet(call: CallbackQuery):
    db = get_user(call.from_user.id)
    free = db[2] if db else 0
    orders = db[3] if db else 0
    await call.message.edit_text(
        f'👤 <b>Kabinet</b>\n\n'
        f'🆔 ID: <code>{call.from_user.id}</code>\n'
        f'💧 Bepul: <b>{free} ta</b>\n'
        f'📦 Buyurtmalar: <b>{orders} ta</b>',
        parse_mode='HTML'
    )

@dp.message(Order.mavzu)
async def get_mavzu(message: Message, state: FSMContext):
    await state.update_data(mavzu=message.text)
    rows = []
    row = []
    for k, v in SHABLONLAR.items():
        row.append(InlineKeyboardButton(text=v['nomi'], callback_data=f'sh_{k}'))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row: rows.append(row)
    await message.answer(
        f'✅ Mavzu: <b>{message.text}</b>\n\n'
        f'🎨 <b>20 ta shablondan birini tanlang:</b>\n'
        f'<i>(Biz 3 xil dizayn yuboramiz!)</i>',
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )

@dp.callback_query(F.data.startswith('sh_'))
async def cb_shablon(call: CallbackQuery, state: FSMContext):
    shablon_key = call.data.replace('sh_', '')
    data = await state.get_data()
    mavzu = data.get('mavzu', '')
    soni = data.get('soni', 1)
    bet = data.get('bet', 5)
    shrift = data.get('shrift', 'f1')

    await call.message.edit_text(
        f'⏳ <b>Slaydlar yaratilmoqda...</b>\n\n'
        f'📝 Mavzu: {mavzu}\n'
        f'📊 Slayd: {soni} ta | 📄 Bet: {bet} ta\n'
        f'🤖 AI kontent tayyorlamoqda...',
        parse_mode='HTML'
    )

    try:
        slides = generate_content(mavzu, soni, bet)
        if not slides:
            await bot.send_message(call.from_user.id, '❌ Xatolik! Qayta urinib ko\'ring.')
            return

        keys = list(SHABLONLAR.keys())
        chosen = [shablon_key]
        other = [k for k in keys if k != shablon_key]
        chosen += random.sample(other, min(2, len(other)))

        for key in chosen:
            pptx = make_pptx(mavzu, slides, key, shrift, bet)
            sh_name = SHABLONLAR[key]['nomi']
            await bot.send_document(
                call.from_user.id,
                document=(f'{mavzu[:15]}_{sh_name}.pptx', pptx),
                caption=f'✅ <b>{mavzu}</b>\n🎨 {sh_name}\n📄 {len(slides)} slayd | {bet} bet\n\n💧 @suvtekin_slayd_bot',
                parse_mode='HTML'
            )

        if data.get('paket') == 'bepul':
            use_free(call.from_user.id)
        add_order(call.from_user.id)
        await state.clear()

        db = get_user(call.from_user.id)
        free = db[2] if db else 0
        await bot.send_message(
            call.from_user.id,
            '🎉 <b>Tayyor!</b> Slaydlaringiz yuborildi!\n\n👇 Yana buyurtma:',
            parse_mode='HTML',
            reply_markup=main_kb(free)
        )

    except Exception as e:
        await bot.send_message(call.from_user.id, f'❌ Xatolik: {e}')

@dp.message(Command('tolov'))
async def cmd_tolov(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer('Format: /tolov <user_id> <paket>')
        return
    uid = int(parts[1])
    paket = parts[2]
    soni = PAKETLAR.get(paket, {}).get('soni', 0)
    update_free(uid, soni)
    await bot.send_message(
        uid,
        f'✅ <b>To\'lovingiz tasdiqlandi!</b>\n\n'
        f'🎁 <b>{soni} ta slayd</b> qo\'shildi!\n\n'
        f'📝 Mavzuni yozing:',
        parse_mode='HTML'
    )
    await message.answer(f'✅ {uid} ga {soni} ta slayd berildi!')

# === RAILWAY HEALTH CHECK ===
async def health_check_server():
    try:
        from aiohttp import web
        async def health(request):
            return web.Response(text='Bot is running! ✅')
        app = web.Application()
        app.router.add_get('/', health)
        app.router.add_get('/health', health)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', PORT)
        await site.start()
        print(f'Health check: http://0.0.0.0:{PORT}')
    except Exception as e:
        print(f'Health check error: {e}')

async def main():
    init_db()
    print('✅ SuvTekin Slayd Bot ishga tushdi!')
    await health_check_server()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
