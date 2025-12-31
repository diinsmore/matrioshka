from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Keyboard
    from procgen import ProcGen
    from sprite_manager import SpriteManager

import pygame as pg

from settings import Z_LAYERS, RES
from colonist import Colonist
from inventory import PlayerInventory

class Player(Colonist):
    def __init__(
        self, 
        xy: pg.Vector2,
        cam_offset: pg.Vector2, 
        frames: dict[str, int],
        assets: dict[str, any],
        screen: pg.Surface,
        sprite_manager: SpriteManager,
        sprite_groups: list[pg.sprite.Sprite],
        proc_gen: ProcGen,
        keyboard: Keyboard, 
        save_data: dict[str, any],
    ):
        super().__init__(
            xy, 
            cam_offset, 
            frames, 
            assets,
            screen,
            sprite_manager, 
            sprite_groups, 
            proc_gen,  
            save_data=save_data
        )
        self.keyboard = keyboard
        self.z = Z_LAYERS['player']
        self.inventory = PlayerInventory(parent_sprite=self, save_data=save_data)

        self.heart_surf = self.graphics['icons']['heart']
        self.heart_width = self.heart_surf.get_width()
    
    def render_hearts(self) -> None:
        for i in range(self.hp):
            self.screen.blit(self.heart_surf, (RES[0] - (5 + self.heart_width + (25 * i)), 5))

    def respawn(self) -> None:
        self.hp = self.max_hp
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
        super().update(dt)
        self.inventory.get_idx_selection(self.keyboard)
        self.render_hearts()