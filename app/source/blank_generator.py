import numpy as np
import app.source.graphics as graphics
import json

from app.source.config import config


class Blank:
    def __init__(self) -> None:
        self.canvas = graphics.get_canvas(
            height=config.page.height,
            width=config.page.width
        )

    def save(self, path) -> None:
        graphics.save_canvas(
            path=f'{path}.png',
            canvas=self.canvas
        )

    def copy(self):
        blank_copy = Blank()
        blank_copy.canvas = self.canvas.copy()
        return blank_copy


class BlankGenerator:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self._coords = {'Fields': dict()}
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
        # x_step = config.fields.box_size + config.fields.box_spacing
        # y_step = config.fields.box_size + config.fields.row_spacing
        row = f'Row {self._fields_rows_count + 1}'
        box = f'Box {pos+1}'
        self._coords['Fields'][row][box] = graphics.draw.rectangle(
            canvas=self._product.canvas,
            top_left_x=config.page.margin +
            pos * config.fields.x_step + shift_x,
            top_left_y=config.page.header +
            self._fields_rows_count * config.fields.y_step,
            size=config.fields.box_size
        )['coords']
        self._coords['thickness'] = graphics.draw.rectangle.thickness

        if (numbered):
            graphics.draw.text(
                canvas=self._product.canvas,
                text=str(pos+1),
                x=self._coords['Fields'][row][box][0][0],
                y=self._coords['Fields'][row][box][1][1] + 5,
                font_scale=1,
                pos='top',
                color_style='second'
            )

    def _draw_row_num(self) -> int:
        return graphics.draw.text(
            canvas=self._product.canvas,
            text=str(self._fields_rows_count + 1) + '.',
            x=config.page.margin,
            y=config.page.header +
            self._fields_rows_count * config.fields.y_step +
            config.fields.box_size//2,
            font_scale=2,
            pos='mid'
        )['width']

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
        
        # self.dump_data(path)

        for code in codes:
            product = self._product.copy()
            graphics.draw.text(
                canvas=product.canvas,
                text=str(code).zfill(3),
                x=400, y=180,
                font_scale=4,
                thickness=5
            )
            for pos, qr_coord in zip(positions, pos_coords):
                graphics.draw.qr(
                    canvas=product.canvas,
                    coord=qr_coord,
                    data=f'{pos}|{code}'
                )
            # product.save(f'{path}/blanks/{code}')
            product.save(f'demo/blank_{code}')


def main():
    b = BlankGenerator()
    b.place_fields_row(count=5)
    b.place_fields_row(count=5, numbered=True)
    b.place_fields_row(count=5)
    b.place_fields_row(count=5)
    b.place_fields_row(count=5)
    code = 228
    b.place_codes(codes=[code], path=None)
    b.blank.save(f'demo/blank')


if __name__ == '__main__':
    main()