from .object import generate_rectangle_hitbox, generate_circle_hitbox
from .bossfight import Phase, CycleElement, RandomCycleElement, Boss, BossfightObject
from .spritesheet import Spritesheet
from .audio_data import Audio
from .common import CollisionTest, COLLISIONTEST_COLORS
from random import randint
from math import sqrt


class TTSBoss_At(BossfightObject):
    default_hitbox = None

    def __init__(self, screen, x=0, y=0, init_dict=None):
        self.cycle_delay = 0
        super().__init__(screen, x, y, init_dict)
        self.spritesheet = Spritesheet.spritesheets_byname["ss_boss_tts_ats-48-48.png"]
        self.states = {
            "default": (False, (0, 0)),
        }
        self.state = "default"
        self.activation_delay = self.cycle_delay
        if TTSBoss_At.default_hitbox is None:
            TTSBoss_At.default_hitbox = generate_circle_hitbox(22)
        self.hitbox = TTSBoss_At.default_hitbox
        self.hitbox_type = CollisionTest.DEADLY
        self.offset_x = -2
        self.velocity = (0, 0)
        self.moving = False
        self.hidden = True

    def tick(self, scr, ctrl):
        self.screen.objects_dirty = True
        if self.activation_delay < 30:
            self.hidden = False
        if not self.moving:
            self.activation_delay -= 1
            if self.activation_delay <= 0:
                self.velocity = (0, 8)
                self.moving = True
                ctrl.ambience("at.ogg")
        else:
            self.x += self.velocity[0]
            self.y += self.velocity[1]
            if self.x > 1008 or self.y > 768 or self.x < -20 or self.y < -40:
                self.cleanup()


class TTSBoss_Bit(BossfightObject):
    def __init__(self, screen, x=0, y=0, init_dict=None):
        self.cycle_delay = 0
        super().__init__(screen, x, y, init_dict)
        self.spritesheet = Spritesheet.spritesheets_byname["ss_boss_tts_bullets-24-24.png"]
        self.states = {
            "default": (False, (0, 0)),
        }
        self.state = "default"
        self.activation_delay = self.cycle_delay
        self.hitbox = generate_rectangle_hitbox(20, 20)
        self.hitbox_type = CollisionTest.DEADLY
        self.offset_x = -2
        self.velocity = (0, 0)
        self.moving = False

    def tick(self, scr, ctrl):
        self.screen.objects_dirty = True
        if not self.moving:
            self.activation_delay -= 1
            if self.activation_delay <= 0:
                dx = ctrl.player.x - self.x + randint(-25, 25)
                dy = ctrl.player.y - self.y + randint(-25, 25)
                lv = sqrt(dx * dx + dy * dy)
                self.velocity = (dx / lv * 5, dy / lv * 5)
                self.moving = True
                ctrl.ambience("bits.ogg")
        else:
            self.x += self.velocity[0]
            self.y += self.velocity[1]
            if self.x > 1008 or self.y > 768 or self.x < -20 or self.y < -20:
                self.cleanup()


