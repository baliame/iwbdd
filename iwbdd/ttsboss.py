from .bossfight import Phase, CycleElement, RandomCycleElement, Boss, BossfightObject
from .spritesheet import Spritesheet


class TTSBoss_Bracket(BossfightObject):
    def __init__(self, screen, x=0, y=0, init_dict=None):
        self.cycle_delay = 0
        self.initial_pos = (x, y)
        self.destination_pos = (0, 0)
        super().__init__(screen, x, y, init_dict)
        self.spritesheet = Spritesheet.spritesheets_byname["ss_object_ttsboss_objects-24-72.png"]
        self.states = {
            "opening_square_bracket": (False, (0, 0)),
            "closing_square_bracket": (False, (1, 0)),
            "opening_curly_bracket": (False, (0, 1)),
            "closing_curly_bracket": (False, (1, 1)),
            "opening_parentheses": (False, (0, 2)),
            "closing_parentheses": (False, (1, 2)),
        }


class TTSBoss_Cycle_Brackets(CycleElement):
    def __init__(self, phase):
        super().__init__(phase)
        self.duration = 900




class TTSBoss_Phase1(Phase):
    pass


class TTSBoss(Boss):
    def __init__(self, screen, x=0, y=0, init_dict=None):
        super().__init__(screen, x, y, init_dict)
        self.fight_controller = screen.world.bossfight
        self.phases = [TTSBoss_Phase1, TTSBoss_Phase2, TTSBoss_Phase3]

    def activate_cutscene(self):
        self.fight_controller.boss_audio("donation.ogg")
        self.fight_controller.need_ready(9000)

    def fight_tick(self, advance):
        pass
