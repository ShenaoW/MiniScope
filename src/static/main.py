import os
import json
import pprint
from pathlib import Path
from loguru import logger
from bs4 import BeautifulSoup
import multiprocessing as mp
import utils.utils as utils
from utils.wxapkg_decoder import decompile_wxapkg_with_wxUnpacker
from strategy.violation_checker import ViolationChecker
from miniapp import MiniApp, Page
from mdg import UTG, FCG
from analyzer import ConsistencyAnalyzer


def handle_wxapkgs(wxapkgs):
    """
        Decode wxapkgs in the wxapkgs list.

        -------
        Parameters:
        - wxapkgs: list
            A list of Multi-wxapkgs directory.

        -------
        Return: None
    """
    logger.add('src/log/dec_wxapkgs.log')
    wxapkg_paths = wxapkgs
    for wxapkg_path in wxapkg_paths:
        output_path = 'dataset/miniprograms-11w/'+wxapkg_path.split('/')[-1].replace('.wxapkg', '')
        if os.path.exists(output_path):
            logger.info('Decompile Success: {}'.format(output_path))
        else:
            decompile_wxapkg_with_wxUnpacker(wxapkg_path)
            # decompile_wxapkg_with_unveilr(wxapkg_path, output_path)

def check_compliance_violations():
    logger.add('src/log/comp_vios.log')
    with open('dataset/dataset.json', 'r', encoding='utf-8') as fp:
        miniapp_paths = json.load(fp)
    for miniapp_path in miniapp_paths:
        logger.info('[Start] Static analysis of {}'.format(miniapp_path))
        try:
            miniapp = MiniApp(miniapp_path=miniapp_path)
            checker = ViolationChecker(miniapp=miniapp)
            if checker.blanket_reqs is not None or checker.req_before_use is not None \
                    or checker.compulsory_reqs is not None:
                violations = {
                    'req_before_use': checker.req_before_use,
                    'blanket_reqs': checker.blanket_reqs,
                    'compulsory_req': checker.compulsory_reqs
                }
                with open(miniapp.miniapp_path.replace('miniprograms', 'comp_vios') + '.json', 'w') as fp:
                    json.dump(violations, fp, indent=4)
                logger.critical('[ViolationsFound] Compliance violations found at {}'.format(miniapp_path))
            logger.info('[Finish] Static Analysis finished')
        except Exception as e:
            logger.error(e)

def check_sensi_apis():
    sensi_apis_json = {}
    logger.add('src/log/sensi_apis.log')
    with open('dataset/dataset.json', 'r', encoding='utf-8') as fp:
        miniapp_paths = json.load(fp)
    for miniapp_path in miniapp_paths:
        logger.info('[Start] Static analysis of {}'.format(miniapp_path))
        try:
            miniapp = MiniApp(miniapp_path=miniapp_path)
            sensi_apis_json[miniapp_path] = miniapp.sensi_apis
            with open(miniapp.miniapp_path.replace('miniprograms', 'sensi_apis') + '.json', 'w') as fp:
                json.dump(miniapp.sensi_apis, fp, indent=4)
            logger.info('[Finish] Static Analysis finished')
        except Exception as e:
            logger.error(e)
    with open('dataset/sensi_apis.json', 'w') as fp:
        json.dump(sensi_apis_json, fp, indent=4)

def get_sensi_page_text():
    result_json = {}
    with open('dataset/sensi_apis_result.json', 'r', encoding='utf-8') as fp:
        json_data = json.load(fp)
    for miniapp_key in json_data.keys():
        sensi_api_dict = {}
        for sensi_api in json_data[miniapp_key].keys():
            page_dict = {}
            for page in json_data[miniapp_key][sensi_api]:
                soup = BeautifulSoup(open(page + '.wxml'), 'html.parser')
                page_dict[page] = soup.text
            sensi_api_dict[sensi_api] = page_dict
        result_json[miniapp_key] = sensi_api_dict
    with open('./dataset/sensi_page_text.json', 'w') as fp:
        json.dump(result_json, fp, indent=4)

def draw_utg():
    logger.add('src/log/utg.log')
    with open('dataset/dataset.json', 'r', encoding='utf-8') as fp:
        miniapp_paths = json.load(fp)
    for miniapp_path in miniapp_paths:
        logger.info('[Start] Static analysis of {}'.format(miniapp_path))
        try:
            miniapp = MiniApp(miniapp_path=miniapp_path)
            miniapp.draw_utg()
        except Exception as e:
            logger.error(e)

def draw_fcg():
    logger.add('src/log/fcg.log')
    with open('dataset/dataset.json', 'r', encoding='utf-8') as fp:
        miniapp_paths = json.load(fp)
    for miniapp_path in miniapp_paths:
        logger.info('[Start] Static analysis of {}'.format(miniapp_path))
        try:
            miniapp = MiniApp(miniapp_path=miniapp_path)
            for page in miniapp.pages.values():
                page.draw_fcg()
        except Exception as e:
            logger.error(e)

