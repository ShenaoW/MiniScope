from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import WebDriverException

from ...utils.confman.pcy import PcyMan
from ...builtins.context import get_crawler
from ...builtins.context.actions import exit_enter
from ...builtins.cv import CVMatcher


class MiniappNativePage:
    def __init__(self, page_source, wxapath):
        self.elem_locations = []
        self.page_source = page_source
        self.wxapath = wxapath
        self.trigger = None

    @property
    def leaves(self):
        """
        获取叶子节点，使用属性函数的原因是满足动态更新需求

        :return: 叶子节点列表
        """
        try:
            test_leaves = get_crawler().driver.find_elements(AppiumBy.XPATH, '//*[count(*) eq 0]')

        except WebDriverException:
            get_crawler().driver = exit_enter()

        for leaf in test_leaves:
            print(leaf.get_attribute('resourceId'))

    def get_key_elements(self):
        """
        获取页面上我们感兴趣元素的坐标，通过 cv 以及 text 方式获取

        :return: [(x, y)]
        """
        pp_prompts = PcyMan().load()

        for some_pp_prompts in pp_prompts:
            for prompt in some_pp_prompts:
                cv_elems = CVMatcher(prompt).get_elements()
                for cv_elem in cv_elems:
                    if cv_elem not in self.elem_locations:
                        self.elem_locations.append(cv_elem)
                        yield [cv_elem]

            for prompt in some_pp_prompts:
                if prompt in self.page_source:
                    txt_elems = get_crawler().driver.find_elements(AppiumBy.XPATH, f'//*[@text="{prompt}"]')
                    txt_elems += get_crawler().driver.find_elements(AppiumBy.XPATH, f'//*[@content-desc="{prompt}"]')
                    for txt_elem in txt_elems:
                        loc = txt_elem.location
                        loc = loc['x'], loc['y']
                        if loc not in self.elem_locations:
                            self.elem_locations.append(loc)
                            yield [loc]
