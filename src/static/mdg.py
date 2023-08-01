# coding: utf8

"""
    Definition of Class
    - Node
    - FuncNode
    - PageNode
    - UTG(miniapp)
    - FCG(page)
    - MDG(miniapp)
"""

import os
import pprint
import graphviz
import pydotplus
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
from loguru import logger
import config as config
from miniapp import MiniApp, Page
from bs4 import Tag
from pdg_js.js_operators import get_node_computed_value
import warnings

# 忽略 DeprecationWarning
warnings.filterwarnings("ignore", category=DeprecationWarning)


class UTG():
    def __init__(self, miniapp: MiniApp):
        self.miniapp = miniapp
        self.page_navigators = {}
        self.utg = self.produce_utg()

    def produce_utg(self):
        graph = nx.DiGraph()
        for tabBar in self.miniapp.tabBars.keys():
            graph.add_edge('MiniApp', str(tabBar))
        for page in self.miniapp.pages.keys():
            for navigator in self.miniapp.pages[page].navigator['UIElement']:
                if navigator.target == 'self':
                    if '..' in navigator.url:
                        url = os.path.abspath(os.path.join(str(page), navigator.url))
                    else:
                        url = navigator.url
                    graph.add_edge(str(page), str(url))
                    self.page_navigators[(str(page), str(navigator.url))] = navigator
            for navigator in self.miniapp.pages[page].navigator['NavigateAPI']:
                if navigator.name in ('wx.switchTab', 'wx.reLaunch', 'wx.redirectTo', 'wx.navigateTo'):
                    if '..' in navigator.target:
                        target = os.path.abspath(os.path.join(str(page), navigator.target))
                    else:
                        target = navigator.target
                    graph.add_edge(str(page), str(target))
                    self.page_navigators[(str(page), str(navigator.target))] = navigator
        return graph

    def get_utg_dict(self):
        graph:nx.DiGraph = self.utg
        utg_dict = {}
        for source in graph.adjacency():
            utg_dict[source[0]] = list(source[1].keys())
        return utg_dict
        
    def draw_utg(self, save_path=config.SAVE_PATH_UTG):
        save_path += '/' + self.miniapp.name + '/' + self.miniapp.name
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        pydot_graph = nx.drawing.nx_pydot.to_pydot(self.utg)
        pydot_graph.write_pdf(save_path+'.pdf')


