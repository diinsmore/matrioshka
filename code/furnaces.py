from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player

import pygame as pg

from sprite_base import SpriteBase
from settings import MACHINES
from furnace_ui import FurnaceUI

class Furnace(SpriteBase):
    def __init__(
        self, 
        coords: pg.Vector2, 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group],
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        mouse: Mouse,
        keyboard: Keyboard,
        player: Player,
        assets: dict[str, dict[str, any]],
        gen_outline: callable,
        gen_bg: callable,
        rect_in_sprite_radius: callable,
        render_item_amount: callable,
        save_data: dict[str, any]
    ):
        super().__init__(coords, image, z, sprite_groups)
        self.screen = screen
        self.cam_offset = cam_offset
        self.mouse = mouse
        self.keyboard = keyboard
        self.player = player
        self.assets = assets
        self.gen_outline = gen_outline
        self.gen_bg = gen_bg
        self.rect_in_sprite_radius = rect_in_sprite_radius
        
        self.active = False
        self.max_capacity = {'smelting': 100, 'fuel': 50}
        self.items_smelted = {
            'copper': {'speed': 4000, 'output': 'copper plate'}, 
            'iron': {'speed': 5000, 'output': 'iron plate'},
            'iron plate': {'speed': 7000, 'output': 'steel plate'},
        }
        
        self.ui = FurnaceUI(
            self.screen, 
            self.cam_offset,
            self.image, 
            self.rect,
            self.items_smelted,
            self.mouse, 
            self.keyboard,
            self.player,
            self.assets,
            self.gen_outline, 
            self.gen_bg,
            self.rect_in_sprite_radius,
            render_item_amount,
            save_data
        )
    
    def smelt(self) -> None:
        pass

    def update(self, dt) -> None:
        self.ui.update()

    def get_save_data(self) -> dict[str, list|str]:
        return {
            'xy': list(self.rect.topleft),
            'smelt input': self.ui.smelt_input,
            'fuel input': self.ui.fuel_input,
            'output': self.ui.output
        }


class BurnerFurnace(Furnace):
    def __init__(
        self,
        coords: pg.Vector2, 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group],
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        mouse: Mouse,
        keyboard: Keyboard,
        player: Player,
        assets: dict[str, dict[str, any]],
        gen_outline: callable,
        gen_bg: callable,
        rect_in_sprite_radius: callable,
        render_item_amount: callable,
        save_data: dict[str, any]
    ):
        super().__init__(
            coords, 
            image, 
            z, 
            sprite_groups, 
            screen, 
            cam_offset, 
            mouse, 
            keyboard, 
            player, 
            assets, 
            gen_outline, 
            gen_bg, 
            rect_in_sprite_radius,
            render_item_amount,
            save_data
        )
        self.variant = 'burner'
        self.ui.variant = self.variant
        self.recipe = MACHINES['burner furnace']['recipe']
        self.fuel_sources = {'wood': {'capacity': 99}, 'coal': {'capacity': 99}}
        self.ui.fuel_sources = self.fuel_sources


class ElectricFurnace(Furnace):
    def __init__(
        self,
        coords: pg.Vector2, 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group],
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        mouse: Mouse,
        keyboard: Keyboard,
        assets: dict[str, dict[str, any]],
        gen_outline: callable,
        gen_bg: callable,
        rect_in_sprite_radius: callable,
        render_item_amount: callable,
        save_data: dict[str, any]
    ):
        super().__init__(
            coords, 
            image, 
            z, 
            sprite_groups, 
            screen, 
            cam_offset, 
            mouse, 
            keyboard, 
            player, 
            assets, 
            gen_outline, 
            get_visbility,
            render_item_amount,
            save_data
        )
        self.variant = 'electric'
        self.ui.variant = self.variant
        self.recipe = MACHINES['electric furnace']['recipe']
        self.fuel_sources = {'electric poles'}
        self.ui.fuel_sources = self.fuel_sources