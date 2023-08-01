import requests
from loguru import logger
from .base import Monitor


class Objection(Monitor):
    def __init__(self, ah='127.0.0.1', ap='6130'):
        super().__init__(
            ['objection', '-g' 'com.tencent.mm', '-ah', ah, '-ap', ap, 'api']
        )

        self.ah = ah
        self.ap = ap
        self.run_task()

    def request_api(self, api):
        req = requests.get(f"http://{self.ah}:{self.ap}/rpc/invoke/{api}")
        if req.status_code != 200:
            logger.warning(f"Objection {api}: {req.status_code}")

        return req.status_code