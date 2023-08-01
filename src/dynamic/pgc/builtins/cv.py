import cv2
import numpy as np
import pytesseract

from typing import List
from pathlib import Path

from ..models.point import Point
from ..models.page.recorder import Snapshot
from ..utils.algorithm.hashing import calc_sha256


class CVMatcher:
    """
    @attr prompt: 我们感兴趣的引导词
    @attr temp_path: 引导词模板图片保存路径
    """
    def __init__(self, prompt):
        self.prompt = prompt
        self.temp_snapshot = Path.cwd() / 'template' / f"{calc_sha256(prompt)}.png"
        self.matched_points:List[Point] = []

    def search_matched(self, src, template, scale) -> List[Point]:
        """将原图中的引导词模板匹配出来并添加到 matched_points 中

        @param src: 原图
        @param template: 模板图
        @param scale: 模板图缩放比例
        """
        threshold = 0.7679687500000001
        img_gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)

        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.resize(template_gray, None, fx=scale, fy=scale)
        template_size = template_gray.shape[:2]

        match_degree = cv2.matchTemplate(img_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        loc = np.where(match_degree >= threshold)

        for candis in zip(*loc[::-1]):
            point = Point(x = candis[0]+template_size[1]/2,
                          y = candis[1]+template_size[0]/2,
                          judge = 0)
            point.judge += 1
            roi = img_gray[candis[1] : candis[1] + template_size[0], candis[0] : candis[0] + template_size[1]]
            text = pytesseract.image_to_string(roi, lang='chi_sim', config='--psm 11')
            if self.prompt in text:
                point.judge += 1

            if not any([point.is_close_to(other) for other in self.matched_points]):
                self.matched_points.append(point)

    def get_elements(self):
        """
        读取截图和模板图，进行模板匹配
        @return: [(x, y), ...] sorted by judge
        """
        ori_img  = cv2.imread(str(Snapshot.get_snapshot_path()))
        temp_img = cv2.imread(str(self.temp_snapshot))
        try:
            temp_h, _, _ = temp_img.shape

        except AttributeError:
            print(f"快去截图！{self.prompt}")
            return []

        scale_low = 10  / temp_h
        scale_hig = 100 / temp_h
        scale_rat = 1   / temp_h
        scale = scale_low
        while scale < scale_hig: # 每次递增 1% 遍历缩放大小
            self.search_matched(ori_img, temp_img, scale)
            scale += scale_rat

        return [ (point.x, point.y) \
                for point in sorted(self.matched_points, key=lambda x: x.judge, reverse=True)]