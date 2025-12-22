from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player
    import numpy as np
    
import pygame as pg
from dataclasses import dataclass, field

from sprite_bases import MachineSpriteBase, Inventory, InvSlot
from settings import MACHINES
from furnace_ui import FurnaceUI
from alarm import Alarm

class Furnace(MachineSpriteBase):
    def __init__(
        self, xy: pg.Vector2, image: dict[str, dict[str, pg.Surface]], z: dict[str, int], sprite_groups: list[pg.sprite.Group], screen: pg.Surface, cam_offset: pg.Vector2,
        mouse: Mouse, keyboard: Keyboard, player: Player, assets: dict[str, dict[str, any]], tile_map: np.ndarray, obj_map: np.ndarray, gen_outline: callable, gen_bg: callable,
        rect_in_sprite_radius: callable, render_item_amount: callable, save_data: dict[str, any]
    ):
        super().__init__(
            xy, image, z, sprite_groups, screen, cam_offset, mouse, keyboard, player, assets, tile_map, obj_map, gen_outline, gen_bg, rect_in_sprite_radius, 
            render_item_amount, save_data
        )
        self.can_smelt = {
            'copper': {'speed': 3000, 'output': 'copper plate'}, 
            'iron': {'speed': 5000, 'output': 'iron plate'},
            'iron plate': {'speed': 7000, 'output': 'steel plate'},
        }
        self.inv = Inventory(input_slots={'fuel': InvSlot(valid_inputs=self.fuel_sources.keys()), 'smelt': InvSlot(valid_inputs=self.can_smelt.keys())})
        self.alarms = {}

    def update_active_state(self) -> None:
        self.active = self.inv.input_slots['smelt'].item and self.inv.input_slots['fuel'].item and self.inv.output_slot.amount < self.inv.output_slot.max_capacity
        if not self.active:
            self.alarms.clear()
    
    def smelt(self) -> None:
        if not self.alarms:
            self.alarms['smelt'] = Alarm(self.can_smelt[self.inv.input_slots['smelt'].item]['speed'] // self.speed_factor, self.update_inv_slot, True, True, True, smelt=True)
            self.alarms['smelt'].start()
            if self.variant == 'burner':
                self.alarms['fuel'] = Alarm(
                    self.can_smelt[self.inv.input_slots['smelt'].item]['speed'] // self.speed_factor, self.update_inv_slot, True, True, True, smelt=True, fuel=True
                )
                self.alarms['fuel'].start()
        for alarm in self.alarms.values():
            alarm.update()

    def update_inv_slot(self, smelt: bool=False, fuel: bool=False) -> None:
        data = self.inv.input_slots['smelt' if smelt or self.variant != 'burner' else 'fuel']
        data.amount -= 1
        if not data.amount:
            data.item = None
            self.active = False
        if smelt and data.item:
            output_item = self.can_smelt[data.item]['output']
            if not self.inv.output_slot.item:
                self.inv.output_slot.item = output_item
            self.inv.output_slot.amount += 1

    def get_save_data(self) -> dict[str, list|str]:
        return {'xy': list(self.rect.topleft), 'smelt input': self.smelt_input, 'fuel input': self.fuel_input, 'output': self.output}

    def update(self, dt: float) -> None:
        self.ui.update()
        self.update_active_state()
        if self.active:
            self.smelt()
        
            
class BurnerFurnace(Furnace):
    def __init__(
        self, xy: pg.Vector2, image: dict[str, dict[str, pg.Surface]], z: dict[str, int], sprite_groups: list[pg.sprite.Group], screen: pg.Surface, cam_offset: pg.Vector2,
        mouse: Mouse, keyboard: Keyboard, player: Player, assets: dict[str, dict[str, any]], tile_map: np.ndarray, obj_map: np.ndarray, gen_outline: callable, gen_bg: callable,
        rect_in_sprite_radius: callable, render_item_amount: callable, save_data: dict[str, any]
    ):  
        self.fuel_sources = {'wood': {'capacity': 99, 'burn speed': 2000}, 'coal': {'capacity': 99, 'burn speed': 4000}}
        super().__init__(
            xy, image, z, sprite_groups, screen, cam_offset, mouse, keyboard, player, assets, tile_map, obj_map, gen_outline, gen_bg, rect_in_sprite_radius, 
            render_item_amount, save_data
        )
        self.variant = 'burner'
        self.recipe = MACHINES['burner furnace']['recipe']
        self.speed_factor = 1
        self.init_ui(FurnaceUI)


class SteelFurnace(Furnace):
    def __init__(
        self, xy: pg.Vector2, image: dict[str, dict[str, pg.Surface]], z: dict[str, int], sprite_groups: list[pg.sprite.Group], screen: pg.Surface, cam_offset: pg.Vector2,
        mouse: Mouse, keyboard: Keyboard, player: Player, assets: dict[str, dict[str, any]], tile_map: np.ndarray, obj_map: np.ndarray, gen_outline: callable, gen_bg: callable,
        rect_in_sprite_radius: callable, render_item_amount: callable, save_data: dict[str, any]
    ):  
        super().__init__(
            xy, image, z, sprite_groups, screen, cam_offset, mouse, keyboard, player, assets, tile_map, obj_map, gen_outline, gen_bg, rect_in_sprite_radius, 
            render_item_amount, save_data
        )
        self.variant = 'steel'
        self.recipe = MACHINES['steel furnace']['recipe']
        self.fuel_sources = {
            'non-electric': {
                'wood': {'capacity': 99, 'burn speed': 3000}, 
                'coal': {'capacity': 99, 'burn speed': 6000}
            },
            'electric': {'electric poles'}
        }
        self.speed_factor = 2
        self.init_ui(FurnaceUI)


class ElectricFurnace(Furnace):
    def __init__(
        self, xy: pg.Vector2, image: dict[str, dict[str, pg.Surface]], z: dict[str, int], sprite_groups: list[pg.sprite.Group], screen: pg.Surface, cam_offset: pg.Vector2,
        mouse: Mouse, keyboard: Keyboard, player: Player, assets: dict[str, dict[str, any]], tile_map: np.ndarray, obj_map: np.ndarray, gen_outline: callable, gen_bg: callable,
        rect_in_sprite_radius: callable, render_item_amount: callable, save_data: dict[str, any]
    ):  
        super().__init__(
            xy, image, z, sprite_groups, screen, cam_offset, mouse, keyboard, player, assets, tile_map, obj_map, gen_outline, gen_bg, rect_in_sprite_radius, 
            render_item_amount, save_data
        )
        self.variant = 'electric'
        self.recipe = MACHINES['electric furnace']['recipe']
        self.inv = Inventory(input_slots={'smelt': InvSlot(valid_inputs=self.can_smelt.keys())})
        self.fuel_sources = {'electric poles'}
        self.speed_factor = 2.5
        self.init_ui(FurnaceUI)