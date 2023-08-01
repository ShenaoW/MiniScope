import frida
import time

from pathlib import Path
from typing import Union, List, Dict
from loguru import logger

from ..context import set_hooker


class FridaHooker:
    def __init__(self, script_path: Union[Path, str]):
        self.device = frida.get_usb_device()
        self.script_path = Path(__file__).parent / script_path
        self.recorded_api = []
        set_hooker(self)

    def hook(self, use_module: str, is_show: bool = True, process: str = 'com.tencent.mm:appbrand0', wait_time: int = 0) -> List[Dict]:
        """ HOOK 指定模块的 Android API

        :param: use_module: 需要 hook 的模块
        :return: 返回 hook 的 API 信息 -> List[Dict]
        """
        def on_message(message, payload):
            """ communication with frida

            :param: message: received message from frida
            """
            if message['type'] == 'send':
                data = message['payload']
                if data['type'] == 'notice':
                    time = data['time']
                    action = data['action']
                    messages = data['messages']
                    stacks = data['stacks']
                    arg = data['arg']
                    if is_show:
                        print('\033[1;34m ============================= \033[0m')
                        print(f"API: {action}\nAction: {messages}\n")
                        print("call stack: ")
                        print(stacks)

                    self.recorded_api.append({
                        'time': time,
                        'action': action,
                        'messages': messages,
                        'arg': arg
                    })

                elif data['type'] == 'app_name':
                    get_app_name = data['data']
                    logger.info(get_app_name)
                    my_data = False if get_app_name == process else True
                    script.post({"my_data": my_data})

                elif data['type'] == 'isHooked':
                    nonlocal isHooked
                    isHooked = True
                    script.post({"use_module": use_module})

                elif data['type'] == 'noFoundModule':
                    logger.info(f"输入 {data['data']} 模块错误，请检查")

                elif data['type'] == 'loadModule':
                    if data['data']:
                        logger.info(f"已加载模块{', '.join(data['data'])}")

                    else:
                        logger.warning('无模块加载，请检查')

        isHooked = False
        use_module = {'type': 'use', 'data': use_module}
        try:
            session = self.device.attach(process)
        
        except frida.ProcessNotFoundError:
            logger.critical(f"进程 {process} 不存在，请检查")
            return

        with open(self.script_path, 'r', encoding='utf-8') as fin:
            script_raw = fin.read()

        if wait_time != 0:
            script_raw += f"setTimeout(main, {str(wait_time)}000);\n"

        else:
            script_raw += 'setImmediate(main);\n'

        script = session.create_script(script_raw)
        script.on("message", on_message)
        script.load()
        time.sleep(1)

        wait_time += 1
        time.sleep(wait_time)

        if isHooked:
            logger.info('hook success')

        else:
            logger.critical('hook fail, try delaying hook, adjusting delay time')