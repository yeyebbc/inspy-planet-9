# !/usr/bin/env python
# -*- coding: utf-8 -*
from lib.game_data_center import gameDataCenterInstance, PlayerData
from lib.tools.common_utils import commonUtils
from lib.tools.config_reader import configReader
from lib.tools.plugin_helper import PluginHelper
from plugins.map_vote_plugin import MapVotePlugin

from lib.event_callback import EventCallback


class PitacnomicPlugin(EventCallback):
    helper = PluginHelper()
    cmdMap = {}
    register = None

    def __init__(self, register):
        self.register = register

    def enbale(self):
        return configReader.getPitacnomicEnable()

    def init(self, requester):
        self.helper.init(requester)
        arr = configReader.getPitacnomicArray()
        if arr is not None and len(arr) > 0:
            for a in arr:
                items = a.split("::")
                cmd = items[0]
                text = items[1]
                self.cmdMap[cmd] = text

    def chat(self, log, data):
        if not self.enbale():
            return
        if data is None:
            return
        content: str = data.get("content")
        if commonUtils.isBlank(content):
            return
        text = self.cmdMap.get(content)
        playerGUID = data.get("playerGUID")
        playerName = data.get("playerName")
        if playerName is None:
            playerName = ""
        if not commonUtils.isBlank(text) and self.isAllow(content, playerGUID):
            self.helper.requester.apiSay("[" + playerName + "]" + text)

    def isAllow(self, cmd, playerGUID):
        votePlugin: MapVotePlugin = self.register.getPlugin(MapVotePlugin)
        if votePlugin is not None and votePlugin.isStartVote:
            return False
        livePlayersOnly = configReader.getPitacnomicLivePlayersOnly()
        # 未配置 livePlayersOnly（空）表示不做“存活”限制，所有指令一律放行
        if commonUtils.isBlank(livePlayersOnly):
            return True
        player: PlayerData = gameDataCenterInstance.playerDict.get(playerGUID)
        arr = livePlayersOnly.split(" ")
        # 仅当指令在“限存活指令”列表里，且玩家死亡(或不在场)时才拦截
        if cmd in arr and (player is None or player.isCurrentAlive != 1):
            return False
        return True
