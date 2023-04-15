import cv2
import numpy as np
import qrcode

from config import config

class Blank:
    def __init__(self, height=1754, width=1240) -> None:
        self.canvas = np.ones((height, width), dtype=np.uint8) * 255

    def save(self, path) -> None:
        cv2.imwrite(f'{path}.png', self.canvas)


class BlankBuilder:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self._fields_rows_count = 0
        self._product = Blank()

    @property
    def blank(self) -> Blank:
        product = self._product
        self.reset()
        return product

    def _draw_field(self, pos, shift_x=0, numbered=False) -> None:
        x1 = config.page.margin + pos * \
            (config.fields.box_size + config.fields.box_spacing) + shift_x
        y1 = config.page.header + self._fields_rows_count * \
            (config.fields.row_spacing + config.fields.box_size)
        x2 = x1 + config.fields.box_size
        y2 = y1 + config.fields.box_size
        cv2.rectangle(self._product.canvas, (x1, y1), (x2, y2),
                      color=0, thickness=4, lineType=cv2.LINE_4)
        if (numbered):
            font_scale = 1
            x = x1
            y = y2 + font_scale*config.font.base_height + 5
            cv2.putText(self._product.canvas, str(pos+1), (x, y),
                        config.font.style, fontScale=font_scale, color=100, thickness=1, lineType=cv2.LINE_AA)

    def _draw_row_num(self) -> int:
        x = config.page.margin
        y = config.page.header + self._fields_rows_count * \
            (config.fields.row_spacing + config.fields.box_size)
        font_scale = 2
        y += (config.font.base_height*font_scale + config.fields.box_size) // 2
        num = str(self._fields_rows_count + 1) + '.'
        cv2.putText(self._product.canvas, num, (x, y),
                    config.font.style, fontScale=font_scale, color=0, thickness=2, lineType=cv2.LINE_AA)
        return config.font.base_width*font_scale*len(num)

    def place_fields_row(self, count, numbered=False) -> None:
        shift_x = self._draw_row_num()
        for pos in range(count):
            self._draw_field(pos, shift_x, numbered)
        self._fields_rows_count += 1
        pass

    def place_info(self) -> None:
        # will be implemented
        pass

    def place_code(self, code) -> None:
        cv2.putText(self._product.canvas, str(code).zfill(3), [
                    400, 180], config.font.style, fontScale=4, color=0, thickness=5, lineType=cv2.LINE_AA)

        qr = qrcode.QRCode(version=1, box_size=config.qr.box_size, border=0)
        qr.add_data(code)
        img_qr = qr.make_image(
            fill_color="black", back_color="white").convert('RGB')
        img_qr = cv2.cvtColor(
            np.array(img_qr, dtype=np.uint8), cv2.COLOR_RGB2GRAY)
        img_qr = cv2.resize(
            img_qr, (config.qr.size, config.qr.size), interpolation=cv2.INTER_NEAREST)
        x1 = config.page.margin
        y1 = config.page.margin
        x2 = config.page.margin+config.qr.size
        y2 = config.page.margin+config.qr.size
        self._product.canvas[x1:x2, y1:y2] = img_qr
        pass


if __name__ == '__main__':
    b = BlankBuilder()
    b.place_fields_row(count=5)
    b.place_fields_row(count=5, numbered=True)
    b.place_fields_row(count=5)
    b.place_fields_row(count=5)
    b.place_fields_row(count=5)
    b.place_code(code=200)
    b.blank.save('aaa')
