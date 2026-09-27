# !/usr/bin/env python
# -*- coding: utf-8 -*
import platform
import sys
import time
import os
import traceback

from lib.player_data_center import playerDataCenterInstance
from lib.tools.common_utils import commonUtils
from lib.tools.config_reader import configReader
from lib.event_dispatcher import eventDispatcher
from lib.tools.logger import logger
from lib.tools.mcrcon_command import MCrconCommand
SS_SUBSTR_WINDOWS_ROUND_STARTED = "Display: State: PreRound -> RoundActive"
SS_SUBSTR_WINDOWS_ROUND_OVER = "Display: Round Over"
# [2022.11.22-15.12.47:780][537]LogGameState: Match State Changed from PreRound to RoundActive
SS_SUBSTR_ROUND_STATE_CHANGE = "LogGameplayEvents: Display: Round "
SS_SUBSTR_GAME_START = "Match State Changed from GameStarting to PreRound"
SS_SUBSTR_GAME_END_NOW = "LogGameMode: Display: State: WaitingPostMatch -> GameOver"
# [2022.11.30-01.21.43:085][607]LogNet: NotifyAcceptingConnection accepted from: 222.84.97.250:52318
SS_SUBSTR_REGCLIENT_IP = "LogNet: NotifyAcceptingConnection accepted from:"
# 正在请求加入 [2022.11.30-01.33.10:687][633]LogNet: Login request: ?Name=测试1 userId: SteamNWI:76561198213693677 platform: SteamNWI
SS_SUBSTR_REGCLIENT_REQUEST = "LogNet: Login request:"
# [2022.11.30-01.33.13:204][782]LogNet: Join succeeded: 测试1
SS_SUBSTR_REGCLIENT = "LogNet: Join succeeded:"
# 退出 [2022.11.30-01.41.41:997][779]LogNet: UChannel::Close: Sending CloseBunch.....Owner: INSPlayerController_2147481869, UniqueId: SteamNWI:76561198213693677
SS_SUBSTR_UNREGCLIENT = "LogNet: UChannel::Close:"
SS_SUBSTR_OBJECTIVE = "LogGameMode: Display: Advancing spawns for faction"
SS_SUBSTR_MAPCHANGE = "SeamlessTravel to:"
SS_SUBSTR_CAPTURE = "LogSpawning: Spawnzone '"
SS_SUBSTR_SHUTDOWN = "LogExit: Game engine shut down"
SS_SUBSTR_CHAT = "LogChat: Display:"
SS_SUBSTR_WINLOSE = "LogGameMode: Display: Round Over: Team"
SS_SUBSTR_TRAVEL = "LogGameMode: ProcessServerTravel:"
SS_SUBSTR_SESSIONLOG = "HttpStartUploadingFinished. SessionName:"

SS_SUBSTR_BP_CHARNAME = "' cached new pawn '"

SS_SUBSTR_MAP_OBJECTIVE = "LogObjectives: Verbose: Authority: Adding objective '"
SS_SUBSTR_MESHERR = "LogGameMode: Verbose: RestartPlayerAt"
SS_SUBSTR_KILLED = " killed "
SS_SUBSTR_TAKE_OBJECTIVE = "LogGameplayEvents: Display: Objective "
SS_SUBSTR_SERVER_ERROR = "OnCreateSessionComplete: Session: (GameSession) Result: (0)"


