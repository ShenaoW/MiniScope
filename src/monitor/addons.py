import os.path
from loguru import logger
from mitmproxy import ctx, http
from pathlib import Path
import pickle
import json
import re
import sys
from zstandard import decompress


SAVE_DIRECTORY = Path.cwd() / "data" / "download"
SAVE_FLOW_DIRECTORY = Path.cwd() / "data" / "flow"

CHECK_RULES = {
    "name": r"/^[\u4e00-\u9fa5]{2,4}$/",
    "phone": r"\W1[3-9]\d{9}\W",
    "mail": r"/^\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$/",
    "GPS_longtitude": r"/^[\-\+]?(0(\.\d{1,10})?|([1-9](\d)?)(\.\d{1,10})?|1[0-7]\d{1}(\.\d{1,10})?|180\.0{1,10})$/",
    "GPS_latitude": r"/^[\-\+]?((0|([1-8]\d?))(\.\d{1,10})?|90(\.0{1,10})?)$/",
    "file": r"^[\s\S]*\.(pdf|png|jpeg|jpg|docx|xlsx|pjpg|svg|gif|bmp|tiff|tif|raw|webp)$"
}

WX_DOMAIN_NAME = ['3gimg.qq.com', '3glogo.gtimg.com', 'cdnsource.sparta.3g.qq.com', 'cmsimg.qq.com', 'cxhba.qq.com',
                  'cxhbb.qq.com', 'cxhbc.qq.com', 'cxhbd.qq.com', 'd3g.qq.com', 'dl.tcdntip.com', 'dldir1.qq.com',
                  'dldir2.qq.com', 'dldir3.qq.com', 'dlied.myapp.com', 'dlied1.cdntips.com', 'dlied1.myapp.com',
                  'dlied1.qq.com', 'dlied2.qq.com', 'dlied4.myapp.com', 'dlied4.qq.com', 'dlied5.myapp.com',
                  'dlied5.qq.com', 'dlied6.qq.com', 'down-update.qq.com', 'down.qq.com', 'icrash.qq.com',
                  'ifeedback.qq.com', 'mapdown.map.gtimg.com', 'mmbiz.qlogo.cn', 'mmbiz.qpic.cn', 'mmcard.qpic.cn',
                  'mp.weixin.qq.com', 'mp.weixinbridge.com', 'own-update.qq.com', 'pcbrowser.dd.qq.com', 'pr.qq.com',
                  'qpic.cn', 'res.servicewechat.com', 'res2.servicewechat.com', 'resstatic.servicewechat.com',
                  'servicewechat.com', 'shuru.qq.com', 'soft.imtt.qq.com', 'stdl.qq.com', 'sz.preview.qpic.cn',
                  'test.qq.com', 'update1.dlied.qq.com', 'ups-3gimg.qq.com', 'ups-cmsimg.qq.com', 'ups-cxhba.qq.com',
                  'ups-soft.imtt.qq.com', 'ups-stdl.qq.com', 'ups-wximg.qq.com', 'ups-xlongresource.qq.com',
                  'ups-yybimg.qq.com', 'url.cn', 'we.chat', 'we.qq.com', 'wechat.com', 'wechat.org', 'wechatapp.com',
                  'weixin.com', 'weixin.qq.com', 'weixin110.qq.com', 'weops.qq.com', 'wgdl.qq.com', 'wx.qq.com',
                  'wx2.qq.com', 'wximg.qq.com', 'wxtest.qq.com', 'xlongresource.qq.com', 'yybimg.qq.com', '.3g.qq.com',
                  '.api.weixin.qq.com', '.beta.gtimg.com', '.beta.myapp.com', '.cdnsource.sparta.3g.qq.com',
                  '.dl.tcdntip.com', '.dlied1.cdntips.com', '.gtimg.com', '.iot-tencent.com', '.mp.weixin.qq.com',
                  '.open.weixin.qq.com', '.photo.qq.com', '.photo.store.qq.com', '.pr.qq.com', '.preview.qpic.cn',
                  '.qlogo.cn', '.qpic.cn', '.shuru.qq.com', '.store.qq.com', '.support.wechatapp.com',
                  '.sz.preview.qpic.cn', '.test.qq.com', '.url.cn', '.we.qq.com', '.wechat.com', '.wechat.org',
                  '.wechatapp.com', '.weixin.com', '.weixin.qq.com', '.weixin110.qq.com', '.weops.qq.com', '.wx.qq.com',
                  '.wx2.qq.com']


def hexdump(data, length=16):
    filter_mine = ''.join([(len(repr(chr(x))) == 3)
                           and chr(x)
                           or '.'
                           for x in range(256)])

    lines = []
    digits = 4 if isinstance(data, str) else 2
    for c in range(0, len(data), length):
        chars = data[c:c + length]
        hex_str = ' '.join(["%0*x" % (digits, x) for x in chars])
        printable = ''.join([
            "%s" % ((x <= 127 and filter_mine[x]) or '.')
            for x in chars
        ])
        lines.append("%04x  %-*s | %s\n" % (c, 3 * length, hex_str, printable))

    return ''.join(lines)


def sensi_info_match(content):
    if isinstance(content, bytes):
        content = content.decode('latin1')

    result = {}
    for rule in CHECK_RULES:
        matches = re.findall(CHECK_RULES[rule], content)
        if matches:
            result[rule] = matches

    return result


def pck_filter(flow):
    for domain in WX_DOMAIN_NAME:
        if domain in flow.request.host:
            return True
    return False


class Inspector:
    def __init__(self) -> None:
        ...

    def request(self, flow: http.HTTPFlow):
        if pck_filter(flow):
            return

        filename = str(SAVE_FLOW_DIRECTORY / f"{flow.timestamp_start:.22f}")
        if os.path.exists(filename):
            filename = str(SAVE_FLOW_DIRECTORY / f"{(flow.timestamp_start + sys.float_info.epsilon):.22f}")

        # with open(f"{filename}.packet", 'wb+') as f:
        #     pickle.dump(flow, f)
        with open(f"{filename}.json", 'w+', encoding='utf-8') as f:
            data = {
                "url": flow.request.url,
                "method": flow.request.method,
                "headers": str(flow.request.headers),
                "timestamp": flow.timestamp_start,
                "file": f"{filename}.packet",
                "sensi_info": sensi_info_match(flow.request.raw_content)
            }
            json.dump(data, f)

        ctx.log.info(f"floaw_host: {flow.request.host} is  saved to {filename}")

    # def response(self, flow: http.HTTPFlow):
    #     print(flow.response.headers)
    #     print(len(flow.response.raw_content))
    #     print(flow.response)
    #     print(hexdump(flow.response.raw_content))
    #     ctx.log.info(hexdump(flow.response.raw_content))


class HijackWxapkg:
    def __init__(self) -> None:
        pass

    def response(self, flow: http.HTTPFlow):
        req = flow.request
        rep = flow.response
        if 'servicewechat.com/weapp/release_encrypt' not in req.url \
                or rep.status_code != 200:
            return
    
        file_content = rep.get_content()
        if "zstd" in req.url:
            file_content = decompress(file_content)

        elif "wxapkg" in req.url:
            file_content = file_content

        logger.info("mitm: get package {}".format(f"{str(req.timestamp_start)}.wxapkg"))
        with open(SAVE_DIRECTORY / f"{str(req.timestamp_start)}.wxapkg", 'wb') as f:
            f.write(file_content)


addons = [
    Inspector(),
    HijackWxapkg()
]