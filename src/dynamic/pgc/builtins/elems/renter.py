from appium.webdriver.common.appiumby import AppiumBy
from time import sleep
from ..context import get_crawler

from . import more


def click():
    more.click()
    sleep(1)
    get_crawler().reconnect_driver()
    renter_elem = get_crawler().driver.find_element(AppiumBy.XPATH, '//*[@text="重新进入\n小程序"]')
    renter_elem.click()
