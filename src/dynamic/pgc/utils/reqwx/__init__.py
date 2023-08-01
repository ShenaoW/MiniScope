from .actions import request_appid_by_appname, request_wxapath, request_appname_by_appid
from .config import get_lucky_boy


class RequestWX:
    DEFAULT_ACTIONS = {
        'copywxapath' : request_wxapath,
        'search_weappid': request_appid_by_appname,
        'search_weappname': request_appname_by_appid,
    }

    DEFAULT_HAEDERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.121 Safari/537.36",
    }

    DEFAULT_DATA = {
        'lang': 'zh_CN',
        'f': 'json',
        'ajax': '1',
    }

    def __init__(self, action:str, arg:str) -> None:
        self.action = action
        self.arg    = arg

    def dispatcher(self):
        lucky_boy = get_lucky_boy()
        cookie = lucky_boy[1]['cookie']
        token  = lucky_boy[1]['token']
        headers = {
            'Cookie': f"{cookie}",
            'Referer': f"https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1&type=77&createType=0&token={token}&lang=zh_CN"
        }
        headers.update(self.DEFAULT_HAEDERS)
        if self.action == 'copywxapath':
            wxid = lucky_boy[1]['wxID']
            data = {
                'appid': self.arg,
                'username': wxid,
                'token': token,
            }
            data.update(self.DEFAULT_DATA)

        elif self.action == 'search_weappid' or self.action == 'search_weappname':
            data = {
                'key'  : f"{self.arg}",
                'token': f"{token}",
            }
            data.update(self.DEFAULT_DATA)

        result = self.DEFAULT_ACTIONS[self.action](headers, data)
        if result == False or result == None:
            return self.dispatcher()  # recursively try again

        return result