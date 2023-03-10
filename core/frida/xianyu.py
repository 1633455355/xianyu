import json
from urllib.parse import quote_plus

from loguru import logger
import frida


# 生成随机字符串
def random_str(random_length=8):
    """
    生成一个指定长度的随机字符串，其中
    string.digits=0123456789
    string.ascii_letters=abcdefghigklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ
    """
    import random
    import string
    str_list = [random.choice(string.digits + string.ascii_letters) for i in range(random_length)]
    return ''.join(str_list)


class XianYu:
    def __init__(self, file_path):
        self.sign = None
        self.app_name = "闲鱼"
        self.file_path = file_path
        self.hook_code = self.read_js()
        self.process = frida.get_remote_device().attach(self.app_name)
        self.script = self.process.create_script(self.hook_code)
        self.script.on("message", self.on_message)
        self.script.load()

    def read_js(self):
        """
        读取js文件
        :return:
        """
        with open(self.file_path, encoding='utf-8') as f:
            hook_code = f.read()
        return hook_code

    def get_sign(self, data: str, headers: dict, t):
        """
        获取sign
        :param headers: 请求头
        :param data: 请求参数
        :param t: 时间戳
        :return:
        """
        sign_params = {
            'deviceId': headers['x-devid'],
            'appKey': headers['x-appkey'],
            'x-features': headers['x-features'],
            'api': 'mtop.taobao.idlemtopsearch.search',
            'v': '1.0',
            'utdid': headers['x-utdid'],
            'sid': headers.get('x-sid'),
            'ttid': headers['x-ttid'],
            'extdata': headers['x-extdata'],
            'uid': headers.get('x-uid'),
            'data': data,
            'lat': '0',
            'lng': '0',
            't': t
        }
        self.script.exports.getSign(json.dumps(sign_params))
        return self.sign

    def on_message(self, message, data):
        """
        获取sign
        :param message:
        :param data:
        :return:
        """
        sign = message.get("payload").get("sign")
        self.sign = dict([x.split('=', 1) for x in sign[1:-1].split(", ")])
        for k, v in self.sign.items():
            self.sign[k] = quote_plus(v)
        logger.info(self.sign)

