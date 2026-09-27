import json
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

from lib.tools.common_utils import commonUtils
from lib.tools.logger import logger
from lib.tools.mcrcon_command import MCrconCommand


# 保持最新的玩家列表
# TODO 解析玩家，更新map。玩家加入是根根據名字獲取信息
class Player:
    netId: str = ""
    uid: str = ""
    name: str = ""
    score: int = 0
    ip: str = ""


class PlayerDataCenter:
    TAG = "PlayerDataCenter"
    threadPool = None
    callback = None
    playerRequestingMap = {}

    def __init__(self):
        self.playerList: list = []

    def init(self, rcon: MCrconCommand):
        self.rcon = rcon
        if self.threadPool is None:
            self.threadPool = ThreadPoolExecutor(max_workers=1)
        self.isStarted = False
        self.playerList: list = []
        self.playerRequestingMap = {}

    def start(self):
        self.isStarted = True
        self.threadPool.submit(self.loop)

    def loop(self):
        while (self.isStarted):
            try:
                self.update()
            except Exception as e:
                logger.writeException()
            time.sleep(10)

    def update(self):
        response = None
        if commonUtils.isOnline():
            response = self.rcon.exeCommand("listplayers", logLevel=2)
        else:
            file = open('test\\rcon-resp-listplayers.txt', 'r', encoding="UTF-8")
            response = file.read()
        # commonUtils.writeFile(commonUtils.getOutputLogPath()+"/players.txt",response)
        self.playerList = self.parse(response)

    def setPlayerChangeCallback(self, callback):
        self.callback = callback

    def stop(self):
        self.isStarted = False

    def getPlayers(self) -> list:
        return self.playerList

    def getPlayerCount(self) -> int:
        if self.playerList is None:
            return 0
        return len(self.playerList)

    def parse(self, r):
        players = []
        if r is None:
            return players
        listPlayers = []
        index = 0
        startStr = "============"
        if startStr in r:
            r = r[r.rfind(startStr) + len(startStr):]
        while True:
            preIndex = index + 1
            # find end str
            index = r.find("\011\011 |", preIndex)
            p = ""
            if index < 0:
                # end
                p = r[preIndex:len(r)]
            else:
                p = r[preIndex:index]
            if p.replace("|", "").strip().startswith("SteamNWI:"):
                # merge
                listPlayers[len(listPlayers) - 1] = listPlayers[len(listPlayers) - 1] + p
            else:
                listPlayers.append(p)
            if index < 0:
                break
        for pp in listPlayers:
            if pp.find("SteamNWI:") > 0:
                player = Player()
                arr = pp.split(" | ")
                startIndex = 0
                if len(arr[0].strip()) == 0:
                    startIndex = 1
                player.netId = arr[startIndex].strip()
                player.name = arr[startIndex + 1].strip()
                player.uid = arr[startIndex + 2].replace("SteamNWI:", "").strip()
                if len(arr) > startIndex + 3:
                    player.ip = arr[startIndex + 3].strip()
                if len(arr) > startIndex + 4:
                    player.score = commonUtils.toInt(arr[startIndex + 4].strip(), 0)
                players.append(player)
                # logger.d(self.TAG,
                #          "player:" + player.netId + "|" + player.name + "|" + player.uid + "|" + player.ip + "|" + str(
                #              player.score))
        return players

    def addPlayerRequesting(self, uid, name):
        self.playerRequestingMap[name] = {"uid": uid, "time": int(time.time()), "needClear": False}

    def getPlayerUidByName(self, name):
        data = self.playerRequestingMap.get(name)
        if data is not None:
            return data.get("uid")
        for player in self.playerList:
            if player.name == name:
                return player.uid

    def getPlayerNameByUid(self, uid):
        for key in self.playerRequestingMap.keys():
            if self.playerRequestingMap[key]["uid"] == uid:
                return key
        for player in self.playerList:
            if player.uid == uid:
                return player.name
        return None

    def removePlayer(self, name):
        # auto clear timeout,or exit player
        for key in list(self.playerRequestingMap.keys()):
            if self.playerRequestingMap[key]["needClear"] == True or (int(time.time()) - self.playerRequestingMap[key][
                "time"]) > 3 * 60 * 60:
                self.playerRequestingMap.pop(key)
        # mark, wait next clear
        data = self.playerRequestingMap.get(name)
        if data is not None:
            data["needClear"] = True
        logger.d(self.TAG, "removePlayer curr count:" + str(len(self.playerRequestingMap)) + " name:" + str(name))
        if len(self.playerRequestingMap) > 100:
            self.playerRequestingMap.clear()



playerDataCenterInstance = PlayerDataCenter()
