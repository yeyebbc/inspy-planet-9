import sqlite3
import time
from typing import Dict, Any
from datetime import datetime
import logging

from lib.tools.config_reader import configReader
from lib.tools.logger import logger


class TempRankTableManager:
    """根据其他表数据创建临时排行榜表，查询排名只查询这个表性能高"""

    def __init__(self):
        self.db_path = configReader.getDbPath()
        self._init_config_table()

    def _init_config_table(self):
        """初始化配置表（如果不存在）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_key TEXT NOT NULL UNIQUE,
            config_value TEXT NOT NULL
        )
        ''')

        conn.commit()
        conn.close()

    def get_last_update_time(self) -> int:
        """获取上次更新时间"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT config_value FROM config WHERE config_key = 'update_rank_time'"
            )
            row = cursor.fetchone()
            if row:
                return int(row[0])
            return 0
        except Exception as e:
            logger.e(f"获取上次更新时间失败: {e}")
            return 0
        finally:
            conn.close()

    def set_last_update_time(self, update_time: int = None) -> bool:
        """设置上次更新时间"""
        if update_time is None:
            update_time = int(time.time())

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 使用 INSERT OR REPLACE 来更新或插入配置
            cursor.execute('''
            INSERT OR REPLACE INTO config (config_key, config_value)
            VALUES ('update_rank_time', ?)
            ''', (str(update_time),))

            conn.commit()
            return True
        except Exception as e:
            logger.e(f"设置更新时间失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def recreate_temp_rank_table(self, force: bool = False, min_interval_minutes: int = 30) -> Dict[str, Any]:
        """
        重新创建临时排名表

        Args:
            force: 是否强制更新，忽略时间间隔限制
            min_interval_minutes: 最小更新间隔（分钟）

        Returns:
            包含执行结果的字典
        """
        start_time = time.time()

        # 检查上次更新时间
        if not force:
            last_update_time = self.get_last_update_time()
            diff_seconds = start_time - last_update_time
            diff_minutes = diff_seconds / 60

            if diff_seconds < min_interval_minutes * 60:
                return {
                    "code": 1,
                    "msg": f"need not update, last update time: {diff_seconds:.0f}S ({diff_minutes:.1f} minutes ago)",
                    "data": None
                }

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 删除旧表（如果存在）
            cursor.execute("DROP TABLE IF EXISTS temp_rank_all")
            # 创建新的临时排名表
            # SQLite 的语法与 MySQL 略有不同
            create_sql = """
            CREATE TABLE temp_rank_all AS
            SELECT 
                t1.server_id,
                t1.uid,
                SUM(t1.maxScore) as sumScore,
                SUM(t1.sumKillCount) as sumKillCount,
                SUM(t1.sumTakeCount) as sumTakeCount,
                MAX(t1.maxScore) as maxScore,
                MAX(t1.sumKillCount) as maxKillCount,
                MAX(t1.sumTakeCount) as maxTakeCount,
                SUM(t1.gameIdCount) as gameCount
            FROM (
                SELECT 
                    server_id,
                    uid,
                    MAX(score) as maxScore,
                    SUM(kill_count) as sumKillCount,
                    SUM(take_count) as sumTakeCount,
                    COUNT(DISTINCT game_id) as gameIdCount
                FROM player
                GROUP BY server_id, game_id, uid
            ) t1
            GROUP BY server_id, uid
            ORDER BY sumScore DESC
            """

            cursor.execute(create_sql)
            logger.d("更新临时排名表 temp_rank_all")

            # 获取表中的记录数
            cursor.execute("SELECT COUNT(*) FROM temp_rank_all")
            row_count = cursor.fetchone()[0]

            conn.commit()

            # 更新最后更新时间
            self.set_last_update_time(int(start_time))

            end_time = time.time()
            cost_seconds = end_time - start_time
            diff_seconds = start_time - self.get_last_update_time() if not force else 0

            return {
                "code": 0,
                "msg": f"success, costTime: {cost_seconds:.2f}S, 距离上次更新: {diff_seconds:.0f}S, 记录数: {row_count}",
                "data": {
                    "cost_time": cost_seconds,
                    "last_update_interval": diff_seconds,
                    "record_count": row_count
                }
            }

        except Exception as e:
            logger.e(f"重建临时排名表失败: {e}")
            conn.rollback()
            return {
                "code": 1,
                "msg": f"failed: {str(e)}",
                "data": None
            }
        finally:
            conn.close()

    def update_temp_rank_table_if_needed(self, force: bool = False) -> Dict[str, Any]:
        """
        如果需要则更新临时排名表（带时间检查）

        Args:
            force: 是否强制更新

        Returns:
            执行结果字典
        """
        return self.recreate_temp_rank_table(force=force)

temp_rank_table_manager = TempRankTableManager()
