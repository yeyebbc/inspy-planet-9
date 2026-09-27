# !/usr/bin/env python
# -*- coding: utf-8 -*
import json
import os
import time

from lib.player_data_center import playerDataCenterInstance
from lib.tools.common_utils import commonUtils
from lib.tools.config_reader import configReader
from lib.tools.logger import logger
from lib.tools.net_utils import netUtils


# 实时更新玩家数据

# 梳理原来投票和同步数据的事件。
# X聊天
# X玩家加入、退出事件
# X本局開始、結束
# X本回合開始、結束
# X站點、擊殺

# 监听各种事件，累计数据。
# 写一个插件同步数据
# 插件可以随时获取这个数据，还有玩家数据

# 重写sissm欢迎功能
class RoundData:
    serverId: int = 0
    gameStartTime: int = 0
    gameRoundLimit: int = 0
    gameIsFull: int = 0
    roundId: int = 0
    roundStartTime: int = 0
    roundEndTime: int = 0
    mapName: str = ""
    camp: int = 0
    win: int = 0
    endReason: str = ""
    takePosition: int = -1


class KillWay:
    name: str = ""
    count: int = 0


class PlayerData:
    name: str = ""  # 玩家名字
    uid: str = ""  # 玩家steamId
    score: int = 0  # 玩家得分
    ip: str = ""
    killCount: int = 0
    tkCount: int = 0
    deadCount: int = 0
    assistCount: int = 0  # 助攻数量
    suicideCount: int = 0  # 自杀数量
    takeCount: int = 0
    joinTime: int = 0
    leaveTime: int = 0
    killWay: dict = {}
    deadWay: dict = {}
    isAlive: int = 0
    lastDeadWay = ""
    isCurrentAlive: int = 0  # 当前是否活着

    def __init__(self):
        self.killWay = {}
        self.deadWay = {}


class ChatData:
    uid: str = ""
    name: str = ""
    msg: str = ""
    time: int = 0


