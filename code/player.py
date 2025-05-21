from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import numpy as np
    from physics_engine import PhysicsEngine
    from inventory import Inventory

import pygame as pg
import numpy as np

from settings import *

# not inheriting from the base Sprite class in sprites.py since it's not a static image
# there will probably be an AnimatedSprite type class to inherit from in the future 
class Player(pg.sprite.Sprite):
    def __init__(
        self, 
        coords: tuple[int, int], 
        frames: dict[str, pg.Surface],
        z: dict[str, int],
        sprite_groups: list[pg.sprite.Group], 
        tile_map: np.ndarray,
        tile_IDs: dict[str, dict[str, any]],
        biome_order: dict[str, int],
        physics_engine: PhysicsEngine,
        inventory: Inventory
    ):
        super().__init__(*sprite_groups)
        self.frames = frames
        self.frame_index = 0
        self.state = 'idle'
        self.image = self.frames[self.state][self.frame_index]
        self.rect = self.image.get_rect(midbottom = coords)
        self.z = z
        # TODO: the jumping system technically works fine but there has to be a better solution than keeping values of 0 for states with 1 frame
        self.animation_speed = {'walking': 6, 'mining': 4, 'jumping': 0}

        self.tile_map = tile_map
        self.tile_IDs =  tile_IDs

        self.biome_order = biome_order
        self.current_biome = 'forest'

        self.physics_engine = physics_engine

        self.inventory = inventory
        self.item_holding = 'iron pickaxe' # just for testing purposes, normally self.inv[self.inv_index]
        
        self.direction = pg.Vector2()
        self.speed = 200
        self.gravity = 1200
        self.jump_height = 350
        
        self.health = 100
        self.arm_strength = 4
        self.spawned = False
        self.facing_left = True
        self.grounded = True

    def place_block(self, tile_coords: tuple[int, int], tile_id: int) -> None:
        self.tile_map[tile_coords] = self.tile_IDs[self.item_holding][tile_id]

    def place_item(self, rect: pg.Rect) -> None:
        coords = self.get_item_coords(rect)

       # for coords in tile_coords:
           # self.tile_map[coords] = self.tile_IDs['solid object']

    def get_item_coords(self, rect: pg.Rect) -> list[tuple[int, int]]:
        left, top = rect.left // TILE_SIZE, rect.top // TILE_SIZE
        coords = []
        for x in range(1, (rect.width // TILE_SIZE) + 1):
            for y in range(1, (rect.height // TILE_SIZE) + 1):
                coords.append((left + (x * TILE_SIZE), top + (y * TILE_SIZE)))

    def get_current_biome(self) -> None:
        biome_index = (self.rect.x // TILE_SIZE) // BIOME_WIDTH
        if self.biome_order[self.current_biome] != biome_index:
            for biome in self.biome_order.keys():
                if self.biome_order[biome] == biome_index:
                    self.current_biome = biome
                    return
        
    def update(self, dt: float) -> None:
        self.get_current_biome()