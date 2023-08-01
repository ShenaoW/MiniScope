from typing import List
from time import sleep

from .pagelyze import is_pp_wind, is_pp_toast
from .context import get_crawler
from .context.actions import rexplore, slideback, is_mainpage
from .elems import copy

from ..models.page.recorder import Snapshot
from ..models.page.nativepage import MiniappNativePage


MAX_DEPTH = 4


def goback(call_stack:List[MiniappNativePage]) -> bool:
    """直接返回到微信主页，然后依据 call_stack 重新进入点击"""
    slideback()
    call_stack.pop()  # TODO: side effect
    return True

def goto_ppage(call_stack: List[MiniappNativePage] = None, depth=0):
    '''
    @param call_stack: call page stack
    @param depth: recusive depth
    :return: call page stack or None
    '''
    if call_stack is None:
        call_stack = []

    sleep(1)
    if is_mainpage():
        rexplore()

    if depth > MAX_DEPTH:
        return None

    if is_pp_wind():
        return call_stack

    # TODO: if privacy policy is a toast, then click it
    # is_pp_toast()

    wxapath_now = copy.wxapath()
    wxapath_pre = None
    if call_stack:
        wxapath_pre = call_stack[-1].wxapath

    if wxapath_pre == wxapath_now:
        return None

    if wxapath_pre is not None:
        get_crawler().utg_add_edge(wxapath_pre.split("?")[0], wxapath_now.split("?")[0], call_stack[-1].trigger)

    native_page_source = get_crawler().driver.page_source
    curr_native_page = MiniappNativePage(native_page_source, wxapath_now.split("?")[0])
    call_stack.append(curr_native_page)

    Snapshot.set_snapshot_path(wxapath_now.split("?")[0])
    Snapshot.take()
    result = None
    for res_loc in curr_native_page.get_key_elements():
        curr_native_page.trigger = res_loc
        get_crawler().driver.tap(res_loc)
        result = goto_ppage(call_stack, depth + 1)
        if result is not None:
            return result

    if not goback(call_stack):
        return None

    curr_native_page.trigger = None