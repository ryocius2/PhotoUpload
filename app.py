import os
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from PIL import Image, ImageOps
from werkzeug.utils import secure_filename

load_dotenv()

# Cap Pillow decompression to ~25 megapixels (prevents decompression bombs)
Image.MAX_IMAGE_PIXELS = 25_000_000

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-key-change-me")

limiter = Limiter(get_remote_address, app=app, default_limits=[])

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "16"))
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024

UPLOAD_FOLDER = Path(os.getenv("UPLOAD_FOLDER", "./photos"))
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
THUMB_FOLDER = UPLOAD_FOLDER / "thumbs"
THUMB_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "heic", "heif", "webp"}
ADMIN_KEY = os.getenv("ADMIN_KEY", "wedding-admin-2026")

# Magic bytes for allowed image formats
IMAGE_SIGNATURES = [
    b"\xff\xd8\xff",          # JPEG
    b"\x89PNG\r\n\x1a\n",    # PNG
    b"RIFF",                   # WebP (RIFF....WEBP)
    b"\x00\x00\x00",          # HEIC/HEIF (ftyp box, starts with size bytes)
]


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def valid_image_bytes(stream):
    """Check that the file starts with known image magic bytes."""
    header = stream.read(12)
    stream.seek(0)
    if not header:
        return False
    for sig in IMAGE_SIGNATURES:
        if header.startswith(sig):
            return True
    # HEIC/HEIF: check for 'ftyp' marker at offset 4
    if header[4:8] == b"ftyp":
        return True
    return False


def make_thumbnail(filepath, max_size=(400, 400)):
    """Create a thumbnail for the uploaded photo."""
    try:
        with Image.open(filepath) as img:
            img = ImageOps.exif_transpose(img)
            img = img.convert("RGB")
            img.thumbnail(max_size, Image.LANCZOS)
            thumb_name = Path(filepath).stem + ".jpg"
            thumb_path = THUMB_FOLDER / thumb_name
            img.save(thumb_path, "JPEG", quality=80)
            return thumb_name
    except Exception:
        return None


def get_photo_count():
    """Count total uploaded photos."""
    count = 0
    for ext in ALLOWED_EXTENSIONS:
        count += len(list(UPLOAD_FOLDER.glob(f"*.{ext}")))
    return count


@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self' fonts.googleapis.com fonts.gstatic.com; style-src 'self' 'unsafe-inline' fonts.googleapis.com; font-src fonts.gstatic.com; img-src 'self' blob:; script-src 'self' 'unsafe-inline'"
    return response


VALID_THEMES = {"classic", "kodak", "clear"}


@app.route("/")
def index():
    table = request.args.get("table", "")
    theme = request.args.get("theme", "clear")
    if theme not in VALID_THEMES:
        theme = "classic"
    return render_template(f"theme_{theme}.html", table=table, theme=theme)


@app.route("/upload", methods=["POST"])
@limiter.limit("30/minute")
def upload():
    table = request.form.get("table", "unknown")
    guest_name = request.form.get("guest_name", "anonymous")

    if "photo" not in request.files:
        return jsonify({"error": "No photo selected"}), 400

    file = request.files["photo"]
    if file.filename == "":
        return jsonify({"error": "No photo selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    if not valid_image_bytes(file.stream):
        return jsonify({"error": "File does not appear to be a valid image"}), 400

    # Build filename: table_timestamp_guestname_uuid.ext
    ext = file.filename.rsplit(".", 1)[1].lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = secure_filename(guest_name)[:30] or "anon"
    safe_table = secure_filename(table)[:10] or "unknown"
    unique_id = uuid.uuid4().hex[:6]
    filename = f"table{safe_table}_{timestamp}_{safe_name}_{unique_id}.{ext}"

    filepath = UPLOAD_FOLDER / filename
    file.save(filepath)

    # Generate thumbnail
    thumb = make_thumbnail(filepath)

    photo_count = get_photo_count()

    return jsonify({
        "success": True,
        "filename": filename,
        "thumb": thumb,
        "photo_count": photo_count,
    })


@app.route("/thumbs/<filename>")
def serve_thumb(filename):
    return send_from_directory(THUMB_FOLDER, filename)


@app.route("/photos/<filename>", methods=["GET", "DELETE"])
def serve_photo(filename):
    if request.method == "DELETE":
        if request.args.get("key") != ADMIN_KEY:
            return jsonify({"error": "Unauthorized"}), 403
        safe = secure_filename(filename)
        photo_path = UPLOAD_FOLDER / safe
        thumb_path = THUMB_FOLDER / (Path(safe).stem + ".jpg")
        if not photo_path.exists():
            return jsonify({"error": "Not found"}), 404
        photo_path.unlink()
        if thumb_path.exists():
            thumb_path.unlink()
        return jsonify({"success": True})
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route("/photos")
def photo_list():
    photos = []
    for ext in ALLOWED_EXTENSIONS:
        photos.extend(UPLOAD_FOLDER.glob(f"*.{ext}"))
    photos.sort(key=lambda p: p.stat().st_mtime)
    return jsonify([p.name for p in photos])


@app.route("/slideshow")
def slideshow():
    admin = request.args.get("admin", "") == ADMIN_KEY
    return render_template("slideshow.html", admin=admin, admin_key=ADMIN_KEY if admin else "")


@app.route("/count")
def count():
    return jsonify({"count": get_photo_count()})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
