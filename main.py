import logging
import os
import io
import sqlite3
import json
import random

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from groq import Groq
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RgbColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# === SOZLAMALAR ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

# === DATABASE ===
def init_db():
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (telegram_id INTEGER PRIMARY KEY,
                  username TEXT,
                  free_slides INTEGER DEFAULT 2,
                  total_orders INTEGER DEFAULT 0,
                  balance INTEGER DEFAULT 0,
                  referral_by INTEGER DEFAULT 0,
                  referral_count INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def get_user(telegram_id):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
    user = c.fetchone()
    conn.close()
    return user

def add_user(telegram_id, username, referral_by=0):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (telegram_id, username, referral_by) VALUES (?, ?, ?)',
              (telegram_id, username, referral_by))
    conn.commit()
    conn.close()

def update_free_slides(telegram_id, count):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('UPDATE users SET free_slides = free_slides + ? WHERE telegram_id = ?', (count, telegram_id))
    conn.commit()
    conn.close()

def use_free_slide(telegram_id):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('UPDATE users SET free_slides = free_slides - 1 WHERE telegram_id = ?', (telegram_id,))
    conn.commit()
    conn.close()

def add_referral(telegram_id):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('UPDATE users SET referral_count = referral_count + 1 WHERE telegram_id = ?', (telegram_id,))
    conn.commit()
    conn.close()

# === PAKETLAR ===
PAKETLAR = {
    'free': {'name': '🆓 Bepul', 'price': 0, 'slides': 2, 'bet_min': 5, 'bet_max': 5},
    'mini': {'name': '💎 Mini', 'price': 3000, 'slides': 3, 'bet_min': 5, 'bet_max': 10},
    'standart': {'name': '🚀 Standart', 'price': 5000, 'slides': 6, 'bet_min': 5, 'bet_max': 12},
    'pro': {'name': '⭐ Pro', 'price': 8000, 'slides': 10, 'bet_min': 10, 'bet_max': 20},
    'vip': {'name': '👑 VIP', 'price': 10000, 'slides': 15, 'bet_min': 12, 'bet_max': 25},
    'mega': {'name': '🔥 MEGA', 'price': 15000, 'slides': 20, 'bet_min': 15, 'bet_max': 30},
}

# === 15 TA SHABLON ===
SHABLONLAR = {
    1: {'name': '💼 Biznes Klassik', 'bg': '1a1a2e', 'title': 'e94c4c', 'text': 'ffffff', 'accent': 'e94c4c'},
    2: {'name': '🌟 Zamonaviy', 'bg': '0f3d6e', 'title': 'ffd700', 'text': 'ffffff', 'accent': 'ffd700'},
    3: {'name': '✨ Minimal Oq', 'bg': 'ffffff', 'title': '2c3e50', 'text': '34495e', 'accent': '3a9bd5'},
    4: {'name': '🌿 Tabiat', 'bg': '1a3a2a', 'title': '2ecc71', 'text': 'ffffff', 'accent': '2ecc71'},
    5: {'name': '🚀 Kosmik', 'bg': '0d0d2b', 'title': '9b59b6', 'text': 'ffffff', 'accent': '9b59b6'},
    6: {'name': '🔥 Energiya', 'bg': '2c0b0e', 'title': 'e74c3c', 'text': 'ffffff', 'accent': 'f39c12'},
    7: {'name': '💧 Suv', 'bg': '0a3d62', 'title': '00d2ff', 'text': 'ffffff', 'accent': '00d2ff'},
    8: {'name': '🌙 Tungi', 'bg': '1a1a2e', 'title': 'a29bfe', 'text': 'dfe6e9', 'accent': 'a29bfe'},
    9: {'name': '🌸 Gul', 'bg': 'fdf2f8', 'title': 'db2777', 'text': '374151', 'accent': 'db2777'},
    10: {'name': '⚡ Elektr', 'bg': '0f172a', 'title': 'fbbf24', 'text': 'e2e8f0', 'accent': 'fbbf24'},
    11: {'name': '🏔️ Tog\'', 'bg': '064e3b', 'title': '34d399', 'text': 'ecfdf5', 'accent': '34d399'},
    12: {'name': '🎨 San\'at', 'bg': '4a044e', 'title': 'e879f9', 'text': 'fae8ff', 'accent': 'e879f9'},
    13: {'name': '🍎 Olma', 'bg': '7f1d1d', 'title': 'fca5a5', 'text': 'fef2f2', 'accent': 'fca5a5'},
    14: {'name': '📱 Texno', 'bg': '111827', 'title': '60a5fa', 'text': 'f3f4f6', 'accent': '60a5fa'},
    15: {'name': '☀️ Quyosh', 'bg': '713f12', 'title': 'fcd34d', 'text': 'fffbeb', 'accent': 'fcd34d'},
}

