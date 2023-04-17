import cv2
import numpy as np
import qrcode
import json

from app.source.config import config

class Blank:
    def __init__(self) -> None:
        self.canvas = np.ones((config.page.height, config.page.width), dtype=np.uint8) * 255

    def save(self, path) -> None:
        cv2.imwrite(f'{path}.png', self.canvas)

    def copy(self):
        blank_copy = Blank()
        blank_copy.canvas = self.canvas.copy()
        return blank_copy


class BlankGenerator:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self._coords = {'Fields' : dict()}
        self._fields_rows_count = 0
        self._product = Blank()

    @property
    def blank(self) -> Blank:
        product = self._product
        self.reset()
        return product
    
    def dump_data(self, path):
        with open(f'{path}data.json', 'w') as f:
            json.dump(self._coords, f, indent=4)


    def _draw_field(self, pos, shift_x=0, numbered=False) -> None:
        x1 = config.page.margin + pos * \
            (config.fields.box_size + config.fields.box_spacing) + shift_x
        y1 = config.page.header + self._fields_rows_count * \
            (config.fields.row_spacing + config.fields.box_size)
        x2 = x1 + config.fields.box_size
        y2 = y1 + config.fields.box_size
        thickness = 5
        cv2.rectangle(self._product.canvas, (x1, y1), (x2, y2),
                      color=0, thickness=thickness, lineType=cv2.LINE_4)
        self._coords['thickness'] = thickness
        self._coords['Fields'][f'Row {self._fields_rows_count + 1}'][f'Box {pos+1}'] = [[x1, y1], [x2, y2]]

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
        self._coords['Fields'][f'Row {self._fields_rows_count + 1}'] = dict()
        for pos in range(count):
            self._draw_field(pos, shift_x, numbered)
        self._fields_rows_count += 1
        pass

    def place_info(self) -> None:
        # will be implemented
        pass
    
    def place_codes(self, codes, path) -> None:
        self._coords['QR'] = dict()
        positions = ['tl', 'tr', 'bl']
        pos_coords = [config.qr.tl, config.qr.tr, config.qr.bl]
        for pos, qr_coord in zip(positions, pos_coords):
            x1, y1, x2, y2 = qr_coord
            self._coords['QR'][pos] = [[x1, y1], [x2, y2]]

        self.dump_data(path)

        for code in codes:
            product = self._product.copy()
            def create_cv2_qr(data):
                qr = qrcode.QRCode(version=1, box_size=config.qr.box_size, border=0)
                qr.add_data(data)
                img_qr = qr.make_image(
                    fill_color="black", back_color="white").convert('RGB')
                img_qr = cv2.cvtColor(
                    np.array(img_qr, dtype=np.uint8), cv2.COLOR_RGB2GRAY)
                img_qr = cv2.resize(
                    img_qr, (config.qr.size, config.qr.size), interpolation=cv2.INTER_NEAREST)
                return img_qr
            
            cv2.putText(product.canvas, str(code).zfill(3), [
                        400, 180], config.font.style, fontScale=4, color=0, thickness=5, lineType=cv2.LINE_AA)
            for pos, qr_coord in zip(positions, pos_coords):
                x1, y1, x2, y2 = qr_coord
                product.canvas[y1:y2, x1:x2] = create_cv2_qr(f'{pos}|{code}')
            product.save(f'{path}/blanks/{code}')


if __name__ == '__main__':
    b = BlankGenerator()
    b.place_fields_row(count=5)
    b.place_fields_row(count=5, numbered=True)
    b.place_fields_row(count=5)
    b.place_fields_row(count=5)
    b.place_fields_row(count=5)
    b.place_code(code=228)
    b.blank.save('blanks/demo')

    # with open('data.json', 'r') as f:
    # # Читаем данные из файла и преобразуем их в объект Python
    #     data = json.load(f)
    
    # x1, y1, x2, y2 = data['Row 1']['Box 2']
    # delta =  (data['thickness']+1)//2
    # img = cv2.imread('aaa.png')
    # cv2.rectangle(img, (x1+delta, y1+delta), (x2-delta, y2-delta),
    #                   color=(255,0,0), thickness=1, lineType=cv2.LINE_4)
    # cv2.imwrite('aaa.png', img)