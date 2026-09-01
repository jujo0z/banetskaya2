"""Generate installer branding assets: app icon (.ico) + Inno Setup wizard images (.bmp).

Run:  python windows-package/installer/make_assets.py
Outputs into windows-package/installer/assets/
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
os.makedirs(ASSETS, exist_ok=True)

CRIMSON = (225, 29, 72)
CRIMSON_DARK = (190, 18, 60)
DARK = (10, 10, 12)
DARK2 = (20, 18, 24)
WHITE = (255, 255, 255)
GREY = (150, 150, 160)


def font(size, bold=True):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()


def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return m


def vgrad(size, top, bottom):
    w, h = size
    img = Image.new("RGB", size, top)
    px = img.load()
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        for x in range(w):
            px[x, y] = (r, g, b)
    return img


def make_icon_layer(S=512):
    """A crimson rounded tile with a white contract sheet + signature swoosh."""
    base = vgrad((S, S), CRIMSON, CRIMSON_DARK).convert("RGBA")
    base.putalpha(rounded_mask((S, S), int(S * 0.22)))
    d = ImageDraw.Draw(base)

    # document sheet
    mx, my = int(S * 0.28), int(S * 0.20)
    dw, dh = S - 2 * mx, int(S * 0.60)
    x0, y0 = mx, my
    x1, y1 = mx + dw, my + dh
    fold = int(dw * 0.26)
    # sheet body (with folded corner) via polygon
    d.polygon(
        [(x0, y0), (x1 - fold, y0), (x1, y0 + fold), (x1, y1), (x0, y1)],
        fill=WHITE,
    )
    # folded corner triangle (subtle grey)
    d.polygon([(x1 - fold, y0), (x1, y0 + fold), (x1 - fold, y0 + fold)], fill=(225, 225, 230))

    # text lines
    lh = int(dh * 0.09)
    ly = y0 + int(dh * 0.22)
    for i in range(4):
        w_line = dw - int(S * 0.10) - (fold if i == 0 else 0)
        d.rounded_rectangle(
            [x0 + int(S * 0.05), ly, x0 + int(S * 0.05) + w_line, ly + int(lh * 0.5)],
            radius=int(lh * 0.25), fill=(205, 205, 212),
        )
        ly += lh

    # signature swoosh
    sy = y1 - int(dh * 0.20)
    pts = [
        (x0 + int(S * 0.06), sy),
        (x0 + int(dw * 0.30), sy - int(dh * 0.10)),
        (x0 + int(dw * 0.50), sy + int(dh * 0.08)),
        (x0 + int(dw * 0.74), sy - int(dh * 0.12)),
        (x1 - int(S * 0.06), sy - int(dh * 0.02)),
    ]
    d.line(pts, fill=CRIMSON, width=max(6, int(S * 0.02)), joint="curve")
    return base


def save_ico():
    icon = make_icon_layer(512)
    path = os.path.join(ASSETS, "icon.ico")
    icon.save(path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    icon.resize((256, 256)).save(os.path.join(ASSETS, "icon.png"))
    print("wrote", path)


def save_wizard_large():
    W, H = 164, 314
    img = vgrad((W, H), DARK, DARK2)
    d = ImageDraw.Draw(img)
    # crimson accent bar on the left
    d.rectangle([0, 0, 6, H], fill=CRIMSON)
    # icon
    ic = make_icon_layer(256).resize((92, 92))
    img.paste(ic, (36, 30), ic)
    # brand text
    d.text((20, 140), "Banetskaya", font=font(22, True), fill=WHITE)
    d.text((20, 166), ".by", font=font(22, True), fill=CRIMSON)
    d.text((21, 196), "DOCUMENT ENGINE", font=font(11, True), fill=GREY)
    # tagline
    d.text((20, H - 70), "Автозаполнение", font=font(12, False), fill=GREY)
    d.text((20, H - 54), "договоров найма", font=font(12, False), fill=GREY)
    d.text((20, H - 38), "из Excel", font=font(12, False), fill=GREY)
    path = os.path.join(ASSETS, "wizard_large.bmp")
    img.save(path, format="BMP")
    print("wrote", path)


def save_wizard_small():
    W, H = 55, 58
    img = vgrad((W, H), DARK, DARK2)
    ic = make_icon_layer(256).resize((44, 44))
    img.paste(ic, ((W - 44) // 2, (H - 44) // 2), ic)
    path = os.path.join(ASSETS, "wizard_small.bmp")
    img.save(path, format="BMP")
    print("wrote", path)


if __name__ == "__main__":
    save_ico()
    save_wizard_large()
    save_wizard_small()
    print("done ->", ASSETS)