def hex_to_rgb(hex_color):
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# === SLAYD YARATISH (Mukammal) ===
def create_pptx(mavzu, slides_data, shablon_ids, num_slides):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    for i in range(num_slides):
        shablon = SHABLONLAR[shablon_ids[i % len(shablon_ids)]]
        slide_layout = prs.slide_layouts[6]
        slide = prs.slides.add_slide(slide_layout)

        # Background
        background = slide.background
        fill = background.fill
        fill.solid()
        r, g, b = hex_to_rgb(shablon['bg'])
        fill.fore_color.rgb = RgbColor(r, g, b)

        # Yuqori header
        header = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(1.1)
        )
        header.fill.solid()
        hr, hg, hb = hex_to_rgb(shablon['accent'])
        header.fill.fore_color.rgb = RgbColor(hr, hg, hb)
        header.line.fill.background()

        # Shablon nomi
        header_box = slide.shapes.add_textbox(Inches(0.3), Inches(0.25), Inches(12.7), Inches(0.6))
        hf = header_box.text_frame
        hf.text = f"{shablon['name']} | {mavzu}"
        hp = hf.paragraphs[0]
        hp.font.size = Pt(13)
        hp.font.bold = True
        hp.font.color.rgb = RgbColor(255, 255, 255)
        hp.alignment = PP_ALIGN.RIGHT

        # Sarlavha
        title_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.3), Inches(12.333), Inches(0.9))
        tf = title_box.text_frame
        title_text = slides_data[i]['title'] if i < len(slides_data) else f"{mavzu} - {i+1}"
        tf.text = title_text
        tp = tf.paragraphs[0]
        tp.font.size = Pt(34)
        tp.font.bold = True
        tr, tg, tb = hex_to_rgb(shablon['title'])
        tp.font.color.rgb = RgbColor(tr, tg, tb)

        # Rasm placeholder (o'ng tomonda)
        img_box = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.5), Inches(2.4), Inches(4.3), Inches(3.6)
        )
        img_box.fill.solid()
        ar, ag, ab = hex_to_rgb(shablon['text'])
        img_box.fill.fore_color.rgb = RgbColor(ar, ag, ab)
        img_box.line.color.rgb = RgbColor(hr, hg, hb)
        img_box.line.width = Pt(3)

        # Placeholder matn
        ph_box = slide.shapes.add_textbox(Inches(8.8), Inches(3.9), Inches(3.7), Inches(1))
        phf = ph_box.text_frame
        phf.text = "🖼️ Rasm joyi"
        php = phf.paragraphs[0]
        php.font.size = Pt(18)
        php.font.color.rgb = RgbColor(255, 255, 255)
        php.alignment = PP_ALIGN.CENTER

        # Kontent (chap tomonda)
        content_box = slide.shapes.add_textbox(Inches(0.5), Inches(2.4), Inches(7.5), Inches(4.3))
        cf = content_box.text_frame
        cf.word_wrap = True
        
        points = slides_data[i].get('points', ['Punkt 1', 'Punkt 2', 'Punkt 3']) if i < len(slides_data) else ['Ma\'lumot yuklanmoqda...']
        
        for j, point in enumerate(points):
            if j == 0:
                p = cf.paragraphs[0]
            else:
                p = cf.add_paragraph()
            p.text = f"▸ {point}"
            p.font.size = Pt(19)
            cr, cg, cb = hex_to_rgb(shablon['text'])
            p.font.color.rgb = RgbColor(cr, cg, cb)
            p.space_after = Pt(14)

        # Pastki chiziq
        line = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0), Inches(7.15), Inches(13.333), Inches(0.06)
        )
        line.fill.solid()
        line.fill.fore_color.rgb = RgbColor(hr, hg, hb)
        line.line.fill.background()

        # Footer
        footer = slide.shapes.add_textbox(Inches(0.5), Inches(7.25), Inches(12.333), Inches(0.3))
        ff = footer.text_frame
        ff.text = f"@suvtekin_slayd_bot | {mavzu} | {i+1}/{num_slides}"
        fp = ff.paragraphs[0]
        fp.font.size = Pt(10)
        fp.font.color.rgb = RgbColor(150, 150, 150)
        fp.alignment = PP_ALIGN.CENTER

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf

# === GROQ AI ===
groq_client = Groq(api_key=GROQ_API_KEY)

def generate_content(mavzu, slayd_soni):
    prompt = f"""Mavzu: "{mavzu}"
{slayd_soni} ta slayd uchun o'zbek tilida batafsil matn yarat.
Har bir slayd uchun:
- Sarlavha (5-7 so'z, qiziqarli)
- 3-4 ta punkt (har biri 1-2 qator, aniq va tushunarli)
JSON formatda:
[{{"title": "...", "points": ["...", "...", "..."]}}, ...]"""
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        content = response.choices[0].message.content
        start = content.find('[')
        end = content.rfind(']') + 1
        if start != -1 and end != 0:
            return json.loads(content[start:end])
    except Exception as e:
        print(f"Groq xato: {e}")
    
    return [{"title": f"{mavzu} - {i+1}", "points": ["Ma'lumot yuklanmoqda...", "Punkt 2", "Punkt 3"]} for i in range(slayd_soni)]

# === BOT ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class OrderState(StatesGroup):
    waiting_topic = State()
    selecting_bet = State()
    selecting_template = State()

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🆓 Bepul slayd (2 ta)", callback_data="paket_free")],
        [
            InlineKeyboardButton("💎 Mini — 3 000", callback_data="paket_mini"),
            InlineKeyboardButton("🚀 Standart — 5 000", callback_data="paket_standart"),
        ],
        [
            InlineKeyboardButton("⭐ Pro — 8 000", callback_data="paket_pro"),
            InlineKeyboardButton("👑 VIP — 10 000", callback_data="paket_vip"),
        ],
        [InlineKeyboardButton("🔥 MEGA (20 ta) — 15 000", callback_data="paket_mega")],
        [InlineKeyboardButton("👤 Kabinet", callback_data="kabinet")],
    ])

