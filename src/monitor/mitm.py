from pathlib import Path
from .base import Monitor


class MitmProxy(Monitor):
    def __init__(self):
        super().__init__(
            ["mitmweb", "-s", Path(__file__).parent / 'addons.py', "--web-host", "0.0.0.0"]
        )

        self.run_task()