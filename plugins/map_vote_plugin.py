# !/usr/bin/env python
# -*- coding: utf-8 -*
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from lib.player_data_center import playerDataCenterInstance
from lib.tools.common_utils import commonUtils
from lib.tools.config_reader import configReader
from lib.tools.plugin_helper import PluginHelper
from lib.event_callback import EventCallback


class MapVotePlugin(EventCallback):
    TAG = "MapVotePlugin"

    def enbale(self):
        return configReader.getMapVoteEnable()

    def __init__(self):
        self.helper = PluginHelper()
        self.lastJoinUid = None
        self.lastQuitUid = None
        self.votePlayerDict: dict[str, VoteResult] = {}
        self.allMapList = [
            ["Prison", "Prison"],
            ["Bab", "Bab"],
            ["Ministry", "Ministry"],
            ["Citadel", "Citadel"],
            ["Crossing", "Canyon"],
            ["Farmhouse", "Farmhouse"],
            ["Gap", "Gap"],
            ["Hideout", "Town"],
            ["Hillside", "Sinjar"],
            ["Outskirts", "Compound"],
            ["Precinct", "Precinct"],
            ["Refinery", "Oilfield"],
            ["Summit", "Mountain"],
            ["PowerPlant", "PowerPlant"],
            ["Tell", "Tell"],
            ["Tideway", "Buhriz"],
            ["LastLight", "LastLight"],
            ["Trainyard", "Trainyard"],
            ["Forest", "Forest"],
            ["Hold", "Hold"]
        ]
        self.mapCycle = {}
        self.mapList = self.readFromMapCycle(self.mapCycle)
        if self.mapList is None or len(self.mapList) == 0:
            self.mapList = self.allMapList.copy()
        self.mapCount = len(self.mapList)
        self.masterVoteCount = -1

    def init(self, requester):
        if not self.enbale():
            return
        self.helper.init(requester)
        self.threadPool = ThreadPoolExecutor(max_workers=1)
        self.isStartVote = False

    def readFromMapCycle(self, mapCycle):
        mapCycleText = commonUtils.readFile(configReader.getMapVoteMapCyclePath())
        if commonUtils.isEmpty(mapCycleText):
            return None
        mapCycleText = mapCycleText.replace("\r", "")
        # 初始化一个列表来存储所有字典
        result = []

        # 使用正则表达式匹配每一组括号内的内容
        pattern = r'\((.*?)\)'
        matches = re.findall(pattern, mapCycleText)
        for match in matches:
            # 分割键值对
            pairs = match.split(',')
            current_dict = {}
            for pair in pairs:
                # 分割键和值
                key, value = pair.split('=')
                # 去除值两边的引号
                value = value.strip('"')
                current_dict[key] = value
            result.append(current_dict)
        for item in result:
            scenarioArr = str(item.get("Scenario")).split("_")
            if len(scenarioArr) == 4:
                mapName = scenarioArr[1]
                if mapName not in mapCycle:
                    mapCycle[mapName] = {}
                Lighting = mapCycle[mapName].get("Lighting")
                if Lighting is None:
                    Lighting = []
                if item.get("Lighting") not in Lighting:
                    Lighting.append(item.get("Lighting"))
                mapCycle[mapName]["Lighting"] = Lighting

                Scenario = mapCycle[mapName].get("Scenario")
                if Scenario is None:
                    Scenario = []
                for s in scenarioArr:
                    if s not in Scenario:
                        Scenario.append(s)
                mapCycle[mapName]["Scenario"] = Scenario

        newMapList = []
        for m in self.allMapList:
            if m[0] in mapCycle:
                newMapList.append(m)
        return newMapList

    def chat(self, log, data):
        if not self.enbale():
            return
        if data is None:
            return
        content = data.get("content")
        if content is None:
            return
        if "vote" in content or "投票" in content:
            self.printMap()
        if self.isStartVote:
            digitStr = ""
            sec = -1
            day = -1
            mapIndex = -1
            for i in range(0, len(content)):
                if content[i] == 'i':
                    sec = 0
                elif content[i] == 'n':
                    day = 0
                elif content[i].isdigit():
                    digitStr += content[i]
            if len(digitStr) > 0:
                mapIndex = int(digitStr)
            if mapIndex >= 1 and mapIndex <= self.mapCount:
                playerGUID = data.get("playerGUID")
                playerName = data.get("playerName")
                if playerGUID not in self.votePlayerDict:
                    self.votePlayerDict[playerGUID] = VoteResult()
                voteResult = self.votePlayerDict[playerGUID]
                voteResult.mapIndex = mapIndex - 1
                mapName = self.mapList[voteResult.mapIndex][0]
                mapCycleItem = self.mapCycle.get(mapName)
                LightingList = None if mapCycleItem is None else mapCycleItem.get("Lighting")
                ScenarioList = None if mapCycleItem is None else mapCycleItem.get("Scenario")
                if day == -1:
                    day = (1 if LightingList is None or "Day" in LightingList else 0)
                if sec == -1:
                    sec = (1 if ScenarioList is None or "Security" in ScenarioList else 0)
                voteResult.sec = sec
                voteResult.day = day
                secStr = "政府軍" if sec == 1 else "叛軍"
                dayStr = "白天" if day == 1 else "夜晚"
                isMater = playerGUID == configReader.getMapVoteAllowDuplicateVoteUid()
                noteStr = "有重复投票特权" if isMater else ""
                self.apiSay("[" + playerName + "]投票: ["
                            + self.mapList[voteResult.mapIndex][0] + "] [" + secStr + "] [" + dayStr + "]" + noteStr)
                if isMater:
                    self.masterVoteCount += 1

    def printMap(self):
        text = ""
        for i in range(0, int(self.mapCount / 2)):
            text += " [" + str(i + 1) + "]" + self.mapList[i][0]
        self.apiSay(text)

        text = ""
        for i in range(int(self.mapCount / 2), self.mapCount):
            text += " [" + str(i + 1) + "]" + self.mapList[i][0]
        self.apiSay(text)
        tipArr = configReader.getMapVoteTipArray()
        for tip in tipArr:
            self.apiSay(tip)
        if self.isStartVote:
            return
        self.reset()
        self.threadPool.submit(self.startVote)

    def reset(self):
        self.isStartVote = True
        self.masterVoteCount = 0
        self.votePlayerDict.clear()

    def apiSay(self, text):
        self.helper.requester.apiSay(text)

    def startVote(self):
        voteTime = configReader.getMapVoteTime()
        warnTime = configReader.getMapVoteWarnTime()
        warn = configReader.getMapVoteWarn()
        if commonUtils.isEmpty(warn) or warnTime <= 0 or voteTime < warnTime:
            time.sleep(voteTime)
        else:
            time.sleep(voteTime - warnTime)
            self.apiSay(warn)
            time.sleep(warnTime)
        self.isStartVote = False
        playerCount = len(playerDataCenterInstance.getPlayers())
        realVotePlayerCount = len(self.votePlayerDict)
        votePlayerCount = len(self.votePlayerDict) + max(self.masterVoteCount, 0)
        if playerCount <= 0:
            self.apiSay("投票取消:原因是没有读取到玩家")
        elif playerCount <= configReader.getMapVoteLessPlayerCountNeedAllVote() and votePlayerCount < playerCount:
            self.apiSay(
                "投票取消:原因是玩家少於3人時需要全票(" + str(realVotePlayerCount) + "/" + str(playerCount) + ")")
        elif votePlayerCount <= 0 or votePlayerCount < playerCount / 2:
            self.apiSay(
                "投票取消:原因是參與投票的人數少於50%(" + str(realVotePlayerCount) + "/" + str(playerCount) + ")")
        else:
            # 索引是地圖索引，元素值是投標次數
            mapIndexArray: list[int] = [0] * self.mapCount
            secNum = 0
            insNum = 0
            dayNum = 0
            nightNum = 0
            for uid in self.votePlayerDict:
                voteResult = self.votePlayerDict[uid]
                # master
                if uid == configReader.getMapVoteAllowDuplicateVoteUid():
                    # 此人权限巨大，多次投票算数
                    mapIndexArray[voteResult.mapIndex] += (1 + max(self.masterVoteCount, 0))
                    print("特权++" + str(mapIndexArray[voteResult.mapIndex]))
                else:
                    mapIndexArray[voteResult.mapIndex] += 1

                if voteResult.sec == 1:
                    secNum += 1
                else:
                    insNum += 1

                if voteResult.day == 1:
                    dayNum += 1
                else:
                    nightNum += 1
            maxMapIndex = -1
            maxMapVoteNum = 0
            for i in range(0, len(mapIndexArray)):
                if mapIndexArray[i] > maxMapVoteNum:
                    maxMapVoteNum = mapIndexArray[i]
                    maxMapIndex = i
            mapName = self.mapList[maxMapIndex][0]
            secStr = "政府軍" if secNum >= insNum else "叛軍"
            dayStr = "白天" if dayNum >= nightNum else "夜晚"
            secCode = "Security" if secNum >= insNum else "Insurgents"
            dayCode = "Day" if dayNum >= nightNum else "Night"
            self.apiSay("投票成功:共" + str(
                votePlayerCount) + "個玩家參與, 投票最多地圖:" + mapName + " [" + secStr + "] [" + dayStr + "](" + str(
                maxMapVoteNum) + "次)")
            time.sleep(5)
            self.helper.requester.requestRconCmd(
                "travel {}?Scenario=Scenario_{}_Checkpoint_{}?Lighting={}".format(self.mapList[maxMapIndex][1],
                                                                                  self.mapList[maxMapIndex][0], secCode,
                                                                                  dayCode))

    def gameEnd(self, log, data):
        if not self.enbale():
            return
        self.printMap()

class VoteResult:

    def __init__(self):
        self.mapIndex = -1
        self.sec: int = 1
        self.day: int = 1
