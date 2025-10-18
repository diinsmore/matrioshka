from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard

import pygame as pg
import numpy as np

from sprite_bases import SpriteBase
from settings import MAP_SIZE

class Pipe:
    def __init__(
        self, 
        xy: pg.Vector2, 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group],
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        assets: dict[str, dict[str, any]],
        direction: str,
        mouse: Mouse,
        keyboard: Keyboard,
        tile_map: np.ndarray,
        tile_IDs: dict[str, int]
    ):
        super().__init__(xy, image, z, sprite_groups)
        self.screen = screen
        self.cam_offset = cam_offset
        self.assets = assets
        self.direction = direction
        self.mouse = mouse
        self.tile_map = tile_map
        self.tile_IDs = tile_IDs

        self.graphics = self.assets['graphics']
        self.item_map = np.zeros(MAP_SIZE, dtype=int)

    def rotate(self) -> None:
        pass