# !/usr/bin/env python
# -*- coding: utf-8 -*
from lib.tools.common_utils import commonUtils
from lib.tools.config_reader import configReader
from lib.tools.plugin_helper import PluginHelper
from lib.event_callback import EventCallback


class PiProtectPlugin(EventCallback):
    helper = PluginHelper()
    register = None
    lastIndex = 0

    def __init__(self, register):
        self.register = register

    def enbale(self):
        return configReader.isProtectPluginEnable()

    def init(self, requester):
        self.requester = requester
        self.helper.init(requester)

    def everyLog(self, log, data):
        if not self.enbale():
            return
        self.fixMapVote(log)

    def fixMapVote(self, log):
        if not configReader.isProtectEnableMapVoteWorkaround():
            return
        if "mapcycle map vote" not in log:
            return
        print("everyLog:" + log)
        print("检测到投票bug，正在自动切换地图修复问题")
        cmd = None
        randomList = configReader.getProtectMapVoteErrRconExRandomList()
        if not commonUtils.isEmpty(randomList):
            # 获取随机命令，避开上次
            self.lastIndex = commonUtils.getRandom(len(randomList), self.lastIndex)
            cmd = randomList[self.lastIndex]

        if commonUtils.isEmpty(cmd):
            # 获取固定命令
            cmd = configReader.getProtectMapVoteErrRconEx()

        # 执行命令
        if cmd is not None and len(cmd) > 5:
            self.requester.requestRconCmd(cmd)
