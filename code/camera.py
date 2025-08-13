import pygame as pg
from settings import RES, MAP_SIZE, TILE_SIZE

class Camera:
    def __init__(self, coords: pg.Vector2):
        '''centers the screen on the player''' 
        self.coords = coords
        self.offset = pg.Vector2()
        self.update_factor = 0.05
        self.half_screen_x, self.half_screen_y = RES[0] // 2, RES[1] // 2
        self.max_x, self.max_y = MAP_SIZE[0] * TILE_SIZE - self.half_screen_x, MAP_SIZE[1] * TILE_SIZE - self.half_screen_y

    def update(self, target_coords: pg.Vector2) -> None:
        self.coords += (target_coords - self.coords) * self.update_factor
        self.coords.x = max(self.half_screen_x, min(self.coords.x, self.max_x))
        self.coords.y = min(self.coords.y, self.max_y) # not adding a minimum limit until the space biome (if one is to exist) is configured 
        self.offset.x, self.offset.y = int(self.coords.x) - self.half_screen_x, int(self.coords.y) - self.half_screen_y