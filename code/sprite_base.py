import pygame as pg
from dataclasses import dataclass, field

from settings import TILE_SIZE
from inventory import SpriteInventory
from alarm import Alarm

class SpriteBase(pg.sprite.Sprite):
    def __init__(
        self, 
        xy: tuple[int, int], 
        cam_offset: pg.Vector2, 
        image: pg.Surface, 
        screen: pg.Surface, 
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group]
    ):
        super().__init__(*sprite_groups)
        self.xy = xy
        self.cam_offset = cam_offset
        self.image = image
        self.rect = self.image.get_rect(topleft=self.xy)
        self.screen = screen
        self.z = z # layer to render on