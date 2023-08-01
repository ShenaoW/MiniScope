from .context import pgc

from pgc import CrawlWXMicroWebView
from pgc.builtins.cv import CVMatcher
from pgc.models.page.recorder import Snapshot
from pgc.builtins.pagelyze import get_is

from pathlib import Path
from toml import load

from nose2.tools import params

from appium.webdriver import Remote


@params(
    '我',
    '我的',
)
def test_get_elements(prompt):
    config_path = Path.cwd() / 'config' / 'crawler' / 'config.toml'
    caps = load('config/crawler/config.toml')['capabilities']
    app = CrawlWXMicroWebView.from_config_file(config_path)
    app.driver = Remote('http://127.0.0.1:4723', caps)

    wxapath = get_is()
    Snapshot.set_snapshot_path(wxapath)
    Snapshot.take()  # resolve side effect
    cv_matcher = CVMatcher(prompt)
    result = cv_matcher.get_elements()
    print(result)
    assert result is not None