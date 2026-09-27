from lib.tools.common_utils import commonUtils
from lib.tools.config_reader import configReader


class TitleModule:
    def __init__(self):
        self.titleMap = configReader.getTitleValueMap()
        self.customTitleMap = configReader.getCustomTitleMap()
        self.titleRules = configReader.getTitleRules()

    def getNameByValue(self, targetValue):
        if commonUtils.isEmpty(self.titleMap):
            return ""
        thanTargetValue = -1
        name = ""
        for key in self.titleMap.keys():
            v = commonUtils.toInt(key, -1)
            if targetValue >= v and v > thanTargetValue:
                thanTargetValue = v
                name = self.titleMap[key]
        return name

    def getTitleName(self, playerGUID, titleType, data):
        # 自定义称号
        titleName = ""
        customTitle = ""
        title = ""
        if configReader.getCustomTitleShow():
            customTitle = self.customTitleMap.get(playerGUID)
        if configReader.getTitleShow():
            # 分数称号
            if commonUtils.isEmpty(self.titleRules):
                self.titleRules = "score"
            ruleField = ""
            if "score" == self.titleRules:
                ruleField = "sumScore"
            elif "kill" == self.titleRules:
                ruleField = "sumKillCount"
            elif "take" == self.titleRules:
                ruleField = "sumTakeCount"

            value = commonUtils.toInt(data.get(ruleField), 0)
            title = self.getNameByValue(value)

        if not commonUtils.isEmpty(customTitle):
            if titleType == 1:
                titleName += "[" + customTitle + "]"
        if not commonUtils.isEmpty(title):
            if titleType == 1:
                titleName += "[" + title + "]"
            else:
                titleName = title
        # 兜底
        if titleType == 1 and commonUtils.isEmpty(titleName):
            joinName = data.get("joinName")
            if not commonUtils.isEmpty(joinName):
                titleName = "[" + joinName + "]"

        if commonUtils.isEmpty(titleName):
            titleName = ""
        return titleName


titleModule = TitleModule()
