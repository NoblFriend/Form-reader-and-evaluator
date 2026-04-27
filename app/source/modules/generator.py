import numpy as np
import app.source.utils.graphics as graphics
import json
import os

from app.source.utils.config import config


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


class Cell:
    def __init__(self, size, number, numbered) -> None:
        self.size = size
        self.thickness = config.fields.thickness
        self.number = number + 1
        self.numbered = numbered

    def draw(self, drawer: graphics.Drawer, cursor: graphics.Cursor) -> None:
        cursor.save_pos()
        if self.numbered:
            drawer.text(
                cursor=cursor.move(dy=config.fields.box_size +
                                   config.fields.number_spacing),
                text=str(self.number),
                letter_height=config.fields.number_height,
                pos='top',
                color_style='second'
            )
        cursor.return_pos()
        self.box = drawer.rectangle(
            cursor=cursor,
            size=self.size,
            thickness=self.thickness
        )['box']

    def dump(self) -> list():
        return self.box


class QuestionNumber:
    def __init__(self, number, height, length) -> None:
        self.length = length
        self.height = height
        self.number = number + 1

    def draw(self, drawer: graphics.Drawer, cursor) -> None:
        drawer.text(
            cursor=cursor,
            text=f'{self.number:>{self.length}}.',
            box_height=self.height,
            letter_height=self.height,
            pos='mid'
        )


class Question:
    def __init__(self, number, description) -> None:
        if description["type"] in ["SORT", "MATCH"]:
            count = len(description["ans"])
            size = config.fields.box_size
            numbered = description["type"] == "MATCH"
        self.number = QuestionNumber(
            number=number,
            height=size,
            length=2
        )
        self.cells = [Cell(size, num, numbered) for num in range(count)]

    def draw(self, drawer: graphics.Drawer, cursor: graphics.Cursor) -> None:
        cursor.save_pos()
        self.number.draw(drawer, cursor)
        cursor.move(dx=config.fields.question_number_gap)
        for cell in self.cells:
            cell.draw(drawer, cursor)
            cursor.move(dx=config.fields.box_spacing)
        cursor.return_pos()
        cursor.move(dy=config.fields.y_step)

    def dump(self) -> dict():
        return {
            'Metadata': {'thickness': config.fields.thickness},
            'Cells': [cell.dump() for cell in self.cells]
        }


class Section:
    def __init__(self, number, description) -> None:
        self.cursor = graphics.Cursor(config.page.margin, config.page.header)
        self.questions = [
            Question(num, desc)for num, desc in enumerate(description["Questions"])
        ]

    def draw(self, drawer: graphics.Drawer) -> None:
        for question in self.questions:
            question.draw(drawer, self.cursor)

    def dump(self) -> dict():
        return {'Questions': [quest.dump() for quest in self.questions]}


