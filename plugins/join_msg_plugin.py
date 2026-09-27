# !/usr/bin/env python
# -*- coding: utf-8 -*
import json
from lib.player_data_center import playerDataCenterInstance
from module.title_module import titleModule
from lib.tools.common_utils import commonUtils
from lib.tools.config_reader import configReader
from lib.tools.logger import logger
from lib.tools.net_utils import netUtils
from lib.tools.plugin_helper import PluginHelper
from lib.event_callback import EventCallback


class JoinMsgPlugin(EventCallback):
    TAG = "JoinMsgPlugin"
    helper = PluginHelper()

    def enbale(self):
        return True

    def __init__(self):
        self.lastJoinUid = None
        self.lastQuitUid = None

    def init(self, requester):
        self.helper.init(requester)

    def sendMsg(self, data, isJoin):
        playerGUID = data.get("playerGUID")
        if isJoin == 1 and self.lastJoinUid is not None and self.lastJoinUid == playerGUID:
            return
        if isJoin == 1:
            self.lastJoinUid = playerGUID
            self.lastQuitUid = None
        if isJoin == 0 and self.lastQuitUid is not None and self.lastQuitUid == playerGUID:
            return
        if isJoin == 0:
            if commonUtils.isEmpty(playerDataCenterInstance.getPlayerNameByUid(playerGUID)):
                logger.d(self.TAG, "不是此服务器玩家:" + str(data))
                return
            self.lastQuitUid = playerGUID
            self.lastJoinUid = None
        # playerName = data.get("playerName").encode('utf-8')
        playerName = data.get("playerName")
        if playerGUID is None:
            return

        msg = ""
        if isJoin == 0:
            msg = configReader.getDisconnectedMsg()
            msg = self.replaceVar(msg, playerName, "", "", "")
        else:
            ipLocal = self.getLocal(data.get("playerIP"))
            params = {"playerGUID": playerGUID,
                      "playerName": playerName,
                      "playerNameFanTi": playerName,
                      "serverId": str(self.helper.serverId),
                      "isJoin": str(isJoin)}
            data = None
            try:
                data = netUtils.httpGet("player_join_msg_v2.php", params)
            except Exception as e:
                logger.writeException()
            if data is not None:
                if "data" in data:
                    d = data["data"]
                    rankIndex = d.get("rankIndex")
                    joinName = titleModule.getTitleName(playerGUID, 1, d)
                    if commonUtils.isEmpty(rankIndex):
                        msg = configReader.getFirstJoinMsg()
                    else:
                        msg = configReader.getConnectedMsg()
                    msg = self.replaceVar(msg, playerName, joinName, ipLocal, rankIndex)
            else:
                print(json.dumps(data))

            if commonUtils.isEmpty(msg):
                msg = configReader.getFirstJoinMsg()
                msg = self.replaceVar(msg, playerName, "", ipLocal, "")

        self.helper.requester.apiSay(msg)

    def getLocal(self, playerIP):
        ipLocal = ""
        if configReader.getShowPlayerLocal() == 1 and not commonUtils.isEmpty(playerIP):
            try:
                localData = netUtils.getLocalByIp(playerIP)
                adcode = localData.get("adcode")
                ipLocal = adcode.get("n")
                localArr = str(ipLocal).split("-")
                if len(localArr) == 2:
                    if localArr[0] == localArr[1]:
                        ipLocal = localArr[0]
            except Exception as e:
                logger.writeException()
        if not commonUtils.isEmpty(ipLocal):
            ipLocal = "[" + ipLocal + "]"
        return ipLocal

    def replaceVar(self, msg, playerName, joinName, ipLocal, rankIndex):
        if commonUtils.isEmpty(msg):
            msg = ""
        if commonUtils.isEmpty(playerName):
            playerName = ""
        if commonUtils.isEmpty(joinName):
            joinName = ""
        if commonUtils.isEmpty(rankIndex):
            rankIndex = ""
        return msg.replace("$name", playerName) \
            .replace("$title", joinName + ipLocal).replace("$rank", str(rankIndex))

    def clientSynthAdd(self, log, data):
        logger.d(self.TAG, "clientSynthAdd:" + str(data))
        self.sendMsg(data, 1)

    def clientSynthDel(self, log, data):
        logger.d(self.TAG, "clientSynthDel:" + str(data))
        self.sendMsg(data, 0)

    def roundStateChange(self, log, data):
        logger.d(self.TAG, "roundStateChange 接收" + str(data))
