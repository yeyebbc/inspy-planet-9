import socket
import time
import traceback

from lib.tools import mcrcon
from lib.tools.common_utils import commonUtils
from lib.tools.logger import logger


# 命令	参数	功能
# ban	<id/netid/名字> [时长分钟] [原因]	封禁玩家
# banid	 [时长分钟] [原因]	以steam ID封禁玩家，不需要玩家正在服务器游玩
# gamemodeproperty	 [new value]	获取或设置地图模式属性
# help		显示所有可用命令
# kick	<id/netid/name> [原因]	将玩家踢出服务器
# listban		显示服务器已封禁的所有玩家
# listgamemodeproperties	[property filter]	显示目前可用的游戏模式属性
# listplayers		显示目前正在服务器游玩的玩家
# maps	[level filter]	显示可用的地图
# permaban	<id/netid/name> [原因]	永久封禁玩家
# restartround	[0 = 不换边, 1 = 换边]	重新开始当前回合
# say		像所有玩家发送一条消息，玩家将在左上角看到一条带[Admin]前缀的消息
# scenarios	[level filter]	显示所有可用地图场景
# travel	<目标地图的完整代码>	将游戏地图场景立刻改为其他地图
# travelscenario	<场景代码>	更改到指定场景.
# unban		为用户解封
# mcrcon from https://github.com/barneygale/MCRcon/
class MCrconCommand:
    TAG = "Rcon"

    def __init__(self, ip, port, password):
        self.ip = ip
        self.port = port
        self.password = password
        self.sock = None
        self.retryCount = 0
        self.retrying = False

    def login(self):
        try:
            if self.sock is not None:
                self.sock.close()
                time.sleep(1)
                self.sock = None
            # Connect
            logger.d(self.TAG, "[" + self.ip + ":" + str(self.port) + ":" + ("*" * len(self.password)) + "]")
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(10)
            socket.setdefaulttimeout(10)
            self.sock.connect((self.ip, self.port))
            result = mcrcon.login(self.sock, self.password)
            if result == True:
                logger.d(self.TAG, "rcon连接成功！")
                return True
        except Exception as e:
            if self.sock is not None:
                self.sock.close()
            logger.d(self.TAG, "rcon连接失败，请确认IP、端口、密码是否正确，游戏服务是否启动。")
            logger.writeException()
            return False

    def exeCommand(self, command, logLevel=1):
        if logLevel == 1:
            logger.d(self.TAG, command)
        elif logLevel == 2:
            logger.logMore(self.TAG, command)
        if self.retrying == True:
            logger.logMore("exeCommand", "exeCommand 底层正在重试，本次命令取消执行", command)
            return
        startTime = time.time()
        if not commonUtils.isOnline():
            return
        try:
            return mcrcon.command(self.sock, command)
        except Exception as e:
            self.retry()
        finally:
            costTime = time.time() - startTime
            if costTime > 30:
                logger.e("exeCommand long time:" + str(costTime) + " command=" + command)

    def retry(self):
        if self.retrying:
            return
        self.retrying = True
        commonUtils.getThreadPool().submit(self._retry)

    def _retry(self):
        while True:
            if self.retryCount < 60:
                # 10分钟之内间隔10秒
                time.sleep(10)
            else:
                # 10分钟以上间隔1小时
                time.sleep(60 * 60)
            self.retryCount += 1
            if self.retryCount > 120:
                logger.e(self.TAG, "rcon重试次数用完，停止重试")
                ret = commonUtils.findProcessName("InsurgencyServer")
                logger.e(self.TAG, "游戏进程存在" + str(ret))
                return False
            logger.e(self.TAG, "rcon断开，正在重连:" + str(self.retryCount) + "次")
            ret = self.login()
            if not ret:
                continue
            else:
                logger.e(self.TAG, "rcon重连成功")
                self.retryCount = 0
                self.retrying = False
                return True

    def release(self):
        self.sock.close()
