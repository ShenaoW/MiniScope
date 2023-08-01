from loguru import logger

from appium.webdriver.common.appiumby import AppiumBy

from selenium.common.exceptions import NoSuchElementException, WebDriverException

from ...utils.reqwx import RequestWX
from ...utils.confman.app import AppMan

from . import more
from ..context.actions import exit_enter
from ..context import get_crawler

def wxapath(appid=None) -> str:
    """
    获取当前页面路径

    @param appid: 小程序 appid
    :return: 页面路径字符串
    """
    cnt     = 0
    max_cnt = 3
    if not appid:
        appid = AppMan().get_id()

    if not RequestWX('copywxapath', appid).dispatcher():
        return None

    logger.success(f"申请 {appid} 的页面复制权限成功")
    while cnt < max_cnt:
        cp_elem    = None
        try:
            more.click()
            cp_elem = get_crawler().driver.find_element(AppiumBy.XPATH, '//*[@text="复制页面路径"]')
        except NoSuchElementException:
            logger.error(f"未找到 `复制页面路径` 元素，重新进入小程序")
            renter_elem = get_crawler().driver.find_element(AppiumBy.XPATH, '//*[@text="重新进入\n小程序"]')
            renter_elem.click()
            get_crawler().reconnect_driver()
            cnt += 1
        except:
            get_crawler().reconnect_driver()
        else:
            assert cp_elem, "Can't find `复制页面路径` element."
            cp_elem.click()
            return get_crawler().driver.get_clipboard().decode()

    logger.error(f"复制页面路径失败，重试次数超过 {max_cnt} 次，尝试退出并重新进入小程序")
    _ = exit_enter()
    return wxapath(appid)