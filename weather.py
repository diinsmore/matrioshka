import pygame as pg

from settings import RES
from timer import Timer

class Weather:
    def __init__(self, screen) -> None:
        self.sky = Sky(screen)

    def update(self) -> None:
        self.sky.update()

class Sky:
    def __init__(self, screen: pg.Surface) -> None:
        self.screen = screen

        self.rgb = [150, 200, 255]
        self.max_rgb = self.rgb[:]
        self.min_rgb = [0, 0, 20]
        self.rgb_update = -1
        
        self.tint_alpha = 0
        self.tint_update = 1
        
        self.timers = {
            'update': Timer(length = 10_000, function = self.day_night_cycle, auto_start = True, loop = True), # sky color updates with the day/night cycle 
            'tint': Timer(length = 1_000, function = self.update_tint, auto_start = False, loop = True)
        }

    def day_night_cycle(self) -> None:
        '''Update the rgb values as time passes.'''
        for i in range(3):
            self.rgb[i] = max(self.min_rgb[i], min(self.rgb[i] + self.rgb_update, self.max_rgb[i]))
            if self.rgb in (self.max_rgb, self.min_rgb):
                self.rgb_update *= -1
    
    def render_tint(self) -> None:
        '''Add a pinkish tint to the sky during twilight/dawn.'''
        image = pg.Surface(RES)
        image.fill((255, 100, 100))
        image.set_alpha(self.tint_alpha)
        self.screen.blit(image, (0, 0), special_flags = pg.BLEND_RGBA_ADD)

    def update_tint(self) -> None:
        self.sky_tint_alpha = max(0, min(self.tint_alpha + self.tint_update, 255))
        
        if self.tint_alpha in (0, 255): 
            self.tint_update *= -1

    def render(self) -> None:
        image = pg.Surface(RES)
        image.fill(self.rgb)
        self.screen.blit(image, (0, 0))

        if 125 < self.rgb[2] < 175 and self.sky_update_dir < 0 or \
            50 < self.rgb[2] < 100 and self.sky_update_dir > 0:

            if not self.timers['sky tint'].running:
                self.timers['sky tint'].start()

            self.render_tint()

    def update(self) -> None:
        self.render()

        for timer in self.timers.values():
            timer.update()