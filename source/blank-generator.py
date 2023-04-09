import cv2 
import numpy as np
import qrcode


class Blank:
    def __init__(self, height=1754, width=1240) -> None:
        self.canvas = np.ones((height, width), dtype=np.uint8) * 255

    def save(self, path) -> None:
        cv2.imwrite(f'{path}.png', self.canvas)
    

class BlankBuilder:
    def __init__(self, header_height=328, margin=80) -> None:
        self.header_height = header_height
        self.margin = margin

        self.field_size = 70
        self.field_spacing = 20

        self.row_spacing = 60

        self._fields_rows_count = 0

        self.font = cv2.FONT_HERSHEY_DUPLEX
        self.font_base_height = 22
        self.font_base_width = 20

        self.qr_box_size = 8
        self.qr_size = 21 * self.qr_box_size 

        self.reset()

    def reset(self) -> None:
        self._product = Blank()

    @property
    def blank(self) -> Blank:
        product = self._product
        self.reset()
        return product
    


    def _draw_field(self, pos, shift_x = 0, numbered=False) -> None:
        x1 = self.margin + pos * (self.field_size + self.field_spacing) + shift_x
        y1 = self.header_height + self._fields_rows_count * (self.row_spacing + self.field_size)
        x2 = x1 + self.field_size
        y2 = y1 + self.field_size
        cv2.rectangle(self._product.canvas, (x1, y1), (x2, y2), color=0, thickness=4, lineType=cv2.LINE_4)
        if (numbered):
            font_scale = 1
            x = x1
            y = y2 + font_scale*self.font_base_height + 5
            cv2.putText(self._product.canvas,str(pos+1), (x,y), 
                        self.font, fontScale=font_scale,color=100, thickness=1, lineType=cv2.LINE_AA)

    def _draw_row_num(self) -> int:
        x = self.margin
        y = self.header_height + self._fields_rows_count * (self.row_spacing + self.field_size)
        font_scale = 2
        y += (self.font_base_height*font_scale + self.field_size) // 2
        num = str(self._fields_rows_count + 1) + '.'
        cv2.putText(self._product.canvas,num, (x,y), 
                    self.font, fontScale=font_scale,color=0, thickness=2, lineType=cv2.LINE_AA)
        return self.font_base_width*font_scale*len(num)

    def place_fields_row(self, count, numbered=False) -> None:
        shift_x = self._draw_row_num()
        for pos in range(count):
            self._draw_field(pos, shift_x, numbered)
        self._fields_rows_count += 1
        pass

    def place_info(self) -> None:
        #will be implemented
        pass

    def place_code(self, code) -> None:
        cv2.putText(self._product.canvas, str(code).zfill(3), [400, 180], self.font, fontScale=4, color=0, thickness=5, lineType=cv2.LINE_AA)

        qr = qrcode.QRCode(version=1,box_size=self.qr_box_size,border=0)
        qr.add_data(code)
        img_qr = (1-np.asarray(qr.make_image(fill_color='black', back_color='white').modules, dtype=np.uint8))*255
        img_qr = cv2.resize(img_qr, (self.qr_size,self.qr_size),interpolation=cv2.INTER_NEAREST)
        x1 = self.margin
        y1 = self.margin
        x2 = self.margin+self.qr_size
        y2 = self.margin+self.qr_size
        self._product.canvas[x1:x2, y1:y2] = img_qr
        pass

if __name__ == '__main__':
    b = BlankBuilder()
    b.place_fields_row(count=5)
    b.place_fields_row(count=5,numbered=True)
    b.place_fields_row(count=5)
    b.place_fields_row(count=5)
    b.place_fields_row(count=5)
    b.place_code(code=200)
    b.blank.save('aaa')
    
