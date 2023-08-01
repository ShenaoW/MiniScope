from .context import pgc

from pgc import CrawlWXMicroWebView
from pgc.models.page.xwebpage import MiniappXwebPage
from pgc.builtins.context.manager import DriverContextManager

from appium.webdriver import Remote

from toml import load
from pathlib import Path
import networkx as nx


def test_get_page_url():
    config_path = Path.cwd() / 'config' / 'crawler' / 'config.toml'
    caps = load('config/crawler/config.toml')['capabilities']
    app = CrawlWXMicroWebView.from_config_file(config_path)
    app.driver = Remote('http://127.0.0.1:4723', caps)
    driver_context_manager = DriverContextManager()
    driver_context_manager.switch_context_to('webview')
    assert app.driver.context == 'WEBVIEW_com.tencent.mm:appbrand0' \
        and ':VISIBLE' in app.driver.title

    page_source = app.driver.page_source

    miniapp_xweb_page = MiniappXwebPage(page_source)
    print(miniapp_xweb_page.get_page_url())
    assert '/' in miniapp_xweb_page.get_page_url()

def test_bind_info():
    config_path = Path.cwd() / 'config' / 'crawler' / 'config.toml'
    caps = load('config/crawler/config.toml')['capabilities']
    app = CrawlWXMicroWebView.from_config_file(config_path)
    app.driver = Remote('http://127.0.0.1:4723', caps)
    driver_context_manager = DriverContextManager()
    driver_context_manager.switch_context_to('webview')
    assert app.driver.context == 'WEBVIEW_com.tencent.mm:appbrand0' \
        and ':VISIBLE' in app.driver.title

    page_source = app.driver.page_source

    miniapp_xweb_page = MiniappXwebPage(page_source)
    miniapp_xweb_page.get_bind_info()
    print(miniapp_xweb_page.binding_event)
    assert miniapp_xweb_page.binding_event is not None

def test_navi_tag():
    config_path = Path.cwd() / 'config' / 'crawler' / 'config.toml'
    caps = load('config/crawler/config.toml')['capabilities']
    app = CrawlWXMicroWebView.from_config_file(config_path)
    app.driver = Remote('http://127.0.0.1:4723', caps)
    driver_context_manager = DriverContextManager()
    driver_context_manager.switch_context_to('webview')
    assert app.driver.context == 'WEBVIEW_com.tencent.mm:appbrand0' \
        and ':VISIBLE' in app.driver.title

    page_source = app.driver.page_source

    miniapp_xweb_page = MiniappXwebPage(page_source)
    miniapp_xweb_page.get_navi_tag()
    print(app.dynamic_utg)
    assert app.dynamic_utg is not None