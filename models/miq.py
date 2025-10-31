import io
import re
from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
import asyncio

DISCORD_EMOJI_RE = re.compile(r"<(a?):([a-zA-Z0-9_]{1,32}):([0-9]{17,22})>")
UNICODE_EMOJI_RE = re.compile(
    r"["
    r"\U0001F600-\U0001F64F"  # Emoticons
    r"\U0001F300-\U0001F5FF"  # Miscellaneous Symbols and Pictographs
    r"\U0001F680-\U0001F6FF"  # Transport and Map Symbols
    r"\U0001F700-\U0001F77F"  # Alchemical Symbols (less common for emojis)
    r"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
    r"\U0001F800-\U0001F82F"  # Supplemental Arrows-C
    r"\U0001F830-\U0001F8FF"  # Supplemental Symbols and Pictographs (continued)
    r"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs (more modern emojis)
    r"\U00002600-\U000027BF"  # Miscellaneous Symbols
    r"\U00002B50"             # Star symbol
    r"]+",
    flags=re.UNICODE
)
COMBINED_EMOJI_RE = re.compile(
    r"<a?:[a-zA-Z0-9_]{1,32}:[0-9]{17,22}>|" + UNICODE_EMOJI_RE.pattern,
    flags=re.UNICODE | re.DOTALL,
)

def wrap_text_with_scroll_cut(text, font, draw, max_width, max_height, line_height):
    lines = []
    for raw_line in text.split("\n"):
        current_line = ""
        for char in raw_line:
            test_line = current_line + char
            bbox = draw.textbbox((0, 0), test_line, font=font)
            w = bbox[2] - bbox[0]
            if w <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = char

            if len(lines) * line_height >= max_height - line_height * 2:
                ellipsis = "…"
                while True:
                    bbox = draw.textbbox((0, 0), current_line + ellipsis, font=font)
                    if bbox[2] - bbox[0] <= max_width:
                        break
                    if len(current_line) == 0:
                        break
                    current_line = current_line[:-1]
                lines.append(current_line + ellipsis)
                return lines

        if current_line:
            lines.append(current_line)

    return lines


def draw_text_with_emojis(img, draw, position, text, font, fill):
    x, y = position
    cursor_x = x
    last_end = 0

    for m in COMBINED_EMOJI_RE.finditer(text):
        if m.start() > last_end:
            part = text[last_end:m.start()]
            if part:
                draw.text((cursor_x, y), part, font=font, fill=fill)
                bbox = draw.textbbox((0, 0), part, font=font)
                cursor_x += bbox[2] - bbox[0]

        token = m.group(0)
        token_clean = token.strip()

        # --- Discord絵文字処理 ---
        # d = DISCORD_EMOJI_RE.fullmatch(token_clean)
        #if d:
        #    is_animated, name, emoji_id = d.groups()
        #    ext = "gif" if is_animated else "png"
        #    url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{ext}?size=64"

        #    try:
        #        resp = requests.get(url, timeout=3)
        #        if resp.status_code == 200:
        #            with io.BytesIO(resp.content) as i:
        #                emoji_img = Image.open(i).convert("RGBA")

        #            ascent, descent = font.getmetrics()
        #            font_height = ascent + descent
        #            emoji_size = int(font_height * 0.9)
        #            emoji_img = emoji_img.resize((emoji_size, emoji_size), Image.Resampling.LANCZOS)

        #            y_offset = y + (font_height - emoji_size) // 2
        #            img.paste(emoji_img, (int(cursor_x), int(y_offset)), emoji_img)

        #            cursor_x += draw.textlength("あ", font=font)
        #            last_end = m.end()
        #            continue
        #    except Exception:
        #        pass

        # --- Unicode絵文字処理 ---
        if UNICODE_EMOJI_RE.fullmatch(token_clean):
            try:
                url = f"https://emojicdn.elk.sh/{token_clean}"
                resp = requests.get(url, timeout=3)
                if resp.status_code == 200:
                    with io.BytesIO(resp.content) as i:
                        emoji_img = Image.open(i).convert("RGBA")

                    ascent, descent = font.getmetrics()
                    font_height = ascent + descent
                    emoji_size = int(font_height * 0.9)
                    emoji_img = emoji_img.resize((emoji_size, emoji_size), Image.Resampling.LANCZOS)

                    y_offset = y + (font_height - emoji_size) // 2
                    img.paste(emoji_img, (int(cursor_x), int(y_offset)), emoji_img)

                    cursor_x += draw.textlength("M", font=font)
                    last_end = m.end()
                    continue
            except Exception:
                pass

        # --- 通常文字 ---
        draw.text((cursor_x, y), token, font=font, fill=fill)
        bbox = draw.textbbox((0, 0), token, font=font)
        cursor_x += bbox[2] - bbox[0]
        last_end = m.end()

    # --- 残りテキスト ---
    if last_end < len(text):
        tail = text[last_end:]
        if tail:
            draw.text((cursor_x, y), tail, font=font, fill=fill)