class TTSBoss_Bracket(BossfightObject):
    spritesheet_init = False
    scaled_hitboxes = {}
    cached_hbds = {}
    destroy_as_annoyance = True

    @classmethod
    def precache(cls):
        return
        if not TTSBoss_Bracket.spritesheet_init:
            ss = Spritesheet.spritesheets_byname["ss_object_ttsboss_objects-24-72.png"]
            TTSBoss_Bracket.spritesheet_init = True
            ss.precache_variant(variant_alpha=0, variant_downscale=4)
            ss.precache_variant(variant_alpha=32, variant_downscale=4)
            ss.precache_variant(variant_alpha=64, variant_downscale=4)
            ss.precache_variant(variant_alpha=96, variant_downscale=4)
            ss.precache_variant(variant_alpha=128, variant_downscale=4)
            ss.precache_variant(variant_alpha=160, variant_downscale=4)
            ss.precache_variant(variant_alpha=192, variant_downscale=4)
            ss.precache_variant(variant_alpha=224, variant_downscale=4)
            ss.precache_variant(variant_alpha=255, variant_downscale=4)
            ss.precache_variant(variant_alpha=255, variant_downscale=2.667)
            ss.precache_variant(variant_alpha=255, variant_downscale=2)
            ss.precache_variant(variant_alpha=255, variant_downscale=1.6)
            ss.precache_variant(variant_alpha=255, variant_downscale=1.333)
            ss.precache_variant(variant_alpha=255, variant_downscale=1.143)
            TTSBoss_Bracket.scaled_hitboxes = {
                "opening_square_bracket": [
                    ss.make_hitbox(0, 0, 4),
                    ss.make_hitbox(0, 0, 2.667),
                    ss.make_hitbox(0, 0, 2),
                    ss.make_hitbox(0, 0, 1.6),
                    ss.make_hitbox(0, 0, 1.333),
                    ss.make_hitbox(0, 0, 1.143),
                    ss.make_hitbox(0, 0, 1),
                ],
                "closing_square_bracket": [
                    ss.make_hitbox(1, 0, 4),
                    ss.make_hitbox(1, 0, 2.667),
                    ss.make_hitbox(1, 0, 2),
                    ss.make_hitbox(1, 0, 1.6),
                    ss.make_hitbox(1, 0, 1.333),
                    ss.make_hitbox(1, 0, 1.143),
                    ss.make_hitbox(1, 0, 1),
                ],
                "opening_curly_bracket": [
                    ss.make_hitbox(0, 1, 4),
                    ss.make_hitbox(0, 1, 2.667),
                    ss.make_hitbox(0, 1, 2),
                    ss.make_hitbox(0, 1, 1.6),
                    ss.make_hitbox(0, 1, 1.333),
                    ss.make_hitbox(0, 1, 1.143),
                    ss.make_hitbox(0, 1, 1),
                ],
                "closing_curly_bracket": [
                    ss.make_hitbox(1, 1, 4),
                    ss.make_hitbox(1, 1, 2.667),
                    ss.make_hitbox(1, 1, 2),
                    ss.make_hitbox(1, 1, 1.6),
                    ss.make_hitbox(1, 1, 1.333),
                    ss.make_hitbox(1, 1, 1.143),
                    ss.make_hitbox(1, 1, 1),
                ],
                "opening_parentheses": [
                    ss.make_hitbox(0, 2, 4),
                    ss.make_hitbox(0, 2, 2.667),
                    ss.make_hitbox(0, 2, 2),
                    ss.make_hitbox(0, 2, 1.6),
                    ss.make_hitbox(0, 2, 1.333),
                    ss.make_hitbox(0, 2, 1.143),
                    ss.make_hitbox(0, 2, 1),
                ],
                "closing_parentheses": [
                    ss.make_hitbox(1, 2, 4),
                    ss.make_hitbox(1, 2, 2.667),
                    ss.make_hitbox(1, 2, 2),
                    ss.make_hitbox(1, 2, 1.6),
                    ss.make_hitbox(1, 2, 1.333),
                    ss.make_hitbox(1, 2, 1.143),
                    ss.make_hitbox(1, 2, 1),
                ],
            }
            inst = cls(None)
            for k, hbs in TTSBoss_Bracket.scaled_hitboxes.items():
                TTSBoss_Bracket.cached_hbds[k] = []
                for hbdef in hbs:
                    inst.hitbox = hbdef[0]
                    inst._offset_x = hbdef[1]
                    inst._offset_y = hbdef[2]
                    inst._regen_hitbox(COLLISIONTEST_COLORS[CollisionTest.DEADLY])
                    TTSBoss_Bracket.cached_hbds[k].append(inst.hitbox_draw_surface)

    def __init__(self, screen, x=0, y=0, init_dict=None):
        self.cycle_delay = 0
        self.initial_pos = (x, y)
        self.destination_pos = (0, 0)
        self.direction = -1
        self.move_frames = 112
        self.wiggle_frames = 88
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
        self.activation_delay = self.cycle_delay
        self.stage = 0
        self.stage_delays = [0, 107, 95]
        self.downscales = [4, 2.667, 2, 1.6, 1.333, 1.143]
        self.managed_hbds = True
        self.state_change = False
        self.state_frames = 0
        self.state_status = 0

        self.hidden = self.activation_delay > 0
        self.hitbox = None
        self.hitbox_type = CollisionTest.DEADLY
        self.offset_x = -6
        self.lifetime = 1600

    def draw(self, wnd):
        if self.stage == 0:
            self.variant_alpha = 0
            self.spritesheet.variant_downscale = 4
        if self.stage == 1:
            self.spritesheet.variant_alpha = 256 - (int(self.activation_delay / 12) * 32)
            if self.spritesheet.variant_alpha > 255:
                self.spritesheet.variant_alpha = 255
            self.spritesheet.variant_downscale = 4
        elif self.stage == 2:
            self.spritesheet.variant_alpha = 255
            vs_idx = 5 - (int(self.activation_delay / 16))
            self.spritesheet.variant_downscale = self.downscales[vs_idx]
        elif self.stage > 2:
            self.spritesheet.variant_alpha = 255
            self.spritesheet.variant_downscale = 1
        super().draw(wnd)

    def tick(self, scr, ctrl):
        self.screen.objects_dirty = True
        if self.stage == 0:
            self.activation_delay -= 1
            if self.activation_delay <= 0:
                self.hidden = False
                self.stage = 1
                self.activation_delay = self.stage_delays[1]
            self.hitbox = TTSBoss_Bracket.scaled_hitboxes[self.state][0][0]
            self.offset_x = TTSBoss_Bracket.scaled_hitboxes[self.state][0][1]
            self.offset_y = TTSBoss_Bracket.scaled_hitboxes[self.state][0][2]
            self.hitbox_draw_surface = TTSBoss_Bracket.cached_hbds[self.state][0]
        elif self.stage == 1:
            self.activation_delay -= 1
            if self.activation_delay <= 0:
                self.stage = 2
                self.activation_delay = self.stage_delays[2]
            self.hitbox = TTSBoss_Bracket.scaled_hitboxes[self.state][0][0]
            self.offset_x = TTSBoss_Bracket.scaled_hitboxes[self.state][0][1]
            self.offset_y = TTSBoss_Bracket.scaled_hitboxes[self.state][0][2]
            self.hitbox_draw_surface = TTSBoss_Bracket.cached_hbds[self.state][0]
        elif self.stage == 2:
            t = self.activation_delay / self.stage_delays[2]
            dx = self.initial_pos[0] - self.destination_pos[0]
            dy = self.initial_pos[1] - self.destination_pos[1]
            self.x = int(self.destination_pos[0] + dx * t)
            self.y = int(self.destination_pos[1] + dy * t)
            vs_idx = 5 - (int(self.activation_delay / 16))
            self.hitbox = TTSBoss_Bracket.scaled_hitboxes[self.state][vs_idx][0]
            self.offset_x = TTSBoss_Bracket.scaled_hitboxes[self.state][vs_idx][1]
            self.offset_y = TTSBoss_Bracket.scaled_hitboxes[self.state][vs_idx][2]
            self.hitbox_draw_surface = TTSBoss_Bracket.cached_hbds[self.state][vs_idx]
            self.activation_delay -= 1
            if self.activation_delay <= 0:
                self.stage = 3
        elif self.stage == 3:
            if self.state_status < 2:
                self.x = self.destination_pos[0]
            else:
                self.x = self.destination_pos[0] + self.direction * 300
            self.y = self.destination_pos[1]
            self.hitbox = TTSBoss_Bracket.scaled_hitboxes[self.state][6][0]
            self.offset_x = TTSBoss_Bracket.scaled_hitboxes[self.state][6][1]
            self.offset_y = TTSBoss_Bracket.scaled_hitboxes[self.state][6][2]
            self.hitbox_draw_surface = TTSBoss_Bracket.cached_hbds[self.state][6]

            if self.state_change and not self.state_frames:
                self.state_frames = self.wiggle_frames
                self.state_change = False
            if self.state_frames:
                self.state_frames -= 1
                if self.state_status == 0 or self.state_status == 2:
                    wiggle = (self.state_frames + 5) % 11 - 5
                    if wiggle <= -4:
                        wiggle = -6 - wiggle
                    elif wiggle >= 5:
                        wiggle = 6 - wiggle
                    self.y = self.destination_pos[1] + wiggle
                    if self.state_frames <= 0:
                        self.state_frames = self.move_frames
                        self.state_status += 1
                elif self.state_status == 1:
                    t = (self.move_frames - self.state_frames) / self.move_frames
                    self.x = int(self.destination_pos[0] + self.direction * t * 300)
                    if self.state_frames <= 0:
                        self.state_status = 2
                elif self.state_status == 3:
                    t = self.state_frames / self.move_frames
                    self.x = int(self.destination_pos[0] + self.direction * t * 300)
                    if self.state_frames <= 0:
                        self.state_status = 0

            self.lifetime -= 1
            if self.lifetime <= 0:
                self.cleanup()


