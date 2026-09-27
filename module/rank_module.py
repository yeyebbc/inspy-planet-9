import datetime

from lib.tools.common_utils import commonUtils
from lib.tools.config_reader import configReader
from lib.tools.net_utils import netUtils
from module.title_module import titleModule


class RankModule:
    def __init__(self):
        self.rankRules = configReader.getRankRules()
        # 今天日期
        self.today = ""
        # 排行榜map，key为日期
        self.rankTop = {}
        # 总榜数据
        self.allRankTop = {}
        # 需要请求的榜单日期
        self.ranTopDateIds = []
        # 广告词里是否有总榜
        self.hasAllRankTop = False
        # 原始广告词数组
        self.adArray = []
        self.adArrayNew = []

    def getPlayerData(self, serverId, playerGUID):
        params = {"playerGUID": playerGUID,
                  "serverId": str(serverId),
                  "rankType": self.rankRules,
                  "rankCount": configReader.getRankListSize()}
        data = netUtils.httpGet("player_rank_v2.php", params)
        if data is not None and "code" in data and data["code"] == 0 and len(data["data"]) > 0:
            return data["data"]
        else:
            return None

    def getRankMeStr(self, playerGUID, playerName, playerData):
        rankMeStr = configReader.getRankMe()
        titleStr = titleModule.getTitleName(playerGUID, 2, playerData)
        ruleField = ""
        if "score" == self.rankRules:
            ruleField = "scoreRankIndex"
        elif "kill" == self.rankRules:
            ruleField = "killRankIndex"
        elif "take" == self.rankRules:
            ruleField = "takeRankIndex"
        else:
            return ""
        newRankMeStr = rankMeStr.replace("$name", playerName) \
            .replace("$title", titleStr) \
            .replace("$rank", str(playerData.get(ruleField))) \
            .replace("$score", str(playerData.get("sumScore"))) \
            .replace("$kill", str(playerData.get("sumKillCount"))) \
            .replace("$take", str(playerData.get("sumTakeCount")))
        return newRankMeStr

    def getRankPlayers(self, playerData):
        rankPlayersStr = configReader.getRankPlayers()
        topPlayers = playerData.get("topPlayers")
        if not commonUtils.isEmpty(topPlayers):
            for i in range(0, len(topPlayers)):
                rankIndex = topPlayers[i].get("rankIndex")
                name = topPlayers[i].get("name")
                rankPlayersStr = rankPlayersStr.replace("$rank[" + str(i) + "]", str(rankIndex)) \
                    .replace("$name[" + str(i) + "]", name)
            return rankPlayersStr
        return ""

    def isRank(self, pinyin: str):
        pinyin = pinyin.lower()
        if not configReader.getRankShow() or commonUtils.isEmpty(pinyin):
            return False
        arrPinyin = configReader.getRankKeywordsPinyin()
        if commonUtils.isEmpty(arrPinyin):
            return False
        if pinyin in arrPinyin:
            return True
        return False

    # ==============下面是欢迎语里的逻辑==========

    def initAdArray(self):
        self.adArray = configReader.getAdsArray()
        self.adArrayNew = self.adArray.copy()
        self.ranTopDateIds.clear()
        self.hasAllRankTop = False
        if not commonUtils.isEmpty(self.adArray):
            # 收集变量
            for item in self.adArray:
                if "$yesterdayTop" in item:
                    self.ranTopDateIds.append(commonUtils.DATE_YESTERDAY)
                if "$todayTop" in item:
                    self.ranTopDateIds.append(commonUtils.DATE_TODAY)
                if "$allTop" in item:
                    self.hasAllRankTop = True
            self.ranTopDateIds = set(self.ranTopDateIds)

    def tryUpdateRankTop(self, serverId, forceUpdateToday):
        hasVar = not commonUtils.isEmpty(self.ranTopDateIds) or self.hasAllRankTop
        if hasVar:
            if self.isTodayChange():
                self.updateRankTop(serverId, self.ranTopDateIds, 1)
                self.adArrayNew = self.adArray.copy()
                for i in range(0, len(self.adArray)):
                    self.rankTopReplace(i, "$yesterdayTop", commonUtils.DATE_YESTERDAY)
                    self.rankTopReplace(i, "$todayTop", commonUtils.DATE_TODAY)
                    self.allRankTopReplace(i)
            else:
                if forceUpdateToday:
                    self.updateRankTop(serverId, [commonUtils.DATE_TODAY], 0)
                    self.adArrayNew = self.adArray.copy()
                    for i in range(0, len(self.adArray)):
                        self.rankTopReplace(i, "$yesterdayTop", commonUtils.DATE_YESTERDAY)
                        self.rankTopReplace(i, "$todayTop", commonUtils.DATE_TODAY)
                        self.allRankTopReplace(i)

    def rankTopReplace(self, i, holder, dateId):
        if holder in self.adArray[i]:
            array = self.rankTop.get(dateId)
            playerName = "无"
            if not commonUtils.isEmpty(array) and not commonUtils.isEmpty(array[0]):
                playerName = array[0].get("playerName")
            self.adArrayNew[i] = self.adArrayNew[i].replace(holder, playerName)

    def allRankTopReplace(self, i):
        if "$allTop" in self.adArray[i]:
            allTopPlayerName = "无"
            if not commonUtils.isEmpty(self.allRankTop) and not commonUtils.isEmpty(self.allRankTop[0]):
                allTopPlayerName = self.allRankTop[0].get("name")
            self.adArrayNew[i] = self.adArrayNew[i].replace("$allTop", allTopPlayerName)

    def getAdArrayNew(self):
        if commonUtils.isEmpty(self.adArrayNew):
            self.adArrayNew = self.adArray.copy()
        return self.adArrayNew

    def isTodayChange(self):
        if datetime.date.today() != self.today:
            self.today = datetime.date.today()
            return True
        else:
            return False

    def getRankByTime(self, serverId, allRankTopNum):
        params = {"serverId": str(serverId),
                  "rankType": self.rankRules,
                  "rankCount": 1,
                  "dateIds": ",".join(self.ranTopDateIds),
                  "allRankTopNum": allRankTopNum}
        data = netUtils.httpGet("rank_top.php", params)
        if data is not None and "code" in data and data["code"] == 0 and len(data["data"]) > 0:
            return data["data"]
        else:
            return None

    def updateRankTop(self, serverId, dateIds, allRankTopNum):
        data = self.getRankByTime(serverId, allRankTopNum)
        if not commonUtils.isEmpty(data):
            for dateId in dateIds:
                topPlayers = data.get(dateId)
                if not commonUtils.isEmpty(topPlayers):
                    self.rankTop[dateId] = topPlayers
            allRankTop = data.get("allRankTopPlayers")
            if not commonUtils.isEmpty(allRankTop):
                self.allRankTop = allRankTop

    def getRankTop(self, dateId):
        return self.rankTop[dateId]


rankModule = RankModule()