def bet_keyboard(min_bet, max_bet):
    buttons = []
    row = []
    for i in range(min_bet, max_bet + 1):
        row.append(InlineKeyboardButton(str(i), callback_data=f"bet_{i}"))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def template_keyboard(selected=None):
    if selected is None:
        selected = []
    buttons = []
    for i in range(1, 16):
        shablon = SHABLONLAR[i]
        status = "✅" if i in selected else "⬜"
        text = f"{status} #{i} {shablon['name']}"
        buttons.append([InlineKeyboardButton(text, callback_data=f"shablon_{i}")])
    buttons.append([
        InlineKeyboardButton("✅ Tasdiqlash", callback_data="shablon_confirm"),
        InlineKeyboardButton("🔄 Tozalash", callback_data="shablon_clear"),
    ])
    buttons.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="back_paket")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    args = message.text.split()
    
    referral_by = 0
    if len(args) > 1:
        try:
            referral_by = int(args[1])
        except:
            pass
    
    add_user(user.id, user.username or user.first_name, referral_by)
    
    if referral_by and referral_by != user.id:
        referrer = get_user(referral_by)
        if referrer and referrer[6] < 3:  # referral_count < 3
            update_free_slides(referral_by, 1)
            update_free_slides(user.id, 1)
            add_referral(referral_by)
            try:
                await bot.send_message(referral_by, "🎁 Do'stingiz botga kirdi! +1 bepul slayd sizga ham, unga ham berildi!")
            except:
                pass

    db_user = get_user(user.id)
    free_count = db_user[2] if db_user else 2

    await message.answer(
        f"💧 *Suv Tekin Slayd Bot*\n\n"
        f"Assalomu alaykum, {user.first_name}! 👋\n\n"
        f"🎁 Sizda *{free_count} ta bepul slayd* bor!\n\n"
        f"📦 *Paketlar:*\n"
        f"• 🆓 Bepul — 2 ta slayd\n"
        f"• 💎 Mini — 3,000 so'm (3 ta)\n"
        f"• 🚀 Standart — 5,000 so'm (6 ta)\n"
        f"• ⭐ Pro — 8,000 so'm (10 ta)\n"
        f"• 👑 VIP — 10,000 so'm (15 ta)\n"
        f"• 🔥 MEGA — 15,000 so'm (20 ta)\n\n"
        f"👇 Pastdan tanlang:",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data.startswith("paket_"))
async def paket_select(callback: CallbackQuery, state: FSMContext):
    paket = callback.data.replace("paket_", "")
    
    if paket not in PAKETLAR:
        await callback.answer("❌ Xato!", show_alert=True)
        return
    
    data = PAKETLAR[paket]
    
    if paket == 'free':
        db_user = get_user(callback.from_user.id)
        if not db_user or db_user[2] <= 0:
            await callback.answer("❌ Bepul slaydlaringiz tugagan!", show_alert=True)
            return
        
        await state.set_state(OrderState.waiting_topic)
        await state.update_data(
            paket='free',
            slides=data['slides'],
            bet=5,
            price=0,
            shablonlar=random.sample(range(1, 16), 3),
            is_free=True
        )
        await callback.message.edit_text(
            "🆓 *Bepul Slayd*\n\n"
            "📝 Slayd mavzusini yozing:\n"
            "_(Masalan: O'zbekiston tarixi)_",
            parse_mode="Markdown"
        )
        return
    
    await state.set_state(OrderState.selecting_bet)
    await state.update_data(paket=paket, **data)
    
    await callback.message.edit_text(
        f"{data['name']} Paket\n\n"
        f"💰 Narx: *{data['price']:,} so'm*\n"
        f"📊 Slayd: *{data['slides']} ta*\n\n"
        f"📄 *Nechta bet tanlaysiz?*\n"
        f"({data['bet_min']} - {data['bet_max']})",
        parse_mode="Markdown",
        reply_markup=bet_keyboard(data['bet_min'], data['bet_max'])
    )

@dp.callback_query(OrderState.selecting_bet, F.data.startswith("bet_"))
async def process_bet(callback: CallbackQuery, state: FSMContext):
    bet = int(callback.data.replace("bet_", ""))
    await state.update_data(bet=bet)
    await state.set_state(OrderState.selecting_template)
    await state.update_data(selected_shablonlar=[])
    
    await callback.message.edit_text(
        "🎨 *15 ta shablondan 3 ta tanlang*\n\n"
        "Har bir shablonni bosing va \"Tasdiqlash\" ni bosing:\n\n"
        "⬜ = Tanlanmagan\n"
        "✅ = Tanlangan",
        parse_mode="Markdown",
        reply_markup=template_keyboard()
    )

