from .connection import LocalConnection, RemoteConnection
from .terminal_buffer import TerminalBuffer
from .player import Player
from .inventory import Inventory
from .map import Map
from .spells import Spells
from enum import Enum

import sys
import logging, traceback

logging.basicConfig(
        filename="dcss.py.log",
        level=logging.DEBUG,
        format='%(asctime)s|%(name)s|%(levelname)s|%(message)s')
log = logging.getLogger(__name__)

class Screens(Enum):
    MAIN = 1
    SKILLS = 2
    INVENTORY = 3
    CHARACTER = 4
    DUNGEON = 5
    SPELLS = 6
    RELIGION = 7

class Client:
    def __init__(self, crawlUserName, crawlPassword, useRemoteConnection):
        self.userName = crawlUserName
        self.screen = Screens.MAIN
        self.player = Player()
        self.inventory = Inventory()
        self.map = Map()
        self.spells = Spell()
        
        if useRemoteConnection:
            self.conn = RemoteConnection(crawlUserName, crawlPassword)
        else:
            self.conn = LocalConnection()
        self.terminal = TerminalBuffer()
        if(self.conn and not self.conn.validConnection):
            if(self.conn.connect()):
                self.terminal.input(self.conn.crawl_login())

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


    #BEGIN: COMMAND LIST
    #does python have regions? that's what I'm going for here
    #these are all the functions that encapsulate commands

    def main_screen(self):
        #if we aren't on the main screen, then try sending an ESC key
        if self.screen == Screens.MAIN:
            return true
        self.send_command('\x1b')
        result = self.check_main_screen()
        if result:
            self.screen = Screens.MAIN
        return result

    def skills_screen(self):
        #we only know how to get to skills screen from the main screen
        if self.screen != Screens.MAIN:
            return False
        self.send_command('m')
        #if we send the skills command, and are no longer on the main screen
        #we must be on the skills screen (hopefully?)
        result = not self.check_main_screen()
        if result:
            self.screen = Screens.SKILLS
        return result

    def inventory_screen(self):
        if self.screen != Screens.MAIN:
            return False
        self.send_command('i')
        result = not self.check_main_screen()
        if result:
            self.screen = Screens.INVENTORY
        return result

    def character_screen(self):
        if self.screen != Screens.MAIN:
            return False
        self.send_command('%')
        result = not self.check_main_screen()
        if result:
            self.screen = Screens.CHARACTER
        return result

    def dungeon_screen(self):
        if self.screen != Screens.MAIN:
            return False
        self.send_command('\x0f')
        result = not self.check_main_screen()
        if result:
            self.screen = Screens.DUNGEON
        return result

    def spells_screen(self):
        if self.screen != Screens.MAIN:
            return False
        self.send_command('I')
        result = not self.check_main_screen()
        if result:
            self.screen = Screens.SPELLS
        return result

    def religion_screen(self):
        if self.screen != Screens.MAIN:
            return False
        self.send_command('^')
        result = not self.check_main_screen()
        if result:
            self.screen = Screens.RELIGION
        return result


    #END: COMMAND LIST

if __name__ == '__main__':
    client = Client(sys.argv[1], sys.argv[2], sys.argv[3])
    if not client.conn.validConnection:
        sys.exit(0)