def consistency_analysis():
    logger.add('src/log/consistency_analysis.log')
    with open('dataset/dataset.json', 'r', encoding='utf-8') as fp:
        miniapp_paths = json.load(fp)
    for miniapp_path in miniapp_paths:
        try:
            miniapp_name = miniapp_path.split('/')[-1]
            pp_path = 'dataset/privacy_policy/'+miniapp_name+'.json'
            result_path = 'result/consistency_analysis/'+miniapp_name+'.json'
            if os.path.exists(pp_path):
                with open(str(pp_path), 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                if data['privacy_detail_list']['item']:
                    miniapp = MiniApp(miniapp_path)
                    analyzer = ConsistencyAnalyzer(miniapp, Path(pp_path))
                    redundant_scopes, missing_scopes = analyzer.consistency_analysis()
                    if redundant_scopes is not None:
                        if len(redundant_scopes) or len(missing_scopes):
                            data = {
                                'redundant_scopes': redundant_scopes,
                                'missing_scopes': missing_scopes
                            }
                            with open(result_path, 'w', encoding='utf-8') as fp:
                                json.dump(data, fp, ensure_ascii=False)
                            logger.info('[InconsistencyExists]{}'.format(miniapp_name))
                        else:
                            logger.info('[PerfectConsistency]{}'.format(miniapp_name))
                else:
                    logger.info('[PPEmpty]{}'.format(miniapp_name))
            else:
                    logger.info('[PPEmpty]{}'.format(miniapp_name))
        except Exception as e:
            logger.error('[Error]{}{}'.format(miniapp_name, e))

def multi_scanner(miniapp_paths):
    for miniapp_path in miniapp_paths:
        try:
            miniapp_name = miniapp_path.split('/')[-1]
            result_path = 'result/sensi_apis/'+miniapp_name+'.json'
            miniapp = MiniApp(miniapp_path)
            sensi_apis = miniapp.sensi_apis
            for page in sensi_apis.keys():
                fcg = FCG(miniapp.pages[page])
                for sensi_api in sensi_apis[page].keys():
                    sensi_path = fcg.get_sensi_api_trigger_path(sensi_api)
                    if len(sensi_path):
                        sensi_apis[page][sensi_api] = sensi_path
                    else:
                        sensi_apis[page][sensi_api] = None
            # pprint.pprint(sensi_apis)
            if len(sensi_apis):
                with open(result_path, 'w+', encoding='utf-8') as fp:
                    json.dump(sensi_apis, fp, ensure_ascii=False, indent=2)
            logger.info('[Finished] {}'.format(miniapp_name))
        except Exception as e:
            logger.error('[Error] {} {}'.format(miniapp_name, e))
        

if __name__ == '__main__':
    # Decode wxapkgs with multiprocess
    # with open('dataset/wxapkgs-11w.json', 'r') as fp:
    #     package_names = json.load(fp)
    # processes = 128
    # batch_size = (len(package_names) + processes - 1) // processes
    # batched_package_names = [package_names[i:i+batch_size] for i in range(0, len(package_names), batch_size)]
    # with mp.Pool(processes=processes) as pool:
    #     pool.map(handle_wxapkgs, batched_package_names)


    # Static Analysis with Multiprocess
    logger.add('src/log/sensi_apis.log')
    with open('dataset/dataset.json', 'r') as fp:
        package_names = json.load(fp)
    processes = 128
    batch_size = (len(package_names) + processes - 1) // processes
    batched_package_names = [package_names[i:i+batch_size] for i in range(0, len(package_names), batch_size)]
    with mp.Pool(processes=processes) as pool:
        pool.map(multi_scanner, batched_package_names)


    # Test check_sensi_apis
    # miniapp = MiniApp('/root/minidroid/dataset/miniprograms/wx9c7a3b1a32b7116c')
    # with open(miniapp.miniapp_path.replace('miniprograms', 'sensi_apis')+'.json', 'w') as fp:
    #     json.dump(miniapp.sensi_apis, fp, indent=4)
    # print('success')


    # Test check_compliance_violations
    # miniapp = MiniApp('/root/minidroid/dataset/miniprograms/wx4efaefee87cecc64')
    # checker = ViolationChecker(miniapp=miniapp)
    # if checker.blanket_reqs != None or checker.req_before_use != None \
    #                 or checker.compulsory_reqs != None:
    #             violations = {
    #                 'req_before_use': checker.req_before_use,
    #                 'blanket_reqs': checker.blanket_reqs,
    #                 'compulsory_req': checker.compulsory_reqs
    #             }
    #             with open(miniapp.miniapp_path.replace('miniprograms', 'comp_vios'), 'w') as fp:
    #                 json.dump(violations, fp, indent=4)
    # print('success')
