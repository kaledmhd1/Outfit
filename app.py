from flask import Flask, request, jsonify, send_file
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

app = Flask(__name__)

BASE_IMAGE_URL = "https://i.postimg.cc/DyMZRFqX/IMG-0918-3.png"

API_KEYS = {
    "BNGX": True,
    "20DAY": True,
    "busy": False
}

# ==== الأدوات ====

def is_key_valid(api_key):
    return API_KEYS.get(api_key, False)

def fetch_data(region, uid):
    url = f"https://razor-info.vercel.app/player-info?uid={uid}&region={region}"
    try:
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"Error fetching player data: {e}")
        return None

def get_font(size=24):
    try:
        return ImageFont.truetype("Tajawal-Bold.ttf", size)
    except:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)

def overlay_images(base_image_url, item_ids, avatar_id=None, weapon_skin_id=None, pet_skin_id=None):
    base = Image.open(BytesIO(requests.get(base_image_url).content)).convert("RGBA")
    draw = ImageDraw.Draw(base)

    # مواقع العناصر مع اضافة موقع للحيوان الأليف (مثلا تحت سكن السلاح)
    positions = [
        (520, 550),  # 0
        (330, 646),  # 1
        (320, 140),  # 2
        (519, 210),  # 3
        (590, 390),  # 4
        (100, 510),  # 5
        (150, 550),  # 6 -> سكن سلاح
        (70, 380)   # 7 -> مكان الحيوان الأليف
    ]
    sizes = [(130, 130)] * len(positions)

    # الأفاتار
    if avatar_id:
        try:
            avatar_url = f"https://pika-ffitmes-api.vercel.app/?item_id={avatar_id}&watermark=TaitanApi&key=PikaApis"
            avatar = Image.open(BytesIO(requests.get(avatar_url).content)).convert("RGBA")
            avatar = avatar.resize((130, 130), Image.LANCZOS)

            center_x = (base.width - avatar.width) // 2
            center_y = 370
            base.paste(avatar, (center_x, center_y), avatar)

            # كتابة "DEV: BNGX" تحت الأفاتار
            font = get_font(25)
            text = "DEV: BNGX"
            textbbox = draw.textbbox((0, 0), text, font=font)
            text_width = textbbox[2] - textbbox[0]
            text_x = center_x + (130 - text_width) // 2
            text_y = center_y + 130 + 5
            draw.text((text_x, text_y), text, fill="white", font=font)

        except Exception as e:
            print(f"Error loading avatar {avatar_id}: {e}")

    # العناصر الأخرى
    for idx, item_id in enumerate(item_ids[:6]):
        try:
            item_url = f"https://pika-ffitmes-api.vercel.app/?item_id={item_id}&watermark=TaitanApi&key=PikaApis"
            item = Image.open(BytesIO(requests.get(item_url).content)).convert("RGBA")
            item = item.resize(sizes[idx], Image.LANCZOS)
            base.paste(item, positions[idx], item)
        except Exception as e:
            print(f"Error loading item {item_id}: {e}")
            continue

    # سكن السلاح (واحد فقط)
    if weapon_skin_id:
        try:
            weapon_url = f"https://pika-ffitmes-api.vercel.app/?item_id={weapon_skin_id}&watermark=TaitanApi&key=PikaApis"
            weapon = Image.open(BytesIO(requests.get(weapon_url).content)).convert("RGBA")
            weapon = weapon.resize((130, 130), Image.LANCZOS)
            base.paste(weapon, positions[6], weapon)
        except Exception as e:
            print(f"Error loading weapon skin {weapon_skin_id}: {e}")

    # الحيوان الأليف (واحد فقط)
    if pet_skin_id:
        try:
            pet_url = f"https://pika-ffitmes-api.vercel.app/?item_id={pet_skin_id}&watermark=TaitanApi&key=PikaApis"
            pet = Image.open(BytesIO(requests.get(pet_url).content)).convert("RGBA")
            pet = pet.resize((130, 130), Image.LANCZOS)
            base.paste(pet, positions[7], pet)
        except Exception as e:
            print(f"Error loading pet skin {pet_skin_id}: {e}")

    return base

# ==== المسار الرئيسي ====

@app.route('/api', methods=['GET'])
def api():
    region = request.args.get('region')
    uid = request.args.get('uid')
    api_key = request.args.get('key')

    if not region or not uid or not api_key:
        return jsonify({"error": "Missing region, uid, or key parameter"}), 400

    if not is_key_valid(api_key):
        return jsonify({"error": "Invalid or inactive API key"}), 403

    data = fetch_data(region, uid)
    if not data or "profileInfo" not in data:
        return jsonify({"error": "Failed to fetch valid profile data"}), 500

    profile = data.get("profileInfo", {})
    item_ids = profile.get("equipedSkills", [])
    avatar_id = profile.get("avatarId")

    # قراءة سكن السلاح من basicInfo وليس profileInfo
    weapon_skin_raw = data.get("basicInfo", {}).get("weaponSkinShows", [])
    weapon_skin_id = None
    if isinstance(weapon_skin_raw, list) and weapon_skin_raw:
        weapon_skin_id = weapon_skin_raw[0]
    elif isinstance(weapon_skin_raw, int):
        weapon_skin_id = weapon_skin_raw

    # قراءة سكن الحيوان الأليف من petInfo
    pet_skin_id = None
    pet_info = data.get("petInfo", {})
    if pet_info:
        pet_skin_id = pet_info.get("skinId")

    if not item_ids or not avatar_id:
        return jsonify({"error": "Missing equipped skills or avatar data"}), 500

    image = overlay_images(BASE_IMAGE_URL, item_ids, avatar_id, weapon_skin_id, pet_skin_id)

    img_io = BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

# ==== تشغيل السيرفر محلياً ====

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)