def create_quote_image(
    author,
    text,
    avatar_bytes,
    background,
    textcolor,
    color: bool,
    negapoji: bool = False,
    fake: bool = False
):
    width, height = 800, 400
    background_color = background
    text_color = textcolor

    img = Image.new("RGB", (width, height), background_color)
    draw = ImageDraw.Draw(img)

    avatar_size = (400, 400)
    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
    avatar = avatar.resize(avatar_size)

    mask = Image.new("L", avatar_size, 255)
    for x in range(avatar_size[0]):
        alpha = (
            255
            if x < avatar_size[0] // 2
            else int(255 * (1 - (x - avatar_size[0] // 2) / (avatar_size[0] / 2)))
        )
        for y in range(avatar_size[1]):
            mask.putpixel((x, y), alpha)
    avatar.putalpha(mask)
    img.paste(avatar, (0, height - avatar_size[1]), avatar)

    try:
        font = ImageFont.truetype("data/DiscordFont.ttf", 30)
        name_font = ImageFont.truetype("data/DiscordFont.ttf", 20)
    except:
        font = ImageFont.load_default()
        name_font = ImageFont.load_default()

    text_x = 420
    max_text_width = width - text_x - 50
    max_text_height = height - 80
    line_height = font.size + 10

    lines = wrap_text_with_scroll_cut(
        text, font, draw, max_text_width, max_text_height, line_height
    )

    text_block_height = len(lines) * line_height
    text_y = (height - text_block_height) // 2

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), re.sub(r"<(a?):([a-zA-Z0-9_]{1,32}):([0-9]{17,22})>", 'あ', line), font=font)
        line_width = bbox[2] - bbox[0]
        line_x = (width + text_x - 50 - line_width) // 2
        draw_text_with_emojis(
            img, draw,
            (line_x, text_y + i * line_height),
            line,
            font,
            text_color
        )

    author_text = f"- {author}"
    bbox = draw.textbbox((0, 0), author_text, font=name_font)
    author_width = bbox[2] - bbox[0]
    author_x = (width + text_x - 50 - author_width) // 2
    author_y = text_y + len(lines) * line_height + 10
    draw.text((author_x, author_y), author_text, font=name_font, fill=text_color)

    if fake:
        draw.text((580, 0), "FakeQuote - SharkBot", font=name_font, fill=text_color)
    else:
        draw.text((700, 0), "SharkBot", font=name_font, fill=text_color)

    if negapoji:
        inverted_img = ImageOps.invert(img.convert("RGB"))
        return inverted_img

    if color:
        return img
    else:
        return img.convert("L")
    
async def make_quote_async(
    author,
    text,
    avatar_bytes,
    background,
    textcolor,
    color: bool,
    negapoji: bool = False,
    fake: bool = False
):
    img = await asyncio.to_thread(create_quote_image, author, text, avatar_bytes, background, textcolor, color, negapoji, fake)
    return img