from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import numpy as np
    from inventory import PlayerInventory

import pygame as pg
import numpy as np

from settings import *

# not inheriting from the base Sprite class in sprites.py since it's not a static image
# there will probably be an AnimatedSprite type class to inherit from in the future 
class Player(pg.sprite.Sprite):
    def __init__(
        self, 
        xy: tuple[int, int], 
        frames: dict[str, pg.Surface],
        z: dict[str, int],
        sprite_groups: list[pg.sprite.Group],
        tile_map: np.ndarray,
        tile_IDs: dict[str, dict[str, any]],
        current_biome: str,
        biome_order: dict[str, int],
        inventory: PlayerInventory,
        save_data: dict[str, any]
    ):
        super().__init__(*sprite_groups)
        self.spawn_point = self.xy = xy
        self.frames = frames
        self.z = z
        self.tile_map = tile_map
        self.tile_IDs = tile_IDs
        self.current_biome = current_biome
        self.biome_order = biome_order
        self.inventory = inventory

        self.frame_index = 0
        self.state = 'idle'
        self.image = self.frames[self.state][self.frame_index]
        self.rect = self.image.get_rect(midbottom=self.xy)
        
        self.direction = pg.Vector2()
        self.facing_left = save_data['facing left'] if save_data else True
        self.speed = 225
        self.grounded = False
        self.gravity = GRAVITY
        self.jump_height = 350 
        self.health = save_data['health'] if save_data else 100
        self.item_holding = save_data['item holding'] if save_data else list(self.inventory.contents)[0]
        print(list(self.inventory.contents), self.item_holding)
        self.arm_strength = 4
        self.animation_speed = {'walking': 8, 'mining': 4, 'jumping': 0} # TODO: the jumping system technically works fine but there has to be a better solution than keeping values of 0 for states with 1 frame

    def get_current_biome(self) -> None:
        biome_index = (self.rect.x // TILE_SIZE) // BIOME_WIDTH
        if self.biome_order[self.current_biome] != biome_index:
            for biome in self.biome_order.keys():
                if self.biome_order[biome] == biome_index:
                    self.current_biome = biome
                    return
        
    def update(self, dt: float) -> None:
        self.get_current_biome()

    def get_save_data(self) -> dict[str, any]:
        return {
            'xy': self.spawn_point,
            'current biome': self.current_biome,
            'inventory data': {'contents': self.inventory.contents, 'index': self.inventory.index},
            'facing left': self.facing_left,
            'health': self.health,
            'item holding': self.item_holding
        }