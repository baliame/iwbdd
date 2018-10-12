from .bossfight import Phase, CycleElement, RandomCycleElement


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