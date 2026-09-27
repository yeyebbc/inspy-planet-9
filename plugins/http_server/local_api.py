import sqlite3
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

class LocalApi:
    def __init__(self, db_path: str = 'game.db'):
        """初始化数据库连接"""
        self.db_path = db_path

    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def execute(self, sql: str, params: tuple = ()) -> int:
        """执行 SQL，返回影响的行数"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            affected = cursor.rowcount
            conn.commit()
            return affected
        finally:
            conn.close()

    def query_all(self, sql: str, params: tuple = ()) -> List[Dict]:
        """查询所有记录"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def query_one_row(self, sql: str, params: tuple = ()) -> Optional[Dict]:
        """查询单条记录"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def query_rows(self, sql: str, max_count: int, params: tuple = ()) -> List[Dict]:
        """查询多条记录，限制最大数量"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchmany(max_count)
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def query_player_score_data(self, server_id: int, player_guid: str, result: Dict) -> bool:
        """查询玩家分数数据"""
        sql = """
            SELECT sumScore, sumKillCount, sumTakeCount, 
                   maxScore, maxKillCount, maxTakeCount, gameCount
            FROM temp_rank_all
            WHERE server_id = ? AND uid = ?
        """
        row = self.query_one_row(sql, (server_id, player_guid))

        if row:
            result["sumScore"] = row["sumScore"]
            result["sumKillCount"] = row["sumKillCount"]
            result["sumTakeCount"] = row["sumTakeCount"]
            result["maxScore"] = row["maxScore"]
            result["maxKillCount"] = row["maxKillCount"]
            result["maxTakeCount"] = row["maxTakeCount"]
            result["gameCount"] = row["gameCount"]
            return True
        return False

    def query_rank_index(self, rank_field: str, server_id: int, player_guid: str) -> Optional[int]:
        """查询玩家排名"""
        # SQLite 实现排名查询
        sql = f"""
            SELECT uid FROM temp_rank_all
            WHERE server_id = ?
            ORDER BY {rank_field} DESC
        """
        rows = self.query_all(sql, (server_id,))

        for idx, row in enumerate(rows, 1):
            if row["uid"] == player_guid:
                return idx
        return None

    def query_player_name(self, uid: str) -> str:
        """查询玩家名称"""
        sql = "SELECT name FROM player WHERE uid = ? ORDER BY id DESC LIMIT 1"
        row = self.query_one_row(sql, (uid,))
        return row["name"] if row else ""

    def query_rank_top(self, rank_type: str, server_id: int, num: int) -> List[Dict]:
        """查询排行榜前 N 名"""
        rank_field = self.get_rank_field(rank_type)
        sql = f"""
               SELECT uid FROM temp_rank_all
               WHERE server_id = ?
               ORDER BY {rank_field} DESC
               LIMIT ?
           """
        rows = self.query_all(sql, (server_id, num))

        result = []
        for idx, row in enumerate(rows, 1):
            player_name = self.query_player_name(row["uid"])
            result.append({
                "rankIndex": idx,
                "uid": row["uid"],
                "name": player_name
            })

        return result
    def get_rank_data(self,
            server_id: int,
            date_ids: Optional[str] = None,
            rank_type: str = "score",
            rank_count: int = 3,
            all_rank_top_num: Optional[int] = None
    ) -> str:
        """获取排行榜数据（对应 PHP 代码）"""

        # 处理 dateIds
        if date_ids:
            date_id_list = date_ids.split(",")
        else:
            date_id_list = ["date_yesterday", "date_today"]

        # 处理 rankCount
        if not rank_count:
            rank_count = 3
        if rank_count > 20:
            rank_count = 20

        # 处理 rankType
        if not rank_type:
            rank_type = "score"

        result = {}

        # 查询各日期的排行榜
        for date_id in date_id_list:
            top_players = self.query_rank_top_where(server_id, rank_count, date_id, rank_type)
            if top_players:
                result[date_id] = top_players

        # 查询总榜
        if all_rank_top_num:
            all_rank_top_players = self.query_rank_top(rank_type, server_id, all_rank_top_num)
            if all_rank_top_players:
                result["allRankTopPlayers"] = all_rank_top_players

        # 返回结果
        if result:
            return self.create_data(0, "success", result)
        else:
            return self.create_data(1, "error: no info", None)

    def query_rank_top_where(self, server_id: int, num: int, date_id: str, rank_type: str) -> List[Dict]:
        """根据日期查询排行榜"""
        rank_field = self.get_rank_field(rank_type)
        offset = 7200
        now = datetime.now()

        # 构建日期条件
        if date_id == 'date_today':
            start_time = int(datetime(now.year, now.month, now.day).timestamp()) + offset
            date_condition = f"AND game_id > {start_time}"
        elif date_id == 'date_yesterday':
            yesterday = now - timedelta(days=1)
            start_time = int(datetime(yesterday.year, yesterday.month, yesterday.day).timestamp()) + offset
            end_time = int(datetime(now.year, now.month, now.day).timestamp()) + offset
            date_condition = f"AND game_id > {start_time} AND game_id < {end_time}"
        elif date_id == 'date_month':
            month_ago = now - timedelta(days=30)
            start_time = int(datetime(month_ago.year, month_ago.month, month_ago.day).timestamp())
            date_condition = f"AND game_id > {start_time}"
        elif date_id == 'date_year':
            year_ago = now - timedelta(days=365)
            start_time = int(datetime(year_ago.year, year_ago.month, year_ago.day).timestamp())
            date_condition = f"AND game_id > {start_time}"
        else:
            date_condition = ""

        sql = f"""
            SELECT t1.name as playerName,
                   SUM(t1.maxScore) as sumScore,
                   MAX(t1.maxGameId) as maxGameId,
                   SUM(t1.sumKillCount) as sumKillCount,
                   SUM(t1.sumTakeCount) as sumTakeCount
            FROM (
                SELECT name,
                       MAX(score) as maxScore,
                       MAX(game_id) as maxGameId,
                       SUM(kill_count) as sumKillCount,
                       SUM(take_count) as sumTakeCount
                FROM player
                WHERE server_id = ? {date_condition}
                GROUP BY game_id, name
            ) t1
            GROUP BY name
            ORDER BY {rank_field} DESC
            LIMIT ?
        """

        return self.query_all(sql, (server_id, num))

    def get_rank_field(self, rank_type: str) -> str:
        """根据排名类型获取字段名"""
        rank_fields = {
            "score": "sumScore",
            "kill": "sumKillCount",
            "take": "sumTakeCount"
        }
        return rank_fields.get(rank_type, "sumScore")

    def get_player_info(self, server_id: int, player_guid: str) -> str:
        result = {}

        # 查询排名（SQLite 兼容写法）
        sql = """
            SELECT uid FROM temp_rank_all
            WHERE server_id = ?
            ORDER BY sumScore DESC
        """
        rows = self.query_all(sql, (server_id,))

        rank_index = None
        for idx, row in enumerate(rows, 1):
            if row["uid"] == player_guid:
                rank_index = idx
                break

        if not rank_index:
            result["rankIndex"] = ""
        else:
            result["rankIndex"] = rank_index
        result["joinName"] = ""
        # 查询玩家分数数据
        ret = self.query_player_score_data(server_id, player_guid, result)

        if ret:
            return self.create_data(0, "success", result)
        else:
            return self.create_data(1, "error", result)

    def get_player_rank(
            self,
            server_id: int,
            player_guid: str,
            rank_type: str = "score",
            rank_count: int = 3
    ) -> str:
        """获取玩家排名数据"""

        if not rank_count:
            rank_count = 3
        if rank_count > 20:
            rank_count = 20
        if not rank_type:
            rank_type = "score"

        if not player_guid:
            return self.create_data(1, "参数为空", "")

        score_rank_index = self.query_rank_index("sumScore", server_id, player_guid)
        take_rank_index = self.query_rank_index("sumTakeCount", server_id, player_guid)
        kill_rank_index = self.query_rank_index("sumKillCount", server_id, player_guid)

        top_players = self.query_rank_top(rank_type, server_id, rank_count)

        result = {
            "scoreRankIndex": score_rank_index,
            "takeRankIndex": take_rank_index,
            "killRankIndex": kill_rank_index,
            "topPlayers": top_players
        }

        self.query_player_score_data(server_id, player_guid, result)

        if score_rank_index:
            return self.create_data(0, "success", result)
        else:
            return self.create_data(1, "error: no info", None)

    def create_data(self, code: int, msg: str, inner_data: Any) -> str:
        """创建 JSON 响应数据"""
        data = {
            "msg": msg,
            "code": code,
            "data": inner_data
        }
        # 如果需要调试输出，可以取消注释
        # if debug:
        #     var_dump(data)
        import json
        return json.dumps(data, ensure_ascii=False)

local_api = LocalApi()