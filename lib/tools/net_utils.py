# !/usr/bin/env python
# -*- coding: utf-8 -*
import json
from urllib.parse import urlencode

import requests

from lib.tools.common_utils import commonUtils
from lib.tools.config_reader import configReader
from lib.tools.logger import logger


class NetUtils:
    configReader = None
    timeout = 10
    TAG="NetUtils"

    def init(self, configReader):
        self.configReader = configReader
        self.timeout = 30

    def httpGet(self, fileName, params):
        dataStr = None
        startTime = commonUtils.getCurrTimestampMs()
        try:
            queryString = ""
            if params is not None:
                queryString = '?' + urlencode(params)
            url = 'http://' + configReader.getSyncDataServerIp() + '/insurgency_web/' + fileName + queryString
            logger.d(self.TAG, "get请求:" + str(url))
            r = requests.get(url, timeout=self.timeout)
            dataStr = str(r.text)
            try:
                return json.loads(dataStr)
            except Exception as e:
                logger.e(self.TAG, "请求解析出错")
                logger.writeException()
        except Exception as e:
            logger.e(self.TAG, "请求出错")
            logger.writeException()
        finally:
            costTime = commonUtils.getCurrTimestampMs() - startTime
            logger.d(self.TAG, "请求结果:", "[耗时:", costTime, "ms]", dataStr)

        return None

    def httpPost(self, fileName, data):
        dataStr=None
        startTime = commonUtils.getCurrTimestampMs()
        try:
            url = 'http://' + configReader.getSyncDataServerIp() + '/insurgency_web/' + fileName
            logger.d(self.TAG, "post请求:" + url)
            r = requests.post(url, data=data, timeout=self.timeout)
            dataStr = str(r.text)
            try:
                return json.loads(dataStr)
            except Exception as e:
                logger.e(self.TAG, "请求解析出错")
                logger.writeException()
        except Exception as e:
            logger.e(self.TAG, "请求出错")
            logger.writeException()
        costTime = commonUtils.getCurrTimestampMs() - startTime
        logger.d(self.TAG, "请求结果:", "[耗时:", costTime, "ms]", dataStr)

        return None

    def getLocalByIp(self, ip):
        dataStr=""
        try:
            url = "https://api.vore.top/api/IPdata?ip=" + ip
            r = requests.get(url, timeout=self.timeout)
            dataStr = str(r.text)
        except Exception as e:
            logger.writeException()
        logger.d(self.TAG, "请求结果:" + str(dataStr))
        return json.loads(dataStr)


# "https://www.milianshe.com/" 双拼:

netUtils = NetUtils()
