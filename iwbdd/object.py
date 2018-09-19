from .pygame_oo.main_loop import render_sync_stamp


def generate_rectangle_hitbox(w, h):
    return [[1 for x in range(w)] for y in range(h)]


# Object state
# Unanimated: (False, (sheet_cell_x, sheet_cell_y))
# Animated:   (True, animation_speed, [(sheet_cell_x, sheet_cell_y)...], looping [True|False|next animation state])

class Object:
    def __init__(self, screen, x=0, y=0):
        self.screen = screen
        self.x = x
        self.y = y
        self.offset_x = 0
        self.offset_y = 0
        self.hidden = False
        self.spritesheet = None
        self.states = {}
        self.state = ""
        self.animation_frame = 0
        self.time_accumulator = 0
        self.last_sync_stamp = render_sync_stamp
        self.hitbox = None

    def change_state(self, newstate):
        self.state = newstate
        self.time_accumulator = 0
        self.animation_frame = 0

    def draw(self, wnd):
        if not self.hidden and self.spritesheet is not None and self.state in self.states:
            draw_x = self.x + self.offset_x
            draw_y = self.y + self.offset_y
            state = self.states[self.state]
            if state[0]:
                self.time_accumulator += render_sync_stamp - self.last_sync_stamp
                self.last_sync_stamp = render_sync_stamp

                while state[1] > 0 and ((state[3] is False and self.animation_frame == len(state[2]) - 1) or state[3] is not False) and self.time_accumulator > state[1]:
                    self.time_accumulator -= state[1]
                    if state[3] is True:
                        self.animation_frame = (self.animation_frame + 1) % len(state[2])
                    elif state[3] is False:
                        self.animation_frame += 1
                    else:
                        self.animation_frame += 1
                        if self.animation_frame >= len(state[2]):
                            self.state = state[3]
                            self.animation_frame = 0
                            self.draw(wnd)
                            return

                self.spritesheet.draw_cell_to(wnd.display, state[2][self.animation_frame][0], state[2][self.animation_frame][1], draw_x, draw_y)
            else:
                self.spritesheet.draw_cell_to(wnd.display, state[1][0], state[1][1], draw_x, draw_y)
