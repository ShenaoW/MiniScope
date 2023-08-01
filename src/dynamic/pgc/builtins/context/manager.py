from . import get_config, get_crawler

from loguru import logger
from appium.webdriver.common.appiumby import AppiumBy

from selenium.common import InvalidSessionIdException, JavascriptException
from appium.common.exceptions import NoSuchContextException


class DriverContextManager:
    def __init__(self):
        self.driver_modes = {
            'native': 'NATIVE_APP',
            'webview': 'WEBVIEW_com.tencent.mm:appbrand0'}

    def exec_api(self, api_with_args, mode:str):
        self.switch_context_to(mode)

        if api_with_args:
            try:
                return eval(f"self.driver.{api_with_args}")

            except Exception as e:
                logger.error(e)

    def switch_context_to(self, mode:str):
        try:
            while get_crawler().driver.context != self.driver_modes[mode]:
                try:
                    get_crawler().driver.switch_to.context(self.driver_modes[mode])

                except NoSuchContextException:
                    logger.error(f"{self.driver_modes[mode]} is not in current contexts")

        except InvalidSessionIdException:
            self.reconnect_driver()

        assert get_crawler().driver.context == self.driver_modes[mode], f"Failed to switch to {mode} mode"

        if mode == 'webview':
            # we must switch to visible window
            try:
                windows = get_crawler().driver.window_handles
            
            except :
                get_crawler().reconnect_driver()
                self.switch_context_to('webview')

            else:
                for window in windows:
                    get_crawler().driver.switch_to.window(window)
                    if self.check_visible():
                        break
                
            assert self.check_visible(), "No visible window found"
                
    def check_visible(self):
        js_script = "return document.hidden;"
        try:
            if not get_crawler().driver.execute_script(js_script):
                if get_crawler().driver.find_element(AppiumBy.XPATH, '/html/body').get_attribute('is') is not None:
                    return True
            return False
        except JavascriptException as e:
            logger.warning(f"Failed to execute script!")
            return False