from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Keyboard
    from procgen import ProcGen
    from sprite_manager import SpriteManager

import pygame as pg

from settings import Z_LAYERS, RES
from colonist_sprite_base import Colonist
from inventory import PlayerInventory

class Player(Colonist):
    def __init__(
        self, 
        proc_gen: ProcGen,
        cam_offset: pg.Vector2, 
        frames: dict[str, int],
        assets: dict[str, any],
        screen: pg.Surface,
        sprite_manager: SpriteManager,
        sprite_groups: list[pg.sprite.Sprite],
        keyboard: Keyboard, 
        save_data: dict[str, any],
    ):
        super().__init__(
            save_data['xy'] if save_data else proc_gen.player_spawn_point, 
            cam_offset, 
            frames, 
            assets,
            screen,
            sprite_manager, 
            sprite_groups, 
            proc_gen.tile_map,  
            save_data=save_data
        )
        self.keyboard = keyboard
        self.current_biome = proc_gen.current_biome
        self.biome_order = proc_gen.biome_order
        self.z = Z_LAYERS['player']
        self.inventory = PlayerInventory(parent_sprite=self, save_data=save_data)

        self.heart_surf = self.graphics['icons']['heart']
        self.heart_width = self.heart_surf.get_width()
    
    def render_hearts(self) -> None:
        for i in range(self.hearts):
            self.screen.blit(self.heart_surf, (RES[0] - (5 + self.heart_width + (25 * i)), 5))

    def respawn(self) -> None:
        self.hearts = self.max_hearts
        self.oxygen_lvl = self.max_oxygen_lvl
        self.underwater = False
        self.alarms['lose oxygen'].running = False
        self.rect.center = self.spawn_point
        self.frame_idx = 0
        self.direction = pg.Vector2()
        self.grounded = True
        self.gravity = self.default_gravity
        self.inventory.contents.clear()
        self.item_holding = None
    
    def update(self, dt: float) -> None:
        self.get_current_biome()
        self.inventory.get_idx_selection(self.keyboard)
        self.render_hearts()
        self.update_oxygen_level()