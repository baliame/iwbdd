from .world import World
from .player import Player


class Controller:
    instance = None
    terminal_velocity = 3

    def __init__(self, main_loop):
        if Controller.instance is not None:
            raise RuntimeError("Editor must be a singleton.")
        Controller.instance = self

        self.worlds = []
        self.current_world = None
        self.current_screen = None

        self.player = None

    def add_loaded_world(self, world):
        self.worlds.append(world)
        if self.current_world is None:
            self.current_world = world
            self.current_screen = self.current_world.screens[self.current_world.starting_screen_id]

    def load_world_from_file(self, world):
        loaded_world = World(world)
        self.worlds.append(loaded_world)
        if self.current_world is None:
            self.current_world = loaded_world
            self.current_screen = self.current_world.screens[self.current_world.starting_screen_id]

    def create_player(self):
        if self.player is None:
            self.player = Player()

    def simulate(self):
        if self.player.cached_collision is None:
            self.player.cached_collision = self.current_screen.test_terrain_collision(self.player.x, self.player.y, self.player.hitbox)
        pass

    @staticmethod
    def render_elements_callback(wnd):
        self = Controller.instance
        self.render_elements(wnd)

    def render_elements(self, wnd):
        if self.current_screen is not None:
            self.current_screen.render_to_window(wnd)
