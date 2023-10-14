# Импортируем необходимые библиотеки
import json
import cv2
import numpy as np
import pandas as pd
from keras.models import load_model
import os

# Класс для обработки изображения
class ImageProcessor:
    def get_corners_from_box(box):
        return box[0][0], box[0][1], box[1][0], box[1][1]

    def roi_by_corners(canvas, corners, delta=0):
        x1, y1, x2, y2 = corners
        return canvas[y1-delta:y2+delta, x1-delta:x2+delta]

    def roi_by_wh(canvas, corner_wh, delta=0):
        x, y, w, h = corner_wh
        return ImageProcessor.roi_by_corners(
            canvas=canvas,
            corners=(x, y, x+w, y+h),
            delta=delta
        )

    @staticmethod
    def contours_from_roi(roi):
        gray_img = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, binary_img = cv2.threshold(
            gray_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(
            binary_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return contours

class AnswerRecognizer:
    def __init__(self, model_path):
        self._model = load_model(model_path)
        self.label_names = "ABCDEFGHIJKLM_"

    def recognize(self, processed_roi):
        array = np.array([processed_roi], dtype="float32")
        pred = self._model.predict(array)[0]
        return {
            'pred': round(float(np.max(pred)), 2),
            'ans': self.label_names[np.argmax(pred)]
        }

class BlankReader:
    def __init__(self, path, info_file='generator_data.json', model='app/model/AM_50.model'):
        info_file = os.path.join(path, info_file)
        with open(info_file, 'r') as f:
            self._ref_coords = json.load(f)
        self.recognized_data = {}
        self.answer_recognizer = AnswerRecognizer(model)

    def find_nearest_contour(self, box, contours):
        x1, y1, x2, y2 = box[0][0], box[0][1], box[1][0], box[1][1]
        contour_area = (x2 - x1) * (y2 - y1)
        min_diff = float('inf')
        nearest_contour = None
        for c in contours:
            area = cv2.contourArea(c)
            diff = abs(area - contour_area)
            if diff < min_diff and area > contour_area:
                min_diff = diff
                nearest_contour = c
        return nearest_contour

    def prepare_roi_for_recognition(self, roi):
        dilated_img = cv2.erode(
            src=roi,
            kernel=np.ones((2, 2), np.uint8),
            iterations=1
        )
        square_img = cv2.bitwise_not(cv2.cvtColor(dilated_img, cv2.COLOR_BGR2GRAY))
        return square_img.astype("float32") / 255.0


    def recognize_answers_in_folder(self, folder_path):
        for image_name in os.listdir(folder_path):
            if not image_name.startswith("Fail_"):
                image_path = os.path.join(folder_path, image_name)
                print(image_path)
                self.recognize_answers(image_path)
        

    def recognize_answers(self, image_path):
        self._cur_canvas = cv2.imread(image_path)
        self._cur_code = os.path.splitext(os.path.basename(image_path))[0]
        self.recognized_data[self._cur_code] = {}
        
        for section_idx, section in enumerate(self._ref_coords['Sections']):
            section_key = f"Section_{section_idx+1}"
            self.recognized_data[self._cur_code][section_key] = {}
            for question_idx, question in enumerate(section['Questions']):
                question_key = f"Question_{question_idx+1}"
                self.recognized_data[self._cur_code][section_key][question_key] = {}
                for idx, box in enumerate(question['Cells']):
                    box_key = f"Cell_{idx+1}"
                    wide_roi = ImageProcessor.roi_by_corners(
                        canvas=self._cur_canvas,
                        corners=(box[0][0], box[0][1], box[1][0], box[1][1]), 
                        delta=3 * question['Metadata']['thickness']
                    )
                    contours = ImageProcessor.contours_from_roi(wide_roi)
                    nearest_contour = self.find_nearest_contour(box, contours)
                    
                    if nearest_contour is not None:
                        processed_roi = self.prepare_roi_for_recognition(
                            ImageProcessor.roi_by_wh(
                                canvas=wide_roi,
                                corner_wh=cv2.boundingRect(nearest_contour),
                                delta=-int(question['Metadata']['thickness']*2)
                            )
                        )
                        processed_roi = cv2.resize(processed_roi, (32, 32))
                        self.recognized_data[self._cur_code][section_key][question_key][box_key] = self.answer_recognizer.recognize(processed_roi)
                    else:
                        self.recognized_data[self._cur_code][section_key][question_key][box_key] = {"pred": 0, "ans": "N/A"}

    def save_data(self, path):
        with open(os.path.join(path, 'recognized.json'), 'w') as f:
            json.dump(self.recognized_data, f, indent=4)
        df_data = {}
        
        for code, sections in self.recognized_data.items():
            df_data[code] = {}
            for section_key, questions in sections.items():
                section_number = section_key.split("_")[-1]
                
                for question_key, cells in questions.items():
                    question_number = question_key.split("_")[-1] 
                    column_name = f"S{section_number}Q{question_number}"
                    
                    answers = "".join(cells[cell_key]["ans"] if cells[cell_key]["ans"] != "N/A" else "_" for cell_key in sorted(cells.keys()))
                    df_data[code][column_name] = answers

        df = pd.DataFrame.from_dict(df_data, orient='index')
        df.sort_index(ascending=True).to_csv(os.path.join(path, 'recognized.csv'), index_label='Code')

