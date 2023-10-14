import cv2
import numpy as np
import json
from app.source.utils.config import config
import os

class BlankRestorer:
    def __init__(self, set_path):
        self.scans_path = os.path.join(set_path, 'scans')
        os.mkdir(self.scans_path)
        with open(os.path.join(set_path, 'generator_data.json'), 'r') as f:
            self.ref_coords = json.load(f)['Codes']
        self.fail_count = 0  
        self.warning_list = []
        self.error_list = []

    def _get_image(self, src_image):
        tmp_file = os.path.join(self.scans_path, 'tmp.png')
        src_image.save(tmp_file, 'PNG')
        image = cv2.resize(cv2.imread(tmp_file), (config.page.width, config.page.height))
        os.remove(tmp_file)
        return image

    def restore(self, src_image):
        image = self._get_image(src_image)
        retval, data, points, _ = cv2.QRCodeDetector().detectAndDecodeMulti(image)
        coords = {pos: None for pos in self.ref_coords.keys()}
        image_key = "UNKNOWN"

        if retval:
            for i, (d, p) in enumerate(zip(data, points)):
                if '|' in d:
                    pos, image_key = d.split('|')
                    coords[pos] = [p[0], p[2]]
                    
            found_codes = [key for key, value in coords.items() if value is not None]
            num_found = len(found_codes)

            if num_found == 3:
                src_pts = np.float32([coords[pos][1] for pos in found_codes])
                dst_pts = np.float32([self.ref_coords[pos][1] for pos in found_codes])
                M = cv2.getAffineTransform(src_pts, dst_pts)
                image = cv2.warpAffine(image, M, (config.page.width, config.page.height), flags=cv2.INTER_LINEAR)
                
            elif num_found == 2:
                self.warning_list.append(f"{image_key}: Only two QR codes found.")
                

            elif num_found == 1:
                self.warning_list.append(f"{image_key}: Only one QR code found.")
                # Handle the case with only one point here, if needed

        else:
            self.fail_count += 1
            self.error_list.append(f"Fail_{self.fail_count}: No QR codes found.")
            image_key = f"Fail_{self.fail_count}"

        output_path = os.path.join(self.scans_path, f"{image_key}.png")
        cv2.imwrite(output_path, image)

    def get_logs(self):
        return self.warning_list, self.error_list

