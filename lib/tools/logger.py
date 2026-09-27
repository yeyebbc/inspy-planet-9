# !/usr/bin/env python
# -*- coding: utf-8 -*
import logging
import os.path
import traceback
from datetime import datetime
from os import sep

from lib.tools.common_utils import commonUtils

# 配置日志
logging.basicConfig(level=logging.INFO)
loggerCore = logging.getLogger(__name__)


class Logger:
    def __init__(self):
        self.enableLog = False
        self.enableMoreLog = False
        self.enableLogFile = False
        self.logFile = None

    def _write(self, log):
        if os.path.exists(commonUtils.getOutputLogPath()):
            if self.logFile is None:
                self.logFile = open(
                    commonUtils.getOutputLogPath() + "/log-" + commonUtils.getFileNameByTime() + ".txt",
                    "a", encoding='utf-8')
        if self.logFile is None:
            return
        self.logFile.write("[" + commonUtils.getCurrTime() + "] " + log + "\n")
        self.logFile.flush()

    def setEnableLog(self, enableLog, enableMoreLog, enableLogFile):
        self.enableLog = enableLog is True
        self.enableMoreLog = enableMoreLog is True
        self.enableLogFile = enableLogFile is True
        if not self.enableLog:
            print("已关闭控制台日志")
        else:
            if self.enableMoreLog:
                print("已开启控制台详细日志")
            else:
                print("已开启控制台少量日志 （可配置main.enableMoreLog 1开启更详细日志）")
        if not self.enableLogFile:
            print("已关闭文件日志 （可配置main.enableLogFile 1开启文件日志）")

    def d(self, tag, *args):
        self._printLog("d", tag, *args)

    def i(self, tag, *args):
        self._printLog("i", tag, *args)

    def e(self, tag, *args):
        self._printLog("e", tag, *args)

    def logNoShow(self, tag, msg):
        self._printLog("n", tag, msg)

    def log(self, *args):
        self._printLog(None, None, *args)


    def logMore(self, tag, *args):
        self._printLog("m", tag, *args)

    def _getArgsStr(self, *args):
        if args:
            return "".join(str(arg) for arg in args)
        return ""

    def _printLog(self, level, tag, *args):
        if self.enableLog or self.enableLogFile:
            tag = "" if tag is None else str(tag)
            msg = self._getArgsStr(*args)
            wrapLog = self.wrap(level, tag, msg)
            if self.enableLog:
                if level == "n": # noShow
                    pass
                elif level == "m": # more
                    if self.enableMoreLog:
                        print(wrapLog)
                    else:
                        # 关闭更多日志的时候，也不写入文件
                        return
                else:
                    print(wrapLog)
            if self.enableLogFile:
                self._write(wrapLog)

    def writeException(self):
        if self.enableLog:
            traceback.print_exc()
        exception = commonUtils.getException()
        self.logNoShow("exception", exception)

    def wrap(self, level, tag, msg):
        now = datetime.now()
        level = "" if level is None else str(level) + " "
        # 格式化为字符串
        time_str = "[" + now.strftime("%Y-%m-%d %H:%M:%S") + "]"
        if commonUtils.isEmpty(tag):
            log = level + time_str + " " + msg
        elif commonUtils.isEmpty(msg):
            log = level + time_str + " " + tag
        else:
            log = level + time_str + " [" + tag + "] " + msg
        return log


logger = Logger()
