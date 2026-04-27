from typing import Any
import numpy as np
import cv2
import qrcode
from PIL import Image, ImageDraw, ImageFont
from app.source.utils.config import config


def get_canvas(height, width) -> np.ndarray:
    return np.ones((height, width), dtype=np.uint8) * 255


def save_canvas(path: str, canvas: np.ndarray) -> None:
    cv2.imwrite(path, canvas)


class Cursor:
    def __init__(self, *coords):
        self.coords = np.array([*coords])
        self.saved_pos = list()

    def move(self, dx=0, dy=0):
        self.coords += np.array([dx, dy])
        return self

    def save_pos(self):
        self.saved_pos.append(self.coords.copy())

    def return_pos(self):
        self.coords = self.saved_pos.pop()

    @property
    def x(self):
        return self.coords[0]

    @property
    def y(self):
        return self.coords[1]


class Drawer:
    main_color: int = 0
    second_color: int = 100

    class Rectangle:
        thickness: int
        line_type: int
        color: int

        def __init__(self, canvas,  color: int, thickness: int = 5, line_type: int = cv2.LINE_4):
            self.canvas = canvas
            self.thickness = thickness
            self.line_type = line_type
            self.color = color

        def __call__(self, cursor: Cursor, width: int = None, height: int = None, size=None, thickness: int = None) -> Any:
            if thickness == None:
                thickness = self.thickness

            if size and (width or height):
                raise ValueError(
                    f'Cannot parse both size and width or height'
                )
            if size == None and (width == None or height == None):
                raise ValueError(
                    f'Cannot parse without size or both width and height'
                )

            if size:
                width = size
                height = size

            top_left = cursor.coords
            bot_right = cursor.coords + np.array([width, height])

            cv2.rectangle(
                img=self.canvas,
                pt1=tuple(top_left),
                pt2=tuple(bot_right),
                color=self.color,
                thickness=thickness,
                lineType=self.line_type
            )

            dump_coords = {
                'box': [top_left.tolist(), bot_right.tolist()]
            }

            cursor.move(dx=width, dy=0)

            return dump_coords

    class Text:
        main_color: int
        second_color: int

        def __init__(self, canvas, main_color: int, second_color: int):
            self.canvas = canvas
            self.main_color = main_color
            self.second_color = second_color

        def __call__(self, cursor: Cursor, text: str, letter_height: int,
                     box_height: int = 0, pos: str = 'bot',
                     color_style: str = 'main', thickness=None,
                     font_path: str = None) -> Any:
            if font_path is None:
                font_path = config.fonts.mono
            color = self.main_color if color_style == 'main' else self.second_color
            font = ImageFont.truetype(font_path, letter_height)
            ascent, descent = font.getmetrics()
            text_top: int
            x, y = cursor.x, cursor.y
            if pos == 'bot':
                text_top = y + box_height - (ascent + descent)
            elif pos == 'top':
                text_top = y
            elif pos == 'mid':
                text_top = y + (box_height - (ascent + descent)) // 2
            else:
                raise ValueError(
                    f'Unknown position {pos}. Supports only mid, bot, top'
                )
            pil_img = Image.fromarray(self.canvas)
            draw = ImageDraw.Draw(pil_img)
            draw.text((x, text_top), text, fill=color, font=font)
            width = int(draw.textlength(text, font=font))
            np.copyto(self.canvas, np.array(pil_img))
            cursor.move(dx=width, dy=0)
            return {'width': width}

    class QR:
        def __init__(self, canvas) -> None:
            self.canvas = canvas

        def _create(self, data: str):
            qr = qrcode.QRCode(
                version=1, box_size=config.qr.box_size, border=0)
            qr.add_data(data)
            img_qr = qr.make_image(
                fill_color="black", back_color="white").convert('RGB')
            img_qr = cv2.cvtColor(
                np.array(img_qr, dtype=np.uint8), cv2.COLOR_RGB2GRAY)
            img_qr = cv2.resize(
                img_qr, (config.qr.size, config.qr.size), interpolation=cv2.INTER_NEAREST)
            return img_qr

        def __call__(self, coords, data: str):
            x1, y1, x2, y2 = coords[0][0], coords[0][1], coords[1][0], coords[1][1]
            self.canvas[y1:y2, x1:x2] = self._create(data)

    def __init__(self, canvas):
        self.canvas = canvas
        self.text = self.Text(
            canvas=canvas,
            main_color=self.main_color,
            second_color=self.second_color
        )
        self.rectangle = self.Rectangle(
            canvas=canvas,
            color=self.main_color
        )
        self.qr = self.QR(
            canvas=canvas
        )

    def ttf_text_centered(self, font_path: str, font_size: int,
                          text: str, center: tuple) -> None:
        pil_img = Image.fromarray(self.canvas)
        draw = ImageDraw.Draw(pil_img)
        font = ImageFont.truetype(font_path, font_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = center[0] - w // 2 - bbox[0]
        y = center[1] - h // 2 - bbox[1]
        draw.text((x, y), text, fill=self.main_color, font=font)
        np.copyto(self.canvas, np.array(pil_img))
