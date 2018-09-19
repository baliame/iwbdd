from .object import Object, generate_rectangle_hitbox


class Player(Object):
    def __init__(self):
        super.__init__(self, None)
        self.hitbox = generate_rectangle_hitbox(8, 12)

