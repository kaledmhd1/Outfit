from flask import Flask, request, jsonify, send_file
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

app = Flask(__name__)

BASE_IMAGE_URL = "https://iili.io/39iE4rF.jpg"

API_KEYS = {
    "BNGX": True,
    "20DAY": True,
    "busy": False
}

def is_key_valid(api_key):
    return API_KEYS.get(api_key, False)

def fetch_data(region, uid):
    url = f"https://razor-info.vercel.app/player-info?uid={uid}&region={region}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[Error] Razor Info API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"[Exception] Failed to fetch data: {e}")
        return None

def overlay_images(base_image, item_ids, avatar_id=None, weapon_skin_id=None):
    base = Image.open(BytesIO(requests.get(base_image).content)).convert("RGBA")
    draw = ImageDraw.Draw(base)

    positions = [
        (485, 473),
        (295, 546),
        (290, 40),
        (479, 100),
        (550, 280),
        (100, 470),
        (600, 50)
    ]
    sizes = [(130, 130)] * len(positions)

    if avatar_id:
        try:
            avatar_url = f"https://pika-ffitmes-api.vercel.app/?item_id={avatar_id}&watermark=TaitanApi&key=PikaApis"
            avatar = Image.open(BytesIO(requests.get(avatar_url).content)).convert("RGBA")
            avatar = avatar.resize((130, 130), Image.LANCZOS)
            center_x = (base.width - avatar.width) // 2
            center_y = (base.height - avatar.height) // 2
            base.paste(avatar, (center_x, center_y), avatar)

            # محاولة تحميل arial.ttf من المجلد، وإن لم يكن موجودًا نستخدم الخط الافتراضي
            try:
                font_path = os.path.join(os.path.dirname(__file__), "arial.ttf")
                font = ImageFont.truetype(font_path, 24)
            except:
                font = ImageFont.load_default()

            text = "BNGX"
            text_width, text_height = draw.textsize(text, font=font)
            text_x = center_x + (130 - text_width) // 2
            text_y = center_y + 130 + 5
            draw.text((text_x, text_y), text, fill="white", font=font)

        except Exception as e:
            print(f"[Error] Loading avatar {avatar_id}: {e}")

    for idx, item_id in enumerate(item_ids[:6]):
        item_url = f"https://pika-ffitmes-api.vercel.app/?item_id={item_id}&watermark=TaitanApi&key=PikaApis"
        try:
            item = Image.open(BytesIO(requests.get(item_url).content)).convert("RGBA")
            item = item.resize(sizes[idx], Image.LANCZOS)
            base.paste(item, positions[idx], item)
        except Exception as e:
            print(f"[Error] Loading item {item_id}: {e}")
            continue

    if weapon_skin_id:
        try:
            weapon_url = f"https://pika-ffitmes-api.vercel.app/?item_id={weapon_skin_id}&watermark=TaitanApi&key=PikaApis"
            weapon = Image.open(BytesIO(requests.get(weapon_url).content)).convert("RGBA")
            weapon = weapon.resize((130, 130), Image.LANCZOS)
            base.paste(weapon, positions[6], weapon)
        except Exception as e:
            print(f"[Error] Loading weapon skin {weapon_skin_id}: {e}")

    return base

@app.route('/api', methods=['GET'])
def generate_image():
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

    profile = data["profileInfo"]
    item_ids = profile.get("equipedSkills", [])
    avatar_id = profile.get("avatarId")

    weapon_skin_raw = profile.get("weaponSkinShows")
    weapon_skin_id = None
    if isinstance(weapon_skin_raw, list) and weapon_skin_raw:
        weapon_skin_id = weapon_skin_raw[0]
    elif isinstance(weapon_skin_raw, int):
        weapon_skin_id = weapon_skin_raw

    if not item_ids or not avatar_id:
        return jsonify({"error": "Missing equipped skills or avatar data"}), 500

    try:
        image = overlay_images(BASE_IMAGE_URL, item_ids, avatar_id, weapon_skin_id)
        img_io = BytesIO()
        image.save(img_io, 'PNG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/png')
    except Exception as e:
        print(f"[Exception] Error generating image: {e}")
        return jsonify({"error": f"Image generation failed: {str(e)}"}), 500

# Vercel handler
handler = app
