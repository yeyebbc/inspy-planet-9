from urllib.parse import quote

import requests
import sqlite3
import json
import os
import logging
from typing import Dict, List, Any

from lib.tools.common_utils import commonUtils
from lib.tools.config_reader import configReader
from lib.tools.logger import logger


class DataImporter:
    def __init__(self):
        """
        初始化数据导入器

        Args:
            sqlite_db_path: SQLite数据库文件路径
        """
        self.db_path = configReader.getDbPath()
        self.conn = None
        self.cursor = None
        self.TAG = "DataImporter"

    def connect(self):
        """连接SQLite数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # 允许按列名访问
        self.cursor = self.conn.cursor()
        # 启用外键约束
        self.cursor.execute("PRAGMA foreign_keys = ON")

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

    def create_table_if_not_exists(self, table_name: str, columns: List[str], column_types: Dict = None):
        """
        创建表（如果不存在）

        Args:
            table_name: 表名
            columns: 列名列表
            column_types: 字段类型信息（从MySQL获取）
        """
        # 检查表是否存在
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        exists = self.cursor.fetchone()

        if not exists and columns:
            # 构建CREATE TABLE语句
            columns_def = []
            for col in columns:
                # 简单的类型映射
                col_type = 'TEXT'  # 默认类型

                # 根据列名或MySQL类型信息猜测SQLite类型
                if column_types and col in column_types:
                    mysql_type = column_types[col].lower()
                    if 'int' in mysql_type:
                        col_type = 'INTEGER'
                    elif 'float' in mysql_type or 'double' in mysql_type or 'decimal' in mysql_type:
                        col_type = 'REAL'
                    elif 'text' in mysql_type or 'blob' in mysql_type:
                        col_type = 'TEXT'
                    elif 'datetime' in mysql_type or 'timestamp' in mysql_type:
                        col_type = 'TEXT'
                else:
                    # 根据列名猜测类型
                    if col.endswith('_id') or col == 'id':
                        col_type = 'INTEGER'
                    elif 'time' in col or 'date' in col:
                        col_type = 'TEXT'
                    elif 'count' in col or 'num' in col or 'amount' in col:
                        col_type = 'INTEGER'
                    elif 'price' in col or 'rate' in col:
                        col_type = 'REAL'

                columns_def.append(f'"{col}" {col_type}')

            create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns_def)})"
            self.cursor.execute(create_sql)
            self.conn.commit()
            logger.d(self.TAG, f"创建表: {table_name}")

    def clear_table_data(self, table_name: str):
        """清空表数据"""
        self.cursor.execute(f"DELETE FROM {table_name}")
        self.conn.commit()
        logger.d(self.TAG, f"清空表数据: {table_name}")

    def import_table_data(self, table_name: str, columns: List[str], rows: List[Dict],
                          column_types: Dict = None, clear_first: bool = False):
        """
        导入表数据

        Args:
            table_name: 表名
            columns: 列名列表
            rows: 数据行列表
            column_types: 字段类型信息
            clear_first: 是否先清空表数据
        """
        if not rows:
            logger.d(self.TAG, f"表 {table_name} 没有数据需要导入")
            return

        # 确保表存在
        self.create_table_if_not_exists(table_name, columns, column_types)

        # 清空已有数据（可选）
        if clear_first:
            self.clear_table_data(table_name)

        # 构建INSERT语句
        placeholders = ', '.join(['?' for _ in columns])
        columns_str = ', '.join([f'"{col}"' for col in columns])
        insert_sql = f"INSERT OR REPLACE INTO {table_name} ({columns_str}) VALUES ({placeholders})"

        # 批量插入数据
        batch_size = 100
        batch_data = []
        total_count = 0

        for row in rows:
            # 确保数据顺序与列对应
            row_data = [row.get(col) for col in columns]
            batch_data.append(row_data)

            if len(batch_data) >= batch_size:
                self.cursor.executemany(insert_sql, batch_data)
                total_count += len(batch_data)
                batch_data = []

        # 插入剩余数据
        if batch_data:
            self.cursor.executemany(insert_sql, batch_data)
            total_count += len(batch_data)

        self.conn.commit()

    def fetch_data_from_api(self, api_url: str, params: dict, tables: List[str] = None, limit: int = 0):
        """
        从API获取数据

        Args:
            api_url: API地址
            server_id: 服务器ID
            tables: 要导出的表列表，None表示导出所有表
            limit: 限制导出的记录数

        Returns:
            解析后的JSON数据
        """
        if tables:
            params['tables'] = ','.join(tables)
        if limit > 0:
            params['limit'] = limit

        logger.d(self.TAG, f"请求API: {api_url}, 参数: {params}")
        text = ""
        try:
            response = requests.post(api_url, data=params, timeout=30)
            # response.raise_for_status()
            if response.status_code == 200:
                text = response.text
                return json.loads(text)
            else:
                text = "status_code:" + str(response.status_code)
        except Exception as e:
            logger.e(self.TAG, f"请求API失败: {e}")
            return None
        finally:
            if len(text) > 200:
                text = text[0:200]
            logger.d(self.TAG, f"返回数据(数据太长日志只显示部分): {text}")

    def import_from_api(self, api_url: str, params: dict, tables: List[str] = None,
                        clear_first: bool = False, limit: int = 0):
        """
        从API获取数据并导入到SQLite

        Args:
            api_url: API地址
            params: 服务器
            tables: 要导入的表列表，None表示导入所有表
            clear_first: 是否先清空表数据
            limit: 限制导出的记录数
        """
        # 获取数据
        logger.d(self.TAG, f"开始从API获取数据 (server={params})...")
        result = self.fetch_data_from_api(api_url, params, tables, limit)

        if not result:
            logger.e(self.TAG, "获取数据失败")
            return 1

        if result.get('code') != 0:
            logger.e(self.TAG, f"API返回错误: {result.get('message')}")
            return 2

        data = result.get('data', {})
        if not data:
            logger.e(self.TAG, "没有数据需要导入")
            return 3
        # 连接数据库
        self.connect()

        try:
            # 开始事务
            self.cursor.execute("BEGIN TRANSACTION")

            # 导入每个表的数据
            for table_name, table_data in data.items():
                columns = table_data.get('columns', [])
                rows = table_data.get('rows', [])
                count = table_data.get('count', 0)
                column_types = table_data.get('columns_info', {})

                logger.d(self.TAG, f"正在导入表: {table_name} ({count} 条记录)")
                self.import_table_data(table_name, columns, rows, column_types, clear_first)

            # 提交事务
            self.conn.commit()

        except Exception as e:
            logger.e(self.TAG, f"导入过程中出错: {e}")
            self.conn.rollback()
            return 4
        finally:
            self.close()
        return 0

    def get_import_from_server_finish(self, db_path):
        """获取上次更新时间"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT config_value FROM config WHERE config_key = 'import_finish'"
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None
        except Exception as e:
            logger.e(f"获取是否导入完成状态失败: {e}")
            return None
        finally:
            conn.close()

    def set_import_from_server_finish(self, serverIdsStr) -> bool:
        """设置导入完成状态"""
        conn = sqlite3.connect(configReader.getDbPath())
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM config WHERE config_key='import_finish'")
            # 使用参数化查询防止 SQL 注入
            cursor.execute(
                "INSERT INTO config (config_key, config_value) VALUES (?, ?)",
                ('import_finish', serverIdsStr)
            )
            conn.commit()  # 重要：提交事务
            return True
        except Exception as e:
            logger.e(f"设置导入完成状态失败: {e}")
            conn.rollback()  # 发生错误时回滚
            return False
        finally:
            conn.close()

    def import_to_db_from_server(self):
        if not configReader.isImportFromInspyServerEnable():
            return
        serverMap = configReader.getHttpServerMap()
        if serverMap is None:
            raise ValueError(
                "发现import_from_inspy_server_enable开启，但是没有设置http_server.server，插件需要知道要导出哪些服务器")
        imported_server_ids = self.get_import_from_server_finish(configReader.getDbPath())
        if imported_server_ids is None:
            imported_server_ids = []

        logger.d(self.TAG, f"之前已导入了这些服务器的数据：{json.dumps(imported_server_ids)}")
        importing_server_ids=[]
        for serverId in serverMap.keys():
            if serverId not in imported_server_ids:
                serverKey = serverMap[serverId][0]
                logger.d(self.TAG, f">>>正在导入服务器{serverId}到本地数据库")
                data = {"serverId": serverId, "serverKey": serverKey}
                API_URL = "http://inspy.yiwowang.com/insurgency_web/export.php"  # 替换为你的PHP接口地址
                # 指定要导出的表（可选），None表示导出所有表
                # TABLES = ['table1', 'table2']
                TABLES = None
                # 限制导出条数（用于测试）
                LIMIT = 0  # 0表示不限
                #
                ret = self.import_from_api(API_URL, data, TABLES, False, LIMIT)
                if ret == 0:
                    importing_server_ids.append(serverId)
                    logger.d(self.TAG, f"从服务器{serverId}导入数据成功！")
                    imported_server_ids.append(serverId)
                    self.set_import_from_server_finish(json.dumps(imported_server_ids))
                else:
                    logger.e(self.TAG,f"从服务器serverId={serverId}导入数据失败！")
        if commonUtils.isEmpty(importing_server_ids):
            logger.d(self.TAG, "本次没有导入")
        else:
            logger.d(self.TAG, f"本次导入的serverId有{json.dumps(importing_server_ids)}")

dataImporter = DataImporter()
