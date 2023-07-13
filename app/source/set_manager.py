import json
from app.source.modules.generator import BlankGenerator
from app.source.modules.blank_reader import BlankReader
import app.source.modules.evaluator as eval
from PIL import Image
import os
import shutil
from pdf2image import convert_from_path
import pandas as pd
import json


class SetManager:
    def __init__(self, path='sets/'):
        self.path = path

    def create_set(self, set_name):
        path = f'{self.path}{set_name}/'
        if not os.path.isdir(path):
            os.makedirs(path)
        data = {
            "Codes": {
                "09-": 1,
                "10-": 1,
                "11-": 1
            },
            "Sections": [
                {
                    "Questions": [
                        {
                            "ans": "ABCDE",
                            "type": "SORT"
                        },
                        {
                            "ans": "ABCDE",
                            "type": "MATCH"
                        }
                    ]
                }
            ]
        }
        with open(f"{path}description.json", "w") as f:
            json.dump(data, f, indent=4)

    def generate_set(self, set_name):
        set_path = os.path.join(self.path, set_name)
        blanks_path = os.path.join(set_path, 'blanks')
        os.mkdir(blanks_path)
        bg = BlankGenerator(set_path)
        bg.generate()

        images = [
            Image.open(os.path.join(blanks_path,f'{blank}.png')) for blank in bg.keys
        ]

        images[0].save(
            os.path.join(set_path, 'blanks.pdf'),
            save_all=True,
            append_images=images[1:])

        shutil.rmtree(blanks_path)

    def get_answers(self, set_name):
        path = f'{self.path}{set_name}/'
        images = convert_from_path(f'{path}scans.pdf')

        os.mkdir(f'{path}scans')
        for i, image in enumerate(images):
            image.save(f'{path}scans/{i}.png', 'PNG')

        reader = BlankReader(path)
        for i in range(len(images)):
            reader.recognize_answers(f'{path}scans/{i}')
        reader.save_data(path)

        shutil.rmtree(f'{path}scans')

    def get_results(self, set_name):
        path = f'{self.path}{set_name}/'
        with open(f'{path}description.json', 'r') as f:
            description = json.load(f)
        problems = list()
        for problem in description['Problems']:
            if problem['type'] == 'MATCH':
                problems.append(eval.MatchProblem(
                    ref_ans=problem['ans'], max_pts=5))
            elif problem['type'] == 'SORT':
                problems.append(eval.SortProblem(
                    ref_ans=problem['ans'], max_pts=5, min_share=0.5))
            else:
                raise ValueError(f'Unknown type {problem["type"]}')
        ans_table = pd.read_csv(f'{path}table_code_answers.csv')
        eval.Evaluator(
            *problems).eval_table(ans_table).to_csv(f'{path}table_results.csv', index=False)


if __name__ == '__main__':
    sm = SetManager()
    # sm.create_set('demo')
    # sm.get_answers('demo')
    sm.get_results('demo')
