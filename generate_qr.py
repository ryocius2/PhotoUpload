"""
Generate QR code cards for each table.

Usage:
    python generate_qr.py --url https://photos.yourdomain.com --tables 15

This creates a 'qr_codes/' folder with one PNG per table, ready to print.
"""

import argparse
from pathlib import Path

try:
    import qrcode
    from qrcode.image.styledpil import StyledPilImage
except ImportError:
    print("Install qrcode: pip install qrcode[pil]")
    raise

from PIL import Image, ImageDraw, ImageFont


def generate_table_qr(base_url: str, table_num: int, output_dir: Path):
    url = f"{base_url}/?table={table_num}"

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=12,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#1a1a1a", back_color="#ffffff").convert("RGB")

    # Build card with label
    qr_w, qr_h = qr_img.size
    card_w = qr_w + 60
    card_h = qr_h + 120
    card = Image.new("RGB", (card_w, card_h), "#ffffff")
    card.paste(qr_img, (30, 30))

    draw = ImageDraw.Draw(card)

    # Use a basic font (monospace look)
    try:
        font_big = ImageFont.truetype("arial.ttf", 28)
        font_small = ImageFont.truetype("arial.ttf", 18)
    except OSError:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    label = f"Table {table_num}"
    sublabel = "Scan to share a photo!"

    # Center the text
    bbox = draw.textbbox((0, 0), label, font=font_big)
    tw = bbox[2] - bbox[0]
    draw.text(((card_w - tw) // 2, qr_h + 40), label, fill="#1a1a1a", font=font_big)

    bbox2 = draw.textbbox((0, 0), sublabel, font=font_small)
    tw2 = bbox2[2] - bbox2[0]
    draw.text(((card_w - tw2) // 2, qr_h + 75), sublabel, fill="#666666", font=font_small)

    out_path = output_dir / f"table_{table_num:02d}.png"
    card.save(out_path)
    print(f"  Created {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate wedding table QR codes")
    parser.add_argument("--url", required=True, help="Base URL (e.g. https://photos.yourdomain.com)")
    parser.add_argument("--tables", type=int, default=10, help="Number of tables")
    args = parser.parse_args()

    output_dir = Path("qr_codes")
    output_dir.mkdir(exist_ok=True)

    base = args.url.rstrip("/")
    print(f"Generating QR codes for {args.tables} tables -> {base}")

    for t in range(1, args.tables + 1):
        generate_table_qr(base, t, output_dir)

    print(f"\nDone! Print the PNGs in '{output_dir}/' folder.")


if __name__ == "__main__":
    main()