class TTSBoss_Cycle_Ats(CycleElement):
    cycle_el_name = "Ats"

    def __init__(self, phase):
        super().__init__(phase)
        self.duration = 400 if self.phase.phase_number > 1 else 800

    def start_cycle_element(self):
        # self.phase.boss.fight_controller.boss_audio("ats_{0}.ogg".format(64 if self.phase.phase_number > 1 else 27))
        self.phase.boss.fight_controller.boss_audio("ats_64.ogg")
        for i in range(64):
            at = TTSBoss_At(self.phase.boss.screen, randint(0, 960), -30, {"cycle_delay": 120 + i * 10})
            at.create(self)


class TTSBoss_Cycle_Brackets(CycleElement):
    cycle_el_name = "Brackets"

    def __init__(self, phase):
        super().__init__(phase)
        self.duration = 2000
        self.next_event = 350
        self.timeout = 1800
        self.last_pick = -1
        self.status = [False, False, False]
        self.status_name = {False: "opening", True: "closing"}
        self.bracket_name = ["square_bracket", "curly_bracket", "parentheses"]
        self.brackets = [[], [], [], [], [], []]

    def start_cycle_element(self):
        y = 0
        xd = 0
        ix = self.phase.boss.x
        iy = self.phase.boss.y + 80
        helper = ("opening_square_bracket", "closing_square_bracket", "opening_curly_bracket", "closing_curly_bracket", "opening_parentheses", "closing_parentheses")
        for i in range(30):
            bit = TTSBoss_Bit(self.phase.boss.screen, ix + i * 3, iy, {"cycle_delay": 70 + i * 9})
            bit.create(self)
        iy += 24
        for i in range(3):
            ix = self.phase.boss.x
            direction = -1
            for j in range(6):
                init_dict = {"state": helper[j], "cycle_delay": 20 + (i * 6 + j) * 10, "destination_pos": (480 + xd, y), "direction": direction}
                if self.phase.phase_number > 1:
                    init_dict["move_frames"] = 80
                    init_dict["wiggle_frames"] = 66
                brack = TTSBoss_Bracket(self.phase.boss.screen, ix, iy, init_dict)
                brack.create(self)
                direction = -direction
                if xd == 0:
                    xd = 48
                else:
                    xd = 0
                    y += 84
                ix += 12
                self.brackets[j].append(brack)
            iy += 24
        if self.phase.phase_number > 1:
            self.phase.boss.fight_controller.boss_audio("prepare_to_die_2.ogg")
        else:
            self.phase.boss.fight_controller.boss_audio("prepare_to_die.ogg")

    def end_cycle_element(self):
        pass
        # for l in self.brackets:
        #     for b in l:
        #        b.cleanup()

    def on_tick(self):
        self.next_event -= 1
        self.timeout -= 1
        if self.timeout <= 0:
            return
        if self.next_event <= 0:
            self.next_event = 90
            which = randint(0, 2)
            if which == self.last_pick:
                which = (which + randint(1, 2)) % 3
            self.last_pick = which
            for elem in self.brackets[2 * which]:
                elem.state_change = True
            for elem in self.brackets[2 * which + 1]:
                elem.state_change = True
            if self.phase.phase_number > 1:
                self.phase.boss.fight_controller.boss_audio("{0}_{1}_2.ogg".format(self.status_name[self.status[which]], self.bracket_name[which]))
            else:
                self.phase.boss.fight_controller.boss_audio("{0}_{1}.ogg".format(self.status_name[self.status[which]], self.bracket_name[which]))
            self.status[which] = not self.status[which]


