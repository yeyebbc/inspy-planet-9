# !/usr/bin/env python
# -*- coding: utf-8 -*
import logging

from lib.tools.logger import logger
from plugins.http_server.chat_record import chat_record_mgr
from lib.game_data_center import gameDataCenterInstance, PlayerData
from lib.player_data_center import playerDataCenterInstance
from lib.tools.common_utils import commonUtils
from lib.tools.config_reader import configReader
from lib.tools.plugin_helper import PluginHelper
from lib.event_callback import EventCallback
from threading import Thread

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from plugins.http_server.html_view_generator import view_gen
from plugins.http_server.import_from_server import dataImporter
from plugins.http_server.local_api import local_api
from plugins.http_server.local_db import local_db
from plugins.http_server.temp_rank_table_manager import temp_rank_table_manager

app = FastAPI()


def init_server_db():
    if not configReader.isMainServer():
        return
    # 创建数据库
    local_db.init()
    # 尝试从服务器导入数据
    dataImporter.import_to_db_from_server()
    # 重启插件刷一次临时表
    temp_rank_table_manager.update_temp_rank_table_if_needed(force=True)

@app.get("/")
def read_root():
    # global data
    return HTMLResponse(create_html(get_json_object()))


@app.get("/api")
def get_json():
    # 在线玩家：玩家名字，分数，是否死亡
    return HTMLResponse(json.dumps(get_json_object()))


@app.get("/test")
def test(id: int = 0):
    print(f"Received id: {id}")
    return {"id": id}

# http://127.0.0.1:8000/view.php
@app.get("/view.php")
def view(serverId: int = -2, dateId: str = "date_today", recordNumId: str = "num_1"):
    if not configReader.isMainServer():
       return HTMLResponse("你请求的不是主服务器")
    html_content = view_gen.generate_html(
        server_id=serverId,  # 使用存在的server_id
        date_id=dateId,
        record_num_id=recordNumId,
        hide_filter=False,
        client_ip="192.168.1.100",
        include_form=True
    )
    return HTMLResponse(html_content)


# http://127.0.0.1:8000/insurgency_web/chat_record.php
@app.get("/chat_record.php")
def chat_record(serverId: int = -2, page: int = 1):
    if not configReader.isMainServer():
       return HTMLResponse("你请求的不是主服务器")
    serverName = configReader.getHttpServerName(str(serverId), "")
    html_content = chat_record_mgr.generate_html(
        server_id=serverId,
        server_name=serverName,
        page=page,
        page_size=20,
        days=30,
        base_url=f"/view.php?serverId={serverId}"
    )
    return HTMLResponse(html_content)


@app.post("/insurgency_web/game_data.php")
async def game_data(request: Request):
    if not configReader.isMainServer():
       return HTMLResponse("你请求的不是主服务器")
    query_params = request.query_params
    serverId = query_params.get('serverId')  # 获取 serverId 参数
    serverKey = query_params.get('serverKey')  # 获取 serverId 参数
    if not configReader.checkServerKey(serverId, serverKey):
        return HTMLResponse(json.dumps({"code":1,"msg":"serverId和serverKey问题:serverId="+serverId+", serverKey="+serverKey}))

    data = await request.json()
    html_content = local_db.insertData(
        data=data
    )
    return HTMLResponse(html_content)


# http://127.0.0.1:8000/rank_top.php?serverId=-2&dateIds=date_today&rankType=score&rankCount=3&allRankTopNum=3
# 公屏查询今天，昨天的第一
@app.get("/insurgency_web/rank_top.php")
def rank_top(serverId: str = "", dateIds: str = -2, rankType: str = 3, rankCount: int = 1,
             allRankTopNum: int = 3):
    if not configReader.isMainServer():
       return HTMLResponse("你请求的不是主服务器")
    html = local_api.get_rank_data(server_id=serverId, date_ids=dateIds, rank_type=rankType,
                                   rank_count=rankCount, all_rank_top_num=allRankTopNum)
    return HTMLResponse(html)


# http://127.0.0.1:8000/player_join_msg_v2.php?serverId=-2&playerGUID=76561198802199179
@app.get("/insurgency_web/player_join_msg_v2.php")
def player_join_msg_v2(serverId: str = "", playerGUID: str = ""):
    if not configReader.isMainServer():
       return HTMLResponse("你请求的不是主服务器")
    html = local_api.get_player_info(server_id=serverId, player_guid=playerGUID)
    return HTMLResponse(html)


