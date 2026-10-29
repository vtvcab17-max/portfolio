#!/usr/bin/env python3
"""Ảnh bằng cấp: in chìm hình mờ rồi mã hoá AES-256-GCM vào assets/edu/creds.bin.

Ảnh gốc nằm ở private/creds/ (không đưa lên git). Trang chỉ giải mã trong trình duyệt và vẽ lên
<canvas>: không có đường dẫn ảnh nào để tải, không lưu được bằng chuột phải, Google Ảnh không lấy được.
Khoá phải nằm trong trang để người xem thấy ảnh, nên đây là che giấu chứ không phải bí mật tuyệt đối;
lớp bảo vệ thật là hình mờ in thẳng vào điểm ảnh.
    python3 scripts/creds.py
"""
import base64, io, json, os, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "private" / "creds"
OUT = ROOT / "assets" / "edu" / "creds.bin"
KEY_FILE = ROOT / "private" / "creds-key.txt"  # khoá hex (không đưa lên git); index.html giữ cùng khoá dưới dạng đã trộn
ITEMS = ["fpt", "arena", "ml"]
FONT = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
MARK = "PHẠM VIỆT HÀ · CHỈ ĐỂ XEM · portfolio.vtvcab17.workers.dev"


def find(name):
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        if (SRC / (name + ext)).exists():
            return SRC / (name + ext)
    raise SystemExit(f"thiếu ảnh gốc {name} trong {SRC}")


def watermark(im):
    im = im.convert("RGB")
    s = 1500 / max(im.size)
    if s < 1:
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    w, h = im.size
    size = max(16, round(min(w, h) / 30))
    font = ImageFont.truetype(FONT, size)
    tile = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    tw = d.textlength(MARK, font=font) + size * 3
    for row, y in enumerate(range(0, h * 2, round(size * 3.4))):
        for x in range(-int(tw) if row % 2 else 0, w * 2, int(tw)):
            d.text((x, y), MARK, font=font, fill=(255, 255, 255, 52), stroke_width=1, stroke_fill=(110, 35, 85, 58))
    tile = tile.rotate(28, resample=Image.BICUBIC).crop((w // 2, h // 2, w // 2 + w, h // 2 + h))
    out = Image.alpha_composite(im.convert("RGBA"), tile)
    band = ImageDraw.Draw(out)
    bh = size * 2
    band.rectangle((0, h - bh, w, h), fill=(20, 18, 30, 170))
    note = "Ảnh đã được mã hoá. Mọi lượt tải ảnh đều được ghi nhận địa chỉ IP."
    fs = round(size * .8)
    while fs > 9 and band.textlength(note, font=ImageFont.truetype(FONT, fs)) > w - size * 2:
        fs -= 1
    band.text((size, h - bh + (bh - fs) // 2 - 2), note, font=ImageFont.truetype(FONT, fs), fill=(255, 255, 255, 235))
    return out.convert("RGB")


def jpg(im, q):
    b = io.BytesIO()
    im.save(b, "JPEG", quality=q, optimize=True)
    return base64.b64encode(b.getvalue()).decode()


def main():
    if not KEY_FILE.exists():
        KEY_FILE.write_text(os.urandom(32).hex())
    key = bytes.fromhex(KEY_FILE.read_text().strip())
    data = {}
    for n in ITEMS:
        im = watermark(Image.open(find(n)))
        th = im.copy(); th.thumbnail((260, 260))
        data[n] = {"full": jpg(im, 80), "thumb": jpg(th, 72), "w": im.width, "h": im.height}
        if "--xem" in sys.argv:
            im.save(ROOT / "private" / f"xem-{n}.jpg")
    iv = os.urandom(12)
    ct = AESGCM(key).encrypt(iv, json.dumps(data).encode(), None)
    OUT.write_bytes(b"PFC1" + iv + ct)
    print(f"Đã mã hoá {len(ITEMS)} ảnh → {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
