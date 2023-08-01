# coding: utf8

"""
    Definition of Class
    - UIElement(name, contents, tag)
    - Event(name, contents, tag, trigger, handler)
    - Navigator(name, content, tag, type, target, url, extra_data, bindings)
    - Page(page_path)
    - MiniApp(miniapp_path)
"""

import os
import json
import re
import pprint
from pathlib import Path
from loguru import logger
import config as config
from bs4 import BeautifulSoup, Tag
from pdg_js.build_pdg import get_data_flow
from utils.utils import get_page_expr_node, get_page_method_nodes
from pdg_js.js_operators import get_node_computed_value


class UIElement:
    """
        Definition of UIElement.

        -------
        Properties:
        - name: str =>
            Name of the UIElement, such as button
        - contents: str =>
            Contents of the UIElement
        - tag: Tag
            The UIElement itself, which is stored as a Tag class(BeautifulSoup4)
    """

    def __init__(self, name, contents, tag: Tag):
        self.name = name  # UIElement type name, such as button
        self.contents = contents  # Element contents
        self.tag = tag  # The UI element itself (Class Tag in BeautifulSoup)


class Event(UIElement):
    """
        Definition of Event(Extends from UIElement).

        -------
        Properties:
        - name: str =>
            Name of the UIElement, such as button
        - contents: str =>
            Contents of the UIElement
        - tag: Tag
            The UIElement itself, which is stored as a Tag class(BeautifulSoup4)
        - trigger: str
            Trigger of the event, such as bindtap
        - handler: str
            The corresponding event handler in Logical Layer(js)
    """

    def __init__(self, name, contents, tag, trigger, handler):
        super().__init__(name, contents, tag)
        self.trigger = trigger  # Event trigger action, such as bindtap
        self.handler = handler  # Event handler function


class Navigator(UIElement):
    """
        Definition of Navigator(Extends from UIElement).

        -------
        Properties:
        - name: str =>
            Name of the UIElement(Here is navigator of course)
        - contents: str =>
            Contents of the UIElement
        - tag: Tag
            The UIElement itself, which is stored as a Tag class(BeautifulSoup4)
        - type: str =>
            Type of navigator(navigate/redirect/switchTab/reLaunch/navigateBack)
        - target: str =>
            self(routing between pages) or appid(jumping between miniapps)
        - url: str =>
            Routing/Jumping destination page url
        - extra_data: str =>
            Data transmitted by cross-pages/cross-miniapps communication
        - bindings: dict =>
            Bind success/fail/complete event
    """

    def __init__(self, name, contents, tag, navigate_type='', target='', url='',
                 extra_data='', bindsuccess='', bindfail='', bindcomplete=''):
        super().__init__(name, contents, tag)
        self.type = navigate_type  # navigate/redirect/switchTab/reLaunch/navigateBack
        self.target = target  # target miniprogram(self/miniprogram appid)
        self.url = url  # target page url
        self.extra_data = extra_data  # extradata when navigateToMiniprogram
        self.bindings = {
            'success': bindsuccess,
            'fail': bindfail,
            'complete': bindcomplete
        }


class NavigateAPI:
    """
        Definition of NavigateAPI.

        -------
        Properties:
        - type: str =>
            route(between pages) or jump(between miniapps)
        - name: str =>
            The name of API
        - target: str/dict =>
            page_url(if routing between pages) or {appid:path}(if jumping between miniapps)
        - extradite: str =>
            Data transmitted by cross-pages/cross-miniapps communication
        - bindings: dict =>
            Bind success/fail/complete event
    """

    def __init__(self, navigate_type, name, target=None, extra_data='',
                 bindsuccess=None, bindfail=None, bindcomplete=None):
        self.type = navigate_type  # route/jump
        '''
            route: wx.navigateTo/redirectTo/switchTab/reLaunch/navigateBack
            jump: wx.navigateToMiniprogram/navigateBackMiniprogram/exitMiniprogram
        '''
        self.name = name
        self.target = target  # target page_url/appid
        self.extra_data = extra_data  # extra_data when jump
        self.bindings = {
            'success': bindsuccess,
            'fail': bindfail,
            'complete': bindcomplete
        }


