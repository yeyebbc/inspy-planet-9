import os
import re

from lib.tools.common_utils import commonUtils
from lib.tools.config_reader import configReader


class EnvChecker:
    ''' 检查环境 '''
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def check_env(self):
        if not commonUtils.isOnline():
            return
        logFile = configReader.getServerLogFile()
        if not os.path.exists(logFile):
            raise Exception(f"{logFile}路径不存在")
        # sandstorm_server\Insurgency\Saved
        saved_dir = os.path.dirname(os.path.dirname(logFile))
        self._checkEnginIni(saved_dir)

    def _checkEnginIni(self, saved_dir):
        if commonUtils.isWin():
            enginIniFile = os.path.join(saved_dir, "Config\WindowsServer\Engine.ini")
        else:
            enginIniFile = os.path.join(saved_dir, "Config\LinuxServer\Engine.ini")
        if not os.path.exists(enginIniFile):
            commonUtils.writeFile(enginIniFile, "")

        enginIniText = commonUtils.readFile(enginIniFile)

        # 需要检查的配置
        required = [
            'LogGameplayEvents=Verbose',
            'LogDemo=Verbose',
            'LogObjectives=Verbose',
            'LogGameMode=Verbose',
            'LogINSGameInstance=Verbose',
            'LogUObjectGlobals=Verbose'
        ]

        # 检查每个配置
        missing = []
        for item in required:
            key, value = item.split('=')
            # 简单检查是否包含
            if key not in enginIniText:
                missing.append(item)

        # 输出结果
        if missing:
            print("❌ Engine.ini文件缺少以下配置:")
            for item in missing:
                print(f"  {item}")
