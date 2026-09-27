# !/usr/bin/env python
# -*- coding: utf-8 -*
from lib.game_data_center import gameDataCenterInstance
from lib.tools.plugin_helper import PluginHelper
from lib.event_callback import EventCallback


class SyncDataPlugin(EventCallback):
    helper = PluginHelper()
    lastJoinUid = None
    lastQuitUid = None
    def enbale(self):
        return True

    def init(self, requester):
        self.helper.init(requester)
        gameDataCenterInstance.init(self.helper.serverId, self.helper.serverKey)

    def clientSynthAdd(self, log, data):
        gameDataCenterInstance.clientSynthAdd(data)

    def clientDel(self, log, data):
        gameDataCenterInstance.clientDel(data)

    def roundStateChange(self, log, data):
        gameDataCenterInstance.roundStateChange(data)

    def mapChange(self, log, data):
        gameDataCenterInstance.mapChange(data)
    def travel(self, log, data):
        gameDataCenterInstance.travel(data)

    def gameStart(self, log, data):
        gameDataCenterInstance.gameStart(data)

    def gameEnd(self, log, data):
        gameDataCenterInstance.gameEnd(data)

    def killed(self, log, data):
        gameDataCenterInstance.killed(data)

    def chat(self, log, data):
        gameDataCenterInstance.chat(data)

    def takeObject(self, log, data):
        gameDataCenterInstance.takeObject(data)
