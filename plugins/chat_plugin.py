# !/usr/bin/env python
# -*- coding: utf-8 -*
import time

from lib.game_data_center import gameDataCenterInstance, PlayerData
from lib.tools.deep_seek import deepseekSafe
from module.rank_module import rankModule
from lib.tools.common_utils import commonUtils
from lib.tools.config_reader import configReader
from lib.tools.plugin_helper import PluginHelper
from module.title_module import titleModule

from lib.event_callback import EventCallback


class ChatPlugin(EventCallback):
    helper = PluginHelper()

    def enbale(self):
        return True

    def init(self, requester):
        self.helper.init(requester)

    def chat(self, log, data):
        if data is None:
            return
        content: str = data.get("content")
        if content is None:
            return
        playerGUID = data.get("playerGUID")
        # playerName = data.get("playerName").encode('utf-8')
        playerName = data.get("playerName")
        pinyinStr = commonUtils.getPinyin(content)
        responseForKeywords = self.getWordsByKeywords(playerGUID, playerName, pinyinStr)
        if not commonUtils.isEmpty(responseForKeywords):
            self.helper.requester.apiSay(responseForKeywords)
            return
        if rankModule.isRank(pinyinStr):
            playerData = rankModule.getPlayerData(self.helper.serverId, playerGUID)
            if playerData is not None:
                rankMeStr = rankModule.getRankMeStr(playerGUID, playerName, playerData)
                if not commonUtils.isEmpty(rankMeStr):
                    self.helper.requester.apiSay(rankMeStr)
                if configReader.getRankPlayersShow():
                    rankPlayerStr = rankModule.getRankPlayers(playerData)
                    if not commonUtils.isEmpty(rankPlayerStr):
                        self.helper.requester.apiSay(rankPlayerStr)
            else:
                self.helper.requester.apiSay("[" + playerName + "]沒有查詢到信息，請在這局結束後再查詢.")
        if self.isContans(content):
            if len(configReader.getDeepseekKey()) < 5:
                commonUtils.writeLog(commonUtils.getOutputLogPath() + "/ai.txt", "没有配置chat.deepseekKey")
                return
            aiContent = content.lower()
            if aiContent.startswith("ai"):
                aiContent = aiContent[2:]
            aiPrompt = configReader.getAiPrompt()
            if commonUtils.isEmpty(aiPrompt):
                return
            player: PlayerData = gameDataCenterInstance.playerGetOrCreate(playerGUID)
            playerScore = ""
            lastDeadWay = ""
            joinDuration = ""
            if player is not None:
                playerScore = str(player.score)
                if not commonUtils.isEmpty(player.lastDeadWay):
                    lastDeadWay = player.lastDeadWay
                if player.joinTime > 0:
                    joinDuration = str(int(time.time()) - player.joinTime)
            aiPrompt = aiPrompt.replace("$playerName", playerName).replace("$playerScore",
                                                                           playerScore).replace(
                "$lastDeadWay", lastDeadWay).replace("$joinDuration", joinDuration)
            commonUtils.writeLog(commonUtils.getOutputLogPath() + "/ai.txt", aiPrompt)
            aiResponse = deepseekSafe(aiPrompt, aiContent)
            if aiResponse is None:
                return
            if len(aiResponse) > configReader.getAiMsgMaxWords():
                aiResponse = aiResponse[0:configReader.getAiMsgMaxWords()]
            aiResponse = aiResponse.replace("\n", "")
            commonUtils.writeLog(commonUtils.getOutputLogPath() + "/ai.txt", aiResponse)
            if aiResponse:
                maxLength = configReader.getAiMsgSplitThreshold()
                sentNum = 0
                for i in range(0, len(aiResponse), maxLength):
                    currText = aiResponse[i:i + maxLength]
                    sentNum += len(currText)
                    if i == 0:
                        sendText = "AI回复[" + playerName + "]:" + currText
                    else:
                        sendText = currText
                    self.helper.requester.apiSay(sendText)
                    commonUtils.writeLog(commonUtils.getOutputLogPath() + "/ai.txt", sendText)


    def isContans(self, msg):
        arr = configReader.getAiKeywords()
        for word in arr:
            if word.lower() in msg.lower():
                return True
        return False


    def getWordsByKeywords(self, playerGUID, playerName, pinyinStr):
        value = configReader.getValueByKeywordsPinyin(pinyinStr)
        if commonUtils.isEmpty(value):
            return None
        value = value.replace("$name", playerName)
        if "$title" in value:
            playerData = rankModule.getPlayerData(self.helper.serverId, playerGUID)
            title = titleModule.getTitleName(playerGUID, 2, playerData)
            if commonUtils.isEmpty(title):
                title = "无"
            value = value.replace("$title", title)
        # 玩家本回合其他信息的变量赋值
        value = gameDataCenterInstance.replaceVarByPlayerCurrRound(value, playerGUID)
        return value
