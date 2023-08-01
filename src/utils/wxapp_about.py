import js2py
from lxml import etree
import time
import requests

def traverse(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            traverse(value)  # 递归遍历属性值
            if isinstance(value, int) and "time" in key:
                obj[key] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(value))
    elif isinstance(obj, list):
        for item in obj:
            traverse(item)  # 递归遍历列表项        

def get_about_info(appid):
    url = "https://mp.weixin.qq.com/wxawap/waverifyinfo?action=get&appid={}".format(appid)
    rep = requests.get(url)
    if rep.status_code == 200:
        html = rep.content.decode('utf-8')
        node = etree.HTML(html).xpath('/html/body/script[2]')[0]
        js_code = node.text
        rel = js2py.eval_js(js_code)
        info = rel.to_dict()
        traverse(info)
        return info
    return None