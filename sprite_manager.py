from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from asset_manager import AssetManager
    import numpy as np

import pygame as pg
pg.init()
from os.path import join

from settings import TILE_SIZE
from player import Player

class SpriteManager:
    def __init__(
        self, 
        asset_manager: AssetManager,
        tile_map: np.ndarray,
        tile_data: dict[str, dict[str, any]],
        collision_map: dict[tuple[int, int], pg.Rect]
    ) -> None:

        self.asset_manager = asset_manager
        self.tile_map = tile_map
        self.tile_data = tile_data
        self.collision_map = collision_map

        self.all_sprites = pg.sprite.Group()
        self.cloud_sprites = pg.sprite.Group()

    def mining(self, sprite: pg.sprite.Sprite, tile_coords: tuple[int, int], update_map: callable) -> None:
        if isinstance(sprite, Player): 
            mine_radius = 5 # in tiles
            sprite_center = pg.Vector2(sprite.rect.center) // TILE_SIZE
            tile_distance = sprite_center.distance_to(tile_coords)
            if tile_distance <= mine_radius and self.tile_map[tile_coords] != self.tile_data['air']['id']:
                sprite.state = 'mining'
                self.tile_map[tile_coords] = self.tile_data['air']['id']
        else:
            pass

        update_map(tile_coords, self.collision_map)

    def pick_up_item(self, sprite: pg.sprite.Sprite) -> None:
        pass

    def update(self, dt) -> None:
        for sprite in self.all_sprites:
            sprite.update(dt)