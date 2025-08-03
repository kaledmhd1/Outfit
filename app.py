from flask import Flask, request, send_file
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests
import os

app = Flask(__name__)

# تحميل الخط المحلي (ضمن مشروعك)
FONT_PATH = "assets/fonts/arial.ttf"  # تأكد أنك وضعت الخط في هذا المسار

# مواقع الصور على الخلفية
POSITIONS = [
    (485, 473),
    (295, 546),
    (290, 40),
    (479, 100),
    (550, 280),
    (100, 470),
    (600, 50)  # weaponSkinShows
]
SIZES = [(130, 130)] * len(POSITIONS)

@app.route("/outfit-image")
def generate_image():
    try:
        base_image_url = "https://iili.io/39iE4rF.jpg"
        base = Image.open(BytesIO(requests.get(base_image_url).content)).convert("RGBA")
        draw = ImageDraw.Draw(base)

        # الحصول على البيانات من الطلب
        item_ids = request.args.getlist("item_id")
        avatar_id = request.args.get("avatar")
        weapon_skin_id = request.args.get("weaponSkin")

        # رسم العناصر
        for idx, item_id in enumerate(item_ids[:6]):
            url = f"https://pika-ffitmes-api.vercel.app/?item_id={item_id}&watermark=TaitanApi&key=PikaApis"
            try:
                img = Image.open(BytesIO(requests.get(url).content)).convert("RGBA")
                img = img.resize(SIZES[idx], Image.LANCZOS)
                base.paste(img, POSITIONS[idx], img)
            except Exception as e:
                print(f"خطأ تحميل عنصر {item_id}: {e}")

        # رسم سكن السلاح
        if weapon_skin_id:
            try:
                url = f"https://pika-ffitmes-api.vercel.app/?item_id={weapon_skin_id}&watermark=TaitanApi&key=PikaApis"
                img = Image.open(BytesIO(requests.get(url).content)).convert("RGBA")
                img = img.resize((130, 130), Image.LANCZOS)
                base.paste(img, POSITIONS[6], img)
            except Exception as e:
                print(f"خطأ تحميل سكن السلاح {weapon_skin_id}: {e}")

        # رسم صورة الأفاتار
        if avatar_id:
            try:
                avatar_url = f"https://pika-ffitmes-api.vercel.app/?item_id={avatar_id}&watermark=TaitanApi&key=PikaApis"
                avatar = Image.open(BytesIO(requests.get(avatar_url).content)).convert("RGBA")
                avatar = avatar.resize((130, 130), Image.LANCZOS)
                center_x = (base.width - avatar.width) // 2
                center_y = (base.height - avatar.height) // 2
                base.paste(avatar, (center_x, center_y), avatar)

                # كتابة BNGX أسفل الأفاتار
                font_size = 22
                try:
                    font = ImageFont.truetype(FONT_PATH, font_size)
                except:
                    font = ImageFont.load_default()

                text = "BNGX"
                text_width, text_height = draw.textsize(text, font=font)
                text_x = center_x + (avatar.width - text_width) // 2
                text_y = center_y + avatar.height + 5
                draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255, 255))
            except Exception as e:
                print(f"خطأ تحميل الأفاتار {avatar_id}: {e}")

        # حفظ الصورة والإرسال
        img_io = BytesIO()
        base.save(img_io, 'PNG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/png')

    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/")
def index():
    return "Outfit Image Generator by BNGX"

if __name__ == "__main__":
    app.run(debug=True)
