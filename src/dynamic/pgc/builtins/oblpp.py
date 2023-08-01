#!/usr/bin/env python
# -*- coding: utf-8 -*-

# get privacy policy by outbound link

from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options  # for Chrome Options
from selenium.common.exceptions import NoSuchElementException

from .context import get_config
from ..utils.algorithm.string import is_http_url


def get_pp_by_link(obl):
    config = get_config()
    local_chrome = config['localChrome']
    pcy = ""

    # 配置
    ch_options = Options()
    ch_options.add_argument("--headless")  # 配置 Chrome 为无头模式

    # 在启动浏览器时加入配置
    driver = webdriver.Chrome(executable_path=local_chrome, chrome_options=ch_options)
    driver.get(obl)
    sleep(1)

    title = driver.title
    sub_titles = [r'摘要', r'简要', r'简明']
    for sub in sub_titles:
        if sub in title:
            soup = BeautifulSoup(driver.page_source, 'lxml')
            hrefs = [ a['href'] for a in soup.find_all('a') ]
            for href in hrefs:
                pcy = get_pp_by_link(href)
                if pcy:
                    return pcy
    
    try:
        iframe_tags = driver.find_elements(By.XPATH, '//iframe')
        iframe_srcs = [ iframe_tag.get_attribute('src') \
                       for iframe_tag in iframe_tags ]
        for iframe_src in iframe_srcs:
            pcy = get_pp_by_link(iframe_src)
            if pcy:
                return pcy

    except NoSuchElementException:
        ...

    tags = driver.find_elements(By.XPATH, "//*")
    for tag in tags:
        pcy += tag.text
    driver.close()
    return pcy

def get_page_path_obl(page_path):
    """获取页面路径中的外链"""
    res = urlparse(page_path)
    queries = parse_qs(res.query)
    for vs in queries.values():
        for v in vs:
            if is_http_url(v):
                return v