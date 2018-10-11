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


COLLISIONTEST_PREVENTS_MOVEMENT = CollisionTest.SOLID | CollisionTest.CONVEYOR_EAST_SINGLE_SPEED | CollisionTest.CONVEYOR_SOUTH_SINGLE_SPEED | CollisionTest.CONVEYOR_WEST_SINGLE_SPEED | CollisionTest.CONVEYOR_NORTH_SINGLE_SPEED
SCREEN_SIZE_W = 1008
SCREEN_SIZE_H = 768
