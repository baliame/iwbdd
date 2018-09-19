import pygame
import pygame.display


class Window:
    instance = None

    def __init__(self, w, h, title="pygame window"):
        if Window.instance is not None:
            raise RuntimeError("Window must be a singleton.")
        self.w = w
        self.h = h
        self.display = pygame.display.set_mode((w, h))
        pygame.display.set_caption(title)

    def update(self):
        pygame.display.update()


class WindowSection:
    def __init__(self, window, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.window = window
        self.display = pygame.Surface((w, h))

    def update(self):
        self.window.display.blit(self.display, (self.x, self.y))
