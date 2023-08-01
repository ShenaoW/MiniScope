from toml import load
from pathlib import Path
from random import choice

from .. import ConfMan
from ....builtins.context import get_config


class AppMan(ConfMan):
    def __init__(self) -> None:
        super().__init__()
        self._path = Path.cwd() / 'config' / 'token' / 'token.toml'

    def get_token(self):
        tokens = load(self._path)
        return choice(list(tokens.items()))

    def get_id(self):
        config_dict = get_config()
        appid = config_dict['appID']
        return appid

    def get_name(self):
        appName = load(self.config_path)['appName']
        return appName