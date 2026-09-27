# !/usr/bin/env python
# -*- coding: utf-8 -*
import random
from lib.tools.common_utils import commonUtils
from lib.tools.config_reader import configReader
from lib.tools.plugin_helper import PluginHelper
from module.rank_module import rankModule
from lib.event_callback import EventCallback


class PigreetingsPlugin(EventCallback):
    TAG = "PigreetingsPlugin"
    helper = PluginHelper()

    def enbale(self):
        return configReader.getAdsEnable()

    def __init__(self):
        self.isRoundStart = True
        self.adsIndex = 0
        self.timeSeconds = 0
        self.greetingsArray = configReader.getGreetingsArray()
        self.adsArray = configReader.getAdsArray()
        self.adsDelay = configReader.getAdsDelay()
        self.adsInterval = configReader.getAdsInterval()
        self.gameStartDelayFinish = False
        rankModule.initAdArray()

    def init(self, requester):
        self.helper.init(requester)

    def gameStart(self, log, data):
        self.index = 0
        self.timeSeconds = 0
        self.adsIndex = 0
        self.gameStartDelayFinish = False

    def roundStart(self, log, data):
        self.isRoundStart = True
        self.adsIndex = 0
        if not commonUtils.isEmpty(self.greetingsArray):
            for msg in self.greetingsArray:
                self.apiSay(msg)

    def roundEnd(self, log, data):
        self.isRoundStart = False

    def timer(self, data):
        if not self.isRoundStart:
            return
        if self.timeSeconds == 0 or self.timeSeconds % 60:
            rankModule.tryUpdateRankTop(self.helper.serverId, False)

        self.timeSeconds += 1
        if not self.gameStartDelayFinish:
            if self.timeSeconds >= self.adsDelay:
                self.gameStartDelayFinish = True
                self.sayNext()
            return
        else:
            if self.timeSeconds % self.adsInterval == 0:
                self.sayNext()

    def sayNext(self):
        adArrayNew = rankModule.getAdArrayNew()
        if not commonUtils.isEmpty(adArrayNew):
            self.adsArray = adArrayNew

        size = len(self.adsArray)
        if configReader.isRandomAds():
            self.adsIndex = commonUtils.getRandom(size, self.adsIndex)
            self.apiSay(self.adsArray[self.adsIndex])
            return

        if self.adsIndex < len(self.adsArray):
            self.apiSay(self.adsArray[self.adsIndex])
            self.adsIndex += 1
        else:
            self.adsIndex = 0
            self.apiSay(self.adsArray[self.adsIndex])
            self.adsIndex += 1

    def apiSay(self, text):
        self.helper.requester.apiSay(text, logLevel=2)

    def roundStateChange(self, log, data):
        if data.get("isStart") == False:
            rankModule.tryUpdateRankTop(self.helper.serverId, True)