class GameDataCenter:
    # [str, PlayerData]
    playerDict: dict = {}
    # [ChatData]
    chatList: list = []
    gameStartTime: int = 0
    gameIsFull: int = 0
    gameMapName: str = ""
    gameCamp: int = 0
    roundData: RoundData = RoundData()
    serverId: str = ""
    serverKey: str = ""
    roundId: int = 0
    pointMap = {'0': 'A', '1': 'B', '2': 'C', '3': 'D', '4': 'E', '5': 'F', '6': 'G', '7': 'H',
                '8': 'I', '9': 'J', '10': 'K', '11': 'L', '12': 'M', '13': 'N', '14': 'O'}

    def __init__(self):
        # 不在这初始化就像全局变量一样
        self.playerDict = {}
        self.chatList = []
        self.roundData = RoundData()
        self.TAG = "GameDataCenter"

    def init(self, serverId, serverKey):
        self.serverId = serverId
        self.serverKey = serverKey

    def toPointName(self, point):
        if point is None or point < 0:
            return "--"
        name = self.pointMap.get(str(point))
        if commonUtils.isEmpty(name):
            return "--"
        return name

    def mapChange(self, data):
        if commonUtils.isEmpty(self.gameMapName):
            mapName = data.get("mapName")
            if len(mapName) > 0:
                self.gameMapName = mapName

    def travel(self, data):
        mapName = data.get("mapName")
        if len(mapName) > 0:
            self.gameMapName = mapName
        self.gameCamp = data.get("camp")

    def initGameStart(self):
        self.gameStartTime = int(time.time())

    def gameStart(self, data):
        self.initGameStart()
        self.gameIsFull = 1

    def gameEnd(self, data):
        self.gameIsFull = 0
        self.gameStartTime = 0
        self.gameMapName = ""

    def clientSynthAdd(self, data):
        self.syncPlayerData()

    def clientSynthtDel(self, data):
        self.syncPlayerData()

    def roundStateChange(self, data):

        self.roundId = data.get("roundIndex")
        if data.get("isStart"):
            if self.gameStartTime <= 0:
                self.gameIsFull = 0
                self.initGameStart()
            self.resetRound()
            self.syncPlayerData()
            # 回合开始全都复活状态
            for player in self.playerDict.values():
                player.isCurrentAlive = 1

        else:
            self.syncPlayerData()
            self.roundData.roundEndTime = int(time.time())
            self.roundData.mapName = self.gameMapName
            self.roundData.camp = self.gameCamp
            self.roundData.endReason = data.get("reason")
            jsonData = {}
            jsonRoundData = {}
            jsonRoundData["serverId"] = self.roundData.serverId
            jsonRoundData["gameIsFull"] = self.roundData.gameIsFull
            jsonRoundData["gameStartTime"] = self.roundData.gameStartTime
            # jsonRoundData["gameRoundLimit"] = self.roundData.gameRoundLimit
            jsonRoundData["roundId"] = self.roundData.roundId
            jsonRoundData["roundStartTime"] = self.roundData.roundStartTime
            jsonRoundData["roundEndTime"] = self.roundData.roundEndTime
            jsonRoundData["mapName"] = self.roundData.mapName
            jsonRoundData["camp"] = self.roundData.camp
            jsonRoundData["win"] = self.roundData.win
            jsonRoundData["endReason"] = self.roundData.endReason
            jsonRoundData["takePosition"] = self.roundData.takePosition
            jsonData["roundData"] = jsonRoundData

            jsonPlayerList = []
            for key in self.playerDict.keys():
                jsonPlayer = {}
                player = self.playerDict[key]
                jsonPlayer["name"] = player.name
                jsonPlayer["uid"] = player.uid
                jsonPlayer["score"] = player.score
                jsonPlayer["killCount"] = player.killCount
                jsonPlayer["deadCount"] = player.deadCount
                jsonPlayer["assistCount"] = player.assistCount
                jsonPlayer["suicideCount"] = player.suicideCount
                jsonPlayer["takeCount"] = player.takeCount
                jsonPlayer["joinTime"] = player.joinTime
                jsonPlayer["leaveTime"] = player.leaveTime
                jsonPlayer["ip"] = player.ip
                jsonPlayer["killWay"] = player.killWay
                jsonPlayer["deadWay"] = player.deadWay
                jsonPlayerList.append(jsonPlayer)
            jsonData["playerList"] = jsonPlayerList

            jsonChatList = []
            for chat in self.chatList:
                jsonChat = {}
                jsonChat["uid"] = chat.uid
                jsonChat["name"] = chat.name
                jsonChat["msg"] = chat.msg
                jsonChat["time"] = chat.time
                jsonChatList.append(jsonChat)
            jsonData["chatList"] = jsonChatList

            jsonStr = json.dumps(jsonData)
            logger.d(self.TAG, "roundEnd 回合完整数据:" + jsonStr)
            if configReader.getEnableWriteFile():
                path = commonUtils.getOutputDataPath()
                if os.path.exists(path):
                    fileName = path + "/round-" + commonUtils.getFileNameByTime() + ".txt"
                    commonUtils.writeFile(fileName, jsonStr)
                    logger.d(self.TAG, "游戏数据已写入:" + fileName)

            try:
                jsonStr = json.dumps(jsonData)
                netUtils.httpPost("game_data.php?serverId=" + str(self.serverId) + "&serverKey=" + self.serverKey,
                                  jsonStr)
            except Exception as e:
                logger.writeException()

    def killed(self, data):
        killerList = data.get("killer")
        diedList = data.get("died")
        weapon = data.get("weapon")
        if killerList is None or diedList is None:
            return
        for i in range(0, len(killerList)):
            killer = killerList[i]
            if killer is None:
                # TODO why is None?
                continue
            playerGUID = killer.get("playerGUID")
            if self.isVaildUid(playerGUID):
                player = self.playerGetOrCreate(playerGUID)
                player.isCurrentAlive = 0
                if player.name is None or len(player.name.strip()) == 0:
                    player.name = killer.get("playerName")
                for dided in diedList:
                    deadGUID = dided.get("playerGUID")
                    if playerGUID == deadGUID:
                        player.suicideCount += 1
                        return
                    elif i == 0:
                        if self.isVaildUid(deadGUID) and not configReader.isTkWeaponKeywordFilter(weapon):
                            player.tkCount += 1
                        player.killCount += 1
                        self.killWayCount(player.killWay, weapon)
                    else:
                        player.assistCount += 1

        for dided in diedList:
            playerGUID = dided.get("playerGUID")
            if self.isVaildUid(playerGUID):
                player = self.playerGetOrCreate(playerGUID)
                if player.name is None:
                    player.name = dided.get("playerName")
                player.deadCount += 1
                player.lastDeadWay = weapon
                player.isCurrentAlive = 0
                self.killWayCount(player.deadWay, weapon)

    def killWayCount(self, killWay, weapon):
        count = killWay.get(weapon)
        if count is None:
            killWay[weapon] = 1
        else:
            killWay[weapon] += 1

    def isVaildUid(self, uid):
        return len(uid) > 10

    def chat(self, data):
        chat = ChatData()
        chat.name = data.get("playerName")
        chat.uid = data.get("playerGUID")
        chat.msg = data.get("content")
        chat.time = int(time.time())
        self.chatList.append(chat)

    def takeObject(self, data):
        if data is None:
            return
        point = data.get("point")
        if point is not None:
            p = int(point)
            if self.roundData.takePosition < p:
                self.roundData.takePosition = p
        players = data.get("players")
        if players is not None:
            for p in players:
                player = self.playerGetOrCreate(p.get("playerGUID"))
                player.name = p.get("playerName")
                player.takeCount += 1
        # 占点后全复活状态
        for player in self.playerDict.values():
            player.isCurrentAlive = 1

    # 回合开始调用
    def resetRound(self):
        self.playerDict.clear()
        self.chatList.clear()
        self.roundData = RoundData()
        self.roundData.gameStartTime = self.gameStartTime
        self.roundData.gameIsFull = self.gameIsFull
        self.roundData.serverId = self.serverId
        self.roundData.roundId = self.roundId
        self.roundData.roundStartTime = int(time.time())

    def playerGetOrCreate(self, uid) -> PlayerData:
        if uid not in self.playerDict:
            self.playerDict[uid] = PlayerData()
            self.playerDict[uid].uid = uid
        return self.playerDict[uid]

    # 补充玩家信息
    def syncPlayerData(self):
        # 先设置全离开
        for key in self.playerDict.keys():
            player = self.playerDict[key]
            player.isAlive = 0
            if player.joinTime == 0:
                player.joinTime = int(time.time())
        # 再设置在线的
        playerList = playerDataCenterInstance.getPlayers()
        if playerList is None:
            return
        for p in playerList:
            player = self.playerGetOrCreate(p.uid)
            player.isAlive = 1
            player.score = p.score
            player.name = p.name
            player.ip = p.ip
        # 设置离开时间
        for key in self.playerDict.keys():
            player = self.playerDict[key]
            if player.isAlive == 0:
                player.leaveTime = int(time.time())

    def replaceVarByPlayerCurrRound(self, originInfoStr: str, uid: str):
        '''
        将字符串里的变量赋值
        :param originInfoStr: 字符串
        :param uid: 玩家uid，如果传空则不赋值玩家的变量数据
        :return:
        '''
        if "$" not in originInfoStr:
            return originInfoStr
        player = self.playerDict.get(uid)
        originInfoStr = originInfoStr.replace("$name", "无" if player is None else str(player.name))
        originInfoStr = originInfoStr.replace("$killCount", "0" if player is None else str(player.killCount))
        originInfoStr = originInfoStr.replace("$tkCount", "0" if player is None else str(player.tkCount))
        originInfoStr = originInfoStr.replace("$deadCount", "0" if player is None else str(player.deadCount))
        originInfoStr = originInfoStr.replace("$assistCount", "0" if player is None else str(player.assistCount))
        originInfoStr = originInfoStr.replace("$suicideCount", "0" if player is None else str(player.suicideCount))
        originInfoStr = originInfoStr.replace("$takeCount", "0" if player is None else str(player.takeCount))
        if player is not None and not commonUtils.isEmpty(player.lastDeadWay):
            lastDeadWay = commonUtils.getWeaponName(player.lastDeadWay)
            originInfoStr = originInfoStr.replace("$lastDeadWay", str(lastDeadWay))
        else:
            originInfoStr = originInfoStr.replace("$lastDeadWay", "无")
        return originInfoStr

    def replaceVarByRoundBaseInfo(self, originInfoStr: str):
        if originInfoStr is None:
            return ""
        if "$" not in originInfoStr:
            return originInfoStr
        originInfoStr = originInfoStr.replace("$roundIndex", str(self.roundData.roundId))
        return originInfoStr

    def replaceVarByRoundCountInfo(self, originInfoStr: str):
        '''
        将字符串里的变量赋值
        :param originInfoStr: 字符串
        :return:
        '''
        if originInfoStr is None:
            return ""
        if "$" not in originInfoStr:
            return originInfoStr
        originInfoStr = originInfoStr.replace("$roundIndex", str(self.roundData.roundId))
        if "$maxKillCount" in originInfoStr:
            player = self.getMaxKillCountPlayer()
            originInfoStr = originInfoStr.replace("$maxKillCountPlayer",
                                                  "0" if player is None else str(player.name))
            originInfoStr = originInfoStr.replace("$maxKillCount", "0" if player is None else str(player.killCount))
        if "$maxDeadCount" in originInfoStr:
            player = self.getMaxDeadCountPlayer()
            originInfoStr = originInfoStr.replace("$maxDeadCountPlayer",
                                                  "0" if player is None else str(player.name))
            originInfoStr = originInfoStr.replace("$maxDeadCount",
                                                  "0" if player is None else str(player.deadCount))
        if "$maxAssistCount" in originInfoStr:
            player = self.getMaxAssistCountPlayer()
            originInfoStr = originInfoStr.replace("$maxAssistCountPlayer",
                                                  "0" if player is None else str(player.name))
            originInfoStr = originInfoStr.replace("$maxAssistCount",
                                                  "0" if player is None else str(player.assistCount))
        if "$maxSuicideCount" in originInfoStr:
            player = self.getMaxSuicideCountPlayer()
            originInfoStr = originInfoStr.replace("$maxSuicideCountPlayer",
                                                  "0" if player is None else str(player.name))
            originInfoStr = originInfoStr.replace("$maxSuicideCount",
                                                  "0" if player is None else str(player.suicideCount))
        if "$maxTakeCount" in originInfoStr:
            player = self.getMaxTakeCountPlayer()
            originInfoStr = originInfoStr.replace("$maxTakeCountPlayer",
                                                  "0" if player is None else str(player.name))
            originInfoStr = originInfoStr.replace("$maxTakeCount",
                                                  "0" if player is None else str(player.takeCount))

        return originInfoStr

    def replaceVarByRoundCountDict(self, varDict: dict):
        '''
        将字符串里的变量赋值
        :param originInfoStr: 字符串
        :return:
        '''
        if varDict is None:
            return varDict
        varDict["roundIndex"] = self.roundData.roundId
        player = self.getMaxKillCountPlayer()
        varDict["maxKillCountPlayer"] = "无" if player is None else str(player.name)
        varDict["maxKillCount"] = 0 if player is None else player.killCount

        player = self.getMaxDeadCountPlayer()
        varDict["maxDeadCountPlayer"] = "无" if player is None else str(player.name)
        varDict["maxDeadCount"] = 0 if player is None else player.deadCount

        player = self.getMaxAssistCountPlayer()
        varDict["maxAssistCountPlayer"] = "无" if player is None else str(player.name)
        varDict["maxAssistCount"] = 0 if player is None else player.assistCount

        player = self.getMaxSuicideCountPlayer()
        varDict["maxSuicideCountPlayer"] = "无" if player is None else str(player.name)
        varDict["maxSuicideCount"] = 0 if player is None else player.suicideCount

        player = self.getMaxTakeCountPlayer()
        varDict["maxTakeCountPlayer"] = "无" if player is None else str(player.name)
        varDict["maxTakeCount"] = 0 if player is None else player.takeCount

        player = self.getMaxTkCountPlayer()
        varDict["maxTkCountPlayer"] = "无" if player is None else str(player.name)
        varDict["maxTkCount"] = 0 if player is None else player.tkCount

    def getMaxKillCountPlayer(self):
        if not self.playerDict:
            return None
        return max(self.playerDict.values(), key=lambda p: p.killCount)

    def getMaxTkCountPlayer(self):
        if not self.playerDict:
            return None
        player = max(self.playerDict.values(), key=lambda p: p.tkCount)
        if player is not None and player.tkCount > 0:
            return player
        else:
            return None

    def getMaxDeadCountPlayer(self):
        if not self.playerDict:
            return None
        return max(self.playerDict.values(), key=lambda p: p.deadCount)

    def getMaxAssistCountPlayer(self):
        if not self.playerDict:
            return None
        return max(self.playerDict.values(), key=lambda p: p.assistCount)

    def getMaxSuicideCountPlayer(self):
        if not self.playerDict:
            return None
        return max(self.playerDict.values(), key=lambda p: p.suicideCount)

    def getMaxTakeCountPlayer(self):
        if not self.playerDict:
            return None
        return max(self.playerDict.values(), key=lambda p: p.takeCount)


gameDataCenterInstance = GameDataCenter()
