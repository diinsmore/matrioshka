from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from asset_manager import AssetManager
    import numpy as np

import pygame as pg
from os.path import join

from settings import TILE_SIZE, TILES, TOOLS, FPS
from player import Player
from timer import Timer

class SpriteManager:
    def __init__(
        self, 
        asset_manager: AssetManager,
        tile_map: np.ndarray,
        tile_id_map: dict[str, int],
        collision_map: dict[tuple[int, int], pg.Rect],
    ):
        self.asset_manager = asset_manager
        self.tile_map = tile_map
        self.tile_id_map = tile_id_map
        self.collision_map = collision_map

        self.all_sprites = pg.sprite.Group()
        self.cloud_sprites = pg.sprite.Group()
        self.mech_sprites = pg.sprite.Group() 

        self.mining = Mining(
            self.tile_map, 
            self.tile_id_map, 
            self.collision_map, 
            self.get_tool_strength, 
            self.pick_up_item
        )
        
    @staticmethod
    def get_tool_strength(sprite: pg.sprite.Sprite) -> int:
        if sprite.item_holding:
            data = sprite.item_holding.split() # ['<material>', '<tool>']
            return TOOLS[data[1]][data[0]]['strength']
        return sprite.arm_strength

    def pick_up_item(self, sprite: pg.sprite.Sprite) -> None:
        pass

    def update(self, dt) -> None:
        for sprite in self.all_sprites:
            sprite.update(dt)


class Mining:
    def __init__(
        self, 
        tile_map: np.ndarray,
        tile_id_map: dict[str, int],
        collision_map: dict[tuple[int, int], pg.Rect],
        get_tool_strength: callable,
        pick_up_item: callable
    ):
        self.tile_map = tile_map
        self.tile_id_map = tile_id_map
        self.collision_map = collision_map
        self.get_tool_strength = get_tool_strength
        self.pick_up_item = pick_up_item
        
        self.mining_map = {} # {tile coords: {hardness: int, hits: int}}
        self.tile_reach_radius = 100

    def start(self, sprite: pg.sprite.Sprite, tile_coords: tuple[int, int], update_collision_map: callable) -> None:
        if sprite.item_holding.split()[1] == 'pickaxe': # ignore the item's material if specified
            if isinstance(sprite, Player): 
                if self.valid_tile(sprite, tile_coords):
                    sprite.state = 'mining'

                    if tile_coords not in self.mining_map:
                        self.init_tile(tile_coords)

                    self.update_tile(sprite, tile_coords) 
                    update_collision_map(tile_coords, self.collision_map)
            else:
                pass
       
    def init_tile(self, tile_coords: tuple[int, int]) -> None:
        '''initialize a new key/value pair in the mining map'''
        tile_index = self.tile_map[tile_coords]
        # get the tile variant to access its default hardness value
        for index, tile in enumerate(TILES):
            if index == tile_index:
                self.mining_map[tile_coords] = {'hardness': TILES[tile]['hardness'], 'hits': 0}
                return

    def valid_tile(self, sprite: pg.sprite.Sprite, tile_coords: tuple[int, int]) -> bool:
        sprite_coords = pg.Vector2(sprite.rect.center) // TILE_SIZE
        tile_distance = sprite_coords.distance_to(tile_coords)
        return tile_distance <= self.tile_reach_radius and self.tile_map[tile_coords] != self.tile_id_map['air']
    
    # TODO: decrease the strength of the current tool as its usage accumulates    
    def update_tile(self, sprite: pg.sprite.Sprite, tile_coords: tuple[int, int]) -> bool:
        tool_strength = self.get_tool_strength(sprite)     
        data = self.mining_map[tile_coords]
        data['hits'] += 1 / FPS
        data['hardness'] -= tool_strength * data['hits'] 
        
        if self.mining_map[tile_coords]['hardness'] <= 0:
            self.tile_map[tile_coords] = self.tile_id_map['air']
            del self.mining_map[tile_coords]