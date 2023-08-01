from pathlib import Path
from toml import load, dump

from .. import ConfMan


class PcyMan(ConfMan):
    def __init__(self) -> None:
        super().__init__()
        self._pcy_prompts = {
            "direct"  : [ "隐私政策", "隐私条款", "隐私协议", "服务协议", "用户协议", "注册声明", "注册协议",  "隐私", "政策", "条款", "协议"],
            'indirect': ["同意", "授权", "允许", "关于", "设置", "我的", "个人", "我"]
            }
        self._path = Path.cwd() / 'config' / 'keyword' / 'prompt.toml'

    def dump(self):
        dump({'privacyPolicyPrompts':
              {way:
               [ prompt for prompt in prompts ]
               for way, prompts in self._pcy_prompts.items()
              }
             }, open(self._path, 'w', encoding='utf-8'))

    def load(self):
        return [[prompt for prompt in prompts]
                for prompts in load(self._path)['privacyPolicyPrompts'].values()]