from PIL import Image, ImageDraw, ImageFont
import math
import io

class MinistryGenerator:
    def __init__(self):
        self.CANVAS_SIZE = 600
        self.PADDING = 40
        self.BACKGROUND_COLOR = (20, 0, 0)
        self.TEXT_COLOR = (255, 240, 220)

        self.FONT_QUOTE = ImageFont.truetype("data/China.ttf", 26)
        self.FONT_FOOTER = ImageFont.truetype("data/China.ttf", 18)
        self.FONT_LABEL = ImageFont.truetype("data/China.ttf", 12)

        self.WIDTH = self.CANVAS_SIZE
        self.HEIGHT = self.CANVAS_SIZE

    def radial_grad(self, img, cx, cy, inner_color, outer_color, radius):
        px = img.load()

        for y in range(self.HEIGHT):
            for x in range(self.WIDTH):
                dx = x - cx
                dy = y - cy
                d = math.sqrt(dx*dx + dy*dy)
                t = min(1, d / radius)

                r = int(inner_color[0] + (outer_color[0] - inner_color[0]) * t)
                g = int(inner_color[1] + (outer_color[1] - inner_color[1]) * t)
                b = int(inner_color[2] + (outer_color[2] - inner_color[2]) * t)

                old = px[x, y]
                px[x, y] = (
                    min(old[0] + r, 255),
                    min(old[1] + g, 255),
                    min(old[2] + b, 255)
                )


    def linear_gradient_vertical(self, img, top_color, mid_color, bottom_color):
        px = img.load()
        for y in range(self.HEIGHT):
            t = y / self.HEIGHT
            if t < 0.7:
                t2 = t / 0.7
                r = int(top_color[0] + (mid_color[0] - top_color[0]) * t2)
                g = int(top_color[1] + (mid_color[1] - top_color[1]) * t2)
                b = int(top_color[2] + (mid_color[2] - top_color[2]) * t2)
            else:
                t2 = (t - 0.7) / 0.3
                r = int(mid_color[0] + (bottom_color[0] - mid_color[0]) * t2)
                g = int(mid_color[1] + (bottom_color[1] - mid_color[1]) * t2)
                b = int(mid_color[2] + (bottom_color[2] - mid_color[2]) * t2)

            for x in range(self.WIDTH):
                px[x, y] = (r, g, b)


    def draw_emblem(self, draw, scale=2.0, offset=(0,0), color="#f2cf86", width=2):
        ox, oy = offset

        def S(x, y):
            return ox + x * scale, oy + y * scale

        lines = [
            ((40, 70), (40, 30)),
            ((40, 40), (20, 40)),
            ((20, 40), (20, 70)),
            ((160, 40), (180, 40)),
            ((180, 40), (180, 70)),
            ((70, 25), (70, 70)),
            ((100, 20), (100, 70)),
            ((130, 25), (130, 70)),
        ]
        for (x1, y1), (x2, y2) in lines:
            draw.line([S(x1, y1), S(x2, y2)], fill=color, width=width)

        def bezier(points, steps=25):
            pts = []
            for t in [i / steps for i in range(steps + 1)]:
                x = (1 - t)**3 * points[0][0] + 3*(1 - t)**2*t * points[1][0] + 3*(1 - t)*t**2 * points[2][0] + t**3 * points[3][0]
                y = (1 - t)**3 * points[0][1] + 3*(1 - t)**2*t * points[1][1] + 3*(1 - t)*t**2 * points[2][1] + t**3 * points[3][1]
                pts.append(S(x, y))
            return pts

        c1 = bezier([(40,30),(40,20),(55,10),(100,10)])
        c2 = bezier([(100,10),(145,10),(160,20),(160,30)])

        draw.line(c1, fill=color, width=width)
        draw.line(c2, fill=color, width=width)


    def draw_multiline_text_centered(self, draw, text, box, font, fill):
        x1, y1, x2, y2 = box
        lines = text.split("\n")
        line_h = font.getbbox("あ")[3] + 4
        total_h = len(lines) * line_h
        y = (y1 + y2 - total_h) // 2

        for line in lines:
            w = draw.textlength(line, font=font)
            draw.text((x1 + (x2 - x1 - w)//2, y), line, font=font, fill=fill)
            y += line_h


    def generate_image(self, quote, source, date, output=io.BytesIO, is_fake: bool = True):
        img = Image.new("RGB", (self.CANVAS_SIZE, self.CANVAS_SIZE), (0, 0, 0))

        self.linear_gradient_vertical(
            img,
            top_color=(91, 5, 7),       # #5b0507
            mid_color=(28, 0, 0),       # #1c0000
            bottom_color=(0, 0, 0),     # #000000
        )

        self.radial_grad(
            img,
            int(self.WIDTH * 0.15),
            0,
            inner_color=(139, 17, 20),     # #8b1114
            outer_color=(0, 0, 0),
            radius=350
        )

        self.radial_grad(
            img,
            int(self.WIDTH * 0.85),
            0,
            inner_color=(184, 32, 35),     # #b82023
            outer_color=(0, 0, 0),
            radius=350
        )

        self.radial_grad(
            img,
            int(self.WIDTH * 0.5),
            int(self.HEIGHT * 0.80),
            inner_color=(56, 3, 3),        # #380303
            outer_color=(18, 0, 0),        # #120000
            radius=400
        )

        draw = ImageDraw.Draw(img)

        emblem_w = 200 * 2.0
        emblem_x = (self.CANVAS_SIZE - emblem_w) // 2
        self.draw_emblem(draw, scale=2.0, offset=(emblem_x, 35))

        quote_box = (self.PADDING, 150, self.CANVAS_SIZE - self.PADDING, self.CANVAS_SIZE - 180)
        self.draw_multiline_text_centered(draw, quote, quote_box, self.FONT_QUOTE, self.TEXT_COLOR)

        footer_y = self.CANVAS_SIZE - 110
        draw.text((self.PADDING, footer_y), source, font=self.FONT_FOOTER, fill=self.TEXT_COLOR)
        date_w = draw.textlength(date, font=self.FONT_FOOTER)
        draw.text((self.CANVAS_SIZE - self.PADDING - date_w, footer_y), date, font=self.FONT_FOOTER, fill=self.TEXT_COLOR)

        if is_fake:
            label = "Fake Quote"
        w = draw.textlength(label, font=self.FONT_LABEL)
        draw.text(((self.CANVAS_SIZE - w) // 2, self.CANVAS_SIZE - 60), label, font=self.FONT_LABEL, fill=(230,210,180))

        img.save(output, format="png")
        output.seek(0)
        return True