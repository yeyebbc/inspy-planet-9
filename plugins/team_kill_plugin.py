# !/usr/bin/env python
# -*- coding: utf-8 -*
import time

from lib.tools.common_utils import commonUtils
from lib.tools.config_reader import configReader
from lib.tools.logger import logger
from lib.tools.plugin_helper import PluginHelper
from lib.event_callback import EventCallback


class TeamKillPlugin(EventCallback):
    helper = PluginHelper()
    register = None
    teamKillMsg = None
    teamKillCountMap = {}
    # 二维数组
    sryCheckArray = []
    lastTakeObjectTime = 0

    def __init__(self, register):
        self.register = register

    def enbale(self):
        return configReader.getTeamKillPluginState()

    def init(self, requester):
        self.TAG = "TeamKill"
        self.requester = requester
        self.helper.init(requester)
        self.teamKillMsg = configReader.getTeamKillMsg()
        self.isStartGame = True
        array = configReader.getTeamKillSryCheck()
        if not commonUtils.isEmpty(array):
            for a in array:
                if not commonUtils.isEmpty(a):
                    itemArray = []
                    for temp in a.split("|"):
                        itemArray.append(temp.lower())
                    self.sryCheckArray.append(itemArray)

    def gameStart(self, log, data):
        self.isStartGame = True
        self.teamKillCountMap.clear()

    def gameEnd(self, log, data):
        self.isStartGame = False
        self.teamKillCountMap.clear()
    def takeObject(self, log, data):
        self.lastTakeObjectTime = time.time()

    def killed(self, log, data):
        if not self.enbale():
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
        if len(deadUid) < 10 or len(killerUid) < 10 or killerUid == deadUid:
            return
        if weapon is None:
            weapon = ""
        if configReader.isTkWeaponKeywordFilter(weapon):
            logger.d(self.TAG, "军火库引起的tk，tk是允许的")
            return
        if not self.isStartGame:
            logger.d(self.TAG, "游戏还没开始，tk是允许的")
            return
        tkInfo = self.teamKillCountMap.get(killerUid)
        if tkInfo is None:
            tkInfo = {"count": 0, "killerUid": killerUid, "killerName": killerName, "sryFinish": False,
                      "startDelayCheck": False}
            self.teamKillCountMap[killerUid] = tkInfo
        count = tkInfo["count"]
        count += 1
        tkInfo["count"] = count
        if self.checkTimeAllowTK():
            return
        if not commonUtils.isEmpty(self.teamKillMsg):
            msg = (self.teamKillMsg.replace("$killerName", killerName)
                   .replace("$deadName", deadName)
                   .replace("$count", str(count))
                   .replace("$weapon", weapon))
            self.helper.requester.apiSay(msg)
        # 延迟执行
        delay = configReader.getTeamKillExecuteDelay()
        cmd = configReader.getTeamKillExecuteCmd()
        if (delay > 0 and not commonUtils.isEmpty(cmd)
                and not commonUtils.isEmpty(self.sryCheckArray)
                and not tkInfo["startDelayCheck"]):
            print(f">>>>>>>>>>>>>>>>延迟任务踢人：{killerName}")
            # 保证每个人只建立一个异步任务
            tkInfo["startDelayCheck"] = True
            cmd = cmd.replace("$killerUid", killerUid)
            commonUtils.getThreadPool().submit(self.async_delay_task, delay, killerUid,killerName, tkInfo, cmd)

    def chat(self, log, data):
        content = data.get("content")
        if commonUtils.isEmpty(content):
            return
        content = content.lower()
        playerGUID = data.get("playerGUID")
        playerName = data.get("playerName")
        if commonUtils.isEmpty(playerGUID):
            return
        # 检查此人是否为tk过的人
        tkInfo = self.teamKillCountMap.get(playerGUID)
        if tkInfo is not None and not commonUtils.isEmpty(self.sryCheckArray):
            if tkInfo["sryFinish"] or not tkInfo["startDelayCheck"]:
                return
            if self.checkIncludeSry(content):
                tkInfo["sryFinish"] = True
                # 如果在延迟命令时间内又TK会被忽略
                logger.d(self.TAG, "玩家[" + playerName + "]说[" + content + "]，识别出道歉，已取消踢人命令")
                cancelMsg = configReader.getTeamKillCancelExecuteMsg()
                if not commonUtils.isEmpty(cancelMsg):
                    cancelMsg = (cancelMsg.replace("$killerName", playerName)
                                .replace("$count", str(tkInfo["count"])))
                    self.helper.requester.apiSay(cancelMsg)
            else:
                logger.d(self.TAG, "玩家[" + playerName + "]说[" + content + "]，但没识别出道歉")

    def checkIncludeSry(self, content):
        # 每条 sryCheck 配置为一个短语按字符拆分后的集合，如 "对不起" -> 对|不|起
        # 只要 content 命中其中任意一个短语(该短语所有必需字符都已出现)即视为道歉
        for itemArray in self.sryCheckArray:
            if commonUtils.isEmpty(itemArray):
                continue
            if all(item in content for item in itemArray):
                return True
        return False

    def async_delay_task(self, delay, killerUid, killerName, tkInfo, cmd):
        logger.d(self.TAG, "计划延迟", delay, "秒踢出玩家：", killerName)
        time.sleep(delay)
        if killerUid not in self.teamKillCountMap:
            logger.d(self.TAG, "延迟时间到，tk已经跨局延迟还没到，豁免玩家：", killerName)
            return
        if tkInfo["sryFinish"]:
            logger.d(self.TAG, "延迟时间到，发现玩家已经道歉了，停止执行命令，玩家：", killerName)
            tkInfo["startDelayCheck"] = False
            tkInfo["sryFinish"] = False
            return
        if self.checkTimeAllowTK():
            tkInfo["startDelayCheck"] = False
            return
        tkInfo["startDelayCheck"] = False
        self.helper.requester.requestRconCmd(cmd)
        afterMsg: str = configReader.getTeamKillAfterMsg()
        if not commonUtils.isEmpty(afterMsg):
            afterMsg = (afterMsg.replace("$killerName", killerName)
                        .replace("$count", str(tkInfo["count"])))
            self.helper.requester.apiSay(afterMsg)

    def checkTimeAllowTK(self):
        diff = abs(self.lastTakeObjectTime - time.time())
        half = configReader.getAllowTKTookObjectiveTime() / 2.0
        if diff <= half:
            logger.d(self.TAG, f"在TK安全时间内不惩罚: 距离占点时间{diff}s，exceptTookObjectiveTime的一半时间是{half}s")
            return True
        else:
            logger.d(self.TAG, f"不在TK安全时间内:距离占点时间{diff}s，exceptTookObjectiveTime的一半时间是{half}s")
            return False
