from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from asset_manager import AssetManager
    import numpy as np

import pygame as pg
from os.path import join

from settings import TILE_SIZE, TILES, TOOLS
from player import Player
from timer import Timer

class SpriteManager:
    def __init__(
        self, 
        asset_manager: AssetManager,
        tile_map: np.ndarray,
        tile_id_map: dict[str, int],
        collision_map: dict[tuple[int, int], pg.Rect],
        mining_map: dict[tuple[int, int], dict[str, int]],
    ):
        self.asset_manager = asset_manager
        self.tile_map = tile_map
        self.tile_id_map = tile_id_map
        self.collision_map = collision_map
        self.mining_map = mining_map

        self.all_sprites = pg.sprite.Group()
        self.cloud_sprites = pg.sprite.Group()
        self.mech_sprites = pg.sprite.Group() 

        self.timers = {
            'mining': Timer(length = 1_000, function = self.hit_tile, auto_start = False, loop = False)
        }

    def mining(self, sprite: pg.sprite.Sprite, tile_coords: tuple[int, int], update_map: callable) -> None:
        if isinstance(sprite, Player): 
            mine_radius = 4
            sprite_center = pg.Vector2(sprite.rect.center) // TILE_SIZE
            tile_distance = sprite_center.distance_to(tile_coords)
            if tile_distance <= mine_radius and self.tile_map[tile_coords] != self.tile_id_map['air']:
                sprite.state = 'mining'
                if tile_coords not in self.mining_map:
                    # initialize the tile's hardness value
                    tile_index = self.tile_map[tile_coords]
                    for index, tile in enumerate(TILES):
                        if index == tile_index:
                            self.mining_map[tile_coords] = {'hardness': TILES[tile]['hardness'], 'hits': 0}
                            break

                # increment the hit counter once per second
                # TODO: add varying mining speeds based on the tool used, fatigue, hunger/thirst, etc.
                if not self.timers['mining'].running:
                    self.timers['mining'].start()
                    # this is less than an ideal solution but passing tile_coords as a parameter to hit_tile() throws an error
                    # since currently the Timer class lacks a system to handle parameters within functions it's assigned to call
                    self.tile_coords = tile_coords 

                if self.tile_is_mined(sprite, tile_coords):
                   self.tile_map[tile_coords] = self.tile_id_map['air']  
        else:
            pass

        update_map(tile_coords, self.collision_map)

    def hit_tile(self) -> None:
        self.mining_map[self.tile_coords]['hits'] += 1
        
    def tile_is_mined(self, sprite: pg.sprite.Sprite, tile_coords: tuple[int, int]) -> bool:
        tool_strength = self.get_tool_strength(sprite)
        mining_data = self.mining_map[tile_coords]
        # TODO: decrease the strength of the current tool as its usage accumulates
        mining_data['hardness'] -= mining_data['hits'] * tool_strength
        if mining_data['hardness'] <= 0:
            return True
        return False

    @staticmethod
    def get_tool_strength(sprite: pg.sprite.Sprite) -> str:
        data = sprite.item_holding.split() # ['<material>', '<tool>']
        return TOOLS[data[1]][data[0]]['strength']

    def pick_up_item(self, sprite: pg.sprite.Sprite) -> None:
        pass

    def update(self, dt) -> None:
        for sprite in self.all_sprites:
            sprite.update(dt)

        for timer in self.timers.values():
            timer.update()