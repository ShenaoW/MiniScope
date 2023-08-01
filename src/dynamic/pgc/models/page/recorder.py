import pytesseract

from pathlib import Path
from typing import Optional
from PIL import Image
from loguru import logger

from ...builtins.context import get_crawler
from ...utils.confman.app import AppMan


class Snapshot:
    snapshot_path =  Optional[None]

    @classmethod
    def take(cls):
        """
        即时性截图

        注意：保存截图的路径为始终为调用完一次 screenshot() 方法后的最新截图路径，
             因此尽量保证调用该函数后立刻处理，否则路径会有改变
        """
        try:
            get_crawler().driver.save_screenshot(f"{cls.snapshot_path}")
        except:
            logger.warning("Lack {} screenshot.".format(cls.snapshot_path))

    @classmethod
    def set_snapshot_path(cls, wxapath:str):
        cls.snapshot_path = Path.cwd() / 'snapshot' / f"{AppMan().get_id()}_{wxapath.replace('/', '_')}.png"

    @classmethod
    def get_snapshot_path(cls):
        return cls.snapshot_path

    @classmethod
    def get_ocr_result(cls):
        """
        从截图中获取文字信息
        """
        return pytesseract.image_to_string(Image.open(cls.snapshot_path), lang='chi_sim')