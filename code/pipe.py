from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard

import pygame as pg
import numpy as np

from sprite_bases import SpriteBase
from settings import MAP_SIZE, TILE_SIZE, PIPE_TRANSPORT_DIRECTIONS

class Pipe(SpriteBase):
    def __init__(
        self, 
        xy: pg.Vector2, 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group],
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        mouse: Mouse,
        keyboard: Keyboard,
        assets: dict[str, dict[str, any]],
        direction_idx: int,
        tile_map: np.ndarray,
        tile_IDs: dict[str, int]
    ):
        super().__init__(xy, image, z, sprite_groups)
        self.screen = screen
        self.cam_offset = cam_offset
        self.mouse = mouse
        self.keyboard = keyboard
        self.assets = assets
        self.direction_idx = direction_idx
        self.tile_map = tile_map
        self.tile_IDs = tile_IDs
        
        self.tile_xy = (int(xy.x) // TILE_SIZE, int(xy.y) // TILE_SIZE)
        self.item_map = np.zeros(MAP_SIZE, dtype=int)
        self.graphics = self.assets['graphics']
        
    def rotate(self) -> None:
        if self.rect.collidepoint(self.mouse.world_xy) and self.keyboard.pressed_keys[pg.K_r]:
            self.direction_idx = (self.direction_idx + 1) % len(PIPE_TRANSPORT_DIRECTIONS)
            self.image = self.graphics[f'pipe {self.direction_idx}']
            self.tile_map[self.tile_xy] = self.tile_IDs[f'pipe {self.direction_idx}']

    def update(self, dt: float) -> None:
        self.rotate()