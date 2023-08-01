from contextvars import ContextVar


_conf = ContextVar('global_config')
_crawler = ContextVar('public_crawler')
_hooker = ContextVar('public_hooker')

def get_config() -> dict:
    """
    获取全局配置

    不要直接使用config中的 set_config 修改全局配置，
    持久化请直接修改 get_config 并调用 Crawler 对象的 dump_config_file
    :return: 含有全局配置信息的 dict
    """
    try:
        return _conf.get()
    except LookupError:
        raise LookupError('全局配置未初始化，请检查是否未初始化 CrawlWXMicroWebView 对象')

set_config = _conf.set

def get_crawler() -> "CrawlWXMicroWebView":  # FIXME: recursively import
    """
    获取当前爬虫对象
    保证异步测试时的一一对应
    :return: 当前线程的爬虫对象
    """
    try:
        return _crawler.get()
    except LookupError:
        raise LookupError('当前线程爬虫对象未初始化')

set_crawler = _crawler.set

def get_hooker() -> "FridaHooker":
    try:
        return _hooker.get()

    except LookupError:
        raise LookupError('当前线程对象未初始化')

set_hooker = _hooker.set