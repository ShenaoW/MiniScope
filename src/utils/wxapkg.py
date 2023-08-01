import struct
import os
import sys
from loguru import logger


class Wxapkg:
    def __init__(self, pkg_path,) -> None:
        self.pkg_path = pkg_path

    def get_wxapkg_file_list(self):
        with open(self.pkg_path, 'rb') as pkg:
            first_mark = struct.unpack('B', pkg.read(1))[0]
            _ = struct.unpack('>L', pkg.read(4))[0]
            _ = struct.unpack('>L', pkg.read(4))[0]
            _ = struct.unpack('>L', pkg.read(4))[0]
            last_mark = struct.unpack('B', pkg.read(1))[0]

        if first_mark != 0xBE or last_mark != 0xED:
            logger.critical(f"{self.pkg_path} is not a wxapkg")

        file_count = struct.unpack('>L', pkg.read(4))[0]

        file_list = []
        for _ in range(file_count):
            data = {}
            data["nameLen"] = struct.unpack('>L', pkg.read(4))[0]
            data["name"] = pkg.read(data["nameLen"]).decode()
            data["offset"] = struct.unpack('>L', pkg.read(4))[0]
            data["size"] = struct.unpack('>L', pkg.read(4))[0]
            file_list.append(data)

        return file_list

    def unpack(self, file_name):
        with open(self.pkg_path, 'rb') as pkg:
            file_data = None
            for data in self.file_list:
                if data["name"] == file_name:
                    file_data = data
                    break

            if file_data is None:
                logger.error("{} has no file {}".format(self.pkg_path, file_name))

            pkg.seek(file_data['offset'])
            file_content = pkg.read(file_data['size'])
            return file_content