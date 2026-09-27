import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from html import escape
from urllib.parse import urlencode
import math

from lib.tools.config_reader import configReader


class ChatRecordViewer:
    """聊天记录查看器"""

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
        """过滤敏感词"""
        # 这里可以添加敏感词过滤逻辑
        return self._escape_html(text)

    def _get_chat_list(self, server_id: int, page: int = 1, page_size: int = 20, days: int = 30) -> Dict:
        """
        获取分页聊天记录

        Args:
            server_id: 服务器ID
            page: 当前页码
            page_size: 每页数量
            days: 查询最近多少天的记录

        Returns:
            包含分页数据的字典
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # 计算时间范围（最近N天）
            start_time = int((datetime.now() - timedelta(days=days)).timestamp())

            # 计算偏移量
            offset = (page - 1) * page_size

            # 查询总记录数
            cursor.execute('''
                SELECT COUNT(*) as count 
                FROM chat 
                WHERE server_id = ? AND time >= ?
            ''', (server_id, start_time))
            total_count = cursor.fetchone()['count']

            # 查询分页数据
            cursor.execute('''
                SELECT name, msg, time 
                FROM chat 
                WHERE server_id = ? AND time >= ? 
                ORDER BY time ASC 
                LIMIT ? OFFSET ?
            ''', (server_id, start_time, page_size, offset))

            rows = cursor.fetchall()
            data = [dict(row) for row in rows]

            return {
                'table_count': total_count,
                'pageSize': page_size,
                'data': data,
                'current_page': page
            }

        finally:
            conn.close()

    def _generate_pagination_html(self, data: Dict, base_params: Dict, server_name: str) -> str:
        """
        生成分页HTML

        Args:
            data: 包含分页数据的字典
            base_params: 基础URL参数
            server_name: 服务器名称
        """
        total_count = data['table_count']
        page_size = data['pageSize']
        current_page = data['current_page']

        if total_count == 0:
            return ""

        total_pages = math.ceil(total_count / page_size)

        # 移除page参数，后面会重新添加
        params = {k: v for k, v in base_params.items() if k != 'page'}

        html = '<div class="pagination">'

        # 首页和上一页
        if current_page == 1:
            html += '<span>首页</span> '
            html += '<span>上一个</span> '
        else:
            params['page'] = 1
            html += f'<a href="?{urlencode(params)}">首页</a> '
            params['page'] = current_page - 1
            html += f'<a href="?{urlencode(params)}">上一个</a> '

        # 下一页和尾页
        if current_page == total_pages:
            html += '<span>下一个</span> '
            html += '<span>尾页</span> '
        else:
            params['page'] = current_page + 1
            html += f'<a href="?{urlencode(params)}">下一个</a> '
            params['page'] = total_pages
            html += f'<a href="?{urlencode(params)}">尾页</a> '

        # 显示页码信息
        html += f'<span class="page-info">第{current_page}/{total_pages}页，共{total_count}条记录</span>'
        html += '</div>'

        return html

    def generate_html(
            self,
            server_id: int,
            server_name: str = "",
            page: int = 1,
            page_size: int = 20,
            days: int = 30,
            base_url: str = "/"
    ) -> str:
        """
        生成聊天记录页面HTML

        Args:
            server_id: 服务器ID
            server_name: 服务器名称
            page: 当前页码
            page_size: 每页显示数量
            days: 查询最近多少天
            base_url: 返回首页的URL

        Returns:
            HTML字符串
        """
        if not server_id:
            return ""

        # 获取服务器名称（如果没有传入则从数据库获取）
        if not server_name:
            server_name = self._get_server_name(server_id)

        # 获取聊天记录数据
        chat_data = self._get_chat_list(server_id, page, page_size, days)

        # 构建基础参数（用于分页链接）
        base_params = {
            'serverId': server_id,
            'serverName': server_name
        }

        # 生成分页HTML
        pagination_html = self._generate_pagination_html(chat_data, base_params, server_name)

        # 生成表格行HTML
        table_rows_html = ""
        for row in chat_data['data']:
            name = self._filter_words(row.get('name', ''))
            msg = self._filter_words(row.get('msg', ''))
            time_str = datetime.fromtimestamp(row.get('time', 0)).strftime("%Y-%m-%d %H:%M:%S")

            table_rows_html += f"""
            <tr>
                <td>{name}</td>
                <td>{msg}</td>
                <td>{time_str}</td>
            </tr>
            """

        if not table_rows_html:
            table_rows_html = '<tr><td colspan="3" style="text-align: center;">暂无聊天记录</td></tr>'

        # 生成完整HTML
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>服务器《{self._escape_html(server_name)}》的聊天记录</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
            color: #333;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .server-info {{
            font-size: 18px;
            margin-bottom: 15px;
            padding: 10px;
            background: #f8f9fa;
            border-left: 4px solid #3498db;
        }}
        .back-link {{
            display: inline-block;
            margin-bottom: 15px;
            color: #3498db;
            text-decoration: none;
            padding: 5px 10px;
            border: 1px solid #3498db;
            border-radius: 4px;
            transition: all 0.3s;
        }}
        .back-link:hover {{
            background-color: #3498db;
            color: white;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 14px;
        }}
        table th {{
            background-color: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        table td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        table tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        table tr:hover {{
            background-color: #f1f1f1;
        }}
        .pagination {{
            margin-top: 20px;
            font-size: 14px;
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 5px;
        }}
        .pagination a {{
            display: inline-block;
            padding: 6px 12px;
            background-color: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            transition: background-color 0.3s;
        }}
        .pagination a:hover {{
            background-color: #2980b9;
        }}
        .pagination span {{
            display: inline-block;
            padding: 6px 12px;
            color: #999;
            background-color: #f0f0f0;
            border-radius: 4px;
        }}
        .page-info {{
            margin-left: 10px;
            color: #666;
            background: transparent !important;
        }}
        .server-name {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .info-text {{
            margin-bottom: 15px;
            padding: 10px;
            background: #e8f4fc;
            border-radius: 4px;
        }}
        .no-data {{
            text-align: center;
            padding: 40px;
            color: #999;
        }}
    </style>
</head>
<body>
<div class="container">
    <div class="info-text">
        服务器 <span class="server-name">《{self._escape_html(server_name)}》</span> 的聊天记录，时间范围：最近{days}天
    </div>
    <a href="{base_url}" class="back-link">← 回到服务器首页</a>

    <table>
        <thead>
            <tr>
                <th style="width: 15%">称呼</th>
                <th style="width: 65%">内容</th>
                <th style="width: 20%">时间</th>
            </tr>
        </thead>
        <tbody>
            {table_rows_html}
        </tbody>
    </table>

    {pagination_html}
</div>
</body>
</html>"""

        return html

    def _get_server_name(self, server_id: int) -> str:
        """获取服务器名称"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT server_name FROM server WHERE server_id = ?",
                (server_id,)
            )
            row = cursor.fetchone()
            return self._filter_words(row['server_name']) if row else f"服务器{server_id}"
        finally:
            conn.close()

chat_record_mgr = ChatRecordViewer()  # 使用你的数据库路径
