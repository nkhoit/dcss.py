from .connection import LocalConnection, RemoteConnection
from .terminal_buffer import TerminalBuffer
from .player import Player
from .inventory import Inventory
from .map import Map
from .spells import Spells
from .abilities import Abilities
from .screens import Screens
from enum import Enum

import sys
import logging, traceback

logging.basicConfig(
        filename="dcss.py.log",
        level=logging.DEBUG,
        format='%(asctime)s|%(name)s|%(levelname)s|%(message)s')
log = logging.getLogger(__name__)

class Direction(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4

class Client:
    def __init__(self, crawlUserName, crawlPassword, useRemoteConnection):
        self.userName = crawlUserName
        self.screen = Screens.MAIN
        self.player = Player()
        self.inventory = Inventory()
        self.map = Map()
        self.spells = Spells()
        self.abilities = Abilities()
        self.fresh = False
        
        if useRemoteConnection:
            self.conn = RemoteConnection(crawlUserName, crawlPassword)
        else:
            self.conn = LocalConnection(crawlUserName)
        self.terminal = TerminalBuffer()
        if(self.conn and not self.conn.validConnection):
            if(self.conn.connect()):
                self.terminal.input(self.conn.crawl_login())
            else:
                raise Exception("failed to connect")

    def get_screen(self):
        return self.terminal.get_text()

    def get_screen_type(self):
        return self.screen

    def send_command(self, command):
        self.terminal.input(self.conn.send_command(command, False))
        return self.terminal.get_text()

    def check_main_screen(self):
        name = self.terminal.get_text(37, 0, len(self.userName), 1, False)
        return name == self.userName

    def quit(self):
        #TODO:support actually saving/quitting based on a parameter
        self.conn.disconnect()

    def update(self):
        #go through each screen type, and update each parser with that screen
        #at the end, if everything completed properly, mark data as 'fresh'
        result = True

        #if at any point a transition fails, stop trying to update
        #do not update data freshness
        for s in Screens:
            result = result and self.set_screen(s)
            if result:
                self.player.update(s, self.terminal)
                self.inventory.update(s, self.terminal)
                self.map.update(s, self.terminal)
                self.spells.update(s, self.terminal)
                self.abilities.update(s, self.terminal)

        self.fresh = result
        return result

    def set_screen(self, screenType):
        result = True
        if self.screen == screenType:
            return True
        #if we are trying to get to the main screen, send ESC key
        if screenType == Screens.MAIN:
            self.send_command('\x1b')
            result = self.check_main_screen()
        else:
            #moving between secondary screens requires going to main first
            if self.screen != Screens.MAIN:
                result = self.set_screen(Screens.MAIN)
            #ensure transition was successful (if needed)
            if result:
                if screenType == Screens.SKILLS:
                    self.send_command('m')
                elif screenType == Screens.INVENTORY:
                    self.send_command('i')
                elif screenType == Screens.CHARACTER:
                    self.send_command('%')
                elif screenType == Screens.DUNGEON:
                    self.send_command('\x0f')
                elif screenType == Screens.SPELLS:
                    self.send_command('I')
                elif screenType == Screens.RELIGION:
                    self.send_command('^')
                elif screenType == Screens.ABILITIES:
                    self.send_command('a')
                else:
                    raise Exception('Unrecognized screen type: ' + str(screenType))
                #being on the main screen is a precondition for getting here
                #so, if we are not on the main screen after this command
                #the screen transition was successful
                result = not self.check_main_screen()
        if result:
            self.screen = screenType
        return result

if __name__ == '__main__':
    client = Client(sys.argv[1], sys.argv[2], sys.argv[3])
    if not client.conn.validConnection:
        sys.exit(0)
