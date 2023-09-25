import json
from app.source.modules.generator import BlankGenerator
from app.source.modules.restorer import BlankRestorer
from app.source.modules.reader import BlankReader
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

    def restore_blanks(self, set_name):
        set_path = os.path.join(self.path, set_name)
        images = convert_from_path(os.path.join(set_path, 'scans.pdf')) 

        restorer = BlankRestorer(set_path)

        for image in images:
            restorer.restore(image)

        warnings, errors = restorer.get_logs()

        print(warnings, errors)


    def get_answers(self, set_name):
        set_path = os.path.join(self.path, set_name)
        scans_path = os.path.join(set_path, 'scans')  
        
        reader = BlankReader(set_path) 
        reader.recognize_answers_in_folder(scans_path)  
        reader.save_data(set_path) 


    def get_results(self, set_name):
        set_path = os.path.join(self.path, set_name)
        with open(os.path.join(set_path, 'description.json'), 'r') as f:
            description = json.load(f)
        # Загрузка проблем из разделов
        problems = []
        for section in description['Sections']:
            for problem in section['Questions']:
                problem_type = problem['type']
                ref_ans = problem['ans']
                if problem_type == 'MATCH':
                    problems.append(eval.MatchProblem(ref_ans=ref_ans, max_pts=5))
                elif problem_type == 'SORT':
                    problems.append(eval.SortProblem(ref_ans=ref_ans, max_pts=5, min_share=0.5))
                else:
                    raise ValueError(f'Unknown type {problem_type}')
        ans_table = pd.read_csv(os.path.join(set_path, 'recognized.csv'))
        evaluated_table = eval.Evaluator(*problems).eval_table(ans_table)
        evaluated_table.to_csv(os.path.join(set_path, 'results.csv'), index=False)


if __name__ == '__main__':
    sm = SetManager()
    # sm.create_set('demo')
    # sm.get_answers('demo')
    sm.get_results('demo')