class Page:
    """
        Definition of Page

        -------
        Properties:
        - page_path: str =>
            Relative page path
        - abs_page_path: str =>
            Absolute page path
        - miniapp: MiniApp =>
            The original miniapp to which the page belongs
        - pdg_node: Node =>
            Head node of the PDG of page.js
        - page_expr_node: Node =>
            Node of Page() in the PDG of page.js
        - page_method_nodes: dict =>
            A dict of {page_method_name : page_method_node}
        - wxml_soup: Soup =>
            Soup instance of page.wxml
        - binding_event: dict =>
            Store Event(extends from UIElement) which triggers binding from Render Layer(wxml) to Logical Layer(js)
        - navigator: dict =>
            Store Navigator(extends from UIElement) or NavigateAPI to build UI State Transition Graph
        - sensi_apis: dict =>
            A dict of {sensi_api : page_method_node}
    """

    def __init__(self, page_path, miniapp):
        self.page_path = page_path
        self.abs_page_path = os.path.join(miniapp.miniapp_path, page_path)
        self.miniapp = miniapp
        # Get pdg node
        if os.path.exists(self.abs_page_path + '.js'):
            self.pdg_node = get_data_flow(input_file=self.abs_page_path + '.js', benchmarks={})
        elif os.path.exists(self.abs_page_path + '.ts'):
            self.pdg_node = get_data_flow(input_file=self.abs_page_path + '.ts', benchmarks={})
        else:
            self.pdg_node = None
        # Get page expression node
        if self.pdg_node is not None:
            self.page_expr_node = get_page_expr_node(self.pdg_node)
        else: self.page_expr_node = None
        # Get page method nodes
        if self.page_expr_node is not None:
            self.page_method_nodes = get_page_method_nodes(self.page_expr_node)
        else:
            self.page_method_nodes = {}

        self.wxml_soup = None
        self.binding_event = {}
        self.navigator = {
            'UIElement': [],  # Navigator element trigger, such as <navigator url="/page/index/index">切换 Tab</navigator>
            'NavigateAPI': []  # API Trigger, such as wx.navigateTo()
        }
        self.sensi_apis = {}
        self.set_page_sensi_apis()
        if os.path.exists(self.abs_page_path + '.wxml'):
            self.set_wxml_soup(self.abs_page_path)
            if self.wxml_soup is not None:
                self.set_binding_event()
                self.set_navigator()

    def set_wxml_soup(self, page_path):
        try:
            soup = BeautifulSoup(open(page_path + '.wxml', encoding='utf-8'), 'html.parser')
            self.wxml_soup = soup
        except Exception as e:
            logger.error('WxmlNotFoundError: {}'.format(e))

    def set_binding_event(self):
        for binding in config.BINDING_EVENTS:
            for tag in self.wxml_soup.find_all(attrs={binding: True}):
                if len(re.findall(r"\{\{(.+?)\}\}", tag.attrs[binding])):
                    pattern = re.compile(r'\b(' + '|'.join(self.page_method_nodes.keys()) + r')\b')
                    handler = pattern.findall(tag.attrs[binding])
                else:
                    handler = tag.attrs[binding]
                event = Event(name=tag.name, trigger=binding,
                            handler=handler, contents=tag.contents, tag=tag)
                if binding not in self.binding_event.keys():
                    self.binding_event[binding] = []
                self.binding_event[binding].append(event)

    def set_navigator(self):
        self.set_navigator_ui()
        if self.pdg_node is not None:
            self.set_navigator_api(self.pdg_node)

    def set_navigator_ui(self):
        tags = self.wxml_soup.find_all('navigator')
        for tag in tags:
            target = tag['target'] if 'target' in tag.attrs.keys() else 'self'
            navigate_type = tag['open-type'] if 'open-type' in tag.attrs.keys() else 'navigate'
            bindsuccess = tag['bindsuccess'] if 'bindsuccess' in tag.attrs.keys() else None
            bindfail = tag['bindfail'] if 'bindfail' in tag.attrs.keys() else None
            bindcomplete = tag['bindcomplete'] if 'bindcomplete' in tag.attrs.keys() else None

            if target.lower() == 'miniprogram' and navigate_type.lower() in ('navigate', 'navigateBack'):
                extradata = tag['extra-data'] if 'extra-data' in tag.attrs.keys() else None
                if navigate_type.lower() == 'navigate':
                    # <navigator open-type=navigateBack>
                    target = tag['app-id'] if 'app-id' in tag.attrs.keys() else 'miniprogram'
                    url = tag['path'] if 'path' in tag.attrs.keys() else 'index'
                    if isinstance(url, str):
                        url = os.path.normpath(os.path.join(self.page_path, url))

                    self.navigator['UIElement'].append(
                        Navigator(
                            name='navigator', contents=tag.contents, tag=tag,
                            navigate_type=navigate_type, target=target, url=url, extra_data=extradata,
                            bindsuccess=bindsuccess, bindfail=bindfail, bindcomplete=bindcomplete
                        )
                    )
                else:
                    # <navigator open-type=navigateBack>
                    self.navigator['UIElement'].append(
                        Navigator(
                            name='navigator', contents=tag.contents, tag=tag,
                            navigate_type=navigate_type, extra_data=extradata,
                            bindsuccess=bindsuccess, bindfail=bindfail, bindcomplete=bindcomplete
                        )
                    )
            else:
                url = tag['url'] if 'url' in tag.attrs.keys() else None
                if isinstance(url, str):
                    url = os.path.normpath(os.path.join(self.page_path, url))
                self.navigator['UIElement'].append(
                    Navigator(
                        name='navigator', contents=tag.contents, tag=tag,
                        navigate_type=navigate_type, target=target, url=url,
                        bindsuccess=bindsuccess, bindfail=bindfail, bindcomplete=bindcomplete
                    )
                )

    def set_navigator_api(self, node):
        for child in node.children:
            if child.name in ('CallExpression', 'TaggedTemplateExpression'):
                if len(child.children) > 0 and child.children[0].body in ('callee', 'tag'):
                    if child.children[0].name == 'MemberExpression':
                        if get_node_computed_value(child.children[0].children[0]) == 'wx':
                            callee = child.children[0]
                        else:
                            callee = child.children[0].children[1]
                    else:
                        callee = child.children[0]
                    call_expr_value = get_node_computed_value(callee)
                    if isinstance(call_expr_value, str):
                        if call_expr_value in config.NAVIGATE_API:
                            self.jump_api_handler(child, call_expr_value)
                        elif call_expr_value in config.ROUTE_API:
                            self.route_api_handler(child, call_expr_value)
            self.set_navigator_api(child)

    def jump_api_handler(self, child, call_expr_value):
        if call_expr_value == 'wx.navigateToMiniProgram':
            props = {
                'appId': '',
                'path': '',
                'extraData': '',
                'success': None,
                'fail': None,
                'complete': None
            }
            props = self.search_obj_props(obj_exp=child.children[1], props=props)
            if isinstance(props['appId'], list):
                props['appId'] = props['appId'][0]
            self.navigator['NavigateAPI'].append(
                NavigateAPI(
                    navigate_type='jump', name='wx.navigateToMiniProgram', target={props['appId']: props['path']},
                    extra_data=props['extraData'], bindsuccess=props['success'], bindfail=props['fail'],
                    bindcomplete=props['complete']
                )
            )
        elif call_expr_value == 'wx.navigateBackMiniProgram':
            props = {
                'extraData': '',
                'success': None,
                'fail': None,
                'complete': None
            }
            props = self.search_obj_props(obj_exp=child.children[1], props=props)
            self.navigator['NavigateAPI'].append(
                NavigateAPI(
                    navigate_type='jump', name='wx.navigateBackMiniProgram',
                    extra_data=props['extraData'], bindsuccess=props['success'],
                    bindfail=props['fail'], bindcomplete=props['complete']
                )
            )
        else:  # wx.exitMiniProgram
            props = {
                'success': None,
                'fail': None,
                'complete': None
            }
            if len(child.children) >= 2:
                props = self.search_obj_props(obj_exp=child.children[1], props=props)
                self.navigator['NavigateAPI'].append(
                    NavigateAPI(
                        navigate_type='jump', name='wx.exitMiniProgram',
                        bindsuccess=props['success'], bindfail=props['fail'],
                        bindcomplete=props['complete']
                    )
                )

    def route_api_handler(self, child, call_expr_value):
        if call_expr_value in ('wx.switchTab', 'wx.reLaunch', 'wx.redirectTo'):
            props = {
                'url': '',
                'success': None,
                'fail': None,
                'complete': None
            }
            props = self.search_obj_props(obj_exp=child.children[1], props=props)
            if isinstance(props['url'], list):
                props['url'] = props['url'][0]
            if props['url']:
                self.navigator['NavigateAPI'].append(
                    NavigateAPI(
                        navigate_type='route', name=call_expr_value, target=props['url'].split('?')[0],
                        bindsuccess=props['success'], bindfail=props['fail'],
                        bindcomplete=props['complete']
                    )
                )
        # TODO: 对于'wx.navigateTo'的页面间通信, 暂不支持解析EventChannel通信 
        elif call_expr_value == 'wx.navigateTo':
            props = {
                'url': '',
                'success': None,
                'fail': None,
                'complete': None
            }
            props = self.search_obj_props(obj_exp=child.children[1], props=props)
            if isinstance(props['url'], list):
                props['url'] = props['url'][0]
            if props['url']:
                self.navigator['NavigateAPI'].append(
                    NavigateAPI(
                        navigate_type='route', name=call_expr_value, target=props['url'].split('?')[0],
                        bindsuccess=props['success'], bindfail=props['fail'],
                        bindcomplete=props['complete']
                    )
                )
        elif call_expr_value == 'wx.navigateBack':
            props = {
                'delta': '',
                'success': None,
                'fail': None,
                'complete': None
            }
            if len(child.children) > 1:
                props = self.search_obj_props(obj_exp=child.children[1], props=props)
                self.navigator['NavigateAPI'].append(
                    NavigateAPI(
                        navigate_type='route', name=call_expr_value, target=props['delta'],
                        bindsuccess=props['success'], bindfail=props['fail'],
                        bindcomplete=props['complete']
                    )
                )
            else:
                self.navigator['NavigateAPI'].append(
                    NavigateAPI(
                        navigate_type='route', name=call_expr_value, target=1,
                        bindsuccess=None, bindfail=None,
                        bindcomplete=None
                    )
                )

    def search_obj_props(self, obj_exp, props):
        for prop in obj_exp.children:
            if len(prop.children):
                key = get_node_computed_value(prop.children[0])
                if key in props.keys():
                    if key in ('success', 'fail', 'complete'):
                        props[key] = prop.children[1]  # value is FunctionExpression 
                    else:
                        props[key] = get_node_computed_value(prop.children[1])  # value is Literal/ObjectExpression
        return props

    def set_page_sensi_apis(self):
        for page_method in self.page_method_nodes.keys():
            page_method_node = self.page_method_nodes[page_method]
            self.traverse_children_to_find_sensi_apis(page_method, page_method_node)

    def traverse_children_to_find_sensi_apis(self, page_method, node):
        for child in node.children:
            if child.name in ('CallExpression', 'TaggedTemplateExpression'):
                if len(child.children) > 0 and child.children[0].body in ('callee', 'tag'):
                    callee = child.children[0]
                    call_expr_value = get_node_computed_value(callee)
                    if isinstance(call_expr_value, str):
                        if call_expr_value in config.SENSITIVE_API.keys():
                            if call_expr_value in self.sensi_apis.keys():
                                self.sensi_apis[call_expr_value].add(page_method)
                            else:
                                self.sensi_apis[call_expr_value] = set()
                                self.sensi_apis[call_expr_value].add(page_method)
            self.traverse_children_to_find_sensi_apis(page_method, child)


