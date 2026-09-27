# !/usr/bin/env python
# -*- coding: utf-8 -*
import time

from lib.game_data_center import gameDataCenterInstance
from lib.player_data_center import playerDataCenterInstance
from lib.tools.common_utils import commonUtils
from lib.tools.config_reader import configReader
from lib.tools.logger import logger
from lib.tools.plugin_helper import PluginHelper
from lib.event_callback import EventCallback


class ExecPlugin(EventCallback):
    cmdMap = {}
    TAG = "ExecPlugin"
    helper = PluginHelper()
    namespace = {}

    def __init__(self):
        self.globalData = {}
        self.gameSecond = 0
        self.roundSecond = 0

    def enbale(self):
        return configReader.getExecEnable()

    def init(self, requester):
        self.helper.init(requester)
        self.resetGameData()
        mapObject = configReader.getMapObject("exec")
        # 暂时使用这种方式关闭，后续注册插件统一判断
        if not self.enbale():
            return

        if not commonUtils.isEmpty(mapObject):
            for index in mapObject:
                obj = mapObject[index]
                event = obj.get("event")
                execCode = obj.get("execCode")
                condition = obj.get("condition")
                conditionExecCode = obj.get("conditionExecCode")
                cmd = obj.get("cmd")
                prop = obj.get("property")
                cmdList = self.cmdMap.get(event)
                if commonUtils.isEmpty(cmdList):
                    cmdList = []
                    self.cmdMap[event] = cmdList
                cmdList.append(
                    {"condition": condition, "execCode": execCode, "conditionExecCode": conditionExecCode, "cmd": cmd,
                     "property": prop})
    def executeCmd(self, eventName, eventData, tempVarData: dict = None):
        cmdList = self.cmdMap.get(eventName)
        if commonUtils.isEmpty(cmdList):
            return
        for cmdObject in cmdList:
            condition = cmdObject.get("condition")
            conditionExecCode = cmdObject.get("conditionExecCode")
            execCode = cmdObject.get("execCode")
            # 随机选一个
            cmdAll: str = str(cmdObject.get("cmd"))
            cmd = None
            if not commonUtils.isEmpty(cmdAll):
                arr = cmdAll.split("---")
                index = commonUtils.getRandom(len(arr), -1)
                cmd = arr[index]
            # 随机选一个
            propAll = cmdObject.get("property")
            prop = None
            if not commonUtils.isEmpty(propAll):
                arr = propAll.split("---")
                index = commonUtils.getRandom(len(arr), -1)
                prop = arr[index]
            self.globalData = self.getGlobalData()
            allVarData: dict = self.getAllVarData(tempVarData)
            allVarData.update(eventData)
            allVarData["gameStartTime"] = time.time() - self.globalData["_gameStartTimestamp"]
            allVarData["roundStartTime"] = time.time() - self.globalData["_roundStartTimestamp"]
            if commonUtils.isBlank(cmd) and commonUtils.isBlank(prop):
                continue
            if not commonUtils.isBlank(execCode):
                try:
                    exec(execCode, allVarData, self.globalData)
                except Exception as e:
                    logger.writeException()
                    logger.d(self.TAG,
                             "eval eventName=" + eventName + "; execCode=(" + str(execCode) + ");执行错误")

            if commonUtils.isBlank(condition) or self.execCondition(eventName, condition, eventData, allVarData):
                if not commonUtils.isBlank(conditionExecCode):
                    try:
                        # eval值负责表达式，没有赋值功能
                        exec(conditionExecCode, allVarData, self.globalData)
                    except Exception as e:
                        logger.writeException()
                        logger.d(self.TAG,
                                 "eval eventName=" + eventName + "; evalCode=(" + str(conditionExecCode) + ");执行错误")
                cmd = self.replaceAllVar(cmd, allVarData)
                prop = self.replaceAllVar(prop, allVarData)
                # add cmd
                rconCmdList = commonUtils.split(cmd, "|")
                if rconCmdList is None:
                    rconCmdList = []
                # add prop
                propList = commonUtils.split(prop, "|")
                for p in propList:
                    rconCmdList.append("gamemodeproperty " + p)
                # each execute
                for rconCmd in rconCmdList:
                    if commonUtils.isEmpty(rconCmd):
                        continue
                    rconCmd = str(rconCmd).strip()
                    if len(rconCmd) < 4:
                        continue
                    self.helper.requester.requestRconCmd(rconCmd)
                    logger.d(self.TAG, "requestRconCmd eventName=" + eventName + "; rconCmd=" + rconCmd)

    def replaceAllVar(self, data: str, tempVarData: dict = None):
        if data is None:
            return data
        globalData: dict = self.getGlobalData()
        if tempVarData is None:
            tempVarData = globalData.copy()
        else:
            tempVarData.update(globalData)
        finalData = data
        for key in tempVarData.keys():
            finalData = finalData.replace(key, str(tempVarData[key]))
        return finalData

    def execCondition(self, eventName, params, eventData, allVarData: dict = None):
        result = False
        try:
            # eval值负责表达式，没有赋值功能
            result = eval(params, allVarData, eventData)
        except Exception as e:
            logger.writeException()
            logger.e(self.TAG, "事件" + eventName + "后面的值" + str(params) + "有误，你需要重新写条件")
        logger.logMore(self.TAG, "eval eventName=" + eventName + "; params=(" + str(params) + "); result=" + str(result))
        return result

    def getAllVarData(self, tempVarData: dict = None):
        globalData: dict = self.getGlobalData()
        if tempVarData is None:
            tempVarData = globalData.copy()
        else:
            tempVarData.update(globalData)
        return tempVarData

    def clientSynthAdd(self, log, data):
        if not self.enbale():
            return
        self.executeCmd("clientAdd", data)

    def clientSynthDel(self, log, data):
        if not self.enbale():
            return
        self.executeCmd("clientDel", data)

    def roundStateChange(self, log, data):
        if not self.enbale():
            return
        self.updateRoundData(data)
        if data.get("isStart"):
            self.executeCmd("roundStart", data)
        else:
            self.executeCmd("roundEnd", data)

    def updateRoundData(self, data):
        if data is None:
            return
        if data.get("isStart"):
            self.resetRoundData()
            self.globalsData["roundIndex"] = data.get("roundIndex")
        else:
            gameDataCenterInstance.replaceVarByRoundCountDict(self.globalsData)

    def mapChange(self, log, data):
        if not self.enbale():
            return
        self.executeCmd("mapChange", data)

    def travel(self, log, data):
        if not self.enbale():
            return
        self.executeCmd("travel", data)

    def gameStart(self, log, data):
        if not self.enbale():
            return
        self.resetGameData()
        self.executeCmd("gameStart", data)

    def gameEnd(self, log, data):
        if not self.enbale():
            return
        self.executeCmd("gameEnd", data)
        self.resetGameData()

    def resetGameData(self):
        self.gameSecond = 0
        self.globalsData = {"playerCount": -1,
                            "AIDeadCountForGame": 0,
                            "AIDeadCountForCurrRound": 0,
                            "AIDeadCountForCurrPoint": 0,
                            "PlayerDeadCountForGame": 0,
                            "PlayerDeadCountForCurrRound": 0,
                            "PlayerDeadCountForCurrPoint": 0,
                            "roundIndex": 1,
                            "_gameStartTimestamp": time.time(),
                            }
        self.resetRoundData()

    def resetRoundData(self):
        self.roundSecond = 0
        self.globalsData["point"] = "A"
        self.globalsData["takePointAllPlayerName"] = ""
        self.globalsData["_roundStartTimestamp"] = time.time()

    def takeObject(self, log, data):
        if not self.enbale():
            return
        if data is None:
            return
        point = data.get("point")
        if point is None:
            return
        pointStr = gameDataCenterInstance.pointMap.get(str(point))
        if commonUtils.isEmpty(pointStr):
            return
        self.globalsData["point"] = pointStr
        players = data.get("players")
        playersNameList = []
        isPlayerTakeObject = False
        if not commonUtils.isEmpty(players):
            for player in players:
                playerGUID = player.get("playerGUID")
                if playerGUID is not None and len(playerGUID) > 14:
                    isPlayerTakeObject = True
                if not commonUtils.isEmpty(playerGUID):
                    playersNameList.append(str(player.get("playerName")))
        if not commonUtils.isEmpty(playersNameList):
            playersNameStr = ",".join(playersNameList)
            self.globalsData["takePointAllPlayerName"] = playersNameStr
        data["isPlayerTakeObject"] = isPlayerTakeObject
        self.executeCmd("takeObject", data)

    def killed(self, log, data):
        if not self.enbale():
            return
        tempVarData = {}
        if self.updateKillData(data, tempVarData):
            self.executeCmd("killed", data, tempVarData)

    def updateKillData(self, data, tempVarData: dict = None):
        if data is None:
            return False
        died = data.get("died")
        if died is None or len(died) == 0 or died[0] is None:
            return False
        uid = died[0].get("playerGUID")
        if uid is None or len(uid) < 15:
            self.globalsData["AIDeadCountForGame"] += 1
            self.globalsData["AIDeadCountForCurrRound"] += 1
            self.globalsData["AIDeadCountForCurrPoint"] += 1
        else:
            self.globalsData["PlayerDeadCountForGame"] += 1
            self.globalsData["PlayerDeadCountForCurrRound"] += 1
            self.globalsData["PlayerDeadCountForCurrPoint"] += 1
        # 更新变量
        killerList = data.get("killer")
        deadList = data.get("died")
        weapon = data.get("weapon")
        if weapon is None:
            weapon = ""
        if commonUtils.isEmpty(killerList) or commonUtils.isEmpty(deadList):
            return False
        killer = killerList[0]
        dead = deadList[0]
        killerUid = killer.get("playerGUID")
        killerName = killer.get("playerName")
        deadUid = dead.get("playerGUID")
        deadName = dead.get("playerName")
        if commonUtils.isEmpty(killerUid) or commonUtils.isEmpty(deadUid) or commonUtils.isEmpty(
                killerName) or commonUtils.isEmpty(deadName):
            return False
        if weapon is None:
            weapon = ""
        weapon = commonUtils.getWeaponName(weapon)
        tempVarData["killerName"] = killerName
        tempVarData["deadName"] = deadName
        tempVarData["killerUid"] = killerUid
        tempVarData["weapon"] = weapon
        tempVarData["deadIsPlayer"] = len(deadUid) > 14
        tempVarData["killerIsPlayer"] = len(killerUid) > 14
        player = gameDataCenterInstance.playerGetOrCreate(killerUid)
        tempVarData["killerTkCount"] = player.tkCount if player is not None else 0
        return True

    def chat(self, log, data):
        if not self.enbale():
            return
        self.executeCmd("chat", data)

    def timer(self, data):
        if not self.enbale():
            return
        if self.gameSecond % 10 == 0:
            data["gameSecond"] = self.gameSecond
            data["roundSecond"] = self.roundSecond
            self.executeCmd("timer", data)
        self.gameSecond += 1
        self.roundSecond += 1

    def getGlobalData(self):
        self.globalsData["playerCount"] = playerDataCenterInstance.getPlayerCount()
        return self.globalsData
