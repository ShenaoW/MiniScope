
from loguru import logger
from time import sleep
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common import ElementNotInteractableException, ElementClickInterceptedException

from .pagelyze import is_pp_wind, is_pp_toast, is_rp_toast, get_full_text
from .context.actions import slideback, is_mainpage
from .elems import copy
from .context import get_crawler, get_config
from ..builtins.elems import renter
from .context.manager import DriverContextManager
from ..models.page.recorder import Snapshot
from ..models.page.xwebpage import MiniappXwebPage


def goback() -> bool:
    """
    直接返回到微信主页，然后依据 call_stack 重新进入点击
    """
    slideback()
    sleep(1)

def explore_pages_by_tag(last_page = None):
    sleep(1)
    driver_context_manager = DriverContextManager()
    driver_context_manager.switch_context_to('webview')
    page_source = get_crawler().driver.page_source
    curr_page = MiniappXwebPage(page_source)

    wxapath_now = curr_page.get_page_url()
    if wxapath_now is None:
        wxapath_now = copy.wxapath().split("?")[0]

    sleep(2)

    if wxapath_now in get_crawler().explored_pages:
        logger.info("Miniapp {} page {} has been explored.".format(get_config()["appName"], wxapath_now))
        slideback()
        return
    
    wxapath_pre = None
    
    if isinstance(last_page, list):
        get_crawler().add_tarbar(wxapath_now, last_page[0])
        get_crawler().utg_add_edge('MiniApp', wxapath_now, last_page[0])
        
    elif isinstance(last_page, MiniappXwebPage):
        wxapath_pre = last_page.get_page_url()

    if wxapath_pre == wxapath_now:
        # TODO page is stuck(remain blank empty or toast)
        return
    elif isinstance(last_page, MiniappXwebPage):
        get_crawler().utg_add_edge(wxapath_pre, wxapath_now, last_page.trigger)

    Snapshot.set_snapshot_path(wxapath_now)
    Snapshot.take()

    for element_xpath in curr_page.navi_tags:
        driver_context_manager.switch_context_to('webview')
        # element = driver_context_manager.exec_api(f"", "webview")
        element = get_crawler().driver.find_element(AppiumBy.XPATH, element_xpath)
        try:
            curr_page.trigger = element_xpath
            element.click()

        except ElementNotInteractableException:
            logger.warning(f"{element.tag} is not interactable. Handling...")
            done = False
            parent = curr_page.html_tag.xpath(element_xpath)[0].getparent().getparent()
            while curr_page.get_element_xpath(parent) != "/html/body":
                if done:
                    break

                children = parent.getchildren()
                for child in children:
                    if done:
                        break
                    try:
                        get_crawler().driver.find_element(AppiumBy.XPATH, curr_page.get_element_xpath(child)).click()
                        get_crawler().driver.find_element(AppiumBy.XPATH, element_xpath).click()
                        done = True
                    except ElementNotInteractableException:
                        continue

                    except Exception:
                        logger.warning(f"Unknown error when click {child.tag}")

                parent = parent.getparent()

        explore_pages_by_tag(curr_page)

    get_crawler().explored_pages.append(wxapath_now)
    if not goback():
        return

def explore_pages_by_click(last_page = None):
    sleep(3)
    try:
        driver_context_manager = DriverContextManager()
        driver_context_manager.switch_context_to('webview')
        page_source = get_crawler().driver.page_source
        curr_page = MiniappXwebPage(page_source)
    except:
        logger.error("Failed to get page source")
        slideback()
        return

    wxapath_now = curr_page.get_page_url()
    if wxapath_now is None:
        wxapath_now = copy.wxapath().split("?")[0]

    sleep(2)


    wxapath_pre = None
    
    if isinstance(last_page, list):
        get_crawler().add_tarbar(wxapath_now, last_page[0])
        get_crawler().utg_add_edge('MiniApp', wxapath_now, last_page[0])
        
    elif isinstance(last_page, MiniappXwebPage):
        wxapath_pre = last_page.get_page_url()

    elif isinstance(last_page, MiniappXwebPage):
        get_crawler().utg_add_edge(wxapath_pre, wxapath_now, last_page.trigger)
    
    if wxapath_pre == wxapath_now:
        # TODO page is stuck(remain blank empty or toast)
        return
    
    if wxapath_now in get_crawler().explored_pages:
        if isinstance(last_page, list):
            logger.warning("Tarbar element is not clicked.")
            renter.click()
            get_crawler().driver.tap(last_page)
            explore_pages_by_click(last_page)
            return 
        else:
            logger.info("Miniapp {} page {} has been explored.".format(get_config()["appName"], wxapath_now))
            slideback()
            return

    Snapshot.set_snapshot_path(wxapath_now)
    Snapshot.take()
    get_crawler().explored_pages.append(wxapath_now)
    if not is_pp_wind():
        for element_xpath in curr_page.get_leaves("/html/body"):
            if is_mainpage():
                return
            driver_context_manager.switch_context_to('webview')
            curr_page.trigger = element_xpath
            # element = driver_context_manager.exec_api(f"", "webview")
            if not get_crawler().click_handler(element_xpath):
                continue
            explore_pages_by_click(curr_page)

    if not goback():
        return