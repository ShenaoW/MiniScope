import requests
import json
import time
import re
import os
import config


class pp_crawler(object):
    def __init__(self):
        self.cookie = {'wap_sid2': config.WAP_SID2}
        self.header = config.HEADER
        self.uin = config.UIN
        self.key = config.KEY

    def js2json(self, data_str):
        def json_replace(match):
            # 获取属性名和属性值
            name = match.group(1)
            value = match.group(2)

            # 将属性名使用双引号包裹起来
            name = '"' + name + '"'

            # 将属性值使用双引号或单引号包裹，但不要使用反斜杠转义引号
            if value.startswith("'") and value[:-1].endswith("'"):
                value = '"' + value[1:-2].replace('"', '\\"') + '"' +','
            if value == ',':
                value = '"",'
            return name + ': ' + value
        # 移除注释和多余的字符
        data_str = re.sub(r'[\s]*//\s+[^\n\r]*[\n\r]+', '\n', data_str)
        data_str = re.sub(r'\.item[^,}]*', '', data_str)
        data_str = re.sub(r'\.list[^,}]*', '', data_str)
        data_str = re.sub(r';\s*$', '', data_str)
        data_str = re.sub(r'\,[\r\n\s]*}', '\n}', data_str)
        # print(data_str)
        # 匹配属性名和属性值，并将属性名用双引号包裹，属性值用单引号或双引号包裹
        pattern = re.compile(r'([^\s:]+)\s*:\s*([^\n\r]+)')

        json_str = pattern.sub(json_replace, data_str)
        # 将字符串转换为JSON对象
        # print(json_str)
        json_obj = json.loads(json_str)
        # print(json_obj)
        return json_obj

    def crawl(self, appid):
        start = 'window.cgiData'
        end = 'window.cgiData.app_nickname'
        params = {'action': 'show'}
        params['appid'] = appid
        params['uin'] = self.uin
        params['key'] = self.key

        #构造url
        url = 'http://mp.weixin.qq.com/wxawap/waprivacyinfo'

        r = requests.get(url, params=params, headers=self.header, cookies=self.cookie)
        # print(r.text)
        if r.status_code == 200:
            index_start = r.text.index(start) + len(start) + 3 # +3是为了去掉等号
            index_end = r.text.index(end)
            privacy = r.text[index_start:index_end]
            if not os.path.exists(config.SAVE_PATH):
                os.makedirs(config.SAVE_PATH)
            with open(file=config.SAVE_PATH + appid + '.json', mode='w', encoding='utf-8') as f:
                privacy_json = self.js2json(privacy)
                json.dump(privacy_json,f,ensure_ascii=False,indent=4)


if __name__=='__main__':
    crawler = pp_crawler()
    appid_id = 'wxe5f52902cf4de896'
    crawler.crawl(appid_id)