class MiniApp:
    """
        Definition of MiniApp.

        -------
        Properties:
        - miniapp_path: str =>
            Path of the miniapp
        - name: str =>
            Name/AppID of miniapp
        - pdg_node: Node =>
            Head node of the PDG of app.js
        - app_expr_node: Node =>
            Node of App() expression
        - app_method_nodes: list =>
            A list of app_method_node
        - pages: dict =>
            A dict of {page_path : Page instance} parsed from app.json(only main package considered)
        - index_page: str =>
            The index_page_path of the miniapp
        - tabBars: dict =>
            A dict of {tabBar_path : Page instance}
        - sensi_apis: dict =>
            A dict of {page_path : sensi_api}
            For simple scan, the implementation is based on regular matching
    """

    def __init__(self, miniapp_path):
        self.miniapp_path = miniapp_path
        self.name = miniapp_path.split('/')[-1]
        self.pdg_node = get_data_flow(input_file=os.path.join(miniapp_path, 'app.js'), benchmarks={})
        self.app_expr_node = get_page_expr_node(self.pdg_node)  # App() node
        if self.app_expr_node is not None:
            self.app_method_nodes = get_page_method_nodes(self.app_expr_node)
        else:
            self.app_method_nodes = None

        self.pages = {}
        self.index_page = None
        self.tabBars = {}
        self.sensi_apis = {}
        self.set_pages_and_tab_bar(miniapp_path)
        # Case1: Use regular expressions to scan the sensi_api directly in each page 
        # self.find_sensi_api_by_reg_directly(miniapp_path)

        # Case2: Use PDG to find the sensi_api and corresponding page method to which it belongs
        self.set_miniapp_sensi_apis()

    def set_pages_and_tab_bar(self, miniapp_path):
        if os.path.exists(os.path.join(miniapp_path, 'app.json')):
            with open(os.path.join(miniapp_path, 'app.json'), 'r', encoding='utf-8') as fp:
                app_config = json.load(fp)
                app_config_keys = {i.lower(): i for i in app_config.keys()}
                # Set pages
                if 'pages' in app_config_keys.keys():
                    pages = app_config[app_config_keys['pages']]
                    self.index_page = pages[0]
                    for page in pages:
                        self.pages[page] = Page(page, self)
                self.pages['app'] = Page('app', self)
                # Set subpackages
                if "subpackages" in app_config_keys.keys():
                    for sub_pkg in app_config[app_config_keys['subpackages']]:
                        root_path = sub_pkg["root"]
                        for page in sub_pkg["pages"]:
                            page_path = Path(root_path) / page
                            abs_page_dir = Path(self.miniapp_path) / root_path
                            if abs_page_dir.exists():
                                self.pages[str(page_path)] = Page(str(page_path), self)
                            else:
                                logger.warning("SubpackageNotFoundError: lack of subpackage file {}".format(str(abs_page_dir)))
                # Set tabBars
                if app_config.get('tabBar', False):
                    tab_bar_list = app_config['tabBar']['list']
                    for tab_bar in tab_bar_list:
                        self.tabBars[tab_bar['pagePath']] = tab_bar['text']
                else:
                    self.tabBars[self.index_page] = '首页'

    def find_sensi_api_by_reg_directly(self, miniapp_path):
        for page in self.pages.values():
            try:
                with open(os.path.join(miniapp_path, page.page_path + '.js'), 'r', encoding='utf-8') as fp:
                    data = fp.read()
            except FileNotFoundError:
                try:
                    with open(os.path.join(miniapp_path, page.page_path + '.ts'), 'r', encoding='utf-8') as fp:
                        data = fp.read()
                except FileNotFoundError:
                    logger.error('PageNotFoundError: {}'.format(os.path.join(miniapp_path, page.page_path)))
            sensi_api_matched = []
            for sensi_api in config.SENSITIVE_API.keys():
                res = re.search(sensi_api, data)
                if res is not None:
                    sensi_api_matched.append(res.group(0))
            if len(sensi_api_matched):
                self.sensi_apis[page.page_path] = sensi_api_matched
    
    def set_miniapp_sensi_apis(self):
        for page in self.pages.values():
            if len(page.sensi_apis.keys()):
                self.sensi_apis[page.page_path] = page.sensi_apis


if __name__ == "__main__":
    app = MiniApp('/root/minidroid/dataset/miniprograms/wxa79672adcfb8788e')
    pprint.pprint(app.sensi_apis)