class TTSBoss_Phase1(Phase):
    phase_name = "Phase 1"

    def __init__(self, boss):
        super().__init__(boss)
        self.phase_number = 1
        # self.cycle = [RandomCycleElement(TTSBoss_Cycle_Brackets, TTSBoss_Cycle_Ats)]
        self.cycle = [TTSBoss_Cycle_Brackets]


class TTSBoss_Phase2(Phase):
    phase_name = "Phase 2"

    def __init__(self, boss):
        super().__init__(boss)
        self.phase_number = 2
        # self.cycle = [RandomCycleElement(TTSBoss_Cycle_Brackets, TTSBoss_Cycle_Ats)]
        self.cycle = [TTSBoss_Cycle_Ats, TTSBoss_Cycle_Brackets]


class TTSBoss(Boss):
    def __init__(self, screen, x=0, y=0, init_dict=None):
        super().__init__(screen, x, y, init_dict)

        TTSBoss_Bracket.precache()

        self.phases = [TTSBoss_Phase1, TTSBoss_Phase2]
        self.spritesheet = Spritesheet.spritesheets_byname["ss_boss_tts-120-120.png"]
        state_frames = [(i - int(i / 15) * 15, int(i / 15)) for i in range(145)]
        self.states = {
            "default": (True, 0.02, state_frames, True)
        }
        self.state = "default"
        self.boss_music = Audio.audio_by_name["omen.ogg"]
        self.initial_x = x
        self.initial_y = y
        self.dir = 1
        self.initial_health = 120
        self.health = 120
        self.t = 0
        self.spritesheet.variant_alpha = 0
        self.hitbox = generate_rectangle_hitbox(120, 120)
        self.hitbox_type = CollisionTest.PASSABLE
        self.wait_for_phase_transition = False
        self.color_frames = 10
        self.color_dir = 1
        self.color_state = 0
        return

        for a in range(0, 255, 32):
            self.spritesheet.precache_variant(variant_alpha=a)
            self.spritesheet.precache_variant(variant_color=(a, a, 255))

    def on_end_cycle_element(self):
        if self.wait_for_phase_transition:
            self.advance_phase()
            self.invulnerable = False
            self.wait_for_phase_transition = False
            self.spritesheet.variant_color = None

    def activate_cutscene(self):
        super().activate_cutscene()
        self.fight_controller.boss_audio("donation.ogg")
        self.fight_controller.need_ready(7000)
        # self.fight_controller.need_ready(1000)
        self.cutscene_acc = 0
        self.cutscene_a = 0
        self.spritesheet.variant_alpha = 0

    def cutscene_tick(self, diff):
        self.cutscene_acc += diff
        a = int(self.cutscene_acc / 7000 * 255)
        if self.cutscene_a < a and not a % 32:
            self.spritesheet.variant_alpha = a
        self.cutscene_a = a

    def activate_fight(self):
        super().activate_fight()
        self.spritesheet.variant_alpha = 255
        self.hitbox_type = CollisionTest.BOSS
        self.hbds_dirty = True

    def fight_tick(self):
        super().fight_tick()
        if self.dead:
            return
        self.t += 0.01 * self.dir
        if self.t >= 1:
            self.t = 2 - self.t
            self.dir = -1
        elif self.t <= -1:
            self.t = -2 - self.t
            self.dir = 1

        self.y = int(self.initial_y - self.t * 150)

        if self.invulnerable:
            self.color_frames -= 1
            if self.color_frames <= 0:
                self.color_frames = 10
                self.color_state += self.color_dir
                if self.color_state == 0:
                    self.spritesheet.variant_color = None
                    self.color_dir = 1
                elif self.color_state == 8:
                    self.spritesheet.variant_color = (0, 0, 0)
                    self.color_dir = -1
                else:
                    self.spritesheet.variant_color = (256 - self.color_state * 32, 256 - self.color_state * 32, 255)

    def interact(self, ctrl):
        super().interact(ctrl)
        if self.health <= 80 and self.phase_idx == 0:
            self.wait_for_phase_transition = True
            if self.health <= 40:
                self.invulnerable = True
                self.spritesheet.variant_color = None
                self.color_frames = 10
                self.color_state = 0
                self.color_dir = 1
