# !/usr/bin/env python
# -*- coding: utf-8 -*
from lib.event_callback import EventCallback
from lib.tools.common_utils import commonUtils
from lib.tools.logger import logger

class EventDispatcher:
    TAG = "EventDispatcher"
    callbackList = []
    requester = None
    playerMap = {}
    eachCallback = None
    # windows日志回合开始和结束拿不到第几回合数据，自己累加
    roundIndex = 0

    def register(self, callback):
        self.callbackList.append(callback)

    def init(self, requester):
        self.requester = requester
        self.eachCallback = EventCallback()

        if self.callbackList is not None:
            for callback in self.callbackList:
                callback.init(requester)
            self.eachCallback.setCallbackList(self.callbackList)

    def dispatch(self, jsonObject):
        if jsonObject is None:
            return
        cb = self.eachCallback
        log = jsonObject.get("log")
        eventType = jsonObject.get("event_type")
        if eventType == "timer":
            cb.timer(jsonObject)
        elif eventType == "restart":
            cb.restart(log, self.parseRestart(log, jsonObject))
        elif eventType == "mapChange":
            cb.mapChange(log, self.parseMapChange(log, jsonObject))
        elif eventType == "gameStart":
            self.roundIndex = 0
            cb.gameStart(log, self.parseGameStart(log, jsonObject))
        elif eventType == "gameEnd":
            cb.gameEnd(log, self.parseGameEnd(log, jsonObject))
            self.roundIndex = 0
        elif eventType == "roundStateChange":
            result = self.parseRoundStateChange(log, jsonObject)
            cb.roundStateChange(log, result)
            if result is not None and result.get("isStart") == True:
                cb.roundStart(log, self.parseRoundStart(log, jsonObject))
            else:
                cb.roundEnd(log, self.parseRoundEnd(log, jsonObject))
        elif eventType == "takeObject":
            cb.takeObject(log, self.parseTakeObject(log, jsonObject))
        elif eventType == "killed":
            cb.killed(log, self.parseKilled(log, jsonObject))
        elif eventType == "captured":
            cb.captured(log, self.parseCaptured(log, jsonObject))
        elif eventType == "shutdown":
            cb.shutdown(log, self.parseShutdown(log, jsonObject))
        elif eventType == "clientSynthDel":
            cb.clientSynthDel(log, self.parseClientSynthDel(log, jsonObject))
        elif eventType == "clientSynthAdd":
            cb.clientSynthAdd(log, self.parseClientSynthAdd(log, jsonObject))
        elif eventType == "chat":
            cb.chat(log, self.parseChat(log, jsonObject))
        elif eventType == "sigterm":
            cb.sigterm(log, self.parseSigterm(log, jsonObject))
        elif eventType == "winLose":
            cb.winLose(log, self.parseWinLose(log, jsonObject))
        elif eventType == "travel":
            cb.travel(log, self.parseTravel(log, jsonObject))
        elif eventType == "sessionLog":
            cb.sessionLog(log, self.parseSessionLog(log, jsonObject))
        elif eventType == "objectSynth":
            cb.objectSynth(log, self.parseObjectSynth(log, jsonObject))
        elif eventType == "everyLog":
            cb.everyLog(log, jsonObject)
        elif eventType == "serverError":
            cb.serverError(None)
        elif eventType == "python_exception":
            cb.pythonException(log, None)
        cb.event(jsonObject)

    def processResult(self, log, data, result):
        data["parsed"] = result
        logger.logMore(self.TAG, "event:", data)


    def parseRestart(self, log, data):
        self.processResult(log, data, None)
        return data

    def parseMapChange(self, log, data):
        index = log.rfind("/")
        if index > 0:
            data["mapName"] = str(log[index + 1:]).strip()
        self.processResult(log, data, None)
        return data

    def parseGameStart(self, log, data):
        self.processResult(log, data, None)
        return data

    def parseGameEnd(self, log, data):
        self.processResult(log, data, None)
        return data

    def parseRoundStart(self, log, data):
        self.processResult(log, data, None)
        return data

    def parseRoundEnd(self, log, data):
        self.processResult(log, data, None)
        return data

    def parseRoundStateChange(self, log, data):
        result = None
        # 之前适配windows，现在开启e
        # isStart = data.get("isStart")
        # if isStart is not None:
        #     if isStart:
        #         self.roundIndex += 1
        #         roundIndex=self.roundIndex
        #         result = {"roundIndex": int(str(roundIndex)), "isStart": True}
        #     else:
        #         roundIndex = self.roundIndex
        #         result = {"roundIndex": int(str(roundIndex)), "isStart": False}
        #         reasonIndex = log.find("reason:")
        #         if reasonIndex is not None:
        #             result["reason"] = log[reasonIndex + 7:log.find(")")].strip()
        #
        # else:
        roundIndex = commonUtils.getMid(log, "Round", "started")
        if roundIndex is not None:
            result = {"roundIndex": int(str(roundIndex)), "isStart": True}
        else:
            roundIndex = commonUtils.getMid(log, "Round", "Over")
            if roundIndex is not None:
                result = {"roundIndex": int(str(roundIndex)), "isStart": False}
            # 解析回合结束原因，例如: Round 2 Over: Team 0 won (win reason: Elimination)
            # 注意 str.find 找不到返回 -1(而非 None)，result 也可能为 None，需要都判空避免崩溃
            reasonIndex = log.find("reason:")
            if reasonIndex >= 0 and result is not None:
                endIndex = log.find(")", reasonIndex)
                if endIndex > reasonIndex:
                    result["reason"] = log[reasonIndex + len("reason:"):endIndex].strip()
        self.processResult(log, data, result)
        return result

    def _parsePlayer(self, playerStr):
        if playerStr is None:
            return None
        playerName = commonUtils.getLeft(playerStr, "[")
        playerUid = commonUtils.getMid(playerStr, "[", "]")
        playerTeam = None
        if playerUid is not None and "," in playerUid:
            playerTeam = commonUtils.getRight(playerUid, ",")
            playerUid = commonUtils.getLeft(playerUid, ",")

        if playerName is not None and playerUid is not None:
            return {"playerName": playerName, "playerGUID": playerUid, "playerTeam": playerTeam}
        return None

    def _parsePlayersArray(self, arrayStr):
        if arrayStr is None:
            return None
        playerStrArray = []
        if "] +" in arrayStr:
            playerStrArray = arrayStr.split("] +")
        elif "], " in arrayStr:
            playerStrArray = arrayStr.split("], ")
        else:
            playerStrArray.append(arrayStr)
        playerArray = []
        for playerStr in playerStrArray:
            if "]" not in playerStr:
                playerStr = playerStr + "]"
            playerItem = self._parsePlayer(playerStr)
            playerArray.append(playerItem)
        return playerArray

    def parseTakeObject(self, log, data):
        destroyedStr = " was destroyed for team "
        capturedStr = " was captured for team "
        point = None
        rightPlayersStr = None
        if destroyedStr in log:
            point = commonUtils.getMid(log, "Display: Objective ", " owned by team ")
            rightPlayersStr = commonUtils.getRight(log, destroyedStr)
        if capturedStr in log:
            point = commonUtils.getMid(log, "Display: Objective ", " was captured for team ")
            rightPlayersStr = commonUtils.getRight(log, " was captured for team ")
        if rightPlayersStr is None:
            return None
        arrayStr = commonUtils.getRight(rightPlayersStr, " by ")
        result = {}
        result["point"] = point
        result["players"] = self._parsePlayersArray(arrayStr)
        self.processResult(log, data, result)
        return result

    def parseKilled(self, log, data):
        result = {}
        killerStr = commonUtils.getMid(log, " Display:", " killed ")
        result["killer"] = self._parsePlayersArray(killerStr)

        diedStr = commonUtils.getMid(log, " killed ", " with ")
        result["died"] = self._parsePlayersArray(diedStr)

        weapon = commonUtils.getRight(log, " with ")
        if "_C_" in weapon:
            weapon = commonUtils.getLeft(weapon, "_C_")
        else:
            if "\n" in weapon:
                weapon = commonUtils.getLeft(weapon, "\n")
        result["weapon"] = weapon
        self.processResult(log, data, result)
        return result

    def parseCaptured(self, log, data):
        self.processResult(log, data, None)
        return data

    def parseShutdown(self, log, data):
        self.processResult(log, data, None)
        return data

    def parseClientSynthDel(self, log, data):
        result = {}
        result["playerName"] = data.get("playerName")
        result["playerGUID"] = data.get("playerGUID")
        result["playerIP"] = data.get("playerIP")
        self.playerMap[result["playerGUID"]] = result
        self.processResult(log, data, result)
        return result

    def parseClientSynthAdd(self, log, data):
        result = {}
        result["playerName"] = data.get("playerName")
        result["playerGUID"] = data.get("playerGUID")
        result["playerIP"] = data.get("playerIP")
        self.playerMap[result["playerGUID"]] = result
        self.processResult(log, data, result)
        return result

    def parseChat(self, log, data):
        content = commonUtils.getRight(log, " Chat:")
        playerName = commonUtils.getMid(log, " Display:", "(")
        playerUid = commonUtils.getMid(log, "(", ")")
        result = {"playerName": playerName, "playerGUID": playerUid, "content": content}
        self.processResult(log, data, result)
        return result

    def parseSigterm(self, log, data):
        self.processResult(log, data, None)
        return data

    def parseWinLose(self, log, data):
        result = {}
        # humanSide：-1=unknown or PvP, 0=Security, 1=Insurgents
        humanSide = data.get("humanSide")
        if humanSide == 1:
            result["mapSide"] = "Checkpoint_Insurgents"
            # 地图是叛军
            if "Team 0" in log:
                result["mode"] = "PVE"
                result["result"] = "lose"
        elif humanSide == 0:
            result["mapSide"] = "Checkpoint_Security"
            # 地图是政府军
            result["mode"] = "PVE"
            if "Team 0" not in log:
                result["result"] = "win"
        else:
            result["mode"] = "PVP"
        reason = commonUtils.getMid(log, "(win reason:", ")")
        if reason is not None:
            result["reason"] = reason
        self.processResult(log, data, result)
        return result

    def parseTravel(self, log, data):
        mapUrl = log[log.find("Travel:") + 7:].strip()
        camp = 1 if mapUrl.find("Checkpoint_Security") > 0 else 2
        temp = mapUrl[mapUrl.find("Scenario_") + 9:]
        mapName = temp[0:temp.find("_")]
        data["mapUrl"] = mapUrl
        data["camp"] = camp
        data["mapName"] = mapName
        self.processResult(log, data, None)
        return data

    def parseSessionLog(self, log, data):
        self.processResult(log, data, None)
        return data

    def parseObjectSynth(self, log, data):
        self.processResult(log, data, None)
        return data

    def parseEveryLog(self, log, data):
        self.processResult(log, data, None)
        return data


eventDispatcher = EventDispatcher()
