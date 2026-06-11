"""Usta marka placeholder görselleri üretir (icon / adaptive-icon / splash).

Tema "Gece Garajı": koyu zemin (#16181D) + sarı vurgu. Basit, anahtar (wrench)
benzeri bir glif ve "USTA" wordmark çizer. Gerçek bir tasarımcı işi yerine geçmez
ama EAS build'in geçmesi için geçerli, markaya uygun asset'ler sağlar.

Çalıştır:  python scripts/gen_assets.py
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

BG = (22, 24, 29)        # #16181D — gece garajı zemini
YELLOW = (245, 197, 24)  # sarı vurgu
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(HERE, "assets")
os.makedirs(ASSETS, exist_ok=True)


def _font(size: int) -> ImageFont.FreeTypeFont:
    for path in (
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _wrench(draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float, color) -> None:
    """Basit, stilize bir anahtar (eğik kol + iki uçta açık ağız)."""
    import math

    length = int(420 * scale)
    width = int(120 * scale)
    angle = math.radians(-45)
    dx, dy = math.cos(angle), math.sin(angle)
    px, py = -dy, dx  # dik vektör

    half = length / 2
    hw = width / 2
    # Kol gövdesi (dörtgen)
    corners = [
        (cx - dx * half - px * hw, cy - dy * half - py * hw),
        (cx + dx * half - px * hw, cy + dy * half - py * hw),
        (cx + dx * half + px * hw, cy + dy * half + py * hw),
        (cx - dx * half + px * hw, cy - dy * half + py * hw),
    ]
    draw.polygon(corners, fill=color)
    # İki uçta açık ağızlı baş (halka + zemin renginde çentik)
    head_r = int(96 * scale)
    notch_r = int(54 * scale)
    for sign in (-1, 1):
        hx = cx + dx * half * sign
        hy = cy + dy * half * sign
        draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=color)
        nx = hx + dx * head_r * 0.5 * sign
        ny = hy + dy * head_r * 0.5 * sign
        draw.ellipse([nx - notch_r, ny - notch_r, nx + notch_r, ny + notch_r], fill=BG)


def make_icon(path: str, size: int = 1024, pad_ratio: float = 0.0) -> None:
    img = Image.new("RGBA", (size, size), BG + (255,))
    d = ImageDraw.Draw(img)
    # adaptive-icon için güvenli alan: gliftı biraz küçült
    scale = (size / 1024) * (0.66 if pad_ratio else 0.85)
    _wrench(d, size // 2, size // 2, scale, YELLOW)
    img.save(path)
    print("yazildi:", path)


def make_splash(path: str, w: int = 1242, h: int = 2436) -> None:
    img = Image.new("RGBA", (w, h), BG + (255,))
    d = ImageDraw.Draw(img)
    _wrench(d, w // 2, h // 2 - 140, scale=0.95, color=YELLOW)
    font = _font(200)
    text = "USTA"
    bbox = d.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    d.text(((w - tw) // 2, h // 2 + 180), text, font=font, fill=YELLOW)
    img.save(path)
    print("yazildi:", path)


if __name__ == "__main__":
    make_icon(os.path.join(ASSETS, "icon.png"))
    make_icon(os.path.join(ASSETS, "adaptive-icon.png"), pad_ratio=0.34)
    make_splash(os.path.join(ASSETS, "splash.png"))
    print("Tum asset'ler hazir:", ASSETS)
