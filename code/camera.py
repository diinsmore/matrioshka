import pygame as pg
from settings import RES, MAP_SIZE, TILE_SIZE

class Camera:
    def __init__(self):
        '''center the screen on the player'''  
        self.coords = pg.Vector2() 
        self.offset = pg.Vector2()

    def update(self, target_coords: pg.Vector2) -> None:
        speed_offset = 0.05 # update gradually
        self.coords += (target_coords - self.coords) * speed_offset 

        target_x = self.coords.x - (RES[0] // 2)
        target_y = self.coords.y - (RES[1] // 2)
        # only move within the map's borders
        self.offset.x = max(0, min(target_x, (MAP_SIZE[0] * TILE_SIZE) - RES[0]))
        self.offset.y = max(0, min(target_y, (MAP_SIZE[1] * TILE_SIZE) - RES[1]))
        self.offset.x, self.offset.y = int(self.offset.x), int(self.offset.y)