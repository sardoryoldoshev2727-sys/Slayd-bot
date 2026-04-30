import logging
import os
import io
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import groq
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# === SOZLAMALAR ===
BOT_TOKEN = "SIZNING_BOT_TOKENINGIZ"
GROQ_API_KEY = "SIZNING_GROQ_API_KEYINGIZ"
ADMIN_ID = 6557362871  # @userinfobot dan oling

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
                  referral_by INTEGER DEFAULT 0)''')
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

# === SHABLON DIZAYNLAR ===
SHABLONLAR = {
    "biznes": {
        "nomi": "💼 Biznes Klassik",
        "bg": RGBColor(0x1a, 0x1a, 0x2e),
        "title_color": RGBColor(0xe9, 0x4c, 0x4c),
        "text_color": RGBColor(0xff, 0xff, 0xff),
        "accent": RGBColor(0xe9, 0x4c, 0x4c)
    },
    "zamonaviy": {
        "nomi": "🌟 Zamonaviy",
        "bg": RGBColor(0x0f, 0x3d, 0x6e),
        "title_color": RGBColor(0xff, 0xd7, 0x00),
        "text_color": RGBColor(0xff, 0xff, 0xff),
        "accent": RGBColor(0xff, 0xd7, 0x00)
    },
    "minimal": {
        "nomi": "✨ Minimal Oq",
        "bg": RGBColor(0xff, 0xff, 0xff),
        "title_color": RGBColor(0x2c, 0x3e, 0x50),
        "text_color": RGBColor(0x34, 0x49, 0x5e),
        "accent": RGBColor(0x3a, 0x9b, 0xd5)
    },
    "yashil": {
        "nomi": "🌿 Tabiat",
        "bg": RGBColor(0x1a, 0x3a, 0x2a),
        "title_color": RGBColor(0x2e, 0xcc, 0x71),
        "text_color": RGBColor(0xff, 0xff, 0xff),
        "accent": RGBColor(0x2e, 0xcc, 0x71)
    },
    "kosmik": {
        "nomi": "🚀 Kosmik",
        "bg": RGBColor(0x0d, 0x0d, 0x2b),
        "title_color": RGBColor(0x9b, 0x59, 0xb6),
        "text_color": RGBColor(0xff, 0xff, 0xff),
        "accent": RGBColor(0x9b, 0x59, 0xb6)
    }
}

# === SLAYD YARATISH ===
def create_pptx(mavzu, slides_data, shablon_key):
    shablon = SHABLONLAR[shablon_key]
    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)

    for i, slide_info in enumerate(slides_data):
        slide_layout = prs.slide_layouts[6]  # blank
        slide = prs.slides.add_slide(slide_layout)

        # Background
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = shablon["bg"]

        # Accent chiziq
        from pptx.util import Pt
        txBox = slide.shapes.add_shape(
            1, Inches(0), Inches(0), Inches(0.1), Inches(7.5)
        )
        txBox.fill.solid()
        txBox.fill.fore_color.rgb = shablon["accent"]
        txBox.line.fill.background()

        if i == 0:
            # Title slide
            tf = slide.shapes.add_textbox(Inches(1), Inches(2.5), Inches(11), Inches(1.5))
            p = tf.text_frame.add_paragraph()
            p.text = slide_info.get("title", mavzu)
            p.font.size = Pt(44)
            p.font.bold = True
            p.font.color.rgb = shablon["title_color"]
            p.alignment = PP_ALIGN.CENTER

            tf2 = slide.shapes.add_textbox(Inches(1), Inches(4.2), Inches(11), Inches(0.8))
            p2 = tf2.text_frame.add_paragraph()
            p2.text = slide_info.get("subtitle", "")
            p2.font.size = Pt(22)
            p2.font.color.rgb = shablon["text_color"]
            p2.alignment = PP_ALIGN.CENTER

            # Bot watermark
            wm = slide.shapes.add_textbox(Inches(9), Inches(6.8), Inches(4), Inches(0.5))
            wp = wm.text_frame.add_paragraph()
            wp.text = "💧 @termiz_slayd_bot"
            wp.font.size = Pt(10)
            wp.font.color.rgb = shablon["accent"]
            wp.alignment = PP_ALIGN.RIGHT

        else:
            # Content slide
            tf = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12), Inches(1))
            p = tf.text_frame.add_paragraph()
            p.text = slide_info.get("title", "")
            p.font.size = Pt(32)
            p.font.bold = True
            p.font.color.rgb = shablon["title_color"]

            # Divider line
            line = slide.shapes.add_shape(1, Inches(0.5), Inches(1.4), Inches(12), Inches(0.05))
            line.fill.solid()
            line.fill.fore_color.rgb = shablon["accent"]
            line.line.fill.background()

            # Content
            tf2 = slide.shapes.add_textbox(Inches(0.7), Inches(1.6), Inches(11.5), Inches(5.5))
            tf2.text_frame.word_wrap = True
            first = True
            for bullet in slide_info.get("bullets", []):
                if first:
                    p2 = tf2.text_frame.paragraphs[0]
                    first = False
                else:
                    p2 = tf2.text_frame.add_paragraph()
                p2.text = f"▸ {bullet}"
                p2.font.size = Pt(18)
                p2.font.color.rgb = shablon["text_color"]
                p2.space_after = Pt(8)

            # Watermark
            wm = slide.shapes.add_textbox(Inches(9), Inches(6.8), Inches(4), Inches(0.5))
            wp = wm.text_frame.add_paragraph()
            wp.text = "💧 @termiz_slayd_bot"
            wp.font.size = Pt(10)
            wp.font.color.rgb = shablon["accent"]
            wp.alignment = PP_ALIGN.RIGHT

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf

# === GROQ AI ===
def generate_content(mavzu, slayd_soni):
    client = groq.Groq(api_key=GROQ_API_KEY)
    prompt = f"""Siz professional taqdimot mutaxassisisiz. "{mavzu}" mavzusida {slayd_soni} ta slayd uchun kontent yarating.

JSON formatida qaytaring (boshqa hech narsa yozmang):
{{
  "slides": [
    {{
      "title": "Asosiy sarlavha",
      "subtitle": "Kichik izoh"
    }},
    {{
      "title": "Slayd sarlavhasi",
      "bullets": ["Nuqta 1", "Nuqta 2", "Nuqta 3", "Nuqta 4"]
    }}
  ]
}}

Birinchi slayd title slide bo'lsin. Qolgan {slayd_soni-1} ta content slayd bo'lsin.
O'zbek tilida yozing. Professional va qisqa bo'lsin."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=3000
    )
    
    text = response.choices[0].message.content
    # JSON ni ajratib olish
    import re
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        data = json.loads(json_match.group())
        return data["slides"]
    return None

# === BOT HANDLERLAR ===
logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    referral_by = 0
    
    if context.args:
        try:
            referral_by = int(context.args[0])
        except:
            pass
    
    add_user(user.id, user.username or user.first_name, referral_by)
    
    # Referral bonus
    if referral_by and referral_by != user.id:
        update_free_slides(referral_by, 1)
        update_free_slides(user.id, 1)
        try:
            await context.bot.send_message(
                referral_by,
                "🎁 Do'stingiz botga kirdi! +1 bepul slayd sizga ham, unga ham berildi!"
            )
        except:
            pass

    db_user = get_user(user.id)
    free_count = db_user[2] if db_user else 2

    keyboard = [
        [InlineKeyboardButton("🆓 Bepul slayd", callback_data="bepul"),
         InlineKeyboardButton("💎 Mini — 3,000 so'm", callback_data="mini")],
        [InlineKeyboardButton("🚀 Standart — 5,000 so'm", callback_data="standart"),
         InlineKeyboardButton("⭐ Pro — 8,000 so'm", callback_data="pro")],
        [InlineKeyboardButton("👑 VIP — 10,000 so'm", callback_data="vip")],
        [InlineKeyboardButton("👥 Do'st taklif qilish", callback_data="referral"),
         InlineKeyboardButton("👤 Kabinet", callback_data="kabinet")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"💧 *Suv Tekin Slayd Bot*\n\n"
        f"Assalomu alaykum, {user.first_name}! 👋\n\n"
        f"🎁 Sizda *{free_count} ta bepul slayd* bor!\n\n"
        f"📦 *Paketlar:*\n"
        f"• 🆓 Bepul — 2 ta slayd\n"
        f"• 💎 Mini — 3,000 so'm (3 ta)\n"
        f"• 🚀 Standart — 5,000 so'm (6 ta)\n"
        f"• ⭐ Pro — 8,000 so'm (10 ta)\n"
        f"• 👑 VIP — 10,000 so'm (15 ta)\n\n"
        f"👇 Pastdan tanlang:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    db_user = get_user(user.id)

    if query.data == "bepul":
        if db_user and db_user[2] > 0:
            context.user_data['paket'] = 'bepul'
            context.user_data['slayd_soni'] = 5
            await query.edit_message_text(
                "✅ Bepul paket tanlandi!\n\n"
                "📝 Slayd mavzusini yozing:\n"
                "_(Masalan: O'zbekiston tarixi, Sun tizimi)_",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                "❌ Bepul slaydlaringiz tugagan!\n\n"
                "💎 Paket sotib oling yoki do'st taklif qiling (+1 bepul)!"
            )

    elif query.data in ["mini", "standart", "pro", "vip"]:
        paketlar = {
            "mini": ("💎 Mini", 3000, 3),
            "standart": ("🚀 Standart", 5000, 6),
            "pro": ("⭐ Pro", 8000, 10),
            "vip": ("👑 VIP", 10000, 15)
        }
        nom, narx, soni = paketlar[query.data]
        context.user_data['paket'] = query.data
        context.user_data['slayd_soni'] = soni
        
        await query.edit_message_text(
            f"{nom} paket — *{narx:,} so'm*\n\n"
            f"💳 To'lov qilish uchun:\n"
            f"📱 *Payme/Click:* +998 XX XXX XX XX\n"
            f"_(Sarlavhaga: {user.id})_\n\n"
            f"To'lov qilgach admin tasdiqlaydi va slayd yaratishingiz mumkin bo'ladi.\n\n"
            f"✅ To'lov qildim — /tolov_{query.data}_{user.id}",
            parse_mode="Markdown"
        )

    elif query.data == "referral":
        ref_link = f"https://t.me/termiz_slayd_bot?start={user.id}"
        await query.edit_message_text(
            f"👥 *Do'st taklif qilish*\n\n"
            f"Sizning link:\n`{ref_link}`\n\n"
            f"Do'stingiz shu link orqali kirsa:\n"
            f"🎁 Sizga: +1 bepul slayd\n"
            f"🎁 Do'stingizga: +1 bepul slayd\n\n"
            f"Maksimum: 5 ta bepul slayd!",
            parse_mode="Markdown"
        )

    elif query.data == "kabinet":
        free = db_user[2] if db_user else 0
        orders = db_user[4] if db_user else 0
        await query.edit_message_text(
            f"👤 *Sizning kabinetingiz*\n\n"
            f"🆔 ID: `{user.id}`\n"
            f"👤 Ism: {user.first_name}\n"
            f"💧 Bepul slaydlar: *{free} ta*\n"
            f"📦 Jami buyurtmalar: *{orders} ta*",
            parse_mode="Markdown"
        )

    elif query.data.startswith("shablon_"):
        shablon_key = query.data.replace("shablon_", "")
        context.user_data['shablon'] = shablon_key
        mavzu = context.user_data.get('mavzu', '')
        slayd_soni = context.user_data.get('slayd_soni', 5)

        await query.edit_message_text(
            f"⏳ *Slayd tayyorlanmoqda...*\n\n"
            f"📝 Mavzu: {mavzu}\n"
            f"🎨 Shablon: {SHABLONLAR[shablon_key]['nomi']}\n"
            f"📊 Slayd soni: {slayd_soni} ta\n\n"
            f"🤖 AI kontent yaratmoqda...",
            parse_mode="Markdown"
        )

        try:
            slides_data = generate_content(mavzu, slayd_soni)
            if not slides_data:
                await context.bot.send_message(user.id, "❌ Kontent yaratishda xatolik. Qayta urinib ko'ring.")
                return

            pptx_file = create_pptx(mavzu, slides_data, shablon_key)

            if context.user_data.get('paket') == 'bepul':
                use_free_slide(user.id)

            await context.bot.send_document(
                user.id,
                document=pptx_file,
                filename=f"{mavzu[:30]}.pptx",
                caption=f"✅ *Tayyor!*\n\n"
                        f"📝 Mavzu: {mavzu}\n"
                        f"🎨 Shablon: {SHABLONLAR[shablon_key]['nomi']}\n"
                        f"📊 Slayd soni: {len(slides_data)} ta\n\n"
                        f"💧 @termiz_slayd_bot",
                parse_mode="Markdown"
            )

        except Exception as e:
            await context.bot.send_message(user.id, f"❌ Xatolik: {str(e)}")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    if 'paket' in context.user_data and 'mavzu' not in context.user_data:
        context.user_data['mavzu'] = text

        keyboard = []
        row = []
        for key, shablon in SHABLONLAR.items():
            row.append(InlineKeyboardButton(shablon["nomi"], callback_data=f"shablon_{key}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        await update.message.reply_text(
            f"✅ Mavzu qabul qilindi: *{text}*\n\n"
            f"🎨 Shablonni tanlang:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            "👇 /start bosing va paket tanlang!"
        )

# Admin tolov tasdiqlash
async def admin_tolov(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Ishlatish: /tolov <user_id> <paket>")
        return
    
    user_id = int(context.args[0])
    paket = context.args[1]
    
    paket_slaydlar = {"mini": 3, "standart": 6, "pro": 10, "vip": 15}
    soni = paket_slaydlar.get(paket, 0)
    
    update_free_slides(user_id, soni)
    
    await context.bot.send_message(
        user_id,
        f"✅ To'lovingiz tasdiqlandi!\n\n"
        f"🎁 Sizga *{soni} ta slayd* qo'shildi!\n\n"
        f"Endi /start bosing va slayd yarating!",
        parse_mode="Markdown"
    )
    await update.message.reply_text(f"✅ {user_id} ga {soni} ta slayd qo'shildi!")

# Keep-alive server
class KeepAlive(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot ishlayapti!")
    def log_message(self, format, *args):
        pass

def run_server():
    server = HTTPServer(('0.0.0.0', 3000), KeepAlive)
    server.serve_forever()

def main():
    init_db()
    threading.Thread(target=run_server, daemon=True).start()
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tolov", admin_tolov))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    print("✅ Bot ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()
