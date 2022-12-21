import asyncio
import json
import time
from urllib.parse import quote

from aiohttp import TCPConnector
from loguru import logger
from xianyu import XianYu
import aiohttp


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


class Api:
    def __init__(self):
        self.search_url = "https://g-acs.m.goofish.com/gw/mtop.taobao.idlemtopsearch.search/1.0/"
        self.xian_yu = XianYu("rpc.js")
        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "MTOPSDK%2F3.1.1.7+%28Android%3B12%3BXiaomi%3BRedmi+K30+Pro+Zoom+Edition%29",
            "x-pv": '6.3',
            "x-bx-version": '6.5.88',
            "x-ttid": '231200@fleamarket_android_7.8.40',
            "x-app-ver": '7.8.40',
            "x-utdid": random_str(24),
            "x-appkey": "21407387",
            "x-devid": random_str(44),
            "x-features": "27"
        }
        self.proxy = None
        # 不能使用代理
        # 更新一次代理
        # asyncio.run(self.get_proxy())
        # 每隔5分钟更新一次代理
        # threading.Timer(60 * 5, lambda: asyncio.run(self.get_proxy())).start()

    def update_headers(self, data: str):
        t = str(int(time.time()))
        sign = self.xian_yu.get_sign(data, self.headers, t)
        self.headers.update({
            "x-t": t,
            "x-mini-wua": sign.get('x-mini-wua'),
            "x-sgext": sign.get('x-sgext'),
            "x-sign": sign.get('x-sign'),
        })

    async def search(self, keyword):
        data = {'activeSearch': False, 'bizFrom': 'home',
                'clientModifiedCpvNavigatorJson': {'tabList': [], 'fromClient': False}, 'disableHierarchicalSort': 0,
                'forceUseInputKeyword': False, 'forceUseTppRepair': False, 'fromCombo': 'Sort', 'fromFilter': True,
                'fromKits': False, 'fromLeaf': False, 'fromShade': False, 'fromSuggest': False, 'keyword': keyword,
                'pageNumber': 1, 'propValueStr': {'searchFilter': 'publishDays:3'}, 'resultListLastIndex': 0,
                'rowsPerPage': 10, 'searchReqFromActivatePagePart': 'searchButton', 'searchReqFromPage': 'xyHome',
                'searchTabType': 'SEARCH_TAB_MAIN', 'shadeBucketNum': -1, 'sortField': 'create', 'sortValue': 'desc',
                'suggestBucketNum': 37}
        data = json.dumps(data)
        self.update_headers(data)
        data = {
            'data': data,
        }
        # logger.info(f"请求参数: {data}")
        # logger.info(f"请求头: {self.headers}")
        async with aiohttp.ClientSession(
                connector=TCPConnector(ssl=False),
                connector_owner=False,
        ) as session:
            async with session.post(self.search_url, headers=self.headers, data=data, proxy=self.proxy) as resp:
                resp = await resp.json()
                logger.info(f"search请求完成")
                # logger.info(f"search请求结果: {resp}")
                result = self.parser_search_result(resp)
                logger.info(f"search解析结果: {result}")
                return result

    async def get_proxy(self):
        """https://www.hailiangip.com/"""
        api = "http://ecs.hailiangip.com:8422/api/getIpEncrypt?dataType=1&encryptParam=SlDyzgfgDW12vuaMHmQkMz9pKEmWH7kDAoD1ZC4KkxrlVhShpdEjb9vG2YRiwpyE7%2FmtHBf0UytBN%2FbvoFFQxR34HqF6jcH2DIa9lAfHZKAtZ1ij%2BTipB%2BPa4OIC6Fak0EBMPBGst8aumQxGQxXUym0riZNcRTbKMjSvYRYqLmjYFsJvJYxeLU9YDql4IJq6KHmQBjYm32MK13MpScW7XF7%2FeDXlL0x6IKTgy4kKtwD10%2FrggxuKwg%2Fa3uSVATqr"
        # 更新一次代理
        async with aiohttp.request("GET", api) as resp:
            resp = await resp.text()
            logger.info(f"获取代理结果: {resp}")
            self.proxy = f"http://{resp}"
            logger.info(f"更新代理: {self.proxy}")

    @staticmethod
    def parser_search_result(response):
        try:
            res = response.get("data").get("resultList")
            result = []
            for item in res:
                try:
                    main = item.get("data").get("item").get("main")
                    click_param = main.get("clickParam")
                    ex_content = main.get("exContent")
                    target_url = main.get("targetUrl")
                    publish_time = click_param.get('args').get("publishTime")
                    # 时间戳转换
                    publish_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(publish_time) / 1000))
                    title = ex_content.get("title")
                    item_id = ex_content.get("itemId")
                    pic_url = ex_content.get("picUrl")
                    user_nick = ex_content.get('detailParams').get("userNick")
                    price = ex_content.get('detailParams').get("soldPrice")
                    # 组装数据
                    data = {
                        "itemId": item_id,
                        "userNick": user_nick,
                        "price": price,
                        "title": title,
                        "pic_url": pic_url,
                        "publish_time": publish_time,
                    }
                    result.append(data)
                except Exception as e:
                    logger.error(f"解析商品数据失败: {e}")
            return result
        except Exception as e:
            logger.exception(e)
            logger.error(f"解析search结果失败: {e}")
            return []
