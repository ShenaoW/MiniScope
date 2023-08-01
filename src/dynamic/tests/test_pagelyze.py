from .context import pgc

from pgc import CrawlWXMicroWebView
from pgc.builtins.pagelyze import get_is, get_full_text
from pgc.utils.algorithm.string import lcs

from pathlib import Path
from toml import load

from appium.webdriver import Remote


def test_get_is():
    config_path = Path.cwd() / 'config' / 'crawler' / 'config.toml'
    caps = load('config/crawler/config.toml')['capabilities']
    app = CrawlWXMicroWebView.from_config_file(config_path)
    app.driver = Remote('http://127.0.0.1:4723', caps)

    wxapath = get_is()
    print(wxapath)
    assert wxapath is not None

def test_get_full_text():
    config_path = Path.cwd() / 'config' / 'crawler' / 'config.toml'
    caps = load('config/crawler/config.toml')['capabilities']
    app = CrawlWXMicroWebView.from_config_file(config_path)
    app.driver = Remote('http://127.0.0.1:4723', caps)

    full_text = get_full_text()
    assert len(full_text) != 0