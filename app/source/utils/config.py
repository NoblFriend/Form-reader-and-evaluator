

class Configuration:
    class Fonts:
        def __init__(self):
            base = 'app/source/utils/fonts'
            self.mono = f'{base}/RobotoMono-Regular.ttf'
            self.sans = f'{base}/Roboto-Regular.ttf'
            self.handwriting = f'{base}/Caveat-Regular.ttf'

    class Page:
        def __init__(self):
            self.header = 328
            self.margin = 80
            self.height = 1754
            self.width = 1240

    class Fields:
        def __init__(self):
            self.row_spacing = 60
            self.box_size = 70
            self.box_spacing = 20
            self.y_step = self.box_size + self.row_spacing
            self.number_spacing = 4
            self.number_height = 22
            self.question_number_gap = 30
            self.question_number_length = 2
            self.thickness = 4

    class Example:
        def __init__(self, page, fields):
            self.cell_size = fields.box_size
            self.cell_spacing = fields.box_spacing
            self.thickness = fields.thickness
            self.letter_font_size = int(fields.box_size * 0.9)
            self.label = 'П'
            self.caption = 'Пример заполнения'
            self.caption_height = 36
            self.caption_spacing = 15
            self.row_bottom_y = page.height - page.header

    class BlankInfo:
        def __init__(self, page, qr):
            self.x = page.margin + qr.size + 30
            self.y_top = page.height - page.margin - qr.size - 5
            self.title_height = 32
            self.line_height = 24
            self.line_spacing = 8

    class QR:
        def __init__(self, page):
            self.box_size = 9
            self.size = 21 * self.box_size
            self.coords = {
                'tl': [[page.margin, page.margin],
                       [page.margin + self.size, page.margin + self.size]],
                'tr': [[page.width - self.size - page.margin, page.margin],
                       [page.width - page.margin, page.margin + self.size]],
                'bl': [[page.margin, page.height - self.size - page.margin],
                       [page.margin + self.size, page.height - page.margin]]
            }

    def __init__(self):
        self.fonts = self.Fonts()
        self.page = self.Page()
        self.fields = self.Fields()
        self.qr = self.QR(self.page)
        self.example = self.Example(self.page, self.fields)
        self.blank_info = self.BlankInfo(self.page, self.qr)
        self.show_participant_code = False


config = Configuration()
