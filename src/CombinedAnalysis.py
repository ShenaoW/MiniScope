import pickle
import shutil
import time
import os
import json
import networkx as nx

from shutil import copyfile
from pathlib import Path
from loguru import logger

from dynamic.pgc import CrawlWXMicroWebView
from dynamic.pgc.builtins.elems import renter
from dynamic.pgc.builtins.hooker import FridaHooker
from dynamic.pgc.builtins.context import get_config
from dynamic.pgc.builtins.context.actions import quito_mainpage
from dynamic.pgc.utils.confman import ConfMan
from dynamic.pgc.models.page.xwebpage import MiniappXwebPage
from models.monitor import run_mitm_objection

from dynamic.pgc.utils.confman import ConfMan
from dynamic.pgc import CrawlWXMicroWebView
from dynamic.pgc.builtins.elems import renter
from dynamic.pgc.builtins.context.actions import quito_mainpage
from dynamic.pgc.builtins.context import get_config
from dynamic.pgc.models.page.xwebpage import MiniappXwebPage

from static.src.miniapp import MiniApp
from static.src.utils.wxapkg_decoder import decompile_wxapkg_with_unveilr


class CombinedAnalyzer:
    def __init__(self, ids, pkg_path=None, privacy_policy=None, staticAnalyzed=None, dynamicAnalyzed=None,
                 combinedAnalyzed=None):
        self.triggered_func = None
        if "package" in ids:
            pkg_path = ids["package"]
        if "privacy_policy" in ids:
            privacy_policy = ids["privacy_policy"]
        if "staticAnalyzed" in ids:
            staticAnalyzed = ids["staticAnalyzed"]
        if "dynamicAnalyzed" in ids:
            dynamicAnalyzed = ids["dynamicAnalyzed"]
        if "combinedAnalyzed" in ids:
            combinedAnalyzed = ids["combinedAnalyzed"]

        Path.cwd()

        self.traveled_page = []
        self.startTime = time.localtime()
        self.ids = ids

        self.config_path = ConfMan().config_path
        self.lib_path = Path.cwd()
        self.log_path = self.lib_path / 'log' / f'{time.strftime("%Y-%m-%d", self.startTime)}.log'
        logger.add(str(self.log_path), colorize=True, format="<green>{time}</green> <level>{message}</level>")

        FridaHooker('script.js').hook('network')

        self.dynamicAnalyzer = CrawlWXMicroWebView.from_config_file(self.config_path)
        logger.info('PoliGuard Crawler Object Init Done')
        if not self.lib_path.is_dir() or not self.config_path.exists():
            logger.info('Bootstraping...')
            self.dynamicAnalyzer.bootstrap()

        config_dict = get_config()
        config_dict.update(ids)
        self.dynamicAnalyzer.dump_config_file()

        run_mitm_objection('mitm')

        if privacy_policy is None:
            self.explore(mode='pp')

        else:
            self.dynamicAnalyzer.privacy_policy = privacy_policy

        if dynamicAnalyzed is None:
            self.explore(mode='page')

        else:
            self.dynamicAnalyzer.load(dynamicAnalyzed)

        if pkg_path is None:
            pkg_files = self.obtain_package()
            if not decompile_wxapkg_with_unveilr(Path.cwd() / "data" / "data_runtime"):
                logger.error("Miniapp {}({}) pkg unpack failed!".format(self.ids["appName"], self.ids["appID"]))

        else:
            if os.path.isdir(pkg_path):
                files = os.listdir(pkg_path)
                if ".wxapkg" in files[0]:
                    for file in files:
                        shutil.copy(Path(pkg_path) / file, Path.cwd() / "data" / "data_runtime")

                    if not decompile_wxapkg_with_unveilr(Path.cwd() / "data" / "data_runtime"):
                        logger.error("Miniapp {}({}) pkg unpack failed!".format(self.ids["appName"], self.ids["appID"]))   

                else:
                    try:
                        shutil.copytree(pkg_path, Path.cwd() / "data" / "data_runtime" / os.path.basename(pkg_path))

                    except FileExistsError:
                        pass

            elif os.path.isfile(pkg_path):
                shutil.copy(pkg_path, Path.cwd() / "data" / "data_runtime")
                if not decompile_wxapkg_with_unveilr(Path.cwd() / "data" / "data_runtime"):
                    logger.error("Miniapp {}({}) pkg unpack failed!".format(self.ids["appName"], self.ids["appID"]))

        if staticAnalyzed is None:
            self.staticAnalyzer = MiniApp(Path.cwd() / "data" / "data_runtime" / str(self.ids["appId"]))

        else:
            with open(staticAnalyzed, 'rb') as f:
                self.staticAnalyzer = pickle.load(f)

        if combinedAnalyzed is None:
            self.utg = nx.compose(self.staticAnalyzer.utg_instance, self.dynamicAnalyzer.dynamic_utg)
        else:
            self.load(combinedAnalyzed)

        run_mitm_objection('objection')
        self.trigger_sensi_apis()

    def log_to_file(self, file, level, info):
        log_file = logger.add(file, format=f"")
        eval(f"logger.{level}(info)")
        logger.remove(log_file)

    def trigger_sensi_apis(self):
        miniapp_trigger_at_construct = []
        miniapp_trigger_at_destruct = []

        if "app.js" in self.staticAnalyzer.sensi_apis:
            sensi_apis = self.staticAnalyzer.sensi_apis["app.js"]
            for sensi_api in sensi_apis:
                api_triggers = self.staticAnalyzer.get_sensiAPI_trigger(sensi_api)
                for func, trigger, _ in self.staticAnalyzer.pages['app.js']:
                    if func in ["App.onLaunch", "App.onShow"]:
                        miniapp_trigger_at_construct.append(sensi_api)
                    elif func in ["App.onHide"]:
                        miniapp_trigger_at_destruct.append(sensi_api)

        self.dynamicAnalyzer.search_into()
        data = {'action': 'entry miniapp', 'expect': miniapp_trigger_at_construct}
        self.log_to_file(f"{self.ids['appID']}_click.log", 'info', data)

        for _page, _sensi_apis in self.staticAnalyzer.sensi_apis:
            if _page in self.traveled_page:
                continue
            paths = nx.shortest_path(self.utg, source=self.staticAnalyzer.index_page,
                                     target=_page)
            for path in paths:
                if path in self.staticAnalyzer.sensi_apis and path not in self.traveled_page:
                    self.travel_page(path)
                    self.traveled_page.append(path)
                else:
                    self.navigate_to_page(path)

    def travel_page(self, path):
        """Jump to specific page and trigger sensible apis.
        :param path: Page that jump to and test on.
        :return:
        """
        current_page = self.staticAnalyzer.pages[path]
        sensi_apis_triggers = {}
        trigger_at_construct = []
        trigger_at_destruct = []
        for sensi_api in current_page.sensi_apis:
            api_triggers = current_page.get_sensiAPI_trigger(sensi_api)
            for func, trigger in api_triggers:
                if trigger is None:
                    # Life cycle function
                    if func in ["Page.onLoad", "Page.onShow", "Page.onReady", "App.onLaunch", "App.onShow"]:
                        trigger_at_construct.append(sensi_api)
                    elif func in ["Page.onHide", "Page.onUnload", "App.onHide"]:
                        trigger_at_destruct.append(sensi_api)
                else:
                    # Binding function
                    search_info = {
                        "name": trigger.name,
                        "attrs": {k: v for k, v in trigger.tag.attrib.items() if "{{" not in v},
                        "xpath": trigger.xpath,
                        "key_attr": trigger.trigger
                    }
                    api_triggers[func] = search_info
            sensi_apis_triggers[sensi_api] = api_triggers

        self.navigate_to_page(path)

        data = {'action': f"entry page {path}", 'expect': trigger_at_construct}
        self.log_to_file(f"{self.ids['appID']}_click.log", 'info', data)

        webview_source = self.dynamicAnalyzer.exec_api('page_source', 'webview')
        xwebpage = MiniappXwebPage(webview_source)
        for sensi_api, api_triggers in sensi_apis_triggers.keys():
            for func, trigger in api_triggers:
                if trigger is not None:
                    element = xwebpage.fuzz_search(trigger)
                    element.click()
                    data = {'action': f"click {xwebpage.get_element_xpath(element)} in page {xwebpage.get_page_url()}",
                            'expect': sensi_api}
                    self.log_to_file(f"{self.ids['appID']}_click.log", 'info', data)

        data = {'action': f"leave page {path}", 'expect': trigger_at_destruct}
        self.log_to_file(f"{self.ids['appID']}_click.log", 'info', data)

    def navigate_to_page(self, target_page_url):
        """Guide dynamic analyzer to page 'path'
        :param target_page_url: Path that jump to
        :return:
        """
        current_url = self.dynamicAnalyzer.exec_api("find_element(AppiumBy.XPATH, '/html/body').get_attribute('is')",
                                                    'webview')
        path = self.search_path(current_url, target_page_url)

        if self.staticAnalyzer.index_page in path:
            renter.click()
            path = path[path.index(self.staticAnalyzer.index_page):]

        for expected_url_index in range(len(path)):
            expected_url = path[expected_url_index + 1]
            from_url = path[expected_url_index]
            current_url = from_url
            while current_url != expected_url:
                if current_url != from_url:
                    logger.error(
                        "Page path route error! Expected: {}->{} But: {}->{}".format(from_url, expected_url, from_url,
                                                                                     current_url))

                if nx.has_path(from_url, expected_url):
                    webview_source = self.dynamicAnalyzer.exec_api('page_source', 'webview')
                    xwebpage = MiniappXwebPage(webview_source, current_url)
                    trigger = self.staticAnalyzer.utg_instance.page_navigators.get((current_url, expected_url))
                    if trigger is not None:
                        search_info = {
                            "name": trigger.name,
                            "attrs": {k: v for k, v in trigger.tag.attrib.items() if "{{" not in v},
                            "xpath": trigger.xpath,
                            "key_attr": 'url'
                        }
                    else:
                        trigger_xpath = self.utg[from_url][expected_url]['label']
                        element = xwebpage.lxml.xpath(trigger_xpath)[0]
                        search_info = {
                            "name": element.tag,
                            "attrs": {k: v for k, v in element.attrib.items() if "{{" not in v},
                            "xpath": trigger_xpath,
                            "key_attr": 'url'
                        }
                    element = xwebpage.fuzz_search(search_info)
                    element.click()
                else:
                    logger.error("Path searching error: Miniapp {} can't navigate from {} to {}".format(
                        self.staticAnalyzer.name, current_url, expected_url))
                    return
                current_url = xwebpage.get_page_url()

    def search_path(self, frm, to):
        frm_parent = nx.descendants(self.utg, frm)
        to_parent = nx.descendants(self.utg, to)
        common_parent = list((set(frm_parent) | set(frm)) & (set(to_parent) | set(to)))
        path = [0 for i in range(len(self.staticAnalyzer.pages))]
        for parent in common_parent:
            if nx.shortest_path_length(self.utg, source=parent, target=to) < len(path):
                path = nx.shortest_path(self.utg, source=parent, target=to)

        if path[0] == frm:
            return path

        path = nx.shortest_path(self.utg, source=self.staticAnalyzer.index_page, target=path[0]) + path

        if len(path) < len(self.staticAnalyzer.pages):
            return path
        else:
            return None

    def explore(self, mode):
        logger.info('Start to explore!')
        self.dynamicAnalyzer.swipe_into()
        if mode == 'pp':
            pp = self.dynamicAnalyzer.explore_pp()
            if pp!=None:
                with open(f"src/dynamic/pp/{self.ids['appID']}.txt", 'w+') as fout:
                    fout.write(pp)
            else:
                logger.warning("Miniapp {} has no PrivacyPolicy!".format(self.ids['appID']))
        elif mode == 'page':
            self.dynamicAnalyzer.explore_pages(self.ids)

        logger.info('Explore Done!')
        quito_mainpage()

    def classifyPkgs(self, files, path=""):
        key_word = "/app-config.json".encode()
        main_pkg = None
        sub_pkg = []
        for file in files:
            with open(Path(path) / file, 'rb') as f:
                file_data = f.read()

            if key_word in file_data:
                main_pkg = file

            else:
                sub_pkg.append(file)

        return main_pkg, sub_pkg

    def obtain_package(self):
        rel = []
        with open(Path.cwd() / ".." / "data" / "dataset" / "all.json", 'r') as f:
            pkgs = json.loads(f.read())

        app_id = self.ids["appID"]
        if app_id in pkgs.keys():
            for file in pkgs[app_id]:
                copyfile(
                    Path.cwd() / "data" / "dataset" / file,
                    Path.cwd() / "data" / "data_runtime" / file)

                rel.append(Path.cwd() / "data" / "data_runtime" / file)

        else:
            download_path = Path.cwd() / "data" / "download"
            download_files = os.listdir(Path.cwd() / "data" / "download")
            files = [file for file in download_files if float(file) > self.startTime]
            if not len(files):
                return False

            elif len(files) == 1:
                copyfile(
                    files[0],
                    Path.cwd() / "data" / "data_runtime" / files[0])

                rel.append(Path.cwd() / "data" / "data_runtime" / files[0])

            else:
                main_pkg, sub_pkg = self.classifyPkgs(files, str(download_path))
                if main_pkg is None:
                    logger.error("No main pkg was found!")

                copyfile(
                    download_path / main_pkg,
                    Path.cwd() / "data" / "data_runtime" / "{}.wxapkg".format(app_id))

                rel.append(Path.cwd() / "data" / "data_runtime" / "{}.wxapkg".format(app_id))

                for idx in range(len(sub_pkg)):
                    file_path = Path.cwd() / "data" / "data_runtime" / sub_pkg[idx]
                    copyfile(
                        download_path / sub_pkg[idx],
                        file_path)

                    rel.append(file_path)
        return rel

    def coverage_analyze(self):
        result = {
            'page_coverage': self.page_coverage(),
            'func_coverage': self.func_coverage(),
        }
        return result

    def page_coverage(self):
        all_pages = []
        app_config_keys = {i.lower(): i for i in self.staticAnalyzer.app_config.keys()}
        # Set pages
        if 'pages' in app_config_keys.keys():
            all_pages = all_pages + self.staticAnalyzer.app_config[app_config_keys['pages']]

        if "subpackages" in app_config_keys.keys():
            for sub_pkg in self.staticAnalyzer.app_config[app_config_keys['subpackages']]:
                root_path = sub_pkg["root"]
                for page in sub_pkg["pages"]:
                    page_path = root_path + page
                    all_pages.append(page_path)

        static_explored_pages = set(self.staticAnalyzer.utg_instance.utg.nodes) & set(all_pages)
        dynamic_explored_pages = set(self.dynamicAnalyzer.dynamic_utg.nodes) & set(all_pages)
        explored_pages = set(self.utg) & set(all_pages)
        result = {
            'static': len(static_explored_pages) / len(all_pages),
            'dynamic': len(dynamic_explored_pages) / len(all_pages),
            'combined': len(explored_pages) / len(all_pages),
        }
        return result

    def func_coverage(self):
        explored_func = []
        all_func = []
        coverage = {}
        for page in self.staticAnalyzer.pages:
            page_instance = self.staticAnalyzer.pages[page]
            all_func = all_func + page_instance.js_func.js_call_graph.nodes
            page_triggered_func = []
            for triggered_func in self.triggered_func[page]:
                funcs = nx.descendants(page_instance.js_func.js_call_graph, triggered_func)
                page_triggered_func = page_triggered_func + funcs

            explored_func = explored_func + page_triggered_func
            coverage[page] = len(page_triggered_func) / len(page_instance.js_func.js_call_graph.nodes)

        result = {
            "miniapp": len(explored_func) / len(all_func),
            "pages": coverage
        }
        return result

    def load(self, path=Path.cwd() / "data" / "data_runtime" / "CombinedAnalyzer.pkl"):
        with open(path, "rb") as f:
            self.utg = pickle.load(f)

    def save(self):
        self.staticAnalyzer.save()
        self.nlpAnalyzer.save()
        self.dynamicAnalyzer.save()
        with open(Path.cwd() / "data" / "data_runtime" / "CombinedAnalyzer.pkl", "wb") as f:
            pickle.dump(self.utg, f)

        shutil.copytree(Path.cwd() / "data" / "data_runtime", Path.cwd() / "data" / "data_result" / self.ids["appID"])
