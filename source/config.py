import cv2

class Configuration:
    class Page:
        def __init__(self):
            self.header = 328
            self.margin = 80

    class Fields:
        def __init__(self):
            self.row_spacing = 60
            self.box_size = 70
            self.box_spacing = 20

    class Font:
        def __init__(self):
            self.style = cv2.FONT_HERSHEY_DUPLEX
            self.base_height = 22
            self.base_width = 20

    class QR:
        def __init__(self):
            self.box_size = 8
            self.size = 21 * self.box_size
        

    def __init__(self):
        self.page = self.Page()
        self.fields = self.Fields()
        self.font = self.Font()
        self.qr = self.QR()

config = Configuration()
