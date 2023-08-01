from .context import pgc

from pgc import CrawlWXMicroWebView
from pgc.builtins.context.manager import DriverContextManager

from pathlib import Path
from toml import load

from appium.webdriver import Remote

from nose2.tools import params


@params(
    ['webview', 'WEBVIEW_com.tencent.mm:appbrand0'],
    ['native', 'NATIVE_APP'],
)
def test_crawler(args):
    config_path = Path.cwd() / 'config' / 'crawler' / 'config.toml'
    caps = load('config/crawler/config.toml')['capabilities']
    app = CrawlWXMicroWebView.from_config_file(config_path)
    app.driver = Remote('http://127.0.0.1:4723', caps)

    driver_context_manager = DriverContextManager()
    driver_context_manager.switch_context_to(args[0])
    assert app.driver.context == args[1]