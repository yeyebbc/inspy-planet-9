# !/usr/bin/env python
# -*- coding: utf-8 -*

import json
import os.path
import random
import traceback
import re

from lib.tools.common_utils import commonUtils
from lib.tools.logger import logger


class ConfigReader:
    def __init__(self):
        self.config: dict[str, str] = None
        if self.config is None:
            finalFileName = "inspy.cfg"
            localStr = commonUtils.readFile("local_config.json")
            if not commonUtils.isEmpty(localStr):
                local = json.loads(localStr)
                if local.get("isOnline") == False:
                    commonUtils.setOnline(False)
                configFile = local.get("config_file")
                if configFile is not None and os.path.exists(configFile):
                    finalFileName = configFile
            self.read(finalFileName)
        self.cacheMap = {}

    def read(self, configFileName):
        try:
            with open("./" + configFileName, "r", encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    self.parseLine(line)
        except Exception as e:
            logger.writeException()
            logger.e("根目录没找到" + configFileName + "文件")

    def isOnline(self):
        return self.isOnline == True

    def parseLine(self, line):
        line = line.strip()
        # 去掉注释
        temp = commonUtils.getLeft(line, "//")
        if temp is not None:
            line = temp
        if len(line.strip()) < 2:
            return
        # 空白符分割
        words = re.split(r'[\n\t\r\f\b\v\s]', line)
        key = ""
        value = ""
        if len(words) > 0:
            key = words[0]
            v = commonUtils.getRight(line, key)
            if not commonUtils.isEmpty(v):
                value = v.strip()

        # 去掉引号
        if len(value) >= 2:
            if value.startswith("\"") and value.endswith("\"") or value.startswith("'") and value.endswith("'"):
                value = value[1: len(value) - 1].strip()
        if self.config is None:
            self.config = {}
        self.config[key] = value

    def get(self, key):
        return self.config.get(key)

    def getValue(self, key, default):
        v = self.get(key)
        if commonUtils.isEmpty(v):
            return default
        return v

    def getEnableLog(self):
        return self.get("main.enableLog") == "1"

    def getEnableMoreLog(self):
        return self.get("main.enableMoreLog") == "1"

    def getEnableLogFile(self):
        return self.get("main.enableLogFile") == "1"

    def getServerLogFile(self):
        return self.get("sissm.GameLogFile")

    def getServerId(self):
        serverId = self.get("sync_data.serverId")
        if commonUtils.isEmpty(serverId) or commonUtils.toInt(serverId, -1) < 0:
            raise Exception("请配置serverId")
        return self.get("sync_data.serverId")

    def getServerKey(self):
        serverKey = self.get("sync_data.serverKey")
        if serverKey is None:
            serverKey = ""
        if serverKey == "abc" and commonUtils.isOnline():
            raise Exception("请配置serverKey")
        return serverKey

    def getRconIp(self):
        return self.get("sissm.RconIP")

    def getRconPort(self):
        return commonUtils.toInt(self.get("sissm.RconPort"), 0)

    def getRconPassword(self):
        return self.get("sissm.RconPassword")

    def getAdsArray(self):
        return self.getArray("pigreetings.serverads")

    def isRandomAds(self):
        return self.getValue("pigreetings.isRandomAds","0") == "1"

    def getGreetingsArray(self):
        return self.getArray("pigreetings.servergreetings")

    def getAdsEnable(self):
        return self.get("pigreetings.showads") == "1"

    def getAdsDelay(self):
        return commonUtils.toInt(self.get("pigreetings.adsDelay"), 5)

    def getAdsInterval(self):
        return commonUtils.toInt(self.get("pigreetings.adsInterval"), 30)

    def getFirstJoinMsg(self):
        return self.getOneRandomString("pigreetings.firstJoinMsg", "'$name'$title 抵達戰場. 第壹次來本服，熱烈歡迎！")

    def getOneRandomString(self, key, defaultValue):
        value = self.getValue(key, "")
        if not commonUtils.isEmpty(value):
            return value
        else:
            array = self.getArray(key)
            if not commonUtils.isEmpty(array):
                index = random.randint(0, len(array) - 1)
                return array[index]
            else:
                return defaultValue

    def getConnectedMsg(self):
        return self.getOneRandomString("pigreetings.connected","'$name'$title 抵達戰場. 排名第:$rank")

    def getDisconnectedMsg(self):
        return self.getOneRandomString("pigreetings.disconnected", "'$name' 跑了.")

    def getTitleShow(self):
        return self.get("pigreetings.titleShow") == "1"

    def getTitleRules(self):
        return self.get("pigreetings.titleRules")

    def getTitleValueMap(self):
        titleValueList = self.getArray("pigreetings.titleValue")
        if commonUtils.isEmpty(titleValueList):
            return None
        valueNameMap = {}
        for l in titleValueList:
            arr = l.split("|")
            if len(arr) != 2:
                continue
            value = arr[0]
            name = arr[1]
            valueNameMap[value] = name
        return valueNameMap

    def getCustomTitleMap(self):
        titleMap = {}
        titleList = self.getArray("pigreetings.customTitle")
        if commonUtils.isEmpty(titleList):
            return titleMap
        for data in titleList:
            if commonUtils.isEmpty(data):
                continue
            arr1 = data.split("|")
            if len(arr1) != 2:
                continue
            if commonUtils.isEmpty(arr1[0]) or commonUtils.isEmpty(arr1[1]):
                continue
            uidArr = arr1[0].replace("，", ",").split(",")
            for uid in uidArr:
                titleMap[uid] = arr1[1]
        return titleMap

    def getCustomTitleShow(self):
        return self.getValue("pigreetings.customTitleShow", "1") == "1"
    # TODO 后面再开发：替换真名。需要一个统一函数，入参：真实名字，id定制称号，积分称号，内部统一决定。
    def getCustomTitleReplacePlayerName(self):
        return self.getValue("pigreetings.customTitleReplacePlayerName","1")=="1"

    def getMapVoteEnable(self):
        return self.get("map_vote.pluginState") == "1"

    def getAiKeywords(self):
        aiKeywords = self.getValue("chat.aiKeywords", "ai")
        return aiKeywords.split("|")

    def getMapVoteTipArray(self):
        arr = self.getArray("map_vote.tip")
        if arr is None or len(arr) == 0:
            arr = []
            arr.append("[投票換圖]請輸入地圖序號: 序號後面可帶上字母:s,i,d,n,例如:6in")
            arr.append("[字母解釋]:s=Security, i=Insurgents, d=Day, n=Night")
        return arr

    def getMapVoteLessPlayerCountNeedAllVote(self):
        return commonUtils.toInt(self.get("map_vote.lessPlayerCountNeedAllVote"), 3)

    def getMapVoteAllowDuplicateVoteUid(self):
        return self.get("map_vote.allowDuplicateVoteUid")

    def getMapVoteTime(self):
        return commonUtils.toInt(self.get("map_vote.time"), 30)

    def getMapVoteWarnTime(self):
        return commonUtils.toInt(self.get("map_vote.warnTime"), 15)

    def getMapVoteWarn(self):
        return self.get("map_vote.warn")

    def getMapVoteMapCyclePath(self):
        return self.get("map_vote.mapCyclePath")

    def getArray(self, name):
        arr = []
        if self.config is None:
            return arr
        for key in self.config.keys():
            if key.startswith(name):
                index = commonUtils.getMid(key, "[", "]")
                if not commonUtils.isEmpty(index):
                    value = self.config.get(key)
                    arr.append(value)
        return arr

    def getExecEnable(self):
        return self.getValue("exec.pluginState", "0") == "1"

    def getMapObject(self, name):
        # 例如数据为：
        # cmd[0].event "roundStart"
        # cmd[0].condition "killCount>0"
        # 解析最终的数据结构为：{0,{"event":"roundStart","condition":"$killCount>0"}}
        map = {}
        if self.config is None:
            return map
        for key in self.config.keys():
            if key.startswith(name):
                index = commonUtils.getMid(key, "[", "]")
                mapKey = commonUtils.getRight(key, "]")
                if not commonUtils.isEmpty(index) and not commonUtils.isEmpty(mapKey):
                    mapKey = mapKey.replace(".", "")
                    value = self.config.get(key)
                    if index not in map:
                        map[index] = {mapKey: value}
                    else:
                        map[index][mapKey] = value
        return map

    def getRestartScriptPath(self):
        return self.get("sissm.RestartScript")

    def getRestartDelay(self):
        return commonUtils.toInt(self.get("sissm.RestartDelay"), -1)

    def getShowPlayerLocal(self):
        return self.get("pigreetings.showPlayerLocal") == "1"

    def getEnableWriteFile(self):
        return self.get("sync_data.enableWriteFile") == "1"

    def getRankKeywordsPinyin(self):
        strWords = self.get("chat.rankKeywords")
        if commonUtils.isEmpty(strWords):
            strWords = "排名|排行榜|榜单|战绩|成绩"

        arrWords = strWords.split("|")
        arrPinyin = []
        for word in arrWords:
            arrPinyin.append(commonUtils.getPinyin(word).lower())
        return arrPinyin

    def getValueByKeywordsPinyin(self, pinyinStr):
        keywordsArr = self.getArray("chat.keywords")
        if commonUtils.isEmpty(keywordsArr):
            return None
        for keywords in keywordsArr:
            arr = keywords.split("==")
            if len(arr) == 2:
                keyArr = arr[0].split("|")
                for key in keyArr:
                    if commonUtils.getPinyin(key) == pinyinStr:
                        return arr[1]
        return None

    def getRankRules(self):
        return self.get("chat.rankRules")

    def getRankMe(self):
        rankMe = self.get("chat.rankMe")
        if commonUtils.isEmpty(rankMe):
            return "[$name]$title 排名$rank，分數:$score,殺敵：$kill，站點：$take"
        else:
            return rankMe

    def getRankShow(self):
        return self.getValue("chat.rankShow", "1") == "1"

    def getRankPlayersShow(self):
        return self.getValue("chat.rankPlayersShow", "1") == "1"

    def getRankPlayers(self):
        return self.getValue("chat.rankPlayers", "前3名玩家:$rank[0].$name[0]; $rank[1].$name[1]; $rank[2].$name[2]")

    def getRankListSize(self):
        return self.getValue("chat.rankListSize", "3")

    def getAiPrompt(self):
        aiPrompt = self.getValue("chat.aiPrompt",
                                 "")
        if not commonUtils.isEmpty(aiPrompt):
            return aiPrompt
        else:
            aiPromptList = self.getArray("chat.aiPromptList")
            if not commonUtils.isEmpty(aiPromptList):
                return random.choice(aiPromptList)
            else:
                return ""

    def getAiMsgSplitThreshold(self):
        aiMsgSplitThreshold = self.getValue("chat.aiMsgSplitThreshold",
                                            "50")
        try:
            return int(aiMsgSplitThreshold)
        except ValueError:
            logger.e(f"'{aiMsgSplitThreshold}' 不是有效的整数！")
        return 50
    def getAiMsgMaxWords(self):
        maxWords = self.getValue("chat.aiMsgMaxWords",
                                            "150")
        try:
            return int(maxWords)
        except ValueError:
            logger.e(f"'{maxWords}' 不是有效的整数！")
        return 150
    def getDeepseekKey(self):
        return self.getValue("chat.deepseekKey", "")

    def getPlayerQueryCurrentRound(self):
        return self.getValue("chat.playerQueryCurrentRound", "")

    def getPitacnomicEnable(self):
        return self.get("pitacnomic.pluginState") == "1"

    def getPitacnomicArray(self):
        return self.getArray("pitacnomic.shorts")

    def getPitacnomicLivePlayersOnly(self):
        return self.getValue("pitacnomic.livePlayersOnly", "")

    def getGroupnameList(self):
        return self.getArray("sissm.groupname")

    def getGroupcmdsList(self):
        return self.getArray("sissm.groupcmds")

    def getGroupguidFileList(self):
        return self.getArray("sissm.groupguid")

    def getPicladminEnable(self):
        return self.get("picladmin.pluginState") == "1"

    def getTeamKillPluginState(self):
        return self.get("team_kill.pluginState") == "1"

    def getTeamKillMsg(self):
        return self.getValue("team_kill.msg", "[$playerName]TK了[$deadPlayerName]，快道歉，下次看清楚一点！")

    def getTeamKillSryCheck(self):
        return self.getArray("team_kill.sryCheck")

    def getTeamKillCancelExecuteMsg(self):
        return self.getValue("team_kill.cancelExecuteMsg", "")

    def getTeamKillExecuteDelay(self):
        return commonUtils.toInt(self.get("team_kill.executeDelay"), -1)

    def getTeamKillExecuteCmd(self):
        return self.getValue("team_kill.executeCmd", "")

    def getTeamKillAfterMsg(self):
        return self.getValue("team_kill.afterMsg", "")

    def getAllowTKTookObjectiveTime(self):
        return commonUtils.toInt(self.get("team_kill.allowTKTookObjectiveTime"), -1)

    def isProtectPluginEnable(self):
        return self.get("piprotect.pluginState") == "1"
    def isProtectEnableMapVoteWorkaround(self):
        return self.get("piprotect.enableMapVoteWorkaround") == "1"
    def getProtectMapVoteErrRconEx(self):
        return self.getValue("piprotect.mapVoteErrRconEx","travel Ministry?Scenario=Scenario_Ministry_Checkpoint_Security")
    def getProtectMapVoteErrRconExRandomList(self):
        return self.getArray("piprotect.mapVoteErrRconExRandom")

    def getGameEventPluginState(self):
        return self.get("game_event.pluginState")=="1"
    def getGameEventRoundStart(self):
        return self.get("game_event.roundStart")
    def getGameEventRoundEnd(self):
        return self.get("game_event.roundEnd")
    def getGameEventGameStart(self):
        return self.get("game_event.gameStart")
    def getGameEventGameEndWin(self):
        return self.get("game_event.gameEndWin")
    def getGameEventGameEndLose(self):
        return self.get("game_event.gameEndLose")
    def getGameEventGameEnd(self):
        return self.get("game_event.gameEnd")
    def getGameEventTakeObject(self):
        return self.get("game_event.takeObject")
    def getGameEventKill(self):
        return self.get("game_event.kill")

    def isTkWeaponKeywordFilter(self, weapon):
        tkWeaponKeywordFilter = self.get("main.tkWeaponKeywordFilter")
        if commonUtils.isEmpty(weapon) or commonUtils.isEmpty(tkWeaponKeywordFilter):
            return False
        arr = tkWeaponKeywordFilter.split("|")
        for a in arr:
            if a in weapon:
                return True
        return False

    def getPlayerEventPluginState(self):
        return self.get("player_event.pluginState") == "1"

    def getReachScoreArray(self):
        return self.getArray("player_event.reachScore")

    def getReachKillCountArray(self):
        return self.getArray("player_event.reachKillCount")

    def getReachDeadCountArray(self):
        return self.getArray("player_event.reachDeadCount")

    def getReachTakeCountArray(self):
        return self.getArray("player_event.reachTakeCount")

    def getHttpServerPluginState(self):
        return self.get("http_server.pluginState") == "1"

    def getHttpServerPort(self):
        return commonUtils.toInt(self.get("http_server.port"), 80)

    def getHttpServerMap(self):
        '''
        获取配置的服务器列表，返回map格式，key是serverId，value是数组，元素0是serverKey，元素1是服务器名
        '''
        key = "http_server.server"
        cache = self.cacheMap.get(key)
        if cache is not None:
            return cache
        map = {}
        arr = self.getArray(key)
        for a in arr:
            server: list = a.split("|")
            if len(server) == 3:
                map[server[0]] = [server[1], server[2]]
            else:
                raise ValueError(f"http_server.server需要有三部分，serverId|serverKey|服务器名，当前是：{a}")
        self.cacheMap[key] = map
        return map

    def isMainServer(self):
        return self.get("http_server.is_main_server") == "1"

    def checkServerKey(self, serverId, serverKey):
        map = self.getHttpServerMap()
        if map is None:
            return False
        else:
            data = map.get(serverId)
            if commonUtils.len(data) != 2:
                return False
            else:
                return data[0] == serverKey

    def getDbPath(self):
        return self.getValue("http_server.dbPath", "game.db")

    def isImportFromInspyServerEnable(self):
        return self.get("http_server.import_from_inspy_server_enable") == "1"

    def getHttpServerName(self, serverId, defaultValue):
        map = self.getHttpServerMap()
        if map is None:
            return defaultValue
        arr = map.get(serverId)
        if commonUtils.len(arr) == 2:
            return arr[1]
        else:
            return defaultValue


    def getSyncDataServerIp(self):
        serverIp=None
        if commonUtils.isOnline():
            serverIp = self.get("sync_data.serverIp")
            if commonUtils.isEmpty(serverIp):
                serverIp = "inspy.yiwowang.com"
        if commonUtils.isEmpty(serverIp):
            serverIp = "127.0.0.1:8000"
        return serverIp

configReader = ConfigReader()
