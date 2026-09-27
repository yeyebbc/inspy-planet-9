import json
import sqlite3
from typing import Dict, Any, Optional
import logging

from lib.tools.config_reader import configReader
from lib.tools.logger import logger


class LocalDB:
    """游戏数据导入器"""

    def __init__(self):
        self.TAG = "LocalDB"
        self.db_path = configReader.getDbPath()
        # 确保数据库表存在
        self._init_database()

    def _init_database(self):
        """初始化数据库表（如果不存在）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # round表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS round (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id INTEGER NOT NULL,
            game_id INTEGER NOT NULL,
            game_start_time INTEGER NOT NULL,
            game_is_full INTEGER NOT NULL,
            round_id INTEGER NOT NULL,
            round_start_time INTEGER NOT NULL,
            round_end_time INTEGER NOT NULL,
            map_name TEXT NOT NULL,
            camp INTEGER NOT NULL,
            day_night INTEGER NOT NULL,
            win INTEGER NOT NULL,
            end_reason TEXT NOT NULL,
            take_position TEXT NOT NULL
        )
        ''')

        # player表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS player (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id INTEGER NOT NULL,
            game_id INTEGER NOT NULL,
            round_id INTEGER NOT NULL,
            uid TEXT NOT NULL,
            name TEXT NOT NULL,
            score INTEGER NOT NULL,
            kill_count INTEGER NOT NULL,
            assist_count INTEGER NOT NULL,
            suicide_count INTEGER NOT NULL,
            dead_count INTEGER NOT NULL,
            take_count INTEGER NOT NULL,
            join_time INTEGER NOT NULL,
            leave_time INTEGER NOT NULL,
            ip TEXT NOT NULL,
            kill_way TEXT NOT NULL,
            dead_way TEXT NOT NULL
        )
        ''')

        # chat表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id INTEGER NOT NULL,
            game_id INTEGER NOT NULL,
            round_id INTEGER NOT NULL,
            uid TEXT NOT NULL,
            name TEXT NOT NULL,
            msg TEXT NOT NULL,
            time INTEGER NOT NULL
        )
        ''')

        conn.commit()
        conn.close()

    def init(self):
        pass

    def _get_value(self, value: Any, default_value: Any) -> Any:
        """获取值，如果为空则返回默认值"""
        if value is None or (isinstance(value, str) and len(value.strip()) == 0):
            return default_value
        return value

    def _safe_json_encode(self, data: Any) -> str:
        """安全地将数据编码为JSON字符串"""
        if data is None:
            return "{}"
        try:
            return json.dumps(data, ensure_ascii=False)
        except:
            return "{}"

    def import_round_data(self, round_data: Dict[str, Any]) -> bool:
        """导入回合数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            server_id = self._get_value(round_data.get('serverId'), -1)
            game_start_time = self._get_value(round_data.get('gameStartTime'), -1)
            game_id = game_start_time  # 使用开始时间作为game_id
            game_is_full = self._get_value(round_data.get('gameIsFull'), -1)
            round_id = self._get_value(round_data.get('roundId'), -1)
            round_start_time = self._get_value(round_data.get('roundStartTime'), -1)
            round_end_time = self._get_value(round_data.get('roundEndTime'), -1)
            map_name = self._get_value(round_data.get('mapName'), "")
            camp = self._get_value(round_data.get('camp'), -1)
            day_night = self._get_value(round_data.get('dayNight'), -1)
            win = self._get_value(round_data.get('win'), -1)
            end_reason = self._get_value(round_data.get('endReason'), "")
            take_position = self._get_value(round_data.get('takePosition'), "")

            cursor.execute('''
            INSERT INTO round (
                server_id, game_id, game_start_time, game_is_full, round_id,
                round_start_time, round_end_time, map_name, camp, day_night,
                win, end_reason, take_position
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (server_id, game_id, game_start_time, game_is_full, round_id,
                  round_start_time, round_end_time, map_name, camp, day_night,
                  win, end_reason, take_position))

            conn.commit()
            logger.d(self.TAG, f"成功导入回合数据，game_id: {game_id}, round_id: {round_id}")
            return True

        except Exception as e:
            logger.e(self.TAG, f"导入回合数据失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def import_players(self, player_list: list, server_id: int, game_id: int, round_id: int) -> bool:
        """导入玩家数据"""
        if not player_list:
            return True

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        success_count = 0

        try:
            for player in player_list:
                uid = self._get_value(player.get('uid'), "")
                name = self._get_value(player.get('name'), "")
                score = self._get_value(player.get('score'), 0)
                kill_count = self._get_value(player.get('killCount'), 0)
                dead_count = self._get_value(player.get('deadCount'), 0)
                assist_count = self._get_value(player.get('assistCount'), 0)
                suicide_count = self._get_value(player.get('suicideCount'), 0)
                take_count = self._get_value(player.get('takeCount'), 0)
                join_time = self._get_value(player.get('joinTime'), 0)
                leave_time = self._get_value(player.get('leaveTime'), 0)
                ip = self._get_value(player.get('ip'), "")
                kill_way = self._safe_json_encode(player.get('killWay'))
                dead_way = self._safe_json_encode(player.get('deadWay'))

                cursor.execute('''
                INSERT INTO player (
                    server_id, game_id, round_id, uid, name, score, kill_count,
                    assist_count, suicide_count, dead_count, take_count, join_time,
                    leave_time, ip, kill_way, dead_way
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (server_id, game_id, round_id, uid, name, score, kill_count,
                      assist_count, suicide_count, dead_count, take_count, join_time,
                      leave_time, ip, kill_way, dead_way))

                success_count += 1

            conn.commit()
            return True

        except Exception as e:
            logger.e(self.TAG, f"导入玩家数据失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def import_chats(self, chat_list: list, server_id: int, game_id: int, round_id: int) -> bool:
        """导入聊天数据"""
        if not chat_list:
            return True

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        success_count = 0

        try:
            for chat in chat_list:
                uid = self._get_value(chat.get('uid'), "")
                name = self._get_value(chat.get('name'), "")
                msg = self._get_value(chat.get('msg'), "")
                time = self._get_value(chat.get('time'), 0)

                cursor.execute('''
                INSERT INTO chat (server_id, game_id, round_id, uid, name, msg, time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (server_id, game_id, round_id, uid, name, msg, time))

                success_count += 1

            conn.commit()
            return True

        except Exception as e:
            logger.e(self.TAG, f"导入聊天数据失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def insertData(self, data: dict):
        # 检查roundData
        round_data = data.get("roundData")
        if not round_data:
            return json.dumps({"code": 1, "msg": "params error: roundData missing"})

        # 提取公共参数
        server_id = self._get_value(round_data.get('serverId'), -1)
        game_start_time = self._get_value(round_data.get('gameStartTime'), -1)
        game_id = game_start_time
        round_id = self._get_value(round_data.get('roundId'), -1)

        # 导入回合数据
        if not self.import_round_data(round_data):
            return json.dumps({"code": 3, "msg": "导入回合数据失败"})

        # 导入玩家数据
        player_list = data.get("playerList", [])
        if player_list:
            if not self.import_players(player_list, server_id, game_id, round_id):
                return json.dumps({"code": 4, "msg": "导入玩家数据失败"})

        # 导入聊天数据
        chat_list = data.get("chatList", [])
        if chat_list:
            if not self.import_chats(chat_list, server_id, game_id, round_id):
                return json.dumps({"code": 5, "msg": "导入聊天数据失败"})

        return json.dumps({"code": 0, "msg": "success"})


local_db = LocalDB()
