from typing import Any
import numpy as np
import cv2
import qrcode
from app.source.config import config


def get_canvas(height, width) -> np.ndarray:
    return np.ones((height, width), dtype=np.uint8) * 255


def save_canvas(path: str, canvas: np.ndarray) -> None:
    cv2.imwrite(path, canvas)


class Drawer:
    main_color: int = 0
    second_color: int = 100

    class Box:
        thickness: int
        line_type: int
        color: int

        def __init__(self,  color: int, thickness: int = config.fields.box_thickness, line_type: int = cv2.LINE_4):
            self.thickness = thickness
            self.line_type = line_type
            self.color = color

        def __call__(self, canvas, top_left_x: int, top_left_y: int, width: int = None, height: int = None, size=None) -> Any:
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

            top_left = np.array([top_left_x, top_left_y])
            bot_right = top_left + np.array([width, height])

            cv2.rectangle(
                img=canvas,
                pt1=tuple(top_left),
                pt2=tuple(bot_right),
                color=self.color,
                thickness=self.thickness,
                lineType=self.line_type
            )

            return {
                'coords': [top_left.tolist(), bot_right.tolist()]
            }

    class Text:
        thickness: int
        line_type: int
        main_color: int
        second_color: int

        font_style = cv2.FONT_HERSHEY_SIMPLEX
        font_height = 22
        font_width = 20

        def __init__(self,  main_color: int, second_color: int, thickness: int = 2, line_type: int = cv2.LINE_AA):
            self.thickness = thickness
            self.line_type = line_type
            self.main_color = main_color
            self.second_color = second_color

        def __call__(self, canvas, text: str, x: int, y: int, font_scale: int, pos: str = 'bot', color_style: str = 'main', thickness: int = None) -> Any:
            point: tuple
            letter_height: int = int(font_scale * self.font_height)
            letter_width: int = int(font_scale * self.font_width)
            if not thickness:
                thickness = int(font_scale)
            if pos == 'bot':
                point = (x, y)
            elif pos == 'top':
                point = (x, y+letter_height)
            elif pos == 'mid':
                point = (x, y+letter_height//2)
            else:
                raise ValueError(
                    f'Unknown position {pos}. Supports only mid, bot, top'
                )
            color: int
            if color_style == 'main':
                color = self.main_color
            elif color_style == 'second':
                color = self.second_color
            else:
                raise ValueError(
                    f'Unknown color_style {color_style}. Supports only main, second'
                )
            cv2.putText(
                img=canvas,
                text=text,
                org=point,
                fontFace=self.font_style,
                fontScale=font_scale,
                color=color,
                thickness=thickness,
                lineType=self.line_type
            )
            return {
                'width': letter_width * len(text)
            }

    class QR:
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

        def __call__(self, canvas: np.ndarray, coord: tuple, data: str):
            x1, y1, x2, y2 = coord
            canvas[y1:y2, x1:x2] = self._create(data)

    def __init__(self):
        self.text = self.Text(
            main_color=self.main_color,
            second_color=self.second_color
        )
        self.box = self.Box(
            color=self.main_color
        )
        self.qr = self.QR()


draw = Drawer()