@dp.callback_query(OrderState.selecting_template, F.data.startswith("shablon_"))
async def process_shablon(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get('selected_shablonlar', [])
    
    if callback.data == "shablon_confirm":
        if len(selected) != 3:
            await callback.answer(f"❌ 3 ta tanlash kerak! (Hozir: {len(selected)})", show_alert=True)
            return
        
        await state.set_state(OrderState.waiting_topic)
        await callback.message.edit_text(
            f"✅ *Tanlangan shablonlar:*\n"
            f"{chr(10).join([f'🎨 #{s} {SHABLONLAR[s][\"name\"]}' for s in selected])}\n\n"
            f"📝 *Mavzuni yozing:*\n"
            f"Masalan: \"O'zbekiston iqtisodiyoti\"",
            parse_mode="Markdown"
        )
        return
    
    if callback.data == "shablon_clear":
        await state.update_data(selected_shablonlar=[])
        await callback.message.edit_reply_markup(reply_markup=template_keyboard())
        return
    
    shablon_num = int(callback.data.replace("shablon_", ""))
    
    if shablon_num in selected:
        selected.remove(shablon_num)
    else:
        if len(selected) < 3:
            selected.append(shablon_num)
        else:
            await callback.answer("❌ Faqat 3 ta!", show_alert=True)
            return
    
    await state.update_data(selected_shablonlar=selected)
    await callback.message.edit_reply_markup(reply_markup=template_keyboard(selected))

@dp.message(OrderState.waiting_topic)
async def process_topic(message: Message, state: FSMContext):
    topic = message.text
    data = await state.get_data()
    await state.update_data(topic=topic)
    
    if data.get('is_free'):
        await create_and_send_slides(message, state)
        return
    
    selected = data['selected_shablonlar']
    await message.answer(
        f"📋 *Buyurtma tasdiqlash*\n\n"
        f"📦 {data['name']}\n"
        f"📝 Mavzu: *{topic}*\n"
        f"📄 Bet: *{data['bet']} ta*\n"
        f"🎨 Shablonlar: *{', '.join([f'#{s}' for s in selected])}*\n"
        f"💰 Narx: *{data['price']:,} so'm*\n\n"
        f"To'g'rimi?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("✅ Ha, to'g'ri", callback_data="confirm_yes")],
            [InlineKeyboardButton("🔄 Qayta tanlash", callback_data="confirm_no")],
        ])
    )

async def create_and_send_slides(message_or_callback, state: FSMContext):
    data = await state.get_data()
    user_id = message_or_callback.from_user.id if hasattr(message_or_callback, 'from_user') else message_or_callback.chat.id
    
    msg = await message_or_callback.answer("⏳ Slayd tayyorlanmoqda...") if hasattr(message_or_callback, 'answer') else await bot.send_message(user_id, "⏳ Slayd tayyorlanmoqda...")
    
    try:
        topic = data['topic']
        num_slides = data['slides']
        shablonlar = data.get('selected_shablonlar', random.sample(range(1, 16), 3))
        
        await msg.edit_text("🤖 AI matn yaratmoqda...")
        slides_data = generate_content(topic, num_slides)
        
        await msg.edit_text("🎨 Slaydlar yaratilmoqda...")
        
        for sid in shablonlar:
            pptx_file = create_pptx(topic, slides_data, [sid], num_slides)
            
            caption = f"✅ *{topic}*\n🎨 Shablon: #{sid} {SHABLONLAR[sid]['name']}\n📄 {num_slides} ta slayd"
            
            if hasattr(message_or_callback, 'answer_document'):
                await message_or_callback.answer_document(
                    FSInputFile(pptx_file, filename=f"{topic[:30]}_{sid}.pptx"),
                    caption=caption,
                    parse_mode="Markdown"
                )
            else:
                await bot.send_document(
                    user_id,
                    FSInputFile(pptx_file, filename=f"{topic[:30]}_{sid}.pptx"),
                    caption=caption,
                    parse_mode="Markdown"
                )
        
        if data.get('is_free'):
            use_free_slide(user_id)
            db_user = get_user(user_id)
            remaining = db_user[2] if db_user else 0
            await bot.send_message(
                user_id,
                f"✅ Tayyor! Qolgan bepul: *{remaining}* ta",
                parse_mode="Markdown",
                reply_markup=main_menu()
            )
        else:
            await bot.send_message(
                user_id,
                "✅ Buyurtma tayyor! To'lov tasdiqlangandan keyin yuboriladi.",
                parse_mode="Markdown",
                reply_markup=main_menu()
            )
        
        await msg.delete()
        
    except Exception as e:
        await msg.edit_text(f"❌ Xatolik: {str(e)}")
    
    await state.clear()

