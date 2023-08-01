from time import sleep

from appium.webdriver.common.appiumby import AppiumBy

from . import get_crawler
from ...utils.confman import ConfMan


def is_mainpage():
    return get_crawler().driver.current_activity == ".ui.LauncherUI"

def slideback():
    """
    安卓原生 key event(4) 事件实现回退

    如果返回到微信主页，则重新启动小程序
    """
    get_crawler().driver.keyevent(4)
    if is_mainpage():
        rexplore()

def slideto_mainpage():
    '''从当前页面滑动到微信主页'''
    cnt = 0
    max_try = 8
    while not is_mainpage() and cnt < max_try:
        get_crawler().driver.keyevent(4)
        cnt += 1

    assert is_mainpage(), "无法返回到微信主页"

def quito_mainpage():
    '''返回到微信主页'''
    if is_mainpage():
        return
    quit_elem = get_crawler().driver.find_element(AppiumBy.ID, 'com.tencent.mm:id/fc')
    quit_elem.click()

    sleep(1)
    assert is_mainpage(), "无法返回到微信主页"

def rexplore():
    '''重启微信小程序

    :return: 重新获取的 CrawlWXMicroWebView 对象
    '''
    from ... import CrawlWXMicroWebView
    assert is_mainpage()
    get_crawler().driver.quit()
    config_path = ConfMan().config_path
    r = CrawlWXMicroWebView.from_config_file(config_path)
    r.swipe_into()
    return r.driver

def exit_enter():
    '''差错控制，滑动返回到微信主页，重新启动小程序'''
    quito_mainpage()
    return rexplore()