import sys

from .connection import Connection
from .terminal_buffer import TerminalBuffer
from .player import Player
from .inventory import Inventory
from .map import Map
from .spells import Spells


class Client:
    def __init__(self, crawlConnection):
        self.conn = crawlConnection
        self.screen = TerminalBuffer()
        if(self.conn and not self.conn.validConnection):
            if(self.conn.connect()):
                self.screen.input(self.conn.crawl_login())

    def remote_connect(self, sshUsername, sshPassword):
        return

    def remote_login(self, crawlUsername, crawlPassword):
        return

    def local_connect(self):
        return

    def local_login(self):
        return


if __name__ == '__main__':
    client = Client(Connection.RemoteCC(sys.argv[1], sys.argv[2]))
    if not client.conn.validConnection:
        sys.exit(0)
