from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import numpy as np
    from input_manager import InputManager

import pygame as pg
import numpy as np

from settings import GRAVITY, TILE_SIZE, BIOME_WIDTH, Z_LAYERS
from inventory import PlayerInventory

class Player(pg.sprite.Sprite):
    def __init__(
        self, xy: tuple[int, int], frames: dict[str, pg.Surface], sprite_groups: list[pg.sprite.Group], input_manager: InputManager, tile_map: np.ndarray, current_biome: str,
        biome_order: dict[str, int], save_data: dict[str, any]
    ):
        super().__init__(*sprite_groups)
        self.xy, self.spawn_point = xy, xy
        self.frames = frames
        self.keyboard = input_manager.keyboard
        self.mouse = input_manager.mouse
        self.tile_map = tile_map
        self.current_biome = current_biome
        self.biome_order = biome_order
        
        self.inventory = PlayerInventory(parent_spr=self, save_data=save_data)

        self.z = Z_LAYERS['player']
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
        self.inventory.get_idx_selection(self.keyboard)

    def get_save_data(self) -> dict[str, any]:
        return {
            'xy': self.spawn_point, 'current biome': self.current_biome, 'inventory data': {'contents': self.inventory.contents, 'index': self.inventory.index},
            'facing left': self.facing_left, 'health': self.health, 'item holding': self.item_holding
        }