class FCG():
    def __init__(self, page: Page):
        self.page = page
        self.trigger_event = {}
        self.reachable_sensi_api_paths = {}
        self.fcg = self.produce_fcg()
        self.get_all_sensi_apis_trigger_path()

    def produce_fcg(self):
        graph=nx.DiGraph()
        graph.add_node(self.page.page_path)
        # BindingEvent Call Graph
        for binding in self.page.binding_event.keys():
            if len(self.page.binding_event[binding]):
                for event in self.page.binding_event[binding]:
                    if isinstance(event.handler, list):
                        for handler in event.handler:
                            graph.add_edge(self.page.page_path, handler)
                            func = handler
                            self.trigger_event[func] = event
                            call_graph = self.get_all_callee_from_func(func, call_graph={})
                            if call_graph is not None:
                                if func in call_graph.keys():
                                    graph = self.add_callee_edge_to_graph(graph, call_graph, func)
                    elif isinstance(event.handler, str):
                        graph.add_edge(self.page.page_path, event.handler)
                        func = event.handler
                        self.trigger_event[func] = event
                        call_graph = self.get_all_callee_from_func(func, call_graph={})
                        if call_graph is not None:
                            if func in call_graph.keys():
                                graph = self.add_callee_edge_to_graph(graph, call_graph, func)
        # LifecycleEvent Call Graph
        for func in self.page.page_method_nodes.keys():
            if func in (config.LIFECYCLE_CALLBACKS + config.EVENT_HANDLER_CALLBACKS):
                graph.add_edge(self.page.page_path, func)
                call_graph = self.get_all_callee_from_func(func, call_graph={})
                if call_graph is not None:
                    if func in call_graph.keys():
                        graph = self.add_callee_edge_to_graph(graph, call_graph, func)
        return graph
    
    def get_all_callee_from_func(self, func: str, call_graph):
        try:
            func_node = self.page.page_method_nodes[func]
        except:
            logger.warning("FuncNotFoundError: function {} in {} not found!".format(func, self.page.page_path))
            return None
        call_graph = self.traverse_children_to_build_func_call_chain(func, func_node, call_graph)
        return call_graph

    def traverse_children_to_build_func_call_chain(self, func: str, node, call_graph):
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
                        if call_expr_value in self.page.page_method_nodes.keys():
                            if func in call_graph.keys():
                                # avoid self-calling/recursive calling loops with get_fcg_reachable_path
                                if len(self.get_reachable_path_in_fcg_dict(call_graph, call_expr_value, func)) == 0:
                                # if call_expr_value != func and call_expr_value not in call_graph[func]:
                                # if call_expr_value not in call_graph.keys():
                                    call_graph[func].add(call_expr_value)
                                    self.get_all_callee_from_func(call_expr_value, call_graph)
                            else:
                                if len(self.get_reachable_path_in_fcg_dict(call_graph, call_expr_value, func)) == 0:
                                    call_graph[func] = set()    
                                    call_graph[func].add(call_expr_value)
                                    self.get_all_callee_from_func(call_expr_value, call_graph)
                        elif call_expr_value in config.SENSITIVE_API.keys() \
                                            or call_expr_value in config.SINK_API:
                            if func in call_graph.keys():
                                call_graph[func].add(call_expr_value)
                            else:
                                call_graph[func] = set()
                                call_graph[func].add(call_expr_value)
            call_graph = self.traverse_children_to_build_func_call_chain(func, child, call_graph)
        return call_graph
    
    def get_reachable_path_in_fcg_dict(self, call_graph: dict, source, target, path=[]):
        path = path + [source]
        if source == target:
            return [path]
        if source not in call_graph.keys():
            return [] 
        paths = []
        for node in call_graph[source]:
            if node not in path:
                new_paths = self.get_reachable_path_in_fcg_dict(call_graph, node, target, path)
                for p in new_paths:
                    paths.append(p)
        return paths

    def add_callee_edge_to_graph(self, graph: nx.DiGraph, call_graph, func):
        for callee in call_graph[func]:
            if callee in config.SENSITIVE_API.keys() or \
                        callee in config.SINK_API:
                graph.add_edge(func, callee)
            elif callee in call_graph.keys():
                graph.add_edge(func, callee)
                if callee not in call_graph[callee]:  # avoid self-calling loops
                    if func not in call_graph[callee]:  # avoid recursive calling loops
                        graph = self.add_callee_edge_to_graph(graph, call_graph, func=callee)
        return graph

    def get_fcg_dict(self):
        graph:nx.DiGraph = self.fcg
        fcg_dict = {}
        for source in graph.adjacency():
            fcg_dict[source[0]] = list(source[1].keys())
        return fcg_dict

    def draw_fcg(self, save_path=config.SAVE_PATH_FCG):
        save_path += '/' + self.page.miniapp.name + '/' + self.page.page_path
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        pydot_graph = nx.drawing.nx_pydot.to_pydot(self.fcg)
        pydot_graph.write_pdf(save_path+'.pdf')

    def get_all_sensi_apis_trigger_path(self):
        for node in self.fcg.nodes:
            if node in config.SENSITIVE_API.keys():
                paths = list(nx.all_simple_paths(self.fcg, source=self.page.page_path, target=node))
                self.reachable_sensi_api_paths[node] = paths

    def get_sensi_api_trigger_path(self, sensi_api):
        if sensi_api in self.fcg.nodes:
            paths = list(nx.all_simple_paths(self.fcg, source=self.page.page_path, target=sensi_api))
            return paths
        else: 
            return []


class MDG():
    def __init__(self, miniapp: MiniApp):
        self.miniapp = miniapp
    
    def produce_mdgviz(self):
        graph = nx.DiGraph()
        for tabBar in self.miniapp.tabBars.keys():
            graph.add_edge('MiniApp', str(tabBar))
        for page in self.miniapp.pages.keys():
            for navigator in self.miniapp.pages[page].navigator['UIElement']:
                if navigator.target == 'self':
                    graph.add_edge(str(page), str(navigator.url), label=navigator.type)
            for navigator in self.miniapp.pages[page].navigator['NavigateAPI']:
                if navigator.name in ('wx.navigateTo', 'wx.navigateBack'):
                    graph.add_edge(str(page), str(navigator.target), label=navigator.name)
            graph = self.miniapp.pages[page].produce_fcg(graph=graph)
        return graph
    

if __name__ == '__main__':
    miniapp = MiniApp('/root/minidroid/dataset/miniprograms/wx7a3db22c7de906d0')
    # utg = UTG(miniapp)
    # pprint.pprint(utg.get_utg_dict())
    # utg.draw_utg()
    # for page in miniapp.pages.values():
        # fcg = FCG(page)
    fcg = FCG(miniapp.pages["pages/serviceHelp/index"])
    fcg.draw_fcg()
    # print(fcg.reachable_sensi_api_paths)
    # pprint.pprint(fcg.get_fcg_dict())