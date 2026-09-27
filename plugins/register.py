from plugins.admin_plugin import AdminPlugin
from plugins.chat_plugin import ChatPlugin
from plugins.exec_plugin import ExecPlugin
from plugins.game_event_plugin import GameEventPlugin
from plugins.http_server_plugin import HttpServerPlugin
from plugins.join_msg_plugin import JoinMsgPlugin
from plugins.map_vote_plugin import MapVotePlugin
from plugins.pigreetings_plugin import PigreetingsPlugin
from plugins.pitacnomic_plugin import PitacnomicPlugin
from plugins.player_event_plugin import PlayerEventPlugin
from plugins.team_kill_plugin import TeamKillPlugin
from plugins.server_restart_plugin import ServerRestartPlugin
from plugins.sync_data_plugin import SyncDataPlugin
from plugins.update_data_plugin import UpadteDataPlugin
from plugins.piprotect_plugin import PiProtectPlugin

class Register:
    pluginList = None

    def getPluginList(self, pluginList):
        self.pluginList = pluginList
        pluginList.append(PigreetingsPlugin())
        pluginList.append(MapVotePlugin())
        pluginList.append(SyncDataPlugin())
        pluginList.append(JoinMsgPlugin())
        pluginList.append(UpadteDataPlugin())
        pluginList.append(ChatPlugin())
        pluginList.append(ServerRestartPlugin())
        pluginList.append(ExecPlugin())

        pluginList.append(PitacnomicPlugin(self))
        pluginList.append(AdminPlugin(self))
        pluginList.append(TeamKillPlugin(self))
        pluginList.append(PlayerEventPlugin(self))
        pluginList.append(PiProtectPlugin(self))
        pluginList.append(GameEventPlugin())
        pluginList.append(HttpServerPlugin(self))

    def getPlugin(self, cls):
        for plugin in self.pluginList:
            if isinstance(plugin, cls):
                return plugin
        return None