class ExampleRow:
    def __init__(self, letters: str) -> None:
        self.letters = letters

    def draw(self, drawer: graphics.Drawer) -> None:
        cfg = config.example
        row_top = cfg.row_bottom_y - cfg.cell_size

        cursor = graphics.Cursor(config.page.margin, row_top)
        drawer.text(
            cursor=cursor,
            text=f'{cfg.label:>{config.fields.question_number_length}}.',
            box_height=cfg.cell_size,
            letter_height=cfg.cell_size,
            pos='mid',
            font_path=config.fonts.mono
        )
        cursor.move(dx=config.fields.question_number_gap)
        first_cell_x = int(cursor.x)

        caption_top = row_top - cfg.caption_spacing - cfg.caption_height
        drawer.text(
            cursor=graphics.Cursor(first_cell_x, caption_top),
            text=cfg.caption,
            letter_height=cfg.caption_height,
            pos='top',
            font_path=config.fonts.sans
        )

        for letter in self.letters:
            cell_cursor = graphics.Cursor(int(cursor.x), row_top)
            drawer.rectangle(
                cursor=cell_cursor, size=cfg.cell_size, thickness=cfg.thickness
            )
            drawer.ttf_text_centered(
                font_path=config.fonts.handwriting,
                font_size=cfg.letter_font_size,
                text=letter,
                center=(int(cursor.x) + cfg.cell_size // 2,
                        row_top + cfg.cell_size // 2)
            )
            cursor.move(dx=cfg.cell_size + cfg.cell_spacing)


class BlankInfoBlock:
    def __init__(self, info: dict, key: str) -> None:
        cls = key.split('-')[0].lstrip('0') or '0'
        self.title = info.get('name', '')
        self.lines = [
            f'{cls} класс',
            info.get('stage', ''),
            info.get('competition', ''),
            info.get('location', ''),
            info.get('date', ''),
        ]

    def draw(self, drawer: graphics.Drawer) -> None:
        cfg = config.blank_info
        y = cfg.y_top
        if self.title:
            drawer.text(
                cursor=graphics.Cursor(cfg.x, y),
                text=self.title,
                letter_height=cfg.title_height,
                pos='top',
                font_path=config.fonts.sans
            )
            y += cfg.title_height + cfg.line_spacing
        for line in self.lines:
            if not line:
                continue
            drawer.text(
                cursor=graphics.Cursor(cfg.x, y),
                text=line,
                letter_height=cfg.line_height,
                pos='top',
                font_path=config.fonts.sans
            )
            y += cfg.line_height + cfg.line_spacing


class CodeKey:
    def __init__(self, key) -> None:
        self.key = key

    def draw(self, drawer: graphics.Drawer) -> None:
        drawer.text(
            cursor=graphics.Cursor(400, 180),
            text=str(self.key),
            letter_height=100,
            thickness=5
        )


class Qr:
    def __init__(self, pos, key) -> None:
        self.pos = pos
        self.key = key

    def draw(self, drawer: graphics.Drawer) -> None:
        drawer.qr(
            coords=config.qr.coords[self.pos],
            data=f'{self.pos}|{self.key}'
        )


class Codes:
    def __init__(self, key) -> None:
        self.key = CodeKey(key)
        self.qrs = [Qr(pos, key) for pos in config.qr.coords.keys()]

    def key_gen(desc: dict) -> list:
        codes = list()
        for prefix, count in desc.items():
            codes.extend([
                f'{prefix}{num:0{len(str(count-1))}}' for num in range(count)
            ])
        return codes

    def draw(self, drawer: graphics.Drawer) -> None:
        if config.show_participant_code:
            self.key.draw(drawer)
        for qr in self.qrs:
            qr.draw(drawer)

    def dump() -> dict():
        return config.qr.coords


class BlankGenerator:
    def __init__(self, path) -> None:
        self.blank = Blank()
        self.path = path
        with open(os.path.join(path, 'description.json'), 'r') as f:
            description = json.load(f)
        self.sections = [
            Section(num, desc) for num, desc in enumerate(description['Sections'])
        ]
        self.keys = Codes.key_gen(description['Codes'])
        self.codes = [
            Codes(key) for key in self.keys
        ]
        example_letters = description.get('ExampleLetters')
        self.example = ExampleRow(example_letters) if example_letters else None
        self.blank_info = description.get('BlankInfo')

    def draw(self):
        for section in self.sections:
            section.draw(
                drawer=graphics.Drawer(self.blank.canvas)
            )
        if self.example is not None:
            self.example.draw(drawer=graphics.Drawer(self.blank.canvas))
        for code in self.codes:
            new_blank = self.blank.copy()
            drawer = graphics.Drawer(new_blank.canvas)
            code.draw(drawer=drawer)
            if self.blank_info is not None:
                BlankInfoBlock(self.blank_info, code.key.key).draw(drawer)
            new_blank.save(os.path.join(self.path, 'blanks', code.key.key))

    def dump(self):
        with open(os.path.join(self.path, 'generator_data.json'), 'w') as f:
            json.dump(
                obj={
                    'Sections': [sect.dump() for sect in self.sections],
                    'Codes': Codes.dump()
                },
                fp=f,
                indent=4,
                sort_keys=True
            )

    def generate(self):
        self.draw()
        self.dump()
