"""Render captured command output (.txt) as terminal-style PNG images for the report.

Usage: python scripts/render_terminal.py docs/screenshots/*.txt
Each capture .txt becomes a .png with the same name next to it. Lines starting with "$ " are drawn as prompts.
"""
import re
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/liberation/LiberationMono-Regular.ttf",
]
BOLD_CANDIDATES = [
    "/usr/share/fonts/TTF/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
]
SIZE = 15
MAX_COLS = 170
MAX_LINES = 110
PAD = 24
BAR = 38
BG = (24, 26, 33)
BAR_BG = (40, 43, 54)
FG = (220, 223, 228)
PROMPT = (126, 231, 135)
DIM = (139, 148, 158)
ACCENTS = {
    re.compile(r"\b(Running|PASSED|passed|Success|success|UP|deployed|Ready|healthy|Healthy|ok)\b"): (126, 231, 135),
    re.compile(r"\b(ImagePullBackOff|ErrImagePull|FAILED|failed|Failed|Error|error|Warning|<none>|refused|Terminating)\b"): (255, 123, 114),
    re.compile(r"\b(HIGH|CRITICAL|superseded|Pending|ContainerCreating)\b"): (240, 185, 90),
}
BOX_CHARS = set("│┌┐└┘├┤┬┴┼─")
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def load_font(candidates):
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, SIZE)
    return ImageFont.load_default()


FONT = load_font(FONT_CANDIDATES)
BOLD = load_font(BOLD_CANDIDATES) if any(Path(p).exists() for p in BOLD_CANDIDATES) else FONT


def prepare(text):
    lines = []
    for raw in ANSI.sub("", text).expandtabs(8).splitlines():
        raw = raw.rstrip()
        if len(raw) <= MAX_COLS or BOX_CHARS.intersection(raw):  # never wrap tables
            lines.append(raw)
        else:
            wrapped = textwrap.wrap(raw, MAX_COLS, subsequent_indent="  ", drop_whitespace=False,
                                    replace_whitespace=False, break_on_hyphens=False)
            lines.extend(wrapped or [raw[:MAX_COLS]])
    if len(lines) > MAX_LINES:
        hidden = len(lines) - MAX_LINES
        lines = lines[:MAX_LINES] + ["", f"... {hidden} more lines - full output in the matching .txt file"]
    return lines


def draw_line(draw, x, y, line, char_w):
    if line.startswith("$ "):
        draw.text((x, y), "$", font=BOLD, fill=PROMPT)
        draw.text((x + 2 * char_w, y), line[2:], font=BOLD, fill=(255, 255, 255))
        return
    colors = [FG] * len(line)
    for pattern, color in ACCENTS.items():
        for m in pattern.finditer(line):
            colors[m.start():m.end()] = [color] * (m.end() - m.start())
    # Draw contiguous runs of the same colour so nothing is painted twice.
    start = 0
    for i in range(1, len(line) + 1):
        if i == len(line) or colors[i] != colors[start]:
            draw.text((x + start * char_w, y), line[start:i], font=FONT, fill=colors[start])
            start = i


def render(path: Path):
    lines = prepare(path.read_text(errors="replace")) or [""]
    char_w = FONT.getbbox("M")[2]
    ascent, descent = FONT.getmetrics()
    line_h = ascent + descent  # no extra leading, so box-drawing tables join up
    cols = max(len(line) for line in lines)
    width = max(720, PAD * 2 + cols * char_w)
    height = BAR + PAD * 2 + line_h * len(lines)

    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, width, BAR], fill=BAR_BG)
    for i, color in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        cx = 20 + i * 22
        draw.ellipse([cx - 6, BAR // 2 - 6, cx + 6, BAR // 2 + 6], fill=color)
    title = f"vansh@deskflow: {path.stem}"
    tw = FONT.getbbox(title)[2]
    draw.text(((width - tw) // 2, BAR // 2 - SIZE // 2 - 1), title, font=FONT, fill=DIM)

    y = BAR + PAD
    for line in lines:
        draw_line(draw, PAD, y, line, char_w)
        y += line_h
    out = path.with_suffix(".png")
    img.save(out, optimize=True)
    return out


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        print("rendered", render(Path(arg)))
