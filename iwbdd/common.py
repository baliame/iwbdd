from enum import IntEnum


def is_reader_stream(s):
    if callable(getattr(s, "read", None)):
        return True
    return False


def eofc_read(reader, expected):
    data = reader.read(expected)
    if len(data) < expected:
        raise RuntimeError("Unexpected EOF")
    return data


def mousebox(x, y, x0, y0, w, h):
    return x >= x0 and y >= y0 and x < x0 + w and y < y0 + h


def lerp(v1, v2, t):
    return int(v1 * (1 - t) + v2 * t)


class CollisionTest(IntEnum):
    PASSABLE = 0
    SOLID = 1
    DEADLY = 2
    TRANSITION_EAST = 4
    TRANSITION_NORTH = 8
    TRANSITION_WEST = 16
    TRANSITION_SOUTH = 32
    CONVEYOR_EAST_SINGLE_SPEED = 64
    CONVEYOR_NORTH_SINGLE_SPEED = 128
    CONVEYOR_WEST_SINGLE_SPEED = 256
    CONVEYOR_SOUTH_SINGLE_SPEED = 512
    INTERACTABLE = 1024
    SAVE_TILE = 2048
    LENS = 4096
    BULLET_INTERACTABLE = 8192
    BOSS = 8194
    BOSSFIGHT_INIT_TRIGGER = 16384
    BONFIRE = 32768
    TRIGGER = 65536


COLLISIONTEST_PREVENTS_MOVEMENT = CollisionTest.SOLID | CollisionTest.CONVEYOR_EAST_SINGLE_SPEED | CollisionTest.CONVEYOR_SOUTH_SINGLE_SPEED | CollisionTest.CONVEYOR_WEST_SINGLE_SPEED | CollisionTest.CONVEYOR_NORTH_SINGLE_SPEED
SCREEN_SIZE_W = 1008
SCREEN_SIZE_H = 768

COLLISIONTEST_COLORS = {
    CollisionTest.SOLID: (0, 0, 255),
    CollisionTest.DEADLY: (255, 0, 0),
    CollisionTest.CONVEYOR_EAST_SINGLE_SPEED: (0, 128, 0),
    CollisionTest.CONVEYOR_NORTH_SINGLE_SPEED: (0, 129, 0),
    CollisionTest.CONVEYOR_WEST_SINGLE_SPEED: (0, 130, 0),
    CollisionTest.CONVEYOR_SOUTH_SINGLE_SPEED: (0, 131, 0),
    CollisionTest.SAVE_TILE: (0, 0, 128),
    CollisionTest.LENS: (128, 0, 0),
    CollisionTest.BOSSFIGHT_INIT_TRIGGER: (128, 128, 0),
    CollisionTest.BOSS: (254, 0, 0),
    CollisionTest.BONFIRE: (0, 128, 128),
    CollisionTest.TRIGGER: (128, 0, 128),
}


class Controls(IntEnum):
    LEFT = 0
    RIGHT = 1
    JUMP = 2
    SHOOT = 3
    RESET = 4
    SKIP = 5
    LOOK_UP = 6
    LOOK_DOWN = 7
    DEV1 = 16
    DEV2 = 17

MOVEMENT_SPEED = 2
