【更新日志】 2026/08/09 版本2.7  
重要！！！请大家在10月28日之前更新插件，插件版本要大于等于2.7，否则游戏数据会保存失败。  
1、数据服务器从IP更换为域名inspy.yiwowang.com  

【更新日志】 2026/06/20 版本2.6  
1、支持游戏数据保存到自己服务器。详见配置：inspy.cfg-local-db-server-sample.txt  
2、日志统一格式，支持开关：main.enableLog（是否开启控制台日志）和main.enableLogFile（日志是否写入文件）  

【更新日志】 2026/06/12 版本2.5  
1、增加本地化查询网页，玩家可以在浏览器输入http://你的ip:端口查看服务器详细信息（例如http://101.42.161.179:8000），也支持返回json数据，详见插件http_server  

【更新日志】 2026/06/12 版本2.3  
1、exec的killed事件中，支持killerUid和killerTkCount变量，这两个变量组合能够实现tk达到次数踢出玩家，或者警告。支持
2、exec的roundEnd事件中，支持TK最多玩家maxTkCountPlayer和数量maxTkCount。
3、支持过滤掉某些武器造成的tk数量统计，例如能影响exec的killerTkCount变量，具体配置是main.tkWeaponKeywordFilter，设置武器部分关键词即可，多个用|分割。
4、支持某个玩家达到某个分数后，随机提示某些话。具体插件配置见player_event


【更新日志】 2026/05/29 版本2.2  
1、投票换图支持Hold地图  

【更新日志】 2026/05/21 版本2.1  
1、新增exec自定义逻辑插件，支持某个事件发生时，满足某个条件，执行某个命令。详见配置示例inspy.cfg-exec-simple  

【更新日志】 2026/03/10 版本2.0  
1、新增game_event插件，支持在游戏事件中定义消息发送到公屏上，事件包括游戏开始/结束、回合开始/结束、站点成功、击杀，也支持变量。  
2、支持更多变量chat.keywords支持更多变量，包括玩家名字$name，当前回合战绩：杀敌:$killCount;死亡:$deadCount;助攻:$assistCount;站点:$takeCount;最后死亡方式:$lastDeadWay"  
3、支持更高python版本，至少是3.13，3.14也可能支持可以试试。不支持2.7等低版本。

【更新日志】 2026/03/10 版本1.9  
1、修复游戏结束不投票导致无法游戏的问题，请开启piprotect插件，支持指定特定命令（例如换图命令），支持随机执行命令列表（例如随机换图）。  

【更新日志】 2025/08/12 版本1.8  
1、支持随机的欢迎语、广告、AI prompt。  
使用pigreetings.isRandomAds开启随机广告。  
使用pigreetings.connected[0]设置多个，会从中随机展示欢迎语。firstJoinMsg和disconnected也支持  
使用chat.aiPromptList[0]设置多个，会从中随机选择一个。  
因消息太长公屏展示不下，可设置分割阈值：chat.aiMsgSplitThreshold 50  
一次AI消息最多展示的字数：chat.aiMsgMaxWords 150  
  
【更新日志】 2025/07/22 版本1.7  
1、新增TK自定义提示。详见配置里的team_kill  
  
【更新日志】 2025/07/22 版本1.6  
1、新增管理员命令。详见配置里的picladmin  
  
【更新日志】 2025/07/09 版本1.5  
1、增加快捷输入。可以预设关键词和对应的文字，玩家输入关键词即可展示对应的文字。详见配置里的pitacnomic  
  
【更新日志】 2025/07/08 版本1.4  
1、修复一人投票就切地图问题。  
2、AI支持自定义关键词触发。例如设置两个关键词ai和bot: chat.aiKeywords "ai|bot"  
  
【更新日志】 2025/07/07 版本1.3  
1、支持serverKey校验，防止数据被恶意污染。例如配置sync_data.serverKey "112233"，配置完告诉钢钢帮你录入系统  
  
【更新日志】 2025/07/05 版本1.2  
1、支持自定义投票提示  
2、支持设置投票时长  
3、支持结束投票警告提示和时间  
4、支持将MapCycle.txt作为默认地图列表和默认模式