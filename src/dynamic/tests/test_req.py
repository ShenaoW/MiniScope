from .context import pgc

from pgc.utils.reqwx import RequestWX

from nose2.tools import params


@params(
    '肯德基+', '幸运咖咖啡', '知识星球',
)
def test_requestwx(args):
    appid = RequestWX('search_weappid', args).dispatcher()
    appname = RequestWX('search_weappname', appid).dispatcher()
    print(f"{appid}: {appname}")
    assert appname == args
    copy_perm = RequestWX('copywxapath', appid).dispatcher()
    assert copy_perm == True