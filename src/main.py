import os
import json
import argparse

from loguru import logger

from utils.testman import TestMan
from CombinedAnalysis import CombinedAnalyzer

from dynamic.pgc.utils.reqwx import RequestWX


def test_frm_ald():
    testman = TestMan()
    if not testman._path.exists():
        testman.dump()

    with open(testman._path) as f:
        if len(f.read()) == 0:
            testman.dump()
    ids = {}
    logger.info('Ready for crawling miniappps id and name')
    for app_info in testman.load():
        app_name = app_info['name']
        app_id = RequestWX('search_weapp', app_name)
        logger.info(f"App Name: {app_name}, App ID: {app_id}")
        if app_id is not None:
            ids['appName'] = app_name
            ids['appID'] = app_id
            yield ids


def test_frm_configfile(configs):
    for ids in configs:
        if 'appID' not in ids or ids['appID'] is None:
            ids['appID'] = RequestWX('search_weappid', ids['appName']).dispatcher()
        if 'appName' not in ids or ids['appName'] is None:
            ids['appName'] = RequestWX('search_weappname', ids['appID']).dispatcher()
        yield ids


def main():
    args = params()
    if args.config is not None:
        test_list = test_frm_configfile(args.config)
    elif args.AppId is not None or args.AppName is not None:
        ids = {'appID': args.AppId, 'appName': args.AppName}
        test_list = test_frm_configfile([ids])
    else:
        test_list = test_frm_ald()

    for ids in test_list:
        analyzer = CombinedAnalyzer(ids, pkg_path=args.package, privacy_policy=args.privacypolicy,
                                    staticAnalyzed=args.staticAnalyzed, dynamicAnalyzed=args.dynamicAnalyzed,
                                    combinedAnalyzed=args.combinedAnalyzed)
        analyzer.save()


def params():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default=None, type=str, help="AppId\AppName\Pkgs configs")
    # parser.add_argument("-ah", "--appiumHost", default="127.0.0.1", type=str, help="Appium Host")
    # parser.add_argument("-ap", "--appiumPort", default=4723, type=int, help="Appium Port")
    parser.add_argument("-id", "--AppId", default=None, type=str, help="Wechat Miniapp ID")
    parser.add_argument("-n", "--AppName", default=None, type=str, help="Wechat Miniapp Name")
    parser.add_argument("-pkg", "--package", default=None, type=str, help="Package file or folder path")
    parser.add_argument("-pp", "--privacypolicy", default=None, type=str, help="PrivacyPolicy file path")
    parser.add_argument("-sa", "--staticAnalyzed", default=None, type=str, help="Static analyzed file path")
    parser.add_argument("-da", "--dynamicAnalyzed", default=None, type=str, help="Dynamic analyzed file path")
    parser.add_argument("-ca", "--combinedAnalyzed", default=None, type=str, help="Combined analyzed file path")
    parser.add_argument("-da", "--dynamicAnalyzed", default=None, type=str, help="Dynamic analyzed file path")
    parser.add_argument("-ca", "--combinedAnalyzed", default=None, type=str, help="Combined analyzed file path")
    args = parser.parse_args()
    if args.config is not None:
        if os.path.isfile(args.config):
            with open(args.config, 'r') as f:
                configs = json.load(f)
                args.config = configs['config']
        else:
            logger.error("Please specify config file path")
            exit(-1)

    else:
        if args.package is not None and args.AppId is None and args.AppName is None:
            logger.error("Please specify either AppId or AppName")
            exit(-1)

        if args.privacypolicy is not None and os.path.isfile(args.privacypolicy):
            logger.error("Please specify PrivacyPolicy file path")
            exit(-1)

        if args.staticAnalyzed is not None and os.path.isfile(args.staticAnalyzed):
            logger.error("Please specify Static analyzed file path")
            exit(-1)

    return args


if __name__ == '__main__':
    main()