# !/usr/bin/env python
# -*- coding: utf-8 -*
from lib.game_data_center import gameDataCenterInstance
from lib.event_callback import EventCallback
from lib.tools.common_utils import commonUtils
from lib.tools.config_reader import configReader
from lib.tools.plugin_helper import PluginHelper


class GameEventPlugin(EventCallback):
    def __init__(self):
        self.helper = PluginHelper()
        self.roundStartTip = None
        self.roundEndTip = None
        self.gameStartTip = None
        self.gameEndWinTip = None
        self.gameEndLoseTip = None
        self.gameEndTip = None
        self.killTip = None
        self.takeObjectTip = None

    def enbale(self):
        return configReader.getGameEventPluginState()

    def init(self, requester):
        if not self.enbale():
            return
        self.helper.init(requester)
        self.roundStartTip = configReader.getGameEventRoundStart()
        self.roundEndTip = configReader.getGameEventRoundEnd()
        self.gameStartTip = configReader.getGameEventGameStart()
        self.gameEndWinTip = configReader.getGameEventGameEndWin()
        self.gameEndLoseTip = configReader.getGameEventGameEndLose()
        self.gameEndTip = configReader.getGameEventGameEnd()
        self.killTip = configReader.getGameEventKill()
        self.takeObjectTip = configReader.getGameEventTakeObject()

    def roundStateChange(self, log, data):
        if not self.enbale():
            return
        if data is None:
            return
        # roundIndex = data.get("roundIndex")
        ret = None
        if data.get("isStart"):
            if not commonUtils.isEmpty(self.roundStartTip):
                ret = gameDataCenterInstance.replaceVarByRoundBaseInfo(self.roundStartTip)
        else:
            if not commonUtils.isEmpty(self.roundEndTip):
                ret = gameDataCenterInstance.replaceVarByRoundCountInfo(self.roundEndTip)
        if not commonUtils.isEmpty(ret):
            self.helper.requester.apiSay(ret)

    def gameStart(self, log, data):
        if not self.enbale():
            return
        if not commonUtils.isEmpty(self.gameStartTip):
            self.helper.requester.apiSay(self.gameStartTip)

    def gameEnd(self, log, data):
        if not self.enbale():
            return
        if not commonUtils.isEmpty(self.gameEndTip):
            self.helper.requester.apiSay(self.gameEndTip)

    def winLose(self, log, data):
        if not self.enbale():
            return
        if data is None:
            return
        result = data.get("result")
        if commonUtils.isEmpty(result):
            return
        if result == "win":
            if not commonUtils.isEmpty(self.gameEndWinTip):
                self.helper.requester.apiSay(self.gameEndWinTip)
        else:
            if not commonUtils.isEmpty(self.gameEndLoseTip):
                self.helper.requester.apiSay(self.gameEndLoseTip)

    def killed(self, log, data):
        if not self.enbale():
            return
        if data is None:
            return
        if commonUtils.isEmpty(self.killTip):
            return
        killerList = data.get("killer")
        deadList = data.get("died")
        weapon = data.get("weapon")
        if weapon is None:
            weapon = ""
        if commonUtils.isEmpty(killerList) or commonUtils.isEmpty(deadList):
            return
        killer = killerList[0]
        dead = deadList[0]
        killerUid = killer.get("playerGUID")
        killerName = killer.get("playerName")
        deadUid = dead.get("playerGUID")
        deadName = dead.get("playerName")
        if commonUtils.isEmpty(killerUid) or commonUtils.isEmpty(deadUid) or commonUtils.isEmpty(
                killerName) or commonUtils.isEmpty(deadName):
            return
        if weapon is None:
            weapon = ""
        weapon = commonUtils.getWeaponName(weapon)
        ret = self.killTip.replace("$killerName", killerName).replace("$deadName", deadName).replace("$weapon", weapon)
        self.helper.requester.apiSay(ret)

    def takeObject(self, log, data):
        if not self.enbale():
            return
        if data is None:
            return
        if commonUtils.isEmpty(self.takeObjectTip):
            return
        point = data.get("point")
        if point is None:
            return
        pointStr = gameDataCenterInstance.pointMap.get(str(point))
        if commonUtils.isEmpty(pointStr):
            return
        ret = self.takeObjectTip.replace("$point", pointStr)
        players = data.get("players")
        playersNameList = []
        if not commonUtils.isEmpty(players):
            for player in players:
                if not commonUtils.isEmpty(player.get("playerGUID")):
                    playersNameList.append(str(player.get("playerName")))
        if not commonUtils.isEmpty(playersNameList):
            playersNameStr = ",".join(playersNameList)
            ret = ret.replace("$allPlayerName", playersNameStr)
            self.helper.requester.apiSay(ret)
