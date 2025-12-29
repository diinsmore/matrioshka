from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import InputManager
    import numpy as np
    from sprite_manager import SpriteManager

import pygame as pg
from random import choice

from sprite_base_classes import AnimatedSprite
from inventory import SpriteInventory
from item_drop import ItemDrop
from settings import Z_LAYERS, GRAVITY, TILE_SIZE, BIOME_WIDTH
from alarm import Alarm

class Colonist(AnimatedSprite):
    def __init__(
        self,
        xy: tuple[int, int],
        cam_offset: pg.Vector2, 
        frames: dict[str, pg.Surface],
        assets: dict[str, any], 
        screen: pg.Surface,
        sprite_manager: SpriteManager, 
        sprite_groups: list[pg.sprite.Group],
        tile_map: np.ndarray, 
        z: int=Z_LAYERS['main'],
        move_speed: int=225,
        animation_speed: dict[str, int]={'walking': 8, 'mining': 4, 'jumping': 0},
        gravity: int=GRAVITY,
        save_data: dict[str, any]=None
    ):
        super().__init__(xy, cam_offset, frames, assets, screen, sprite_groups, z, move_speed, animation_speed, gravity)
        self.spawn_point = xy
        self.graphics = assets['graphics']
        self.sprite_manager = sprite_manager
        self.save_data = save_data
        
        self.facing_left = save_data['facing left'] if save_data else True
        self.grounded = False
        self.default_gravity = self.gravity
        self.default_jump_height, self.jump_height = 350, 350 
        self.hearts, self.max_hearts = save_data['lives'] if save_data else 8, 8
        self.inventory = SpriteInventory(parent_sprite=self)
        self.item_holding = save_data['item holding'] if save_data else None
        self.arm_strength = 4
        self.underwater = False
        self.oxygen_lvl, self.max_oxygen_lvl = 8, 8
        self.oxygen_icon = self.graphics['icons']['oxygen']
        self.oxygen_icon_w, self.oxygen_icon_h = self.oxygen_icon.get_size()
        self.alarms = {'lose oxygen': Alarm(500, self.lose_oxygen, False, True)}
    
    def get_current_biome(self) -> None:
        if self.direction:
            biome_idx = (self.rect.x // TILE_SIZE) // BIOME_WIDTH
            if self.biome_order[self.current_biome] != biome_idx:
                for biome in self.biome_order.keys():
                    if self.biome_order[biome] == biome_idx:
                        self.current_biome = biome
                        return

    def update_oxygen_level(self) -> None:
        if self.underwater:
            if not self.alarms['lose oxygen'].running:
                self.alarms['lose oxygen'].start()
            else:
                self.alarms['lose oxygen'].update()
            self.render_oxygen_icons()

    def render_oxygen_icons(self) -> None:
        x_padding = self.oxygen_icon_w * (self.oxygen_lvl // 2)
        for i in range(self.oxygen_lvl):
            self.screen.blit(self.oxygen_icon, self.rect.midtop - self.cam_offset + pg.Vector2((self.oxygen_icon_w * i) - x_padding, -self.oxygen_icon_h)) 

    def lose_oxygen(self) -> None:
        if self.oxygen_lvl >= 1:
            self.oxygen_lvl -= 1
        else:
            self.hearts -= 1
            if not self.hearts:
                self.die()
    
    def die(self) -> None: 
        self.drop_inventory()
        if self.z == Z_LAYERS['player']: 
            self.respawn()
        else:
            self.kill()

    def drop_inventory(self) -> None:
        for item_name in self.inventory.contents:
            item = ItemDrop(
                self.rect.center,
                self.graphics[item_name],
                Z_LAYERS['main'],
                [self.sprite_manager.all_sprites, self.sprite_manager.active_sprites],
                self.sprite_manager,
                pg.Vector2(choice((-1, 1)), 1),
                item_name,
                self
            )

    def update(self, dt: float) -> None:
        self.get_current_biome()
        self.inventory.get_idx_selection(self.keyboard)
        self.update_oxygen_level()

    def get_save_data(self) -> dict[str, any]:
        return {
            'xy': self.spawn_point, 
            'current biome': self.current_biome, 
            'inventory data': {'contents': self.inventory.contents, 'index': self.inventory.index},
            'facing left': self.facing_left, 
            'lives': self.health, 
            'item holding': self.item_holding
        }