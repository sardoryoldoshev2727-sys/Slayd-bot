import zipfile
import re
import io
import os
from pptx import Presentation # Ba'zi o'rinlarda kerak bo'lishi mumkin
from aiogram.types import BufferedInputFile

# === 1. SHABLONNI XML ORQALI TAHRIRLASH VA REKLAMALARDAN TOZALASH ===
def process_xml_template(template_path, title, subtitle, slides_data):
    """
    Shablonni ochib, matnlarni joylaydi va barcha reklamalarni o'chiradi.
    """
    if not os.path.exists(template_path):
        return None

    output = io.BytesIO()
    
    with zipfile.ZipFile(template_path, 'r') as zin:
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                
                # Slaydlar, masterlar va layoutlar ichidagi XML fayllarni tekshiramiz
                if item.filename.endswith('.xml') and 'ppt/' in item.filename:
                    content = data.decode('utf-8')
                    
                    # A. 1-slayd: Asosiy Sarlavhalarni joylash
                    if item.filename == 'ppt/slides/slide1.xml':
                        content = content.replace("Title of Your Presentation", title) #
                        content = content.replace("Compelling subtitle goes here", subtitle) #
                    
                    # B. 2-slayd: AI yaratgan matnni joylash
                    if item.filename == 'ppt/slides/slide2.xml' and slides_data:
                        content = content.replace("Slide Title Goes Here", slides_data[0]['title']) #
                        
                        # To'g'ri yangi qatorga o'tish (Single backslash \n)
                        bullets = "\n".join(slides_data[0].get('bullets', []))
                        # Lorem ipsum matnini o'chirib, o'rniga AI matnini qo'yish
                        content = re.sub(r'Lorem ipsum.*?orci\.', bullets, content, flags=re.DOTALL) #

                    # C. REKLAMALARNI 100% TOZALASH
                    reklamalar = [
                        "© Copyright PresentationGO.com – Free Templates & Infographics for PowerPoint and Google Slides",
                        "Visit our FAQ : www.presentationgo.com/faq/",
                        "PresentationGO.com",
                        "Designed with",
                        "Company Name",
                        "email@company.com",
                        "www.company.com"
                    ]
                    
                    for r in reklamalar:
                        content = content.replace(r, "")
                    
                    # Footerlarni bot nomiga almashtirish
                    content = content.replace("Your Footer Here", "@suvtekin_slayd_bot")
                    content = content.replace("Date", "") # Sanani o'chirish yoki bo'sh qoldirish
                    
                    data = content.encode('utf-8')
                
                # D. POTX formatini PPTX ga aylantirish (muammo bo'lmasligi uchun)
                if item.filename == '[Content_Types].xml':
                    data = data.replace(
                        b'presentationml.template.main+xml', 
                        b'presentationml.presentation.main+xml'
                    ) #

                zout.writestr(item, data)
    
    output.seek(0)
    return output

# === 2. BOTDAGI CALLBACK FUNKSIYASI (SHABLON TANLANGANDA) ===
@dp.callback_query(F.data.startswith("sh_"))
async def cb_shablon(call: CallbackQuery, state: FSMContext):
    shablon_key = call.data.replace("sh_", "") # Masalan: "s1", "s2"
    data = await state.get_data()
    mavzu = data.get("mavzu", "")
    
    await call.message.edit_text(f"⏳ <b>{mavzu}</b> mavzusida slayd tayyorlanmoqda...\nReklamalar tozalanmoqda...", parse_mode="HTML")

    # AI dan ma'lumot olish (llama-3 orqali)
    slides = generate_content(mavzu, 1, 5) 
    
    if not slides:
        await bot.send_message(call.from_user.id, "❌ AI kontent yaratishda xatolik yuz berdi.")
        return

    # Fayl nomini GitHub'dagi faylga moslash
    # Agar GitHub'da "1.pptx" bo'lsa, "s1" -> "1.pptx" bo'ladi
    template_id = shablon_key.replace("s", "")
    # Har ikkala formatni ham tekshiramiz
    possible_files = [f"{template_id}.pptx", f"{template_id}.pptx.potx", f"{template_id}.potx"]
    
    template_path = None
    for f in possible_files:
        if os.path.exists(f):
            template_path = f
            break

    if template_path:
        # Slaydni yaratish va tozalash
        result_file = process_xml_template(
            template_path, 
            mavzu, 
            "AI orqali @suvtekin_slayd_bot tomonidan tayyorlandi", 
            slides
        )

        if result_file:
            await bot.send_document(
                call.from_user.id,
                document=BufferedInputFile(result_file.read(), filename=f"{mavzu}.pptx"),
                caption=f"✅ <b>Tayyor!</b>\n\n📝 Mavzu: {mavzu}\n🎨 Dizayn: {template_path}\n\n💧 @suvtekin_slayd_bot",
                parse_mode="HTML"
            )
            # Foydalanuvchi hisobidan chegirib tashlash
            if data.get("paket") == "bepul":
                use_free(call.from_user.id)
            add_order(call.from_user.id)
            await state.clear()
        else:
            await call.answer("❌ Faylni qayta ishlashda xatolik!", show_alert=True)
    else:
        await call.answer(f"❌ GitHub'da {template_id}-shablon topilmadi!", show_alert=True)
