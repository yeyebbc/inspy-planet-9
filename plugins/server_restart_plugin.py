# !/usr/bin/env python
# -*- coding: utf-8 -*
import time
from datetime import datetime
import os

from lib.player_data_center import playerDataCenterInstance
from lib.tools.common_utils import commonUtils
from lib.tools.config_reader import configReader
from lib.tools.logger import logger
from lib.tools.plugin_helper import PluginHelper
from lib.event_callback import EventCallback


class ServerRestartPlugin(EventCallback):
    TAG = "ServerRestartPlugin"
    serverProcessName = "InsurgencyServer"
    # serverProcessName = "notepad"
    helper = PluginHelper()

    def enbale(self):
        return not commonUtils.isEmpty(configReader.getRestartScriptPath()) and os.path.exists(configReader.getRestartScriptPath())

    def __init__(self):
        self.timeCount = 0
        self.restartDelay = configReader.getRestartDelay()
        if self.restartDelay >= 0 and self.restartDelay < 10 * 60:
            # min sec
            logger.i(self.TAG, "sissm.RestartDelay您设置为" + str(
                self.restartDelay) + "，但由于不允许小于600秒，已设置为sissm.RestartDelay=600")
            self.restartDelay = 10 * 60
        self.freeTimeStart = 0
        self.restartingTime = 0

    def init(self, requester):
        self.helper.init(requester)

    def timer(self, data):
        if not self.enbale():
            return
        self.timeCount += 1
        if self.timeCount % 8 == 0:
            ret = commonUtils.findProcessName(self.serverProcessName)
            if ret != True:
                logger.e(self.TAG, "发现游戏进程不存在，正在重启...")
                self._restart()
            else:
                if self.restartDelay > 0:
                    if playerDataCenterInstance.getPlayerCount() > 0:
                        self._setServerFree(False)
                    else:
                        self._setServerFree(True)
                    now = datetime.now()
                    # 强制约定在凌晨
                    if self.freeTimeStart > 0 and (
                            int(time.time()) - self.freeTimeStart) > self.restartDelay and now.hour >= 3 and now.hour <= 7:
                        self._setServerFree(False)
                        logger.e(self.TAG, "发现游戏空闲时间超过" + str(self.restartDelay) + "秒，正在重启...")
                        self._restart()

    def clientSynthAdd(self, log, data):
        self._setServerFree(False)

    def killed(self, log, data):
        self._setServerFree(False)

    def serverError(self, data):
        logger.e(self.TAG, "发现游戏出现异常日志，正在重启...")
        self._restart()

    def _restart(self):
        if self.restartingTime > 0 and (int(time.time()) - self.restartingTime) < 60:
            # last restart time < 60, ignore this restart
            return
        self.restartingTime = int(time.time())
        path = configReader.getRestartScriptPath()
        if commonUtils.isEmpty(path) or not os.path.exists(path):
            logger.e(self.TAG, "脚本不存在:" + str(path))
            return
        if commonUtils.isOnline():
            commonUtils.killProcessName(self.serverProcessName)
            time.sleep(3)
            if commonUtils.isWin():
                os.system("start " + path)
            else:
                # TODO tmux
                os.system(path + " &")
            time.sleep(3)
        else:
            logger.i(self.TAG, "测试环境，假装重启")

    def _setServerFree(self, isFree):
        if not self.enbale():
            return
        if not isFree:
            # free to busy
            self.freeTimeStart = 0
        elif self.freeTimeStart == 0 and isFree:
            # busy to free
            self.freeTimeStart = int(time.time())
