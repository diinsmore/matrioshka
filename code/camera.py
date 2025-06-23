import pygame as pg
from settings import RES, MAP_SIZE, TILE_SIZE

class Camera:
    def __init__(self, coords: pg.Vector2 | list[int, int]):
        '''centers the screen on the player''' 
        self.coords = pg.Vector2(coords)
        self.offset = pg.Vector2()
        self.update_factor = 0.05

    def update(self, target_coords: pg.Vector2) -> None:
        self.coords += (target_coords - self.coords) * self.update_factor
        self.offset.x, self.offset.y = int(self.coords.x) - (RES[0] // 2), int(self.coords.y) - (RES[1] // 2)