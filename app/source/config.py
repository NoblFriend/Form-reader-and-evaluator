

class Configuration:
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
            self.x_step = self.box_size + self.box_spacing
            self.y_step = self.box_size + self.row_spacing


    class QR:
        def __init__(self, page):
            self.box_size = 9
            self.size = 21 * self.box_size
            self.tl = (page.margin, page.margin,
                             page.margin + self.size, page.margin + self.size)
            self.tr = (page.width - self.size - page.margin, page.margin,
                              page.width - page.margin, page.margin + self.size)
            self.bl = (page.margin, page.height - self.size - page.margin,
                             page.margin + self.size, page.height - page.margin)

    def __init__(self):
        self.page = self.Page()
        self.fields = self.Fields()
        self.qr = self.QR(self.page)


config = Configuration()