# http://127.0.0.1:8000/player_rank_v2.php?serverId=-2&playerGUID=76561198802199179&rankType=score&rankCount=3
# 用于聊天输入排行榜
@app.get("/insurgency_web/player_rank_v2.php")
def player_rank_v2(serverId: str = "", playerGUID: str = "", rankType: str = "", rankCount: int = 1):
    if not configReader.isMainServer():
       return HTMLResponse("你请求的不是主服务器")
    html = local_api.get_player_rank(server_id=serverId, player_guid=playerGUID, rank_type=rankType,
                                     rank_count=rankCount)
    return HTMLResponse(html)


def get_json_object():
    body = {}
    body["player_list"] = getPlayerListDict()
    body["chat_list"] = getChatListDict()
    body["round_info"] = getRoundInfo()
    return body


import json
from datetime import datetime

# 你提供的 JSON 数据（已自动处理 Unicode 转义）
# data = {
#   "player_list": [
#     {"name": "\u6d4b\u8bd51", "uid": "76561198213693677", "score": 620, "killCount": 6, "deadCount": 1, "assistCount": 0, "suicideCount": 1, "takeCount": 2, "joinTime": 1781277605},
#     {"name": "\u6d4b\u8bd52", "uid": "76561198200492423", "score": 860, "killCount": 0, "deadCount": 3, "assistCount": 1, "suicideCount": 0, "takeCount": 3, "joinTime": 1781277605},
#     {"name": "\u6d4b\u8bd53", "uid": "76561198802199179", "score": 1020, "killCount": 0, "deadCount": 0, "assistCount": 0, "suicideCount": 0, "takeCount": 2, "joinTime": 1781277605},
#     {"name": "\u6e2c\u8a664", "uid": "765611991832778", "score": 0, "killCount": 0, "deadCount": 0, "assistCount": 0, "suicideCount": 0, "takeCount": 0, "joinTime": 1781277605}
#   ],
#   "chat_list": [
#     {"uid": "76561198213693677", "name": "\u6d4b\u8bd51", "msg": "help", "time": 1781277620},
#     {"uid": "76561198213693677", "name": "\u6d4b\u8bd51", "msg": "\u8fd9\u662f\u6d4b\u8bd51\u8bf4\u7684", "time": 1781277621}
#   ],
#   "round_info": {
#     "serverId": "-2",
#     "gameStartTime": 1781277602,
#     "roundId": 1,
#     "roundStartTime": 1781277603,
#     "roundEndTime": 0,
#     "mapName": "Hideout",
#     "camp": 1,
#     "takePosition": 2
#   }
# }

# 辅助函数：时间戳转可读字符串
def timestamp_to_str(ts):
    return datetime.fromtimestamp(ts).strftime("%H:%M") if ts else "--:--"


