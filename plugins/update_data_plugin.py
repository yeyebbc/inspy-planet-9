# !/usr/bin/env python
# -*- coding: utf-8 -*
from lib.tools.common_utils import commonUtils
from lib.tools.config_reader import configReader
from lib.tools.net_utils import netUtils
from lib.event_callback import EventCallback


class UpadteDataPlugin(EventCallback):
    def enbale(self):
        return True

    def init(self, requester):
        self.serverId = configReader.getServerId()

    def roundStateChange(self, log, data):
        self.updateData()

    def updateData(self):
        if commonUtils.isOnline():
            params = {"type": "update_temp_table"}
            data = netUtils.httpGet("update_every_day.php", params)
