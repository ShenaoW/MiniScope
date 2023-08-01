import os.path

from appium.webdriver.common.appiumby import AppiumBy
from lxml import etree

from loguru import logger
from ...builtins.context import get_crawler
from ...builtins.context.manager import DriverContextManager


BINDING_EVENTS = [
    # Bubbling Event
    'bindtap',
    'bindlongtap',  # including longtap/longpress event

    # Non-bubbling Event in Specific Compenonts
    'bindgetuserinfo',  # <button open-type='getUserInfo' bindgetuserinfo=handler_fun>
    # <button open-type='getPhoneNumber' bindgetphonenumber=handler_fun>
    'bindgetphonenumber',
    'bindchooseavatar',  # <button open-type='chooseAvatar' bindchooseavatar=handler_fun>
    'bindopensetting',  # <button open-type='openSetting' bindopensetting=handler_fun>
    'bindlaunchapp',  # <button open-type='launchApp' bindlaunchapp=handler_fun>

    'bindsubmit'  # <form binsubmit=handler_fun>
]


class MiniappXwebPage:
    def __init__(self, page_source):
        self.url = None
        self.html_tag = etree.HTML(page_source)
        self.wxapath = self.get_page_url()
        self.navi_tags = []
        self.binding_event = {}
        self.get_navi_tag()
        self.get_bind_info()

    def get_leaves(self, base_xpath):
        if base_xpath:
            base_node = self.html_tag.xpath(base_xpath)[0]
        else:
            base_node = self.html_tag
        leaves_nodes = base_node.xpath("//*[not(*)]")
        for node in leaves_nodes:
            yield self.get_element_xpath(node)

    def get_navi_tag(self):
        navi_tags = self.html_tag.xpath("//navigator") + self.html_tag.xpath("//wx-navigator")
        for tag in navi_tags:
            attrs = tag.attrib
            if "url" in attrs:
                tag_xpath = self.get_element_xpath(tag)
                self.navi_tags.append(tag_xpath)

                url = os.path.normpath(os.path.join(self.wxapath, attrs['url']))
                get_crawler().utg_add_edge(self.wxapath.split("?")[0], url.split("?")[0], tag_xpath)

            else:
                continue

    def get_key_elements(self):
        for tag_xpath in self.navi_tags:
            yield self.get_element_location(tag_xpath)

    def get_bind_info(self):
        for binding in BINDING_EVENTS:
            tags_with_class = self.html_tag.xpath(f'//*[@{binding}]')
            for tag in tags_with_class:
                info = {"tag_xpath": self.get_element_xpath(tag),
                        "bind_type": binding,
                        "bind_func": tag[binding]}

                if binding not in self.binding_event.keys():
                    self.binding_event[binding] = []

                self.binding_event[binding].append(info)

    def get_element_xpath(self, element, source=False):
        root_node = self.html_tag.getroottree()
        element_xpath = root_node.getpath(element)
        if source:
            element_xpath = element_xpath.replace("/html/body", "")

        return element_xpath

    def get_page_url(self) -> str:
        if self.url is None:
            try:
                body_tag = self.html_tag.xpath("//body")[0]
                return body_tag.attrib['is'].replace('.html', "")

            except (IndexError, TypeError):
                logger.error("'/html/body' element not found.")

            except KeyError:
                logger.error("'/html/body' has no 'is' attrs.")

        return self.url

    def get_element_location(self, tag_xpath):
        element = get_crawler().driver.find_element(AppiumBy.XPATH, f"/html/body{tag_xpath}")
        x, y = element.location.values()
        hei, wid = element.size.values()
        return x + wid/2, y+hei/2
        # js_script = f'''
        # const element = document.evaluate("{tag_xpath}", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
        # if (!element) {{
        #     console.error(`找不到xpath为 ${{xpath}} 的元素`);
        #     return null;
        # }}
        # // 获取元素在页面上的位置和尺寸
        # const {{ x, y, width, height }} = element.getBoundingClientRect();
        # // 返回元素坐标
        # return {{ x, y, width, height }};'''
        # while True:
        #     try:
        #         rel = driver.execute_script(js_script)
        #         if rel is not None:
        #             return rel["x"] + rel["width"] / 2, rel["y"] + rel["height"] / 2
        #     except Exception:
        #         get_crawler().exec_api(None, 'webview')

    def levenshtein_distance(self, str1, str2):
        m = len(str1)
        n = len(str2)
        
        # 创建一个二维数组来存储计算结果
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        # 初始化第一行和第一列
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        
        # 计算编辑距离
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if str1[i - 1] == str2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]) + 1
        
        # 返回编辑距离
        return dp[m][n]

    def fuzz_search(self, search_info):
        """fuzzy search for the target element from static page to dynamic page

        :param: search_info: dict
        :return: target x, y in the dynamic page
        """
        target_tag_name = search_info["name"]
        target_tag_attrs = search_info["attrs"]
        target_tag_xpath = search_info["xpath"]
        target_tag_key_attr = search_info["key_attr"]
        target_tags_with_points = {}

        target_tags_with_key_attr = self.html_tag.xpath(
            f"//*[@{target_tag_key_attr}='{target_tag_attrs[target_tag_key_attr]}']"
        )
        if len(target_tags_with_key_attr) == 1:
            return target_tags_with_key_attr[0]

        tags_with_target_tag_name = self.html_tag.xpath(f"//{target_tag_name}") + \
                                    self.html_tag.xpath(f"//wx-{target_tag_name}")
        target_tags = set(target_tags_with_key_attr + tags_with_target_tag_name)

        for tag in target_tags:
            common_keys = tag.attrib.keys() & target_tag_attrs.keys()
            attrs_same = True
            for key in common_keys:
                if tag.attrib[key] != target_tag_attrs[key]:
                    attrs_same = False
                    break
            if attrs_same:
                tag_xpath = self.get_element_xpath(tag)
                target_tags_with_points[tag_xpath] = self.levenshtein_distance(tag_xpath, target_tag_xpath)
        
        element = None
        if len(target_tags_with_points)!=0:
            sorted_d = sorted(target_tags_with_points.items(), key=lambda x: x[1])
            element = sorted_d[0][0]
        return element
            
        
        # return self.get_element_location(self.get_element_xpath(sorted_d[0]))
        # return sorted_d[0]
        return driver_context_manager.exec_api(f"find_element(AppiumBy.XPATH, {sorted_d[0]})", 'webview')
    

        