def create_html(data):
    camp = data["round_info"]["camp"]
    campName = "--"
    if camp == 1:
        campName = "政府军"
    elif camp == 2:
        campName = "叛军"
    serverId = data["round_info"]["serverId"]
    if serverId is None or commonUtils.toInt(serverId, 0) <= 0:
        serverId = "--"
    mapName = data["round_info"]["mapName"]
    if commonUtils.isEmpty(mapName):
        mapName = "--"

    roundId = data["round_info"]["roundId"]
    if roundId <= 0:
        roundId = "--"
    # 生成 HTML 内容
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>游戏对局报告</title>
        <style>
            * {{
                box-sizing: border-box;
                font-family: 'Segoe UI', 'Roboto', 'Noto Sans', system-ui, sans-serif;
            }}
            body {{
                background: linear-gradient(145deg, #1a2a3a 0%, #0f1a24 100%);
                margin: 0;
                padding: 30px 20px;
                color: #eef4ff;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
            }}
            /* 卡片通用样式 */
            .card {{
                background: rgba(20, 30, 40, 0.75);
                backdrop-filter: blur(2px);
                border-radius: 2rem;
                padding: 1.5rem 2rem;
                margin-bottom: 2.5rem;
                box-shadow: 0 20px 35px -12px rgba(0,0,0,0.4);
                border: 1px solid rgba(255,255,255,0.1);
                transition: transform 0.2s;
            }}
            .card:hover {{
                transform: translateY(-3px);
            }}
            .card-title {{
                font-size: 1.8rem;
                font-weight: 700;
                margin-bottom: 1.2rem;
                border-left: 6px solid #facc15;
                padding-left: 1rem;
                display: flex;
                align-items: center;
                gap: 12px;
            }}
            .card-title i {{
                font-size: 1.6rem;
            }}
            /* round_info 网格布局 */
            .info-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
                gap: 1rem;
                background: rgba(0,0,0,0.3);
                border-radius: 1.2rem;
                padding: 1.2rem;
            }}
            .info-item {{
                background: #0e1a22;
                border-radius: 1rem;
                padding: 0.8rem 1rem;
                text-align: center;
                box-shadow: inset 0 0 0 1px rgba(255,255,255,0.05), 0 4px 8px rgba(0,0,0,0.2);
            }}
            .info-label {{
                font-size: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 1px;
                color: #9ab3c5;
            }}
            .info-value {{
                font-size: 1.3rem;
                font-weight: bold;
                color: #ffd966;
            }}
            /* 表格样式 */
            .player-table, .chat-table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 0.9rem;
            }}
            .player-table th, .player-table td,
            .chat-table th, .chat-table td {{
                padding: 12px 8px;
                text-align: left;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }}
            .player-table th, .chat-table th {{
                background: #0f212e;
                color: #ffde9c;
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
            .player-table tr:hover, .chat-table tr:hover {{
                background: rgba(255,215,0,0.1);
            }}
            .score-high {{
                font-weight: bold;
                color: #facc15;
            }}
            .kill-badge {{
                background: #2c4b3e;
                padding: 2px 10px;
                border-radius: 40px;
                display: inline-block;
            }}
            .chat-time {{
                color: #8aaec0;
                font-size: 0.75rem;
                font-family: monospace;
            }}
            .chat-msg {{
                background: #1a2f3b;
                padding: 6px 12px;
                border-radius: 20px;
                display: inline-block;
                max-width: 100%;
            }}
            footer {{
                text-align: center;
                margin-top: 30px;
                font-size: 0.75rem;
                color: #7f98aa;
            }}
            @media (max-width: 700px) {{
                .card {{
                    padding: 1rem;
                }}
                .player-table th, .player-table td {{
                    font-size: 0.7rem;
                    padding: 6px 4px;
                }}
            }}
        </style>
    </head>
    <body>
    <div class="container">
        <!-- 第一部分：round_info -->
        <div class="card">
            <div class="card-title">
                <span>📋 当前回合：Round {roundId}</span>
            </div>
            <div class="info-grid">
                <div class="info-item"><div class="info-label">地图</div><div class="info-value">{mapName}</div></div>
                <div class="info-item"><div class="info-label">阵营</div><div class="info-value">{campName}</div></div>
                <div class="info-item"><div class="info-label">已占领点</div><div class="info-value">{gameDataCenterInstance.toPointName(data["round_info"]["takePosition"])}</div></div>
                <div class="info-item"><div class="info-label">服务器ID</div><div class="info-value">{serverId}</div></div>
                <div class="info-item"><div class="info-label">游戏开始时间</div><div class="info-value">{timestamp_to_str(data["round_info"]["gameStartTime"])}</div></div>
                <div class="info-item"><div class="info-label">回合开始时间</div><div class="info-value">{timestamp_to_str(data["round_info"]["roundStartTime"])}</div></div>
            </div>
        </div>

        <!-- 第二部分：player_list -->
        <div class="card">
            <div class="card-title">
                <span>👥 玩家数据 ({len(data["player_list"])})</span>
            </div>
            <div style="overflow-x: auto;">
                <table class="player-table">
                    <thead>
                    <tr>
                        <th>昵称</th><th>UID</th><th>🏆 得分</th><th>💀 击杀</th><th>⚰️ 死亡</th><th>🤝 助攻</th><th>🔫 自杀</th><th>🎯 占点</th><th>加入时间</th>
                    </tr>
                    </thead>
                    <tbody>
    """
    # 按得分排序展示 (可选: 保持原顺序或排序)
    sorted_players = sorted(data["player_list"], key=lambda x: x["score"], reverse=True)
    for p in sorted_players:
        html_content += f"""
                        <tr>
                            <td><strong>{p['name']}</strong></td>
                            <td>{p['uid']}</td>
                            <td class="score-high">{p['score']}</td>
                            <td>{p['killCount']}</td>
                            <td>{p['deadCount']}</td>
                            <td>{p['assistCount']}</td>
                            <td>{p['suicideCount']}</td>
                            <td>{p['takeCount']}</td>
                            <td>{timestamp_to_str(p['joinTime'])}</td>
                        </tr>
        """

    html_content += """
                    </tbody>
                </table>
            </div>
        </div>

        <!-- 第三部分：chat_list -->
        <div class="card">
            <div class="card-title">
                <span>💬 聊天记录</span>
            </div>
            <div style="overflow-x: auto;">
                <table class="chat-table">
                    <thead>
                    <tr><th>玩家</th><th>UID</th><th>消息内容</th><th>时间</th></tr>
                    </thead>
                    <tbody>
    """

    for chat in data["chat_list"]:
        html_content += f"""
                        <tr>
                            <td><strong>{chat['name']}</strong></td>
                            <td>{chat['uid']}</td>
                            <td><span class="chat-msg">{chat['msg']}</span></td>
                            <td class="chat-time">{timestamp_to_str(chat['time'])}</td>
                        </tr>
        """

    html_content += """
                    </tbody>
                </table>
            </div>
        </div>
        <footer>游戏对局报告 · 数据实时生成</footer>
    </div>
    </body>
    </html>
    """
    return html_content

def getPlayerListDict():
    playerList = playerDataCenterInstance.getPlayers()
    if playerList is None:
        return []
    jsonPlayerList = []
    for player in playerList:
        playerData: PlayerData = gameDataCenterInstance.playerDict.get(player.uid)
        if playerData is None:
            continue
        jsonPlayer = {}
        jsonPlayer["name"] = playerData.name
        jsonPlayer["uid"] = playerData.uid
        jsonPlayer["score"] = playerData.score
        jsonPlayer["killCount"] = playerData.killCount
        jsonPlayer["deadCount"] = playerData.deadCount
        jsonPlayer["assistCount"] = playerData.assistCount
        jsonPlayer["suicideCount"] = playerData.suicideCount
        jsonPlayer["takeCount"] = playerData.takeCount
        jsonPlayer["joinTime"] = playerData.joinTime
        # jsonPlayer["leaveTime"] = playerData.leaveTime
        # jsonPlayer["ip"] = playerData.ip
        jsonPlayerList.append(jsonPlayer)
    return jsonPlayerList


def getChatListDict():
    chatList = gameDataCenterInstance.chatList
    if chatList is None:
        return []
    jsonChatList = []
    for chat in chatList:
        jsonChat = {}
        jsonChat["uid"] = chat.uid
        jsonChat["name"] = chat.name
        jsonChat["msg"] = chat.msg
        jsonChat["time"] = chat.time
        jsonChatList.append(jsonChat)
    return jsonChatList


def getRoundInfo():
    roundData = gameDataCenterInstance.roundData
    if roundData is None:
        return {}
    roundData.roundEndTime = 0
    roundData.mapName = gameDataCenterInstance.gameMapName
    roundData.camp = gameDataCenterInstance.gameCamp
    roundData.endReason = ""
    jsonRoundData = {}
    jsonRoundData["serverId"] = roundData.serverId
    # jsonRoundData["gameIsFull"] = roundData.gameIsFull
    jsonRoundData["gameStartTime"] = roundData.gameStartTime
    # jsonRoundData["gameRoundLimit"] = self.roundData.gameRoundLimit
    jsonRoundData["roundId"] = roundData.roundId
    jsonRoundData["roundStartTime"] = roundData.roundStartTime
    # jsonRoundData["roundEndTime"] = roundData.roundEndTime
    jsonRoundData["mapName"] = roundData.mapName
    jsonRoundData["camp"] = roundData.camp
    # jsonRoundData["win"] = roundData.win
    # jsonRoundData["endReason"] = roundData.endReason
    jsonRoundData["takePosition"] = roundData.takePosition
    return jsonRoundData


class HttpServerPlugin(EventCallback):
    helper = PluginHelper()
    register = None

    def __init__(self, register):
        self.register = register
        self.time_seconds = 0
        if configReader.isMainServer():
            init_server_db()

    def enbale(self):
        return configReader.getHttpServerPluginState()

    def init(self, requester):
        self.requester = requester
        self.helper.init(requester)
        if self.enbale():
            server_thread = Thread(target=self.run_server, daemon=True)
            server_thread.start()

    def run_server(self):
        global app
        logger.d("HttpServerPlugin","http server已启动，端口：" + str(configReader.getHttpServerPort()))
        uvicorn.run(app, host="0.0.0.0", port=configReader.getHttpServerPort(), log_level=logging.WARN)

    def timer(self, data):
        self.time_seconds += 1
        if self.time_seconds % 60 == 0:
            temp_rank_table_manager.update_temp_rank_table_if_needed()
