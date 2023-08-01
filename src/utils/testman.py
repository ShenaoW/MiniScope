import json
import requests
from pathlib import Path
from loguru import logger
from toml import dump, load


class TestMan():
    def __init__(self):
        self._path = Path.cwd() / 'config' / 'test' / 'test.toml'

    def dump(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.50 Safari/537.36',
        }
        rep = requests.post(
            "https://zhishuapi.aldwx.com/Main/action/Dashboard/Homepage/data_list",
            headers=headers,
            data={"size": 50}
        )
        if rep.status_code != 200:
            logger.critical("Miniapp data obtain err!")

        miniapp_list = json.loads(rep.text)["data"]
        miniapp_list = [
            miniapp['name']
            for miniapp in miniapp_list
        ]
        dump({'testObjs': miniapp_list},
            open(self._path, 'w', encoding='utf-8'))

    def load(self):
        return load(open(self._path, 'r', encoding='utf-8'))['testObjs']