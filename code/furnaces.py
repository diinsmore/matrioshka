from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player
    import numpy as np
    
import pygame as pg
from dataclasses import dataclass, field

from sprite_bases import MachineSpriteBase
from settings import MACHINES
from furnace_ui import FurnaceUI
from timer import Timer
from machine_ui import InvSlot

@dataclass()
class Inventory:
    smelt: InvSlot
    output: InvSlot
    fuel: InvSlot=None

    def __iter__(self):
        for v in self.__dict__.values():
            if v is not None:
                yield v


class Furnace(MachineSpriteBase):
    def __init__(
        self, 
        xy: pg.Vector2, 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group],
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        mouse: Mouse,
        keyboard: Keyboard,
        player: Player,
        assets: dict[str, dict[str, any]], 
        tile_map: np.ndarray,
        obj_map: np.ndarray,
        gen_outline: callable,
        gen_bg: callable,
        rect_in_sprite_radius: callable,
        render_item_amount: callable,
        save_data: dict[str, any]
    ):
        super().__init__(
            xy, 
            image, 
            z, 
            sprite_groups, 
            screen, 
            cam_offset, 
            mouse, 
            keyboard, 
            player, 
            assets, 
            tile_map, 
            obj_map,
            gen_outline, 
            gen_bg, 
            rect_in_sprite_radius, 
            render_item_amount, 
            save_data
        )
        self.can_smelt = {
            'copper': {'speed': 3000, 'output': 'copper plate'}, 
            'iron': {'speed': 5000, 'output': 'iron plate'},
            'iron plate': {'speed': 7000, 'output': 'steel plate'},
        }
        self.inv = Inventory(
            smelt=InvSlot(item=None, rect=None, valid_inputs=self.can_smelt.keys()),
            output=InvSlot(item=None, rect=None, valid_inputs=None)
        )
        self.timers = {}

    def update_active_state(self) -> None:
        self.active = self.inv.smelt.item and self.inv.fuel.item and self.inv.output.amount < self.inv.output.max_capacity
        if not self.active:
            self.timers.clear()
    
    def smelt(self) -> None:
        if not self.timers:
            self.timers['smelt'] = Timer(
                length=self.can_smelt[self.inv.smelt.item]['speed'] // self.speed_factor, 
                function=self.update_inv_box, 
                auto_start=True, 
                loop=True, 
                store_progress=True,
                smelt=True
            )
            self.timers['smelt'].start()
            if self.variant == 'burner':
                self.timers['fuel'] = Timer(
                    length=self.fuel_sources[self.inv.fuel.item]['burn speed'] // self.speed_factor, 
                    function=self.update_inv_box, 
                    auto_start=True, 
                    loop=True, 
                    store_progress=True,
                    smelt=False,
                    fuel=True
                )
                self.timers['fuel'].start()
        for timer in self.timers.values():
            timer.update()

    def update_inv_box(self, smelt: bool=False, fuel: bool=False) -> None:
        data = self.inv.smelt if smelt else self.inv.fuel
        data.amount -= 1
        if data.amount == 0:
            data.item = None
            self.active = False
        if smelt and data.item:
            output_item = self.can_smelt[data.item]['output']
            if not self.inv.output.item:
                self.inv.output.item = output_item
            self.inv.output.amount += 1

    def get_save_data(self) -> dict[str, list|str]:
        return {
            'xy': list(self.rect.topleft),
            'smelt input': self.smelt_input,
            'fuel input': self.fuel_input,
            'output': self.output
        }

    def update(self, dt: float) -> None:
        self.ui.update()
        self.update_active_state()
        if self.active:
            self.smelt()
        
            
class BurnerFurnace(Furnace):
    def __init__(
        self, 
        xy: pg.Vector2, 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group],
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        mouse: Mouse,
        keyboard: Keyboard,
        player: Player,
        assets: dict[str, dict[str, any]], 
        tile_map: np.ndarray,
        obj_map: np.ndarray,
        gen_outline: callable,
        gen_bg: callable,
        rect_in_sprite_radius: callable,
        render_item_amount: callable,
        save_data: dict[str, any]
    ):
        super().__init__(
            xy, 
            image, 
            z, 
            sprite_groups, 
            screen, 
            cam_offset, 
            mouse, 
            keyboard, 
            player, 
            assets, 
            tile_map, 
            obj_map,
            gen_outline, 
            gen_bg, 
            rect_in_sprite_radius, 
            render_item_amount, 
            save_data
        )
        self.variant = 'burner'
        self.recipe = MACHINES['burner furnace']['recipe']
        self.fuel_sources = {'wood': {'capacity': 99, 'burn speed': 2000}, 'coal': {'capacity': 99, 'burn speed': 4000}}
        self.speed_factor = 1
        self.inv.fuel = InvSlot(item=None, rect=None, valid_inputs=self.fuel_sources.keys())
        self.init_ui(FurnaceUI)


class SteelFurnace(Furnace):
    def __init__(
        self,
        xy: pg.Vector2, 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group],
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        mouse: Mouse,
        keyboard: Keyboard,
        player: Player,
        assets: dict[str, dict[str, any]], 
        tile_map: np.ndarray,
        obj_map: np.ndarray,
        gen_outline: callable,
        gen_bg: callable,
        rect_in_sprite_radius: callable,
        render_item_amount: callable,
        save_data: dict[str, any]
    ):
        super().__init__(
            xy, 
            image, 
            z, 
            sprite_groups, 
            screen, 
            cam_offset, 
            mouse, 
            keyboard, 
            player, 
            assets, 
            tile_map, 
            obj_map,
            gen_outline, 
            gen_bg, 
            rect_in_sprite_radius, 
            render_item_amount, 
            save_data
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
        self.inv.fuel = InvSlot(item=None, rect=None, valid_inputs=self.fuel_sources['non-electric'].keys() + self.fuel_sources['electric'])
        self.speed_factor = 2
        self.init_ui(FurnaceUI)


class ElectricFurnace(Furnace):
    def __init__(
        self,
        xy: pg.Vector2, 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group],
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        mouse: Mouse,
        keyboard: Keyboard,
        player: Player,
        assets: dict[str, dict[str, any]], 
        tile_map: np.ndarray,
        obj_map: np.ndarray,
        gen_outline: callable,
        gen_bg: callable,
        rect_in_sprite_radius: callable,
        render_item_amount: callable,
        save_data: dict[str, any]
    ):
        super().__init__(
            xy, 
            image, 
            z, 
            sprite_groups, 
            screen, 
            cam_offset, 
            mouse, 
            keyboard, 
            player, 
            assets, 
            tile_map, 
            obj_map,
            gen_outline, 
            gen_bg, 
            rect_in_sprite_radius, 
            render_item_amount, 
            save_data
        )
        self.variant = 'electric'
        self.recipe = MACHINES['electric furnace']['recipe']
        self.fuel_sources = {'electric poles'}
        self.speed_factor = 2.5
        self.init_ui(FurnaceUI)