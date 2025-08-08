from flask import Flask, request, jsonify, send_file
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
from concurrent.futures import ThreadPoolExecutor

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

def fetch_image_by_id(item_id):
    try:
        url = f"https://pika-ffitmes-api.vercel.app/?item_id={item_id}&watermark=TaitanApi&key=PikaApis"
        img = Image.open(BytesIO(requests.get(url).content)).convert("RGBA")
        return item_id, img
    except Exception as e:
        print(f"Error loading item {item_id}: {e}")
        return item_id, None

def overlay_images(base_image_url, item_ids, avatar_id=None, weapon_skin_id=None, pet_skin_id=None):
    base = Image.open(BytesIO(requests.get(base_image_url).content)).convert("RGBA")
    draw = ImageDraw.Draw(base)

    positions = [
        (520, 550),  # 0
        (330, 646),  # 1
        (320, 140),  # 2
        (519, 210),  # 3
        (590, 390),  # 4
        (145, 210),  # 5
        (150, 550),  # 6 -> weapon
        (70, 380)    # 7 -> pet
    ]
    sizes = [(130, 130)] * len(positions)

    # كل العناصر لتحميلها متزامناً
    items_to_fetch = [(i, item_ids[i]) for i in range(min(6, len(item_ids)))]

    # إضافة السلاح والحيوان في المواقع المحددة
    if weapon_skin_id:
        items_to_fetch.append((6, weapon_skin_id))
    if pet_skin_id:
        items_to_fetch.append((7, pet_skin_id))

    # تحميل الصور في الخلفية
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_pos = {
            executor.submit(fetch_image_by_id, item_id): pos
            for pos, item_id in items_to_fetch
        }

        for future in future_to_pos:
            pos = future_to_pos[future]
            _, img = future.result()
            if img:
                img = img.resize(sizes[pos], Image.LANCZOS)
                base.paste(img, positions[pos], img)

    # الأفاتار
    if avatar_id:
        try:
            avatar_url = f"https://pika-ffitmes-api.vercel.app/?item_id={avatar_id}&watermark=TaitanApi&key=PikaApis"
            avatar = Image.open(BytesIO(requests.get(avatar_url).content)).convert("RGBA")
            avatar = avatar.resize((130, 130), Image.LANCZOS)

            center_x = (base.width - avatar.width) // 2
            center_y = 370
            base.paste(avatar, (center_x, center_y), avatar)

            font = get_font(25)
            text = "DEV: BNGX"
            textbbox = draw.textbbox((0, 0), text, font=font)
            text_width = textbbox[2] - textbbox[0]
            text_x = center_x + (130 - text_width) // 2
            text_y = center_y + 130 + 5
            draw.text((text_x, text_y), text, fill="white", font=font)

        except Exception as e:
            print(f"Error loading avatar {avatar_id}: {e}")

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

    weapon_skin_raw = data.get("basicInfo", {}).get("weaponSkinShows", [])
    weapon_skin_id = weapon_skin_raw[0] if isinstance(weapon_skin_raw, list) and weapon_skin_raw else (
        weapon_skin_raw if isinstance(weapon_skin_raw, int) else None)

    pet_skin_id = data.get("petInfo", {}).get("skinId")

    if not item_ids or not avatar_id:
        return jsonify({"error": "Missing equipped skills or avatar data"}), 500

    image = overlay_images(BASE_IMAGE_URL, item_ids, avatar_id, weapon_skin_id, pet_skin_id)

    img_io = BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')
