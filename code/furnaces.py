from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player

import pygame as pg

from sprite_base import SpriteBase
from settings import MACHINES
from furnace_ui import FurnaceUI
from timer import Timer

class Furnace(SpriteBase):
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
        gen_outline: callable,
        gen_bg: callable,
        rect_in_sprite_radius: callable,
        render_item_amount: callable,
        save_data: dict[str, any]
    ):
        super().__init__(xy, image, z, sprite_groups)
        self.active = False
        self.max_capacity = {'smelt': 100, 'fuel': 50}
        self.can_smelt = {
            'copper': {'speed': 3000, 'output': 'copper plate'}, 
            'iron': {'speed': 5000, 'output': 'iron plate'},
            'iron plate': {'speed': 7000, 'output': 'steel plate'},
        }
        self.smelt_input = save_data['smelt input'] if save_data else {'item': None, 'amount': 0}
        self.fuel_input = save_data['fuel input'] if save_data else {'item': None, 'amount': 0}
        self.output = save_data['output'] if save_data else {'item': None, 'amount': 0}
        self.timers = {}
        # not initializing self.ui until the furnace variant is determined
        self.ui_params = {
            'screen': screen,
            'cam_offset': cam_offset,
            'mouse': mouse,
            'keyboard': keyboard,
            'player': player,
            'assets': assets,
            'gen_outline': gen_outline,
            'gen_bg': gen_bg,
            'rect_in_sprite_radius': rect_in_sprite_radius,
            'render_item_amount': render_item_amount
        }
    
    def init_ui(self) -> None: 
        self.ui = FurnaceUI(furnace=self, **self.ui_params)

    def get_active_state(self) -> bool:
        if not self.active:
            if self.smelt_input['item'] and self.fuel_input['item']:
                self.active = True
    
        elif not (self.smelt_input['item'] and self.fuel_input['item']):
            self.active = False
            self.timers.clear()

        return self.active
    
    def smelt(self) -> None:
        if not self.timers:
            smelt_item = self.smelt_input['item']
            self.timers['smelt'] = Timer(
                length=self.can_smelt[smelt_item]['speed'] // self.speed_factor, 
                function=self.update_box, 
                auto_start=True, 
                loop=True, 
                store_progress=True,
                smelt_item=smelt_item
            )
            if self.variant == 'burner':
                fuel_item = self.fuel_input['item']
                self.timers['fuel'] = Timer(
                    length=self.fuel_sources[fuel_item]['burn speed'] // self.speed_factor, 
                    function=self.update_box, 
                    auto_start=True, 
                    loop=True, 
                    store_progress=True,
                    fuel_item=fuel_item
                )
        for timer in self.timers.values():
            timer.update()

    def update_box(self, smelt_item: str = None, fuel_item: str = None) -> None:
        input_data = self.smelt_input if smelt_item else self.fuel_input # 'None' will never be passed for both
        input_data['amount'] -= 1
        if input_data['amount'] == 0:
            input_data['item'] = None
            self.active = False
        
        if smelt_item:
            output_item = self.can_smelt[smelt_item]['output']
            if not self.output['item']:
                self.output['item'] = output_item
            
            if output_item == self.output['item']:
                self.output['amount'] += 1

    def get_save_data(self) -> dict[str, list|str]:
        return {
            'xy': list(self.rect.topleft),
            'smelt input': self.smelt_input,
            'fuel input': self.fuel_input,
            'output': self.output
        }

    def update(self, dt: float) -> None:
        self.ui.update()
        if self.get_active_state():
            self.smelt()
        

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
        self.recipe = MACHINES['burner furnace']['recipe']
        self.fuel_sources = {'wood': {'capacity': 99, 'burn speed': 2000}, 'coal': {'capacity': 99, 'burn speed': 4000}}
        self.speed_factor = 1
        self.init_ui()


class SteelFurnace(Furnace):
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
        self.init_ui()


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
        self.recipe = MACHINES['electric furnace']['recipe']
        self.fuel_sources = {'electric poles'}
        self.speed_factor = 2.5
        self.init_ui()