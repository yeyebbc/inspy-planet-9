# !/usr/bin/env python
# -*- coding: utf-8 -*
from lib.game_data_center import gameDataCenterInstance
from lib.player_data_center import playerDataCenterInstance, Player
from lib.tools.common_utils import commonUtils
from lib.tools.config_reader import configReader
from lib.tools.plugin_helper import PluginHelper
from lib.event_callback import EventCallback


class PlayerEventPlugin(EventCallback):
    helper = PluginHelper()
    register = None
    # key是玩家uid，value是上次提示时已经到达的分数配置
    playerReachScoreMap = {}
    playerReachKillCountMap = {}
    playerReachDeadCountMap = {}
    playerReachTakeCountMap = {}
    # 配置,key是阈值，value是提示词数组，使用的时候要随机
    configScoreMap = {}
    configKillCountMap = {}
    configDeadCountMap = {}
    configTakeCountMap = {}
    roundSecond = 0

    sortedScoreList = []
    sortedKillCountList = []
    sortedDeadCountList = []
    sortedTakeCountList = []
    isRoundEnd = True

    def __init__(self, register):
        self.register = register

    def enbale(self):
        return configReader.getPlayerEventPluginState()

    def init(self, requester):
        self.requester = requester
        self.helper.init(requester)
        self.convertMap(configReader.getReachScoreArray(), self.configScoreMap)
        # self.convertMap(configReader.getReachKillCountArray(), self.configKillCountMap)
        # self.convertMap(configReader.getReachDeadCountArray(), self.configDeadCountMap)
        # self.convertMap(configReader.getReachTakeCountArray(), self.configTakeCountMap)

        # 预先对configScoreMap的key排序，避免每次循环都排序
        self.sortedScoreList = sorted(self.configScoreMap.keys())
        # self.sortedKillCountList = sorted(self.configKillCountMap.keys())
        # self.sortedDeadCountList = sorted(self.configDeadCountMap.keys())
        # self.sortedTakeCountList = sorted(self.configTakeCountMap.keys())

    def convertMap(self, array, map):
        if commonUtils.isEmpty(array) or map is None:
            return
        for a in array:
            a = a.replace("\"", "")
            if not commonUtils.isEmpty(a):
                arr = a.split("|")
                if len(arr) == 2:
                    v = commonUtils.toInt(arr[0], 0)
                    if v > 0:
                        map[v] = str(arr[1]).split("---")

    def gameStart(self, log, data):
        self.playerReachScoreMap.clear()

    def gameEnd(self, log, data):
        self.playerReachScoreMap.clear()
        self.isRoundEnd = True
        self.roundSecond = 0

    def roundStart(self, log, data):
        self.playerReachKillCountMap.clear()
        self.playerReachDeadCountMap.clear()
        self.playerReachTakeCountMap.clear()
        self.isRoundEnd = False
        self.roundSecond = 0

    def roundEnd(self, log, data):
        self.playerReachKillCountMap.clear()
        self.playerReachDeadCountMap.clear()
        self.playerReachTakeCountMap.clear()
        self.isRoundEnd = True
        self.roundSecond = 0

    def timer(self, data):
        if not self.enbale():
            return
        if self.isRoundEnd:
            return
        if self.roundSecond % 10 == 0:
            self.checkAndTip()
        self.roundSecond += 1

    def checkAndTip(self):
        if self.isRoundEnd:
            return
        # 获取玩家列表
        playerList = playerDataCenterInstance.getPlayers()
        # playerList = []
        # p = Player()
        # p.name = "测试啊啊"
        # p.uid = "123444556667"
        # p.score = self.roundSecond
        # playerList.append(p)
        if playerList is None:
            return

        # 遍历每个玩家
        for player in playerList:
            currentScore = player.score
            lastReachedScore = self.playerReachScoreMap.get(player.uid, 0)

            # 找到当前分数应该达到的最高节点
            currentMaxReachedScore = 0
            for scoreThreshold in self.sortedScoreList:
                if currentScore >= scoreThreshold:
                    currentMaxReachedScore = scoreThreshold
                else:
                    break

            # 如果有新达到的节点
            if currentMaxReachedScore > lastReachedScore:
                tip = self.getRandomTip(self.configScoreMap.get(currentMaxReachedScore),
                                        player.name)
                if not commonUtils.isEmpty(tip):
                    self.requester.apiSay(tip)
                # 更新缓存
                self.playerReachScoreMap[player.uid] = currentMaxReachedScore

    def getRandomTip(self, tipArray, playerName):
        if commonUtils.isEmpty(tipArray):
            return ""
        index = commonUtils.getRandom(len(tipArray), -1)
        tip: str = tipArray[index]
        if not commonUtils.isEmpty(tip):
            return tip.replace("$name", playerName)
        return tip
