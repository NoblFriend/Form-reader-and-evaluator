import json
from blank_generator import BlankGenerator
from blank_reader import BlankReader
import evaluator as eval
from PIL import Image
import os
import shutil
from pdf2image import convert_from_path
import pandas as pd


class SetManager:
    def __init__(self, path='sets/'):
        self.path = path
    
    def create_set(self, set_name):
        path = f'{self.path}{set_name}/'
        with open(f'{path}description.json', 'r') as f:
            description = json.load(f)

        codes = list()
        for prefix, count in description['Codes'].items():
            codes.extend([f'{prefix}-{num:02}' for num in range(count)])


        blank_generator = BlankGenerator()
        os.mkdir(f'{path}blanks')
        for problem in description['Problems']:
            blank_generator.place_fields_row(count=len(problem['ans']),numbered=(problem['type']=='MATCH'))
        blank_generator.place_codes(codes, f'{path}')

        images = [Image.open(f'{path}blanks/{code}.png') for code in codes]

        images[0].save(f'{path}blanks.pdf', save_all=True, append_images=images[1:])
        shutil.rmtree(f'{path}blanks')

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
        # print(reader.recognized_data)

    def get_results(self, set_name):
        path = f'{self.path}{set_name}/'
        with open(f'{path}description.json', 'r') as f:
            description = json.load(f)
        problems = list()
        for problem in description['Problems']:
            if problem['type'] == 'MATCH':
                problems.append(eval.MatchProblem(ref_ans=problem['ans'], max_pts=5))
            elif problem['type'] == 'SORT':
                problems.append(eval.SortProblem(ref_ans=problem['ans'], max_pts=5, min_share=0.5))
            else:
                raise ValueError(f'Unknown type {problem["type"]}')
        ans_table = pd.read_csv(f'{path}table_code_answers.csv')
        eval.Evaluator(*problems).eval_table(ans_table).to_csv(f'{path}table_results.csv', index=False)


if __name__ == '__main__':
    sm = SetManager()
    # sm.create_set('demo')
    # sm.get_answers('demo')
    sm.get_results('demo')
    

