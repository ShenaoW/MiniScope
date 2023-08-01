import toml
from lxml import etree
from loguru import logger

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from functools import reduce

from .elems import copy

from ..utils.confman.pcy import PcyMan
from ..utils.algorithm.string import lcs

from ..models.page.recorder import Snapshot

from .context import get_crawler
from .context.actions import exit_enter
from .context.manager import DriverContextManager


def get_full_text() -> str:
    """获取当前页面所有文本

    :return: 当前页面所有文本
    """
    try:
        txt_elems = get_crawler().driver.find_elements(
            AppiumBy.XPATH, "//android.widget.TextView")
        
    except WebDriverException:
        get_crawler().reconnect_driver()
        driver_context_mgr = DriverContextManager()
        driver_context_mgr.switch_context_to('webview')
        texts = etree.HTML(get_crawler().driver.page_source).xpath('//text()')
        full_text = ""
        for text in texts:
            full_text += text.strip()

        driver_context_mgr.switch_context_to('native')
        return full_text

    text = ""
    for ele in txt_elems:
        text += ele.get_attribute('text')

    return text

def obtain_txt_pp() -> str:
    """通过 OCR 获取当前页面的隐私政策，请确保已经进入隐私政策页面

    :return: 当前页面的隐私政策
    """
    width, height = get_crawler().driver.get_window_size().values()
    wxapath = copy.wxapath()

    Snapshot.set_snapshot_path(wxapath.split('?')[0] + '_pp')
    Snapshot.take()
    pcy_txt = Snapshot.get_ocr_result()
    is_end = False
    while not is_end:
        get_crawler().driver.swipe(width*0.5, height*0.8, width*0.5, height*0.3, 1000)
        Snapshot.take()
        text = Snapshot.get_ocr_result()
        ss = lcs(pcy_txt, text)
        if len(ss) / len(text) > 0.8:
            is_end = True

        pcy_txt += text[text.index(ss)+len(ss):]

    return pcy_txt

def is_pp_wind():
    keywords = reduce(lambda x, y : x + y, PcyMan().load())

    text = get_full_text()
    if any([ keyword in text for keyword in keywords ] ) \
        and len(text) > 150 \
        and text.count(r"隐私") >= 3:
        return True

    return False

def is_rp_toast():
    """ request for permission toast """
    try:
        toast_block = get_crawler().driver.find_element(AppiumBy.ID, 'com.tencent.mm:id/ipz')
        agree_btn = get_crawler().driver.find_element(AppiumBy.ID, 'com.tencent.mm:id/iq6')

    except NoSuchElementException:
        return None

    else:
        return agree_btn

def is_pp_toast():
    """判断当前页面是否含有一个隐私政策 toast"""

    txt_view_elems = get_crawler().driver.find_elements(AppiumBy.XPATH, '//android.view.View//android.widget.TextView')
    toast_prompts = toml.load('config/keyword/prompt.toml')['toastPrompts']
    visited_txt_view_elems = [0] * len(txt_view_elems)

    score = 0
    for toast_prompt in toast_prompts:
        for txt_view_elem in txt_view_elems:
            if toast_prompt in txt_view_elem.text and \
                visited_txt_view_elems[txt_view_elems.index(txt_view_elem)] == 0:
                score += 1
                visited_txt_view_elems[txt_view_elems.index(txt_view_elem)] = 1

    if score >= len(toast_prompts) * 0.5:
        return True

    else:
        return False

def get_is():
    """ 在 webview 中获取当前页面的 is 即页面路径"""
    driver_context_manager = DriverContextManager()
    driver_context_manager.switch_context_to('webview')

    driver = driver_context_manager.driver
    body_tag = driver.find_element(AppiumBy.TAG_NAME, 'body')
    return body_tag.get_attribute('is')