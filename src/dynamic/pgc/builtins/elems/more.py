from selenium.common.exceptions import NoSuchElementException
from appium.webdriver.common.appiumby import AppiumBy

from ..context import get_crawler


def click():
    targ_elem = None
    get_crawler().reconnect_driver()
    
    try:
        targ_elem = get_crawler().driver.find_element(
            AppiumBy.XPATH, '(//android.widget.ImageButton[@content-desc="更多"])[1]')

    except NoSuchElementException:
        clickables = get_crawler().driver.find_elements(
            AppiumBy.XPATH, '//*[@clickable="true"]')

        for clickable in clickables:
            if clickable.get_attribute("content-desc") == "更多":
                targ_elem = clickable
                break

    assert targ_elem, "Can't find `更多` element."
    targ_elem.click()