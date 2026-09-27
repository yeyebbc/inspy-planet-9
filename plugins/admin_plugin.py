# !/usr/bin/env python
# -*- coding: utf-8 -*
from lib.game_data_center import gameDataCenterInstance, PlayerData
from lib.player_data_center import Player
from lib.tools.common_utils import commonUtils
from lib.tools.config_reader import configReader
from lib.tools.plugin_helper import PluginHelper
from plugins.map_vote_plugin import MapVotePlugin
from lib.event_callback import EventCallback


class AdminPlugin(EventCallback):
    helper = PluginHelper()
    register = None
    # key=uid,value=cmdList
    adminCmdsMap = {}
    arrayCount = 0

    def __init__(self, register):
        self.register = register
        self.parseAdminFileList()

    def parseAdminFileList(self):
        groupguidFileList = configReader.getGroupguidFileList()
        groupCmdList = configReader.getGroupcmdsList()
        if not commonUtils.isEmpty(groupguidFileList):
            for i in range(len(groupguidFileList)):

                # 解析adminCmdsList
                adminCmdsList = []
                if groupCmdList is not None and i < len(groupCmdList):
                    adminCmdsList = groupCmdList[i].split(" ")

                text = commonUtils.readFile(groupguidFileList[i])
                if not commonUtils.isEmpty(text):
                    text = text.replace("\r", "")
                    arr = text.split("\n")
                    for line in arr:
                        p1 = line.find(";")
                        if p1 >= 0:
                            uid = line[:p1].strip()
                        else:
                            uid = line.strip()
                        if not commonUtils.isBlank(uid):
                            self.adminCmdsMap[uid] = adminCmdsList

    def enbale(self):
        return configReader.getPicladminEnable()

    def init(self, requester):
        self.requester = requester
        self.helper.init(requester)

    def chat(self, log, data):
        if not self.enbale():
            return
        if data is None:
            return
        content: str = data.get("content")
        if commonUtils.isBlank(content):
            return
        playerGUID = data.get("playerGUID")
        playerName = data.get("playerName")
        if playerName is None:
            playerName = ""

        arr = content.split(" ")
        cmd = arr[0]
        if cmd == "bf" and len(arr) == 2 and arr[1].isdigit():
            botCount = int(arr[1])
            cmdList = self.adminCmdsMap.get(playerGUID)
            if cmdList is None or "botfixed" not in cmdList:
                self.helper.requester.apiSay("[" + playerName + "] is not an admin")
            else:
                self.requester.requestRconCmd("gamemodeproperty minimumenemies " + str(int(botCount / 2)))
                self.requester.requestRconCmd("gamemodeproperty maximumenemies " + str(int(botCount / 2)))
                self.requester.requestRconCmd("gamemodeproperty soloenemies " + str(int(botCount / 2)))
                self.helper.requester.apiSay("Admin [" + playerName + "] executed command: botfixed")
        elif cmd == "bs" and len(arr) == 3 and arr[1].isdigit() and arr[2].isdigit():
            botMin = int(arr[1])
            botMax = int(arr[2])
            cmdList = self.adminCmdsMap.get(playerGUID)
            if cmdList is None or "botscaled" not in cmdList:
                self.helper.requester.apiSay("[" + playerName + "] is not an admin")
            else:
                self.requester.requestRconCmd("gamemodeproperty minimumenemies " + str(int(botMin / 2)))
                self.requester.requestRconCmd("gamemodeproperty maximumenemies " + str(int(botMax / 2)))
                self.helper.requester.apiSay("Admin [" + playerName + "] executed command: botscaled")
        elif cmd == "bd" and len(arr) == 2:
            #
            cmdList = self.adminCmdsMap.get(playerGUID)
            if cmdList is None or "botdifficulty" not in cmdList:
                self.helper.requester.apiSay("[" + playerName + "] is not an admin")
            else:
                try:
                    botDifficultyF = float(arr[1])
                    self.requester.requestRconCmd("gamemodeproperty aidifficulty " + str(botDifficultyF))
                    self.helper.requester.apiSay(
                        "Admin [" + playerName + "] executed command: botdifficulty=" + str(botDifficultyF))
                except (ValueError, TypeError):
                    pass
        elif cmd == "version":
            cmdList = self.adminCmdsMap.get(playerGUID)
            if cmdList is None or "version" not in cmdList:
                self.helper.requester.apiSay("[" + playerName + "] is not an admin")
            else:
                self.requester.apiSay("插件版本:" + commonUtils.getVersion())
        elif cmd == "help":
            cmdList = self.adminCmdsMap.get(playerGUID)
            if cmdList is None or "help" not in cmdList:
                self.helper.requester.apiSay("[" + playerName + "] is not an admin")
            else:
                self.requester.apiSay("[帮助]支持命令：version,bf,bs,bd")

    def isAllow(self, cmd, playerGUID):
        votePlugin: MapVotePlugin = self.register.getPlugin(MapVotePlugin)
        if votePlugin is not None and votePlugin.isStartVote:
            return False
        livePlayersOnly = configReader.getPitacnomicLivePlayersOnly()
        if not commonUtils.isBlank(livePlayersOnly):
            player: PlayerData = gameDataCenterInstance.playerDict.get(playerGUID)
            arr = livePlayersOnly.split(" ")
            if cmd in arr and (player is None or player.isCurrentAlive != 1):
                return False
            else:
                return True
