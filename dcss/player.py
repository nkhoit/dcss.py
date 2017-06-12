from .screens import Screens


class Player():
    def __init__(self):
        self.current_health = None
        self.max_health = None
        self.total_health = None
        self.current_mana = None
        self.max_mana = None
        self.race = None
        self.title = None
        self.armour_class = None
        self.evasion = None
        self.shielding = None
        self.current_str = None
        self.base_str = None
        self.current_int = None
        self.base_int = None
        self.current_dex = None
        self.base_dex = None
        self.place = None
        self.total_auts = None
        self.last_action_duration = None
        self.experience_level = None
        self.next_experience_level = None
        self.wielded_item = None
        self.quivered_item = None
        self.gold = None
        return

    def update(self, screenType, terminal):
        if screenType == Screens.MAIN:
            self._update_health(terminal)
            self._update_mana(terminal)
            self._update_title(terminal)
            self._update_race(terminal)
            self._update_armour_class(terminal)
            self._update_evasion(terminal)
            self._update_shielding(terminal)
            self._update_str(terminal)
            self._update_int(terminal)
            self._update_dex(terminal)
            self._update_experience_level(terminal)
            self._update_next_experience_level(terminal)
            self._update_place(terminal)
            self._update_actions(terminal)
            self._update_wielded_item(terminal)
            self._update_quivered_item(terminal)
        elif screenType == Screens.CHARACTER:
            pass

    # internal helper functions, just for general cleanliness

    def _update_health(self, terminal):
        # grab the health line from the sidebar, up to the = signs
        # then grab the part after the semicolon
        health = terminal.get_text(37, 2, 18, 1).split(':')[
            1].strip().split('/')

        self.current_health = int(health[0])

        if ' ' in health[1]:
            self.max_health = int(health[1].split(' ')[0])
            self.total_health = int(health[1].split(' ')[1][1:-1])
        else:
            self.max_health = int(health[1])
            self.total_health = self.max_health

    def _update_mana(self, terminal):
        # grab the text immediately after 'Mana: ' from the sidebar
        manaInfo = terminal.get_text(37, 3, 18, 1).split(':')[1].split('/')

        self.current_mana = int(manaInfo[0])
        self.max_mana = int(manaInfo[1])

    def _update_title(self, terminal):
        titleInfo = terminal.get_text(37, 0, 0, 1).strip()
        words = titleInfo.split(' ')
        # if the player's name is short enough, the second word is 'the'
        if words[1] == 'the':
            self.title = words[2]
        # if the player's name is too long, the second word is the title
        else:
            self.title = words[1]

    def _update_race(self, terminal):
        # this only changes if in wizmode. but no reason not to support it
        # grab the race from the sidebar, to the end of the line
        self.race = terminal.get_text(37, 1, 0, 1).strip()

    def _update_armour_class(self, terminal):
        # grab AC from the sidebar
        # wizmode displays GDR, so account for that too
        acInfo = terminal.get_text(37, 4, 18, 1).split(':')[1].strip()

        # there will only be a ' ' left after stripming if in wizmode, for GDR
        if ' ' in acInfo:
            self.armour_class = int(acInfo.split(' ')[0])
        else:
            self.armour_class = int(acInfo)

    def _update_evasion(self, terminal):
        # grab EV from sidebar
        self.evasion = int(
            terminal.get_text(
                37, 5, 18, 1).split(':')[1].strip())

    def _update_shielding(self, terminal):
        # grab SH from sidebar
        self.shielding = int(
            terminal.get_text(
                37, 6, 18, 1).split(':')[1].strip())

    def _update_str(self, terminal):
        strInfo = terminal.get_text(55, 4, 0, 1).split(':')[1].strip()
        if ' ' in strInfo:
            self.current_str = int(strInfo.split(' ')[0])
            self.base_str = int(strInfo.split(' ')[1][1:-1])
        else:
            self.current_str = int(strInfo)
            self.base_str = self.current_str

    def _update_int(self, terminal):
        intInfo = terminal.get_text(55, 5, 0, 1).split(':')[1].strip()
        if ' ' in intInfo:
            self.current_int = int(intInfo.split(' ')[0])
            self.base_int = int(intInfo.split(' ')[1][1:-1])
        else:
            self.current_int = int(intInfo)
            self.base_int = self.current_int

    def _update_dex(self, terminal):
        dexInfo = terminal.get_text(55, 6, 0, 1).split(':')[1].strip()
        if ' ' in dexInfo:
            self.current_dex = int(dexInfo.split(' ')[0])
            self.base_dex = int(dexInfo.split(' ')[1][1:-1])
        else:
            self.current_dex = int(dexInfo)
            self.base_dex = self.current_dex

    def _update_experience_level(self, terminal):
        self.experience_level = int(
            terminal.get_text(
                37, 7, 7, 1).split(':')[1] .strip())

    def _update_next_experience_level(self, terminal):
        # make sure to remove '%' character before conversion
        self.next_experience_level = int(terminal.get_text(
            44, 7, 11, 1).split(':')[1] .strip()[:-1])

    def _update_place(self, terminal):
        # make sure to only split on first ':' since they may be in the value
        self.place = terminal.get_text(55, 7, 0, 1).split(':', 1)[1].strip()

    def _update_actions(self, terminal):
        # last action may not exist after a fresh load
        timeInfo = terminal.get_text(55, 8, 0, 1).split(':')[1].strip()
        if ' ' in timeInfo:
            self.total_auts = float(timeInfo.split(' ')[0])
            self.last_action_duration = float(timeInfo.split(' ')[1][1:-1])
        else:
            self.total_auts = float(timeInfo.split(' ')[0])
            self.last_action_duration = 0.0

    def _update_wielded_item(self, terminal):
        # this will just be a key to get the item from inventory
        # since it's just the index, we only need the one character
        self.wielded_item = terminal.get_text(37, 9, 1, 1)
        # minor convenience: if value is '-' (nothing wielded), use None
        if self.wielded_item == '-':
            self.wielded_item = None

    def _update_quivered_item(self, terminal):
        # this will just be a key to get the item from inventory
        # since it's just the index, we only need the one character
        self.quivered_item = terminal.get_text(37, 10, 1, 1)
        # minor convenience: if value is '-' (nothing quivered), use None
        if self.quivered_item == '-':
            self.quivered_item = None
