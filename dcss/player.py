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
        self.armor_class = None
        self.evasion = None
        self.shielding = None
        self.current_str = None
        self.base_str = None
        self.current_int = None
        self.base_int = None
        self.current_dex = None
        self.base_dex = None
        self.place = None
        self.total_actions = None
        self.last_action_duration = None
        self.experience_level = None
        self.next_experience_level = None
        self.wielded_item = None
        self.gold = None
        return
    
    def update(self, screenType, screen):
        if screenType == Screens.MAIN:
            #TODO:implement the stuffs and things
            pass
        elif screenType == Screens.CHARACTER:
            pass

