import pygame as pg
from abc import ABC

from settings import TILE_SIZE

class Sprite(pg.sprite.Sprite, ABC):
    def __init__(self, xy: tuple[int, int], image: pg.Surface, z: int, sprite_groups: list[pg.sprite.Group]):
        super().__init__(*sprite_groups)
        self.xy = xy
        self.image = image
        self.rect = self.image.get_rect(topleft=self.xy)
        self.z = z # layer to render on


class AnimatedSprite(pg.sprite.Sprite, ABC):
    def __init__(
        self, 
        xy: tuple[int, int], 
        cam_offset: pg.Vector2, 
        frames: dict[str, pg.Surface],
        assets: dict[str, dict],
        screen: pg.Surface, 
        sprite_groups: list[pg.sprite.Group],
        z: int, 
        move_speed: int,
        animation_speed: int | dict[str, int],
        gravity: int
    ):
        super().__init__(*sprite_groups)
        self.xy = xy
        self.cam_offset = cam_offset
        self.frames = frames
        self.screen = screen
        self.z = z
        self.move_speed = move_speed
        self.animation_speed = animation_speed
        self.gravity = gravity

        self.state = 'idle'
        self.frame_idx = 0
        self.image = self.frames[self.state][self.frame_idx]
        self.rect = self.image.get_rect(midbottom=self.xy)
        self.direction = pg.Vector2()
        self.tile_xy = (self.xy[0] // TILE_SIZE, self.xy[1] // TILE_SIZE)