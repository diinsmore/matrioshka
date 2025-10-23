from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player

import pygame as pg
import numpy as np

from settings import MAP_SIZE, TILE_SIZE, PIPE_TRANSPORT_DIRECTIONS
from sprite_bases import SpriteBase
from timer import Timer

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
        player: Player,
        assets: dict[str, dict[str, any]],
        tile_map: np.ndarray,
        item_transport_map: np.ndarray,
        obj_map: np.ndarray,
        tile_IDs: dict[str, int],
        variant_idx: int
    ):
        super().__init__(xy, image, z, sprite_groups)
        self.screen = screen
        self.cam_offset = cam_offset
        self.mouse = mouse
        self.keyboard = keyboard
        self.player = player
        self.assets = assets
        self.tile_map = tile_map
        self.item_transport_map = item_transport_map
        self.obj_map = obj_map
        self.tile_IDs = tile_IDs
        self.variant_idx = variant_idx
        
        self.graphics = self.assets['graphics']
        self.tile_xy = (int(xy.x) // TILE_SIZE, int(xy.y) // TILE_SIZE)
        self.current_item = None
        self.speed_factor = 1
        self.timers = {'move item': Timer(length=2000 * self.speed_factor, function=self.transport, auto_start=False, loop=False, store_progress=False)}
        self.border_directions = {
            0: [(1, 0), (-1, 0)], 
            1: [(0, 1), (0, -1)], 
            2: [(0, -1), (1, 0)], 
            3: [(-1, 0), (0, -1)], 
            4: [(1, 0), (0, 1)], 
            5: [(-1, 0), (0, 1)]
        }
        self.connected_obj = self.get_connected_obj()

    def get_connected_obj(self) -> type | None:
        x, y = self.tile_xy
        for dx, dy in self.border_directions[self.variant_idx]:
            if (0 < x + dx < MAP_SIZE[0] and 0 < y + dy < MAP_SIZE[1]) and (obj := self.obj_map[x + dx, y + dy]):
                return obj
            elif (dx, dy) == self.border_directions[self.variant_idx][-1]: # no matches
                return None

    def check_rotate(self) -> None:
        if self.rect.collidepoint(self.mouse.world_xy) and self.keyboard.pressed_keys[pg.K_r] and not self.player.item_holding:
            self.direction_idx = (self.direction_idx + 1) % len(PIPE_TRANSPORT_DIRECTIONS)
            self.image = self.graphics[f'pipe {self.direction_idx}']
            self.tile_map[self.tile_xy] = self.tile_IDs[f'pipe {self.direction_idx}']
            self.connected_obj = self.get_connected_obj()

    def transport(self) -> None:
        pass

    def update(self, dt: float) -> None:
        self.check_rotate()