@dp.callback_query(F.data == "confirm_yes")
async def confirm_yes(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await create_and_send_slides(callback, state)

@dp.callback_query(F.data == "confirm_no")
async def confirm_no(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderState.selecting_template)
    await state.update_data(selected_shablonlar=[])
    await callback.message.edit_text(
        "🎨 *Qayta tanlash*\n\n"
        "15 ta shablondan 3 ta tanlang:",
        parse_mode="Markdown",
        reply_markup=template_keyboard()
    )

@dp.callback_query(F.data == "back_main")
async def back_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await cmd_start(callback.message, state)

@dp.callback_query(F.data == "back_paket")
async def back_paket(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🎓 *Suv💧Tekin 💙SLAYD*\n\n"
        "Quyidagilardan tanlang:",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "kabinet")
async def kabinet(callback: CallbackQuery):
    user_id = callback.from_user.id
    db_user = get_user(user_id)
    
    free = db_user[2] if db_user else 0
    orders = db_user[4] if db_user else 0
    referral = db_user[6] if db_user else 0
    
    await callback.message.edit_text(
        f"👤 *Sizning kabinetingiz*\n\n"
        f"🆔 ID: `{user_id}`\n"
        f"🆓 Bepul slaydlar: *{free} ta*\n"
        f"📦 Jami buyurtmalar: *{orders} ta*\n"
        f"👥 Do'st keltirgan: *{referral} ta*\n\n"
        f"💡 Do'st keltirsangiz, +1 bepul slayd!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("👥 Do'st taklif qilish", callback_data="referral")],
            [InlineKeyboardButton("⬅️ Asosiy menyu", callback_data="back_main")],
        ])
    )

@dp.callback_query(F.data == "referral")
async def referral(callback: CallbackQuery):
    user_id = callback.from_user.id
    bot_info = await bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={user_id}"
    
    await callback.message.edit_text(
        f"👥 *Do'st taklif qilish*\n\n"
        f"Sizning link:\n`{link}`\n\n"
        f"Do'stingiz shu link orqali kirsa:\n"
        f"🎁 Sizga: +1 bepul slayd\n"
        f"🎁 Do'stingizga: +1 bepul slayd\n\n"
        f"Maksimum: 5 ta bepul slayd!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("📤 Ulashish", url=f"https://t.me/share/url?url={link}&text=🎓 Professional slayd bot!")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="kabinet")],
        ])
    )

@dp.message(Command("tolov"))
async def admin_tolov(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    args = message.text.split()
    if len(args) < 3:
        await message.answer("Ishlatish: /tolov <user_id> <paket>")
        return
    
    user_id = int(args[1])
    paket = args[2]
    
    if paket not in PAKETLAR:
        await message.answer("❌ Noto'g'ri paket!")
        return
    
    soni = PAKETLAR[paket]['slides']
    update_free_slides(user_id, soni)
    
    await bot.send_message(
        user_id,
        f"✅ To'lovingiz tasdiqlandi!\n\n"
        f"🎁 Sizga *{soni} ta slayd* qo'shildi!\n\n"
        f"Endi /start bosing va slayd yarating!",
        parse_mode="Markdown"
    )
    await message.answer(f"✅ {user_id} ga {soni} ta slayd qo'shildi!")

async def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN topilmadi!")
        return
    
    init_db()
    print("🤖 Bot ishga tushmoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
