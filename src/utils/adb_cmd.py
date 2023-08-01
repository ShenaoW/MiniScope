from loguru import logger
import subprocess
import toml
from pathlib import Path


def cmder(executor, command):
    proc = subprocess.Popen(executor, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)

    stdout, stderr = proc.communicate(input=command, timeout=1)
    return stdout.decode('utf-8'), stderr.decode('utf-8')


def als(device_id="863a93c1", path="/data/data/com.tencent.mm/MicroMsg/appbrand/pkg/general/"):
    # TODO get device id and appid from config file
    # device_id = "863a93c1"
    output = cmder(["adb", "-s", device_id, "shell"],
            b"su\nwhoami\n")

    if b'root' not in output:
        logger.warning("Device", device_id, "isn't rooted.")

    output = cmder(["adb", "-s", device_id, "shell"],
            b"su\ncd " + path + b"\nls\n")

    files = output.split("\r\n")
    return files
