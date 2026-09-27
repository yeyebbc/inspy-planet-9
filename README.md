<font color="red">重要！！！请大家在10月28日之前更新插件，插件版本要大于等于2.7，否则游戏数据会保存失败。</font>  
免费开源的沙暴插件，非盈利性质，您也可以选择捐助。    
欢迎加群，一起交流技术，也可以提建议。  
QQ群：816532871  
## 一、📝 更新日志  
【更新日志】 2026/08/22 版本2.8  
1、丰富TK插件，支持TK队友不道歉强制踢出功能，过滤武器库爆炸导致的TK，详见配置里的team_kill。  
2、日志支持是否开启详细日志：main.enableMoreLog，默认关闭，防止日志太多。  

【更新日志】 2026/08/09 版本2.7  
重要！！！请大家在10月28日之前更新插件，插件版本要大于等于2.7，否则游戏数据会保存失败。  
1、数据服务器从IP更换为域名inspy.yiwowang.com  

【更新日志】 2026/06/20 版本2.6  
1、支持游戏数据保存到自己服务器。详见配置：inspy.cfg-local-db-server-sample.txt
2、日志统一格式，支持开关：main.enableLog（是否开启控制台日志）和main.enableLogFile（日志是否写入文件）  

【更新日志】 2026/06/12 版本2.5  
1、增加本地化查询网页，玩家可以在浏览器输入http://你的ip:端口查看服务器详细信息（例如http://101.42.161.179:8000），详见插件http_server  

详见 [CHANGELOG.md](CHANGELOG.md)  

## 二、功能介绍：  
这是一个免费开源的叛乱沙漠风暴游戏服务器软件，服主将此软件运行在游戏服务器上，可以实现很多功能：  
1、自定义玩家欢迎语，支持头衔称号/外号，玩家地理位置  
2、称号系统，可以设置达到某个分数后，设置对应的称号  
3、服务器滚动广告  
4、投票换图，玩家可以投票换图，包含白天夜间，政府军叛军  
5、输入排名查询自己排名和游戏信息  
6、保存玩家数据到服务器，永久查询玩家数据，可以通过web端查看玩家数据，以及聊天。查询网址：  
http://inspy.yiwowang.com/index.php?serverId=3&dateId=date_month&recordNumId=num_1  
7、修复卡界面进不去游戏的问题。  
8、tk队友自定义提示  
9、自定义逻辑，服主可以设置事件、条件、执行的命令。例如：回合开始事件，判断输了次数>3，执行降低难度的命令  
10、监听游戏事件后可自定义消息发送公屏上    
  
## 三、下载inspy到服务器:  
如果你没有inspy，请下载git并且执行下面代码下载inspy  
git clone https://gitee.com/yiwowang/inspy.git  
  
## 四、配置日志级别  
修改文件Insurgency/Saved/Config/LinuxServer/Engine.ini  
内容修改为这样：  
[Core.Log]  
LogGameplayEvents=Verbose  
LogDemo=Verbose  
LogObjectives=Verbose  
LogGameMode=Verbose  
LogINSGameInstance=Verbose  
LogUObjectGlobals=Verbose  
  
## 五、配置插件：  
最简单办法将inspy.cfg-sample改为inspy.cfg，然后搜索TODO，将TODO的变量写正确了就能运行。也可以继续阅读下面配置方法。  
1、打开inspy.cfg文件，
根据自己需求配置  
例如设置rcon密码，以及GameLogFile参数  
其中下面这个很重要，重要！！ 因为这个serverId和serverKey每个服不一样，需要自己免费申请 http://106.75.232.195/insurgency_web/apply.php  
sync_data.serverId -1  
sync_data.serverKey "需申请"  

本地配置 `inspy-my.cfg` 可使用 `${变量名}` 引用 RCON 密码、`sync_data.serverKey` 和 DeepSeek API 密钥。复制 `.env.example` 为 `.env`，填写实际值后安装 `requirements.txt` 中的依赖再启动。项目启动时读取根目录的 `.env`；已设置的系统环境变量优先于 `.env`。例如：

```text
sissm.RconPassword "${RCON_PASSWORD}"
sync_data.serverKey "${SERVER_KEY}"
chat.deepseekKey "${DEEPSEEK_API_KEY}"
```

`http_server.server[n]` 中的 ServerKey 也可使用 `${变量名}`，例如 `1|${SERVER_KEY}|服务器名`。引用的变量缺失时会报错；留空的 `DEEPSEEK_API_KEY` 会保持 AI 功能未配置的状态。`.env` 包含敏感信息，已被 Git 忽略。
  
## 六、安装插件：  
>Linux系统：  
1、 执行su，然后输入密码  
执行apt install python3-pip  
2、再执行install.sh安装依赖  
3、 ./start.sh  

>Windows系统：  
1、安装python:  
https://www.python.org/ftp/python/3.11.6/python-3.11.6-amd64.exe  
安装时勾选：add python.exe to PATH  
2、执行install.bat安装依赖  
3、执行运行插件start.bat  

## 七、后续更新插件  
1、强烈建议第一次下载插件，使用git，并且git clone https://gitee.com/yiwowang/inspy.git ，后续只需要执行update.sh或update.bat来更新插件  
2、如果没用git，每次都要自己下载插件并覆盖文件，要注意备份和恢复inspy.cfg。  