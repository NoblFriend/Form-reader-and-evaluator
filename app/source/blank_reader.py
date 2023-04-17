import json
import cv2
import numpy as np
import pandas as pd
from app.source.config import config
from tensorflow.keras.models import load_model


class BlankReader:
    def __init__(self, path, info_file='data.json', model='app/model/AM_50.model') -> None:
        info_file = f'{path}{info_file}'
        self._model = load_model(model)
        with open(info_file, 'r') as f:
            self._ref_coords = json.load(f)
        self.recognized_data = dict()
        self.recognized_data['Fields'] = self._ref_coords['Fields']
        self.table_code_answers = pd.DataFrame(columns=[f'q{i+1}' for i in range(len(self._ref_coords['Fields']))])
        self.table_code_answers.index.name = 'code'

    def _set_blank(self, path):
        self._cur_coords = {'QR': dict()}
        self._cur_letters = dict()
        self._cur_canvas = cv2.resize(cv2.imread(f'{path}.png'), (config.page.width, config.page.height))
        # cv2.imshow('a', self._cur_canvas)
        # cv2.waitKey()

    def _save_blank(self, path):
        cv2.imwrite(f'{path}_processed.png', self._cur_canvas)

    def _recover_blank(self):
        retval, data, points, aaaaa = cv2.QRCodeDetector().detectAndDecodeMulti(self._cur_canvas)
        unrecognized = False
        if(not retval):
            raise RuntimeError('cannot detect qr-codes')
        for d, p in zip(data, points):
            try:
                self._cur_coords['QR'][d.split('|')[0]] = [p[0], p[2]]
                self._cur_code = d.split('|')[1]
            except:
                if (not unrecognized):
                    unrecognized = True
                else:
                    raise RuntimeError(
                        f'Too many (at least 2) unrecognized qr codes on {self._path}')

        # if only 2 recognized will be implemented

        self._cur_canvas = cv2.warpAffine(src=self._cur_canvas,
                                      M=cv2.getAffineTransform(src=np.float32([self._cur_coords['QR']['bl'][1],
                                                                               self._cur_coords['QR']['tl'][1],
                                                                               self._cur_coords['QR']['tr'][1]]),
                                                               dst=np.float32([self._ref_coords['QR']['bl'][1],
                                                                               self._ref_coords['QR']['tl'][1],
                                                                               self._ref_coords['QR']['tr'][1]])),
                                      dsize=(config.page.width,
                                             config.page.height),
                                      flags=cv2.INTER_LINEAR)

    def _find_boxes(self):
        for row_key, row in self._ref_coords['Fields'].items():
            self._cur_letters[row_key] = dict()
            for box_key, box in row.items():
                delta = 3 * self._ref_coords['thickness']
                x1 = box[0][0]
                y1 = box[0][1]
                x2 = box[1][0]
                y2 = box[1][1]
                roi = self._cur_canvas[y1-delta:y2+delta, x1-delta:x2+delta]
                gray_img = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

                # # Применение пороговой обработки для создания бинарного изображения
                _, binary_img = cv2.threshold(
                    gray_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

                # # Поиск всех контуров в заданной области
                contours, _ = cv2.findContours(
                    binary_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

                # Вычисление площади заданного контура
                contour_area = (x2-x1)*(y2-y1)

                # Поиск контура, ближайшего по площади к заданному контуру
                min_diff = float('inf')
                nearest_contour = None
                for c in contours:
                    area = cv2.contourArea(c)
                    diff = abs(area - contour_area)
                    if diff < min_diff and area > contour_area:
                        min_diff = diff
                        nearest_contour = c

                delta = int(self._ref_coords['thickness']*2)
                x, y, w, h = cv2.boundingRect(nearest_contour)
                x1 = x + delta
                y1 = y + delta
                x2 = x + w - delta
                y2 = y + h - delta
                roi = roi[y1:y2, x1:x2]
                
                kernel = np.ones((2, 2), np.uint8)
                dilated_img = cv2.erode(roi, kernel, iterations=1)

                square_img = cv2.cvtColor(dilated_img, cv2.COLOR_BGR2GRAY)

                if h > w:
                    m1 = (h-w)//2
                    m2 = h-w - m1
                    square_img = cv2.copyMakeBorder(square_img, 0, 0, m1, m2, borderType=cv2.BORDER_CONSTANT, value=255)
                elif w > h:
                    m1 = (w-h)//2
                    m2 = w-h - m1
                    square_img = cv2.copyMakeBorder(square_img, m1, m2, 0, 0, borderType=cv2.BORDER_CONSTANT, value=255)

                square_img = cv2.bitwise_not(square_img)
                # cv2.imshow(f'{row_key}{box_key}', cv2.copyMakeBorder(square_img,10,10,10,10,borderType=cv2.BORDER_CONSTANT, value=255))
                # cv2.waitKey()
                resized_img = cv2.resize(square_img, (32, 32), interpolation=cv2.INTER_AREA)
                # cv2.imshow({}, resized_img)
                # cv2.waitKey()
                self._cur_letters[row_key][box_key] = np.expand_dims(resized_img.astype("float32") / 255.0, axis=-1)

    def _recognize_letters(self):
        self._cur_predictions = dict()
        label_names="ABCDEFGHIJKLM_"
        for row_key, row in self._cur_letters.items():
            self._cur_predictions[row_key] = dict()
            for box_key, box in row.items():
                array = np.array([box], dtype="float32")
                pred = self._model.predict(array)[0]
                self._cur_predictions[row_key][box_key] = dict({'pred' :  round(float(np.max(pred)),2), 'ans' :  label_names[np.argmax(pred)]})
        
        # with open('dump/pred.json', 'w') as f:
        #     json.dump(self._cur_predictions, f, indent=4)
    
    def recognize_answers(self, path):
        self._set_blank(path)
        try:
            self._recover_blank()
        except:
            print(f'ERROR file: {path}')
            raise
        else:
            self._find_boxes()
            self._recognize_letters()

            self.recognized_data[self._cur_code] = self._cur_predictions
            self.table_code_answers.loc[self._cur_code]= [''.join([box['ans'] for box in row.values()]) for row in self._cur_predictions.values()]
    
    def save_data(self, path):
        with open(f'{path}recognized.json', 'w') as f:
            json.dump(self.recognized_data, f, indent=4)
        self.table_code_answers.to_csv(f'{path}table_code_answers.csv')

if __name__ == '__main__':
    reader = BlankReader()
    reader.recognize_answers('sandbox/blanks/test')

    print(reader.recognized_data)

