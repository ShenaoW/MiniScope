import pickle

from time import sleep
from pathlib import Path
from copy import deepcopy
from typing import Optional
from loguru import logger
from toml import loads, dumps
import networkx as nx

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common import ElementNotInteractableException, ElementClickInterceptedException

from .builtins.context import get_config, set_config, set_crawler
from .builtins.context.manager import DriverContextManager
from .builtins.context.actions import is_mainpage
from .builtins.dfs_for_pp import goto_ppage
from .builtins.dfs_for_pages import explore_pages_by_tag, explore_pages_by_click
from .builtins.oblpp import get_page_path_obl, get_pp_by_link
from .builtins.elems import copy, renter
from .builtins.pagelyze import get_full_text


__all__ = ('CrawlWXMicroWebView', '__version__')
__version__ = '0.1.0'


class CrawlWXMicroWebView:
    config_path = Optional[Path]

    def __init__(self, config: dict):
        self.driver = None
        self.config_path = None
        self.explored_pages = []
        self.tarbar = dict()
        self.dynamic_utg = nx.DiGraph()
        set_config(config)
        set_crawler(self)

    @staticmethod
    def from_config_file(config_path: Path) -> "CrawlWXMicroWebView":
        """从指定配置文件初始化 CrawlWXMicroWebView 对象

        :param config_path: 配置文件路径
        :return: CrawlWXMicroWebView 对象
        """
        config_text = loads(config_path.read_text())
        try:
            config_text = loads(config_path.read_text())

        except FileNotFoundError:
            config_text = {}

        config_text = deepcopy(config_text)
        r = CrawlWXMicroWebView(config_text)
        r.config_path = config_path
        return r

    def dump_config_file(self, config_path: Optional[Path] = None):
        """将当前线程上下文配置写回配置文件

        :param config_path: 配置文件路径
        """
        config_text = dumps(get_config())
        if config_path is not None:
            config_path.write_text(config_text, encoding='utf-8')
            return

        elif self.config_path is not None:
            self.config_path.write_text(config_text, encoding='utf-8')
            return

        raise NotImplementedError

    def bootstrap(self):
        """交互式写入配置信息"""
        print(f"PoliGuard-Crawler v{__version__} 启动配置:\n")
        android_device = input(f"\t[1] 安卓设备 ID: ").strip()
        wechat_driver_path = input(f"\t[2] chromedriver 路径 (微信): ").strip()
        local_chrome_path = input(f"\t[2] chromedriver 路径 (本地): ").strip()

        basic_config = {
            "capabilities": {
                'deviceName': android_device,
                'platformName': 'Android',
                'appPackage': 'com.tencent.mm',
                'appActivity': 'com.tencent.mm.ui.LauncherUI',
                'automationName': 'uiautomator2',
                'noReset': True,
                'unicodeKeyboard': True,
                'resetKeyboard': True,
                'chromedriverExecutable': wechat_driver_path,
                'newCommandTimeout': 1200,
            },
            'localChrome': local_chrome_path,
        }
        config = get_config()
        config.update(basic_config)
        self.dump_config_file()

    def swipe_into(self):
        """滑动方式进入小程序

        Hint: 使用该种方法可以保存之前退出时的上下文
        """
        from selenium.common.exceptions import NoSuchElementException
        config_dict = get_config()
        caps = config_dict['capabilities']

        self.driver = Remote('http://127.0.0.1:4723', caps)
        self.driver.implicitly_wait(10)
        app_name = config_dict['appName']
        wind_size = self.driver.get_window_size()
        x = wind_size['width'] * 0.5
        y0 = wind_size['height'] * 0.4
        y1 = wind_size['height'] * 0.9
        self.driver.swipe(x, y0, x, y1)
        sleep(2)
        for elem in self.driver.find_elements(AppiumBy.XPATH, '//*'):
            elem_desc = elem.get_attribute('content-desc')
            if elem_desc is None:
                continue

            if elem_desc.replace(',', '') in app_name:
                elem.click()
                break

        else:
            self.driver.keyevent(4)
            sleep(1)
            self.search_into()

    def search_into(self):
        """搜索方式进入小程序

        Hint: 使用该种方法会丢失之前退出时的上下文
        """
        config_dict = get_config()
        caps = config_dict['capabilities']

        self.driver = Remote('http://127.0.0.1:4723', caps)
        self.driver.implicitly_wait(10)

        app_name = config_dict['appName']
        self.driver.find_element(AppiumBy.XPATH, '//*[@content-desc="搜索"]').click()
        self.driver.find_element(AppiumBy.XPATH, '//android.widget.Button[@text="小程序"]').click()
        sleep(3)

        self.reconnect_driver()
        search_box = self.driver.find_element(AppiumBy.XPATH, '//*[@text="搜索小程序"]')
        search_box.send_keys(app_name)
        self.driver.find_element(AppiumBy.XPATH, '//*[@text="搜索"]').click()
        sleep(3)

        search_results = self.driver.find_elements(AppiumBy.XPATH, '//android.widget.Button')
        search_results[0].click()

    def explore_pp(self) -> str:
        if goto_ppage() is not None:
            logger.success('Privacy Policy Found!')
            pp_path_obl = get_page_path_obl(copy.wxapath())
            if pp_path_obl is not None:
                return get_pp_by_link(pp_path_obl)

            else:
                return get_full_text()

    def explore_pages(self, app_infos: dict):
        config_dict = get_config()
        config_dict.update(app_infos)
        self.dump_config_file()
        renter.click()
        sleep(5)
        tarbars = [[(ele.rect['x'] + ele.rect['width']/2, ele.rect['y'] + ele.rect['height']/2)]
                   for ele in self.driver.find_elements(AppiumBy.XPATH, "//*[@clickable='true']")
                   if ele.location['y'] > self.driver.get_window_size()['height'] * 0.9]
        for tarbar in tarbars:
            if is_mainpage():
                self.swipe_into()
            self.reconnect_driver()
            self.driver.tap(tarbar)
            # explore_pages_by_tag(tarbar)
            explore_pages_by_click(tarbar)

    def utg_add_edge(self, frm, to, label=None):
        if to not in self.dynamic_utg:
            self.dynamic_utg.add_node(to)

        if not self.dynamic_utg.has_edge(frm, to):
            self.dynamic_utg.add_edge(frm, to, label=label)

    def reconnect_driver(self):
        try:
            self.driver.quit()
        except:
            pass
        config_dict = get_config()
        caps = config_dict['capabilities']

        self.driver = Remote('http://127.0.0.1:4723', caps)
        self.driver.implicitly_wait(10)
    
    def get_url(self, detail=True):
        if detail:
            return copy.wxapath()
        else:
            current_url = None
            try_time = 0
            while current_url is None:
                try_time += 1
                if try_time > 3:
                    current_url = self.get_url().split(".")[0]
                try:
                    current_url = self.driver.find_element(AppiumBy.XPATH, '/html/body').get_attribute('is').split(".")[0]
                except:
                    self.reconnect_driver()  
                    DriverContextManager().switch_context_to('webview')              
            return current_url
    
    def click_handler(self, element_xpath, mode='webview', depth=0):
        # DriverContextManager().switch_context_to(mode)
        if depth > 3:
            return False
        try:
            element = self.driver.find_element(AppiumBy.XPATH, element_xpath)

        except:
            logger.warning("Page Virtual DOM change detected.")
            return False

        try:
            element.click()

        except ElementClickInterceptedException:
            logger.error("Elememnt click event is intercepted. Handling...")
            DriverContextManager().switch_context_to('native')
            screen_size = self.driver.get_window_size()
            self.driver.tap([(screen_size['width']/2, screen_size['height']/2)]) # 6
            return self.click_handler(element_xpath, depth+1)

        except ElementNotInteractableException:
            return False

        return True
    
    def add_tarbar(self, tarbar, tarbar_posi):
        self.tarbar[tarbar] = tarbar_posi

    def load(self, path=Path.cwd() / "data" / "data_runtime" / "DynamicAnalyzer.pkl"):
        with open(path, 'rb') as f:
            data = pickle.load(f)
        self.dynamic_utg = data['dynamic_utg']
        self.tarbar = data['tarbar']

    def save(self, path=None):
        if path is None:
            path = Path.cwd() / "data" / "data_runtime"
        data = {
            'dynamic_utg': self.dynamic_utg,
            'tarbar': self.tarbar
        }
        with open( path / "DynamicAnalyzer.pkl", 'wb') as f:
            pickle.dump(data, f)

    def __del__(self):
        self.driver.quit()