class FileEventWorker:
    TAG = "FileEventWorker"
    def __init__(self):
        self.rcon = None
        self.isStart = True
        self.nextPlayerIp = ""
        self.logFile = None
        self.lastLogTime = 0
        self.timeSeconds=0

    def send(self, data, logLevel=1):
        requestName = data.get("requestName")
        requestParams = data.get("requestParams")
        if requestName is None or requestParams is None:
            return
        response = None
        if "apiSay" == requestName:
            command = "say " + requestParams
            response = self.rcon.exeCommand(command, logLevel=logLevel)
        elif "apiGameModePropertySet" in requestName:
            command = "gamemodeproperty " + requestParams.replace("|", " ")
            response = self.rcon.exeCommand(command, logLevel=logLevel)
        elif "apiGameModePropertyGet" in requestName:
            command = "gamemodeproperty " + requestParams
            response = self.rcon.exeCommand(command, logLevel=logLevel)
        elif "apiRcon" in requestName:
            response = self.rcon.exeCommand(requestParams, logLevel=logLevel)
        return response

    def dispatchEvent(self, jsonObject):
        if jsonObject is None:
            return
        startTime = commonUtils.getCurrTimestampMs()
        try:
            eventDispatcher.dispatch(jsonObject)
        except Exception as e:
            logger.writeException()
            logger.i(self.TAG, "dispatchEvent error:" + str(jsonObject))
        finally:
            costTime = commonUtils.getCurrTimestampMs() - startTime
            if costTime > 1000:
                logger.e(self.TAG, "性能提醒：耗时日志处理太久[", costTime, "ms]", jsonObject)

    def dispatchEventException(self):
        self.dispatchEvent({"event_type": "python_exception", "log": ""})

    def follow(self):
        '''generator function that yields new lines in a file
        '''
        while True:
            if self.logFile is None or self.logFile.closed:
                logger.e(self.TAG, "正在读取日志文件")
                time.sleep(5)
                if self.logFile is not None:
                    self.logFile.close()
                gameLogPath = configReader.getServerLogFile()
                self.logFile = open(gameLogPath, "r", encoding='utf-8')
                self.logFile.seek(0, os.SEEK_END)
                logger.e(self.TAG, "读取日志文件成功")
            line = None
            try:
                line = self.logFile.readlines()
            except Exception as e:
                logger.writeException()
            if commonUtils.isEmpty(line):
                if self.lastLogTime == 0:
                    self.lastLogTime = int(time.time())
                if (int(time.time()) - self.lastLogTime) > 3600:
                    self.lastLogTime = 0
                    self.logFile.close()
                    logger.e(self.TAG, "日志文件:很久没读到日志，关闭文件")
                time.sleep(3)
                continue
            else:
                self.lastLogTime = 0
            yield line

    # assume the file already has 2 lines
    def loop(self):
        self.tryRestart()

        rconIp = configReader.getRconIp()
        rconPort = configReader.getRconPort()
        rconPassword = configReader.getRconPassword()
        if rconIp is None or rconPort is None or rconPassword is None:
            logger.i(self.TAG, "配置缺少rconIp或rconPort或rconPort")
            exit()
        self.isStart = True
        commonUtils.getThreadPool().submit(self.timerLoop)
        # commonUtils.getThreadPool().submit(self.findErrorLoop)
        self.rcon = MCrconCommand(rconIp, rconPort, rconPassword)
        if commonUtils.isOnline():
            self.rcon.login()
        # time.sleep(3)
        # response = self.rcon.exeCommand("travel Canyon?Scenario=Scenario_Crossing_Checkpoint_Insurgents?Game=?Lighting=Day")
        # print(response)
        # f=open("data11.txt","w")
        # f.write(str(response))
        # f.close()
        # time.sleep(5)
        playerDataCenterInstance.stop()
        playerDataCenterInstance.init(self.rcon)
        playerDataCenterInstance.start()
        # logfile = open(gameLogPath, "r", encoding="gbk", errors="ignore")
        if commonUtils.isOnline():
            loglineArray = self.follow()
            for arr in loglineArray:
                for line in arr:
                    if len(line) > 10:
                        self.dispatchEvent(self.parseLog(line))
                        self.dispatchEvent({"event_type": "everyLog", "log": line})
        else:
            logfile = open(configReader.getServerLogFile(), "r", encoding='utf-8')
            lines = logfile.readlines()
            for line in lines:
                time.sleep(0.5)
                self.dispatchEvent(self.parseLog(line))
                self.dispatchEvent({"event_type": "everyLog", "log": line})
            time.sleep(30)
        print("=====退出监听")

    def timerLoop(self):
        while self.isStart:
            time.sleep(1)
            try:
                self.dispatchEvent({"event_type": "timer"})
            except Exception as e:
                logger.writeException()

    def findErrorLoop(self):
        while self.isStart:
            time.sleep(300)
            sys.stdout.flush()

    def stop(self):
        self.isStart = False
        if playerDataCenterInstance is not None:
            playerDataCenterInstance.stop()
        if self.rcon is not None:
            self.rcon.release()

    def parseLog(self, log):
        # if platform.system().lower() == "windows":
        #     if SS_SUBSTR_WINDOWS_ROUND_STARTED in log:
        #         return {"event_type": "roundStateChange", "log": log, "isStart": True}
        #     if SS_SUBSTR_WINDOWS_ROUND_OVER in log:
        #         return {"event_type": "roundStateChange", "log": log, "isStart": False}
        # else:
        #     if SS_SUBSTR_ROUND_STATE_CHANGE in log:
        #         return {"event_type": "roundStateChange", "log": log}
        if SS_SUBSTR_ROUND_STATE_CHANGE in log:
            return {"event_type": "roundStateChange", "log": log}
        elif SS_SUBSTR_GAME_START in log:
            return {"event_type": "gameStart", "log": log}
        elif SS_SUBSTR_GAME_END_NOW in log:
            return {"event_type": "gameEnd", "log": log}
        elif SS_SUBSTR_REGCLIENT_REQUEST in log:
            name = commonUtils.getMid(log, "Name=", "userId")
            uid = commonUtils.getMid(log, "SteamNWI:", "platform")
            if name is not None and uid is not None:
                name = commonUtils.trimPlayerName(name)
                playerDataCenterInstance.addPlayerRequesting(uid, name)
        elif SS_SUBSTR_REGCLIENT_IP in log:
            self.nextPlayerIp = commonUtils.getMid(log, "accepted from:", ":")
        elif SS_SUBSTR_REGCLIENT in log:
            playerName = log[log.find(SS_SUBSTR_REGCLIENT) + len(SS_SUBSTR_REGCLIENT):].strip()
            playerName = commonUtils.trimPlayerName(playerName)
            playerUID = playerDataCenterInstance.getPlayerUidByName(playerName)
            result = {}
            result["event_type"] = "clientSynthAdd"
            result["log"] = log
            result["playerName"] = playerName
            result["playerGUID"] = playerUID
            result["playerIP"] = self.nextPlayerIp
            self.nextPlayerIp = ""
            return result
        elif SS_SUBSTR_UNREGCLIENT in log:
            playerUid = commonUtils.getRight(log, "SteamNWI:")
            result = {}
            result["event_type"] = "clientSynthDel"
            result["log"] = log
            result["playerName"] = playerDataCenterInstance.getPlayerNameByUid(playerUid)
            result["playerGUID"] = playerUid
            playerDataCenterInstance.removePlayer(result["playerName"])
            return result
        elif SS_SUBSTR_TAKE_OBJECTIVE in log:
            return {"event_type": "takeObject", "log": log}
        elif SS_SUBSTR_KILLED in log:
            return {"event_type": "killed", "log": log}
        elif SS_SUBSTR_CHAT in log:
            return {"event_type": "chat", "log": log}
        elif SS_SUBSTR_MAPCHANGE in log:
            return {"event_type": "mapChange", "log": log}
        elif SS_SUBSTR_TRAVEL in log:
            return {"event_type": "travel", "log": log}
        elif SS_SUBSTR_SERVER_ERROR in log:
            return {"event_type": "serverError", "log": log}

    def tryRestart(self):
        path = configReader.getRestartScriptPath()
        if commonUtils.isEmpty(path) or not os.path.exists(path):
            logger.d(self.TAG, "重启游戏脚本(RestartScript)不存在，关闭自动重启功能。")
            return
        ret = commonUtils.findProcessName(commonUtils.getGameProcessMame())
        if ret == True:
            logger.i(self.TAG, "进程存在，无需重启")
            return
        logger.i(self.TAG, "进程不存在，即将重启")
        if commonUtils.isOnline():
            commonUtils.killProcessName(commonUtils.getGameProcessMame())
            time.sleep(3)
            if commonUtils.isWin():
                os.system("start " + path)
            else:
                # TODO tmux
                os.system(path + " &")
            time.sleep(3)
        else:
            logger.i(self.TAG, "测试环境，假装重启")
