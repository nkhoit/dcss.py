from .connection import LocalConnection, RemoteConnection
from .terminal_buffer import TerminalBuffer
from .player import Player
from .inventory import Inventory
from .map import Map
from .spells import Spells

import sys
import logging, traceback

log = logging.getLogger(__name__)

class Client:
    def __init__(self, crawlUserName, crawlPassword, useRemoteConnection):
        self.userName = crawlUserName
        if useRemoteConnection:
            self.conn = RemoteConnection(crawlUserName, crawlPassword)
        else:
            self.conn = LocalConnection()
        self.screen = TerminalBuffer()
        if(self.conn and not self.conn.validConnection):
            if(self.conn.connect()):
                self.screen.input(self.conn.crawl_login())

    def get_screen(self):
        return self.screen.get_text()

    def send_command(self, command):
        self.screen.input(self.conn.send_command(command, False))
        return self.screen.get_text()


if __name__ == '__main__':
    client = Client(sys.argv[1], sys.argv[2], sys.argv[3])
    if not client.conn.validConnection:
        sys.exit(0)
