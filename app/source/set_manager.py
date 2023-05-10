import json
from app.source.blank_generator import BlankGenerator
from app.source.blank_reader import BlankReader, SingleAnswerBlankReader
import app.source.evaluator as eval
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
            "Type": "multiple",
            "Codes": {"09": 1, "10": 1, "11": 1},
            "Problems": [
                {"ans": "ABCDE", "type": "SORT"},
                {"ans": "ABCDE", "type": "MATCH"}
            ]
        }
        with open(f"{path}description.json", "w") as f:
            json.dump(data, f, indent=4)

    def generate_set(self, set_name):
        path = f'{self.path}{set_name}/'
        with open(f'{path}description.json', 'r') as f:
            description = json.load(f)

        codes = list()
        for prefix, count in description['Codes'].items():
            codes.extend([f'{prefix}-{num:02}' for num in range(count)])

        blank_generator = BlankGenerator()
        os.mkdir(f'{path}blanks')
        for problem in description['Problems']:
            if description['Type'] == 'multiple':
                blank_generator.place_fields_row(
                    count=len(problem['ans']), numbered=(problem['type'] == 'MATCH'))
            elif description['Type'] == 'single':
                blank_generator.place_fields_row(
                    count=description['Answers']
                )
        blank_generator.place_codes(codes, f'{path}')

        images = [Image.open(f'{path}blanks/{code}.png') for code in codes]

        images[0].save(f'{path}blanks.pdf', save_all=True,
                       append_images=images[1:])
        shutil.rmtree(f'{path}blanks')

    def get_answers(self, set_name):
        path = f'{self.path}{set_name}/'
        input_folder = f'{path}scans/'
        output_folder = f'{path}pro_scans/'

        if os.path.exists(output_folder):
            shutil.rmtree(output_folder)

        os.makedirs(output_folder)

        pdf_files = [f for f in os.listdir(input_folder) if f.endswith('.pdf')]
        cnt = 0
        for pdf_file in pdf_files:
            images = convert_from_path(f'{input_folder}{pdf_file}')

            for image in images:
                image.save(f'{output_folder}{cnt}.png', 'PNG')
                cnt+=1

        reader = SingleAnswerBlankReader(path)
        for i in range(len(images)):
            reader.recognize_answers(f'{output_folder}{i}')
        reader.save_data(path)

        # shutil.rmtree(f'{path}scans')

    def get_results(self, set_name):
        path = f'{self.path}{set_name}/'
        with open(f'{path}description.json', 'r') as f:
            description = json.load(f)
        problems = list()
        for problem in description['Problems']:
            if description['Type'] == 'single':
                problems.append(eval.MarkProblem(
                    ref_ans=problem, max_pts=1)
                )
            elif problem['type'] == 'MATCH':
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
