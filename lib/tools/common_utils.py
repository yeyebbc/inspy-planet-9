# !/usr/bin/env python
# -*- coding: utf-8 -*
import os
import random
import sys
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import psutil

import traceback

from lib.tools.pinyin.pinyin import Pinyin


# underlayer,don't dep others
class CommonUtils:
    def __init__(self):
        self.online = True
        self.threadPool = ThreadPoolExecutor(max_workers=5)
        self.pinyin = Pinyin()
        self.DATE_TODAY = "date_today"
        self.DATE_YESTERDAY = "date_yesterday"

    def getVersion(self):
        return self.readFile("VERSION")

    def getThreadPool(self):
        return self.threadPool

    def isOnline(self):
        return self.online

    def setOnline(self, online):
        self.online = online

    def getOutputPath(self):
        s = "./output"
        if not os.path.exists(s):
            os.makedirs(s)
        return s

    def getOutputLogPath(self):
        s = "./output/log"
        os.makedirs(s, exist_ok=True)
        return s

    def getOutputDataPath(self):
        s = "./output/data"
        if not os.path.exists(s):
            os.makedirs(s)
        return s

    def getFileNameByTime(self):
        now = datetime.now()
        return now.strftime("%Y-%m-%d-%H-%M-%S")


    def getMid(self, strData, key1, key2):
        if strData is None or key1 is None or key2 is None:
            return None
        index1 = strData.find(key1)
        if index1 < 0:
            return None
        index2 = strData.find(key2, index1 + len(key1))
        if index2 > 0 and index2 > index1:
            return strData[index1 + len(key1): index2].strip()
        return None

    def getLeft(self, strData, key1):
        if strData is None or key1 is None:
            return None
        index1 = strData.find(key1)
        if index1 >= 0:
            return strData[0:index1].strip()
        return None

    def getRight(self, strData, key1):
        if strData is None or key1 is None:
            return None
        index1 = strData.find(key1)
        if index1 >= 0:
            return strData[index1 + len(key1):].strip()
        return None

    def isEmpty(self, data):
        if data is None:
            return True
        if isinstance(data, set) or isinstance(data, str) or isinstance(data, dict) or isinstance(data, list):
            return len(data) == 0
        return False

    def isBlank(self, data):
        if data is None:
            return True
        return len(str(data).strip()) == 0
    def trim(self, data):
        if data is None:
            return ""
        return str(data).strip()
    def len(self, data):
        if data is None:
            return 0
        return len(data)

    def safeStr(self, data):
        if data is None:
            return ""
        return str(data)

    def split(self, data, key):
        if self.isBlank(data):
            return []
        return data.split(key)

    def toInt(self, value, defaultValue):
        try:
            return int(value)
        except Exception as e:
            return defaultValue

    def getRandom(self, size, lastIndex):
        index = random.randint(0, size - 1)
        if lastIndex == index and size > 1:
            if index == size - 1:
                index = 0
            else:
                index += 1
        return index

    def getException(self):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        return traceback_str

    def writeLog(self, fileName, content):
        traceback.print_exc()
        f = open(fileName, "a",
                 encoding='utf-8')
        f.write("[" + self.getCurrTime() + "] " + content + "\n")
        f.close()

    def writeFile(self, fileName, content):
        parent = os.path.dirname(fileName)
        if not os.path.exists(parent):
            os.makedirs(parent)
        f = open(fileName, "w", encoding='utf-8')
        f.write(str(content))
        f.close()

    def readFile(self, fileName):
        if fileName is None or not os.path.exists(fileName):
            return None
        f = open(fileName, "r", encoding='utf-8')
        s = f.read()
        f.close()
        return s

    def getGameProcessMame(self):
        return "InsurgencyServer"

    def getCurrTime(self):
        current_time = datetime.now()
        return str(current_time)

    def getCurrTimestampMs(self):
        return int(time.time() * 1000)

    def findProcessName(self, processName):
        pl = psutil.pids()
        for pid in pl:
            try:
                if processName in psutil.Process(pid).name():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    def killProcessName(self, processName):
        pl = psutil.pids()
        for pid in pl:
            try:
                if processName in psutil.Process(pid).name():
                    psutil.Process(pid).kill()
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    def isWin(self):
        return sys.platform.startswith('win')

    def getPinyin(self, words):
        return self.pinyin.get_pinyin(words)

    def getWeaponName(self,weapon):
        if "_" in weapon:
            return weapon[weapon.rindex("_") + 1:]
        return weapon

    def getMapValue(self, map: dict, key: str, defaultValue):
        if map is None:
            return defaultValue
        if key in map:
            return map[key]
        return defaultValue

    def trimPlayerName(self, playerName: str):
        if '??' in playerName:
            playerName = playerName.split('??')[0]
        return playerName

commonUtils = CommonUtils()
