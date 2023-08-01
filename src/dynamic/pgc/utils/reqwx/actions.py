import requests
from json import loads
from loguru import logger


def request_appid_by_appname(headers: dict, data: dict) -> str:
    """通过小程序名获取小程序 appid"""
    req = requests.post('https://mp.weixin.qq.com/cgi-bin/operate_appmsg?sub=search_weapp', headers=headers, data=data)
    if req.status_code != 200:
        return None

    result = loads(req.text)
    if result['base_resp']['err_msg'] == 'ok':
        try:
            return result["items"][0]["weapp"]["appid"]

        except IndexError:
            return None

def request_wxapath(headers: dict, data: dict) -> bool:
    """
    申请小程序复制页面路径权限

    @param appid: 小程序 appid
    :return: 是否申请成功
    """
    req = requests.post("https://mp.weixin.qq.com/cgi-bin/copywxapath?action=sendmsg_of_copywxapath", headers=headers, data=data)
    if req.status_code != 200:
        # logger.error(f"request copywxapath failed: {req.status_code}")
        return False

    result = loads(req.text)
    if result['base_resp']['err_msg'] == 'ok':
        return True

    else:
        # logger.error(f"request copywxapath failed: {result['base_resp']['err_msg']}")
        return False

def request_appname_by_appid(headers: dict, data: dict) -> str:
    """通过小程序 appid 获取小程序名"""
    req = requests.post("https://mp.weixin.qq.com/cgi-bin/operate_appmsg?sub=search_weapp", headers=headers, data=data)
    if req.status_code != 200:
        return None

    result = loads(req.text)
    if result['base_resp']['err_msg'] == 'ok':
        try:
            return result["items"][0]["weapp"]["nickname"]

        except IndexError:
            return None