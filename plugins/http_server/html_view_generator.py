import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from html import escape
import time

from lib.tools.common_utils import commonUtils
from lib.tools.config_reader import configReader


class HTMLViewGenerator:
    """HTML视图生成器"""

    def __init__(self):
        self.db_path = configReader.getDbPath()

    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _escape_html(self, text: str) -> str:
        """转义HTML特殊字符"""
        if not text:
            return ""
        return escape(str(text))

    def _filter_words(self, text: str) -> str:
        """过滤敏感词（简化版，可根据需要扩展）"""
        return self._escape_html(text)

    def _get_player_name_by_ip(self, ip: str) -> Optional[str]:
        """根据IP获取玩家名"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM player WHERE ip = ? ORDER BY id DESC LIMIT 1",
                (ip,)
            )
            row = cursor.fetchone()
            return row['name'] if row else None
        finally:
            conn.close()

    def _get_server_name(self, server_id: int) -> str:
        return configReader.getHttpServerName(str(server_id), "")

    def _get_date_filter_sql(self, date_id: str) -> Tuple[str, str]:
        """
        根据日期ID获取SQL过滤条件和显示文本

        Returns:
            (sql_condition, display_text)
        """
        now = int(time.time())
        today_start = int(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp())

        date_map = {
            "date_today": ("今天", f"AND game_id >= {today_start}"),
            "date_yesterday": ("昨天", f"AND game_id >= {today_start - 86400} AND game_id < {today_start}"),
            "date_month": ("一个月内", f"AND game_id >= {today_start - 30 * 86400}"),
            "date_year": ("一年内", f"AND game_id >= {today_start - 365 * 86400}")
        }

        if date_id in date_map:
            return date_map[date_id][1], date_map[date_id][0]
        return "", "--"

    def _get_rank_limit(self, record_num_id: str) -> int:
        """获取排名显示数量"""
        rank_map = {
            "num_2": 100,
            "num_3": 200,
        }
        return rank_map.get(record_num_id, 30)

    def _get_rank_data(self, server_id: int, date_id: str, record_num_id: str) -> List[Dict]:
        """获取排行榜数据"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            date_condition, _ = self._get_date_filter_sql(date_id)
            limit = self._get_rank_limit(record_num_id)

            # SQLite版本的排行榜查询
            sql = f"""
            SELECT 
                p.name as playerName,
                t1.sumScore,
                t1.maxGameId,
                t1.finalSumKillCount,
                t1.finalSumTakeCount 
            FROM (
                SELECT 
                    t1.uid,
                    SUM(t1.maxScore) as sumScore,
                    MAX(t1.maxGameId) as maxGameId,
                    SUM(t1.sumKillCount) as finalSumKillCount,
                    SUM(t1.sumTakeCount) as finalSumTakeCount 
                FROM (
                    SELECT 
                        uid,
                        MAX(score) as maxScore,
                        MAX(game_id) as maxGameId,
                        SUM(kill_count) as sumKillCount,
                        SUM(take_count) as sumTakeCount 
                    FROM player 
                    WHERE server_id = {server_id} 
                    {date_condition}
                    GROUP BY game_id, uid
                ) t1 
                GROUP BY uid
            ) t1
            JOIN (
                SELECT uid, name 
                FROM player 
                WHERE id IN (
                    SELECT MAX(id) 
                    FROM player 
                    WHERE server_id = {server_id}
                    GROUP BY uid
                )
            ) p ON t1.uid = p.uid
            ORDER BY sumScore DESC 
            LIMIT {limit}
            """

            cursor.execute(sql)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error getting rank data: {e}")
            return []
        finally:
            conn.close()

    def _get_chat_data(self, server_id: int, date_id: str, limit: int = 30) -> List[Dict]:
        """获取聊天数据"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            date_condition, _ = self._get_date_filter_sql(date_id)

            sql = f"""
            SELECT name, msg, time 
            FROM chat 
            WHERE server_id = {server_id} 
            {date_condition} 
            ORDER BY time DESC 
            LIMIT {limit}
            """

            cursor.execute(sql)
            rows = cursor.fetchall()
            # 按时间正序排列（从早到晚）
            return sorted([dict(row) for row in rows], key=lambda x: x['time'])
        except Exception as e:
            print(f"Error getting chat data: {e}")
            return []
        finally:
            conn.close()

    def generate_html(
            self,
            server_id: Optional[int] = None,
            date_id: str = "date_today",
            record_num_id: str = "num_1",
            hide_filter: bool = False,
            client_ip: str = "",
            include_form: bool = True
    ) -> str:
        """
        生成HTML页面

        Args:
            server_id: 服务器ID
            date_id: 日期类型 (date_today, date_yesterday, date_month, date_year, date_all)
            record_num_id: 记录数量 (num_1=30, num_2=100, num_3=200)
            hide_filter: 是否隐藏筛选表单
            client_ip: 客户端IP
            include_form: 是否包含查询表单

        Returns:
            HTML字符串
        """

        # 获取日期显示文本
        _, date_display = self._get_date_filter_sql(date_id)

        # 获取服务器名称
        server_name = ""
        if server_id and not hide_filter:
            server_name = self._get_server_name(server_id)

        # 获取玩家身份信息
        player_identity = ""
        if client_ip:
            player_name = self._get_player_name_by_ip(client_ip)
            if player_name:
                player_identity = f"<div class='player-identity'>您是：{self._filter_words(player_name)}，对吗？</div>"

        # 获取排行榜数据
        rank_data = []
        rank_limit = self._get_rank_limit(record_num_id)
        if server_id:
            rank_data = self._get_rank_data(server_id, date_id, record_num_id)

        # 获取聊天数据
        chat_data = []
        if server_id:
            chat_data = self._get_chat_data(server_id, date_id)

        # 生成HTML
        html = self._render_template(
            server_id=server_id,
            server_name=server_name,
            date_id=date_id,
            date_display=date_display,
            record_num_id=record_num_id,
            hide_filter=hide_filter,
            player_identity=player_identity,
            rank_data=rank_data,
            rank_limit=rank_limit,
            chat_data=chat_data,
            include_form=include_form and not hide_filter
        )

        return html

    def _render_template(
            self,
            server_id: Optional[int],
            server_name: str,
            date_id: str,
            date_display: str,
            record_num_id: str,
            hide_filter: bool,
            player_identity: str,
            rank_data: List[Dict],
            rank_limit: int,
            chat_data: List[Dict],
            include_form: bool
    ) -> str:
        """渲染HTML模板"""

        # 生成筛选表单HTML
        form_html = self._generate_filter_form(server_id, date_id, record_num_id) if include_form else ""

        # 生成排行榜HTML
        rank_html = self._generate_rank_table(rank_data, date_display, rank_limit, server_id)

        # 生成聊天记录HTML
        chat_html = self._generate_chat_table(chat_data, date_display, server_id, server_name)

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <title>沙暴助手</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}

        .container {{
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            padding: 25px;
        }}

        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-top: 0;
        }}

        h4 {{
            color: #3498db;
            margin-bottom: 15px;
        }}

        .welcome {{
            font-size: 18px;
            margin-bottom: 20px;
            padding: 1px 15px;
            background-color: #e8f4fc;
            border-left: 4px solid #3498db;
            border-radius: 4px;
        }}

        .qq-group {{
            font-weight: bold;
            color: #e74c3c;
        }}

        form {{
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 6px;
            margin-bottom: 20px;
        }}

        select, input[type="submit"] {{
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-right: 10px;
        }}

        input[type="submit"] {{
            background-color: #3498db;
            color: white;
            border: none;
            cursor: pointer;
            transition: background-color 0.3s;
        }}

        input[type="submit"]:hover {{
            background-color: #2980b9;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}

        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}

        th {{
            background-color: #3498db;
            color: white;
        }}

        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}

        tr:hover {{
            background-color: #e6f7ff;
        }}

        .gold {{
            color: #ffd700;
            font-weight: bold;
        }}

        .more-link {{
            display: inline-block;
            margin-bottom: 10px;
            color: #3498db;
            text-decoration: none;
            font-weight: bold;
        }}

        .more-link:hover {{
            text-decoration: underline;
        }}

        .player-identity {{
            font-size: 16px;
            color: #27ae60;
            margin: 10px 0;
            padding: 8px;
            background-color: #e8f8f0;
            border-radius: 4px;
        }}

        .no-data {{
            color: #999;
            padding: 20px;
            text-align: center;
        }}

        .server-name-badge {{
            background-color: #e8f4fc;
            padding: 5px 10px;
            border-radius: 4px;
            margin-bottom: 15px;
            display: inline-block;
        }}
    </style>
</head>
<body>
<div class="container">
    {f'<h1>沙暴助手</h1>' if not hide_filter else ''}
    {player_identity}
    {form_html}
    <h4>查询结果：</h4>
    {rank_html}
    <br>
    {chat_html}
</div>
</body>
</html>"""

    def _generate_filter_form(self, server_id: Optional[int], date_id: str, record_num_id: str) -> str:
        """生成筛选表单HTML"""

        # 服务器选项（从数据库获取）
        server_options = self._get_server_options(server_id)

        # 日期选项
        date_options = [
            ("date_today", "今天"),
            ("date_yesterday", "昨天"),
            ("date_month", "一个月内"),
            ("date_year", "一年内"),
            ("date_all", "全部"),
        ]

        # 数量选项
        num_options = [
            ("num_1", "30条"),
            ("num_2", "100条"),
            ("num_3", "200条"),
        ]

        # 生成服务器下拉框
        server_select = '<select name="serverId">'
        for server in server_options:
            selected = ' selected="selected"' if server['id'] == server_id else ''
            server_select += f'<option value="{server["id"]}"{selected}>{self._escape_html(server["name"])}</option>'
        server_select += '</select>'

        # 生成日期下拉框
        date_select = '<select name="dateId">'
        for value, label in date_options:
            selected = ' selected="selected"' if value == date_id else ''
            date_select += f'<option value="{value}"{selected}>{label}</option>'
        date_select += '</select>'

        # 生成数量下拉框
        num_select = '<select name="recordNumId">'
        for value, label in num_options:
            selected = ' selected="selected"' if value == record_num_id else ''
            num_select += f'<option value="{value}"{selected}>{label}</option>'
        num_select += '</select>'

        return f"""
<form method="get" action="">
    {server_select}
    {date_select}
    {num_select}
    <input type="submit" value="查询">
</form>
"""

    def _get_server_options(self, selected_id: Optional[int] = None) -> List[Dict]:
        """获取服务器选项列表"""
        server_options=[]
        map=configReader.getHttpServerMap()
        if not commonUtils.isEmpty(map):
            for key in map.keys():
                server_options.append({"id": key, "name": map[key][1]})
        return server_options

    def _generate_rank_table(self, rank_data: List[Dict], date_display: str, limit: int,
                             server_id: Optional[int]) -> str:
        """生成排行榜表格"""
        if not rank_data:
            return '<p class="no-data">暂无数据</p>'

        html = f'<p><strong>1、{date_display}累计分数排行榜(最多展示{limit}条):</strong></p>'
        html += '<table>'
        html += '<tr><th>序号</th><th>称呼</th><th>累计分数</th><th>累计杀敌</th><th>累计占点数</th></tr>'

        for i, row in enumerate(rank_data, 1):
            gold_icon = '<span class="gold">🥇</span>' if i == 1 else ''
            player_name = self._filter_words(row.get('playerName', ''))
            sum_score = row.get('sumScore', 0)
            kill_count = row.get('finalSumKillCount', 0)
            take_count = row.get('finalSumTakeCount', 0)

            html += f"""
            <tr>
                <td>{i}{gold_icon}</td>
                <td>{player_name}</td>
                <td>{sum_score}</td>
                <td>{kill_count}</td>
                <td>{take_count}</td>
            </tr>
            """

        html += '</table>'
        return html

    def _generate_chat_table(self, chat_data: List[Dict], date_display: str, server_id: Optional[int],
                             server_name: str) -> str:
        """生成聊天记录表格"""
        if not chat_data:
            return '<p class="no-data">暂无聊天记录</p>'

        more_link = ""
        if server_id:
            more_link = f"<a class='more-link' href='/chat_record.php?serverId={server_id}&serverName={server_name}&page=1'>👉 查看更多 👈</a>"

        html = f'<p><strong>2、{date_display}聊天消息({more_link}):</strong></p>'
        html += '<table>'
        html += '<tr><th>序号</th><th>称呼</th><th>消息内容</th><th>时间</th></tr>'

        for i, row in enumerate(chat_data, 1):
            name = self._filter_words(row.get('name', ''))
            msg = self._filter_words(row.get('msg', ''))
            time_str = datetime.fromtimestamp(row.get('time', 0)).strftime("%Y-%m-%d %H:%M:%S")

            html += f"""
            <tr>
                <td>{i}</td>
                <td>{name}</td>
                <td>{msg}</td>
                <td>{time_str}</td>
            </tr>
            """

        html += '</table>'
        return html


# Web框架集成示例（Flask）
def create_flask_app():
    """创建Flask应用"""
    from flask import Flask, request

    app = Flask(__name__)
    view_gen = HTMLViewGenerator()

    @app.route('/')
    def index():
        """首页"""
        server_id = request.args.get('serverId', type=int)
        date_id = request.args.get('dateId', 'date_today')
        record_num_id = request.args.get('recordNumId', 'num_1')
        hide_filter = request.args.get('hideFilter', '0') == '1'
        client_ip = request.remote_addr

        html = view_gen.generate_html(
            server_id=server_id,
            date_id=date_id,
            record_num_id=record_num_id,
            hide_filter=hide_filter,
            client_ip=client_ip,
            include_form=True
        )
        return html

    return app


view_gen = HTMLViewGenerator()  # 使用你的数据库文件名

#
#
# # 使用示例
# if __name__ == "__main__":
#     # 示例1：生成HTML并保存到文件
#     view_gen = HTMLViewGenerator("game.db")  # 使用你的数据库文件名
#
#     html_content = view_gen.generate_html(
#         server_id=-2,  # 使用存在的server_id
#         date_id="date_today",
#         record_num_id="num_1",
#         hide_filter=False,
#         client_ip="192.168.1.100",
#         include_form=True
#     )
#
#     # 保存到文件
#     with open("rank_view.html", "w", encoding="utf-8") as f:
#         f.write(html_content)
#
#     print("HTML已生成并保存到 rank_view.html")
#
#     # 在浏览器中打开（可选）
#     import webbrowser
#
#     # webbrowser.open("rank_view.html")
#
#     # 示例2：启动Flask服务
#     # app = create_flask_app()
#     # app.run(host='0.0.0.0', port=5000)