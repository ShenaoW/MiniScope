import time
import subprocess

from loguru import logger


class Monitor:
    def __init__(self, cmd):
        self.proc = None
        self.cmd = cmd
        self.name = type(self).__name__

    def create_task(self):
        self.proc = subprocess.Popen(self.cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

    def run_task(self):
        self.create_task()
        logger.success(f"{self.name} started")
        self.heart_beating()

    def heart_beating(self):
        while True:
            if self.proc.poll() is not None:
                logger.warning(f"{self.name} terminated")
                self.run_task()

            time.sleep(5)
