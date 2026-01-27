from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import numpy as np

import pygame as pg

class Mining:
    def __init__(
        self, 
        tile_map: np.ndarray, 
        names_to_ids: dict[str, int], 
        ids_to_names: dict[int, str], 
        key_mine: int, 
        update_map: callable, 
        get_tool_strength: callable,
        pick_up_item: callable, 
        get_tile_material: callable, 
        end_action: callable
    ):
        self.tile_map = tile_map
        self.names_to_ids = names_to_ids
        self.ids_to_names = ids_to_names
        self.key_mine = key_mine
        self.update_map = update_map
        self.get_tool_strength = get_tool_strength
        self.pick_up_item = pick_up_item
        self.get_tile_material = get_tile_material
        self.end_action = end_action
        
        self.mining_map = {} # {tile coords: {hardness: int, hits: int}}
        self.invalid_ids = {self.names_to_ids['air'], self.names_to_ids['tree base']} # can't be mined
    
    def run(self, sprite: pg.sprite.Sprite, mouse_tile_xy: tuple[int, int]) -> None:
        if sprite.item_holding and 'pickaxe' in sprite.item_holding:
            if self.valid_tile(sprite, mouse_tile_xy):
                sprite.state = 'mining'
                if mouse_tile_xy not in self.mining_map:
                    self.mining_map[mouse_tile_xy] = {
                        'hardness': TILES[self.get_tile_material(self.tile_map[mouse_tile_xy])]['hardness'], 
                        'hits': 0
                    }
                self.update_tile(sprite, mouse_tile_xy) 

    def valid_tile(self, sprite: pg.sprite.Sprite, mouse_tile_xy: tuple[int, int]) -> bool:
        sprite_coords = pg.Vector2(sprite.rect.center) // TILE_SIZE
        tile_distance = sprite_coords.distance_to(mouse_tile_xy)
        return tile_distance <= TILE_REACH_RADIUS and self.tile_map[mouse_tile_xy] not in self.invalid_ids
    
    # TODO: decrease the strength of the current tool as its usage accumulates    
    def update_tile(self, sprite: pg.sprite.Sprite, mouse_tile_xy: tuple[int, int]) -> bool:   
        data = self.mining_map[mouse_tile_xy]
        data['hits'] += 1 / FPS
        data['hardness'] = max(0, data['hardness'] - (self.get_tool_strength(sprite) * data['hits']))
        if self.mining_map[mouse_tile_xy]['hardness'] == 0:
            sprite.inventory.add_item(self.get_tile_material(self.tile_map[mouse_tile_xy]))
            self.tile_map[mouse_tile_xy] = self.names_to_ids['air']
            self.update_map(mouse_tile_xy, remove_tile = True)
            del self.mining_map[mouse_tile_xy]
    
    def update(self, held_keys: Sequence[bool], player: pg.sprite.Sprite, mouse_tile_xy: tuple[int, int]) -> None:
        if held_keys[self.key_mine]:
            self.run(player, mouse_tile_xy)
        else:
            if player.state == 'mining':
                self.end_action(player)