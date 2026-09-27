# !/usr/bin/env python
# -*- coding: utf-8 -*
import json
import traceback
from urllib.parse import urlencode

import requests

from lib.tools.common_utils import commonUtils
from lib.tools.config_reader import configReader

class PluginHelper:
    requester = None
    configReader = None
    logger = None
    serverId = 0
    serverKey = ""
    host = "82.156.36.121"
    # host = "127.0.0.1"

    def init(self, requester):
        self.requester = requester
        self.serverId = configReader.getServerId()
        self.serverKey = configReader.getServerKey()

    def isStartPinyin(self, text):
        if text is None:
            return False
        ch = ord(text[0:1])
        if ch < 0 or ch > 128:
            return False
        return True
