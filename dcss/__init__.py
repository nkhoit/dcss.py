# -*- coding: utf-8 -*-

__title__ = 'dcss'
__license__ = 'MIT'

from .client import Client
from .abilities import Abilities
from .connection import RemoteConnection, LocalConnection
from .inventory import Inventory
from .map import Map
from .player import Player
from .spells import Spells
from .terminal_buffer import TerminalBuffer
from .screens import Screens

import logging

try:
    from logging import NullHandler
except:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
