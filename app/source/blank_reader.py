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
        self.table_code_answers = pd.DataFrame(
            columns=[f'q{i+1}' for i in range(len(self._ref_coords['Fields']))])
        self.table_code_answers.index.name = 'code'

    def _set_blank(self, path):
        self._cur_coords = {'QR': dict()}
        self._cur_answers = dict()
        self._cur_canvas = cv2.resize(cv2.imread(
            f'{path}.png'), (config.page.width, config.page.height))

    def _save_blank(self, path):
        cv2.imwrite(f'{path}_processed.png', self._cur_canvas)

    def _recover_blank(self):
        retval, data, points, _ = cv2.QRCodeDetector(
        ).detectAndDecodeMulti(self._cur_canvas)
        unrecognized = False
        if (not retval):
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
                    pass

        src_points = []
        dst_points = []
        for pos in ['bl', 'tl', 'tr']:
            if pos in self._cur_coords['QR']:
                src_points.append(self._cur_coords['QR'][pos][1])
                dst_points.append(self._ref_coords['QR'][pos][1])

        # if len(src_points) == 1:
        #     src_points.append(
        #         self._cur_coords['QR'][data[0].split('|')[0]][2])
        #     dst_points.append(
        #         self._ref_coords['QR'][data[0].split('|')[0]][2])

        if len(src_points) == 2:
            src_points.append(
                self._cur_coords['QR'][data[0].split('|')[0]][0])
            dst_points.append(
                self._ref_coords['QR'][data[0].split('|')[0]][0])

        self._cur_canvas = cv2.warpAffine(
            src=self._cur_canvas,
            M=cv2.getAffineTransform(
                src=np.float32(src_points),
                dst=np.float32(dst_points)
            ),
            dsize=(
                config.page.width,
                config.page.height
            ),
            flags=cv2.INTER_LINEAR
        )

    def _get_corners_from_box(self, box):
        return box[0][0], box[0][1], box[1][0], box[1][1]

    def _roi_by_corners(self, canvas, corners, delta=0):
        x1, y1, x2, y2 = corners
        return canvas[y1-delta:y2+delta, x1-delta:x2+delta]

    def _roi_by_wh(self, canvas, corner_wh, delta=0):
        x, y, w, h = corner_wh
        return self._roi_by_corners(
            canvas=canvas,
            corners=(x, y, x+w, y+h),
            delta=delta
        )

    def _contours_from_roi(self, roi):
        gray_img = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        _, binary_img = cv2.threshold(
            gray_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        contours, _ = cv2.findContours(
            binary_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        return contours

    def _find_nearest_contour(self, box, contours):
        x1, y1, x2, y2 = self._get_corners_from_box(box)
        contour_area = (x2-x1)*(y2-y1)

        min_diff = float('inf')
        nearest_contour = None
        for c in contours:
            area = cv2.contourArea(c)
            diff = abs(area - contour_area)
            if diff < min_diff and area > contour_area:
                min_diff = diff
                nearest_contour = c

        return nearest_contour

    def _make_squared(self, img, size):
        h, w = img.shape

        if h > w:
            m1 = (h-w)//2
            m2 = h-w - m1
            square_img = cv2.copyMakeBorder(
                img, 0, 0, m1, m2, borderType=cv2.BORDER_CONSTANT, value=255)
        elif w > h:
            m1 = (w-h)//2
            m2 = w-h - m1
            square_img = cv2.copyMakeBorder(
                img, m1, m2, 0, 0, borderType=cv2.BORDER_CONSTANT, value=255)
        else:
            square_img = img

        return cv2.resize(square_img, (size, size), interpolation=cv2.INTER_AREA)

    def _prepare_roi_to_recognition(self, roi, ):
        dilated_img = cv2.erode(
            src=roi,
            kernel=np.ones((2, 2), np.uint8),
            iterations=1
        )

        return self._make_squared(
            img=cv2.bitwise_not(cv2.cvtColor(dilated_img, cv2.COLOR_BGR2GRAY)),
            size=32
        )

    def _find_boxes(self):
        for row_key, row in self._ref_coords['Fields'].items():
            self._cur_answers[row_key] = dict()
            for box_key, box in row.items():
                wide_roi = self._roi_by_corners(
                    canvas=self._cur_canvas,
                    corners=self._get_corners_from_box(box),
                    delta=3 * self._ref_coords['thickness']
                )

                nearest_contour = self._find_nearest_contour(
                    box=box,
                    contours=self._contours_from_roi(wide_roi)
                )

                self._cur_answers[row_key][box_key] = np.expand_dims(
                    self._prepare_roi_to_recognition(
                        roi=self._roi_by_wh(
                            canvas=wide_roi,
                            corner_wh=cv2.boundingRect(nearest_contour),
                            delta=-int(self._ref_coords['thickness'])*2
                        )
                    ).astype("float32") / 255.0,
                    axis=-1
                )

    def _recognize_letters(self):
        self._cur_predictions = dict()
        label_names = "ABCDEFGHIJKLM_"
        for row_key, row in self._cur_answers.items():
            self._cur_predictions[row_key] = dict()
            for box_key, box in row.items():
                array = np.array([box], dtype="float32")
                pred = self._model.predict(array)[0]
                self._cur_predictions[row_key][box_key] = dict(
                    {'pred':  round(float(np.max(pred)), 2), 'ans':  label_names[np.argmax(pred)]})

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
            self.table_code_answers.loc[self._cur_code] = [''.join(
                [box['ans'] for box in row.values()]) for row in self._cur_predictions.values()]

    def save_data(self, path):
        with open(f'{path}recognized.json', 'w') as f:
            json.dump(self.recognized_data, f, indent=4)
        self.table_code_answers.to_csv(f'{path}table_code_answers.csv')


class SingleAnswerBlankReader(BlankReader):
    def __init__(self, path, info_file='data.json') -> None:
        info_file = f'{path}{info_file}'
        with open(info_file, 'r') as f:
            self._ref_coords = json.load(f)
        self.recognized_data = dict()
        self.recognized_data['Fields'] = self._ref_coords['Fields']
        self.table_code_answers = pd.DataFrame(
            columns=[f'q{i+1}' for i in range(len(self._ref_coords['Fields']))])
        self.table_code_answers.index.name = 'code'

    def _recognize_letters(self):
        self._cur_predictions = dict()
        for row_key, row in self._cur_answers.items():
            self._cur_predictions[row_key] = dict()
            for i, (box_key, box) in enumerate(row.items()):
                self._cur_predictions[row_key][box_key] = dict({
                    'item':  chr(ord('A') + i),
                    'brightness': round(cv2.sumElems(box)[0], -1)
                })

            self._cur_predictions[row_key]['ans'] = max(
                self._cur_predictions[row_key].values(),
                key=lambda item: item['brightness']
            )['item']

    def recognize_answers(self, path):
        self._set_blank(path)
        try:
            self._recover_blank()
        except:
            print(f'ERROR file: {path}')
            # raise
        else:
            self._find_boxes()
            self._recognize_letters()

            self.recognized_data[self._cur_code] = self._cur_predictions
            # self.table_code_answers.loc[self._cur_code] = [''.join(
            #     [box['ans'] for box in row.values()]) for row in self._cur_predictions.values()]
            self.table_code_answers.loc[self._cur_code] = [
            row['ans'] for row in self._cur_predictions.values()]


if __name__ == '__main__':
    reader = BlankReader()
    reader.recognize_answers('sandbox/blanks/test')

    print(reader.recognized_data)
