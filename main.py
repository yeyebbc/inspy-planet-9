#!/usr/bin/env python
# -*- coding: utf-8 -*
import random
import subprocess
import sys
import time

from lib.check_env import EnvChecker
# py -m ensurepip --default-pip
#
# python -m pip install requests
# python -m pip install psutil

from lib.file_event_worker import FileEventWorker
from lib.event_dispatcher import *
from lib.requester import Requester
from lib.tools.config_reader import configReader
from lib.tools.logger import logger
from plugins.register import Register

if __name__ == "__main__":
    logger.setEnableLog(configReader.getEnableLog(), configReader.getEnableMoreLog(), configReader.getEnableLogFile())
    logger.log("插件版本:", commonUtils.getVersion())
    EnvChecker.get_instance().check_env()
    worker = FileEventWorker()
    requester = Requester(worker)
    register = Register()
    pluginList = []
    register.getPluginList(pluginList)
    for plugin in pluginList:
        eventDispatcher.register(plugin)
    eventDispatcher.init(requester)
    random.seed(time.time())
    try:
        worker.loop()
    except Exception as e:
        logger.writeException()
        worker.stop()
        logger.e("main", "exit!!!")
        # no exit
        input()
