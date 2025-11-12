from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player

import pygame as pg
import numpy as np
from collections import Counter
from random import choice

from timer import Timer
from drill_ui import DrillUI
from sprite_bases import MachineSpriteBase
from settings import TILE_SIZE, TILE_ORE_RATIO, MAP_SIZE, RES

class Drill(MachineSpriteBase):
    def __init__(
        self, 
        xy: tuple[int, int], 
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
        item_transport_map: np.ndarray,
        gen_outline: callable,
        gen_bg: callable,
        rect_in_sprite_radius: callable,
        render_item_amount: callable,
        save_data: dict[str, any],
        tile_ids: dict[str, int],
        tile_id_name_map: dict[int, str]
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
            item_transport_map,
            gen_outline, 
            gen_bg, 
            rect_in_sprite_radius, 
            render_item_amount, 
            save_data
        )
        self.tile_map = tile_map
        self.tile_ids = tile_ids
        self.tile_id_name_map = tile_id_name_map

        min_x, max_x = self.rect.left // TILE_SIZE, self.rect.right // TILE_SIZE
        min_y = self.rect.bottom // TILE_SIZE
        max_y = min_y + min(MAP_SIZE[1] - min_y, RES[1] // 4)
        self.span_x, self.span_y = max_x - min_x, max_y - min_y
        self.map_slice = save_data['map slice'] if save_data else self.tile_map[min_x:max_x, min_y:max_y]

        self.ore_data = save_data['ore data'] if save_data else self.get_ore_data()
        self.target_ore = save_data['target ore'] if save_data else None
        self.num_ore_available = save_data['num ore available'] if save_data else None
        self.ore_col = save_data['ore col'] if save_data else 0
        self.ore_row = save_data['ore row'] if save_data else 0

        self.extract_time_factor = 1.05 # extraction times increase as the drill moves deeper into the ground
        self.timers = {
            'extract': Timer(2000 * self.speed_factor * self.extract_time_factor * (self.ore_row + 1), self.extract, auto_start=False, loop=True),
            'burn fuel': Timer(2000 * self.speed_factor * self.extract_time_factor * (self.ore_row + 1), self.extract, auto_start=False, loop=True),
        }

        self.has_inv = True

    def get_ore_data(self) -> dict[str, int]:
        ignore_ids = {self.tile_ids['air'], self.tile_ids['item extended'], self.tile_ids['dirt']}
        ore_data = {self.tile_id_name_map[i]: {'amount': a * TILE_ORE_RATIO} for i, a in zip(*np.unique(self.map_slice, return_counts=True)) if i not in ignore_ids}
        for k in ore_data:
            ore_data[k]['locations'] = np.argwhere(self.map_slice == self.tile_ids[k])
        return ore_data

    def extract(self) -> None:
        self.num_ore_available -= 1
        if not self.num_ore_available: # all ore in this tile has been extracted
            self.convert_tile(self.ore_xy)

        self.fuel_input['amount'] -= 1
        if not self.fuel_input['amount']:
            self.fuel_input['item'] = None
        
        self.output['amount'] += 1
        if not self.output['item']:
            self.output['item'] = self.target_ore

        if self.ore_col % self.span_x == 0:
            self.ore_row += 1
            self.timers['extract'].length *= self.extract_time_factor

    def convert_tile(self, tile_xy: tuple[int, int]) -> None: 
        directions = self.get_neighbor_directions(tile_xy)
        if directions:
            neighbor_ID_counter = Counter(self.tile_map[tile_xy + xy] for xy in directions)
        else:
            self.tile_map[tile_xy] = self.tile_IDs['air']
            return

        tile_freqs = neighbor_ID_counter.most_common()
        (IDs, freqs) = zip(*tile_freqs)
        f0, f1, f2, f3 = (list(freqs) + [0, 0, 0])[:4] # adding zeros to follow in case the original list has less than 4 elements
        if f0 > f1:
            self.tile_map[tile_xy] = IDs[0]

        elif f0 == f1 and f1 != f2: # f0 & f1 have the majority
            self.tile_map[tile_xy] = choice(IDs[:2])

        else: # all indices store different tiles
            self.tile_map[tile_xy] = choice(IDs)

    def get_neighbor_directions(self, tile_xy: tuple[int, int]) -> list[tuple[int, int]]:
        directions = [(0, -1), (1, 0), (0, 1), (-1, 0)] # north, east, south, west
        if not self.ore_row > 1:
            directions.remove((0, -1))

        if tile_xy[0] == MAP_SIZE[0] - 1:
            directions.remove((1, 0))

        if tile_xy[1] == MAP_SIZE[1] - 1:
            directions.remove((0, 1))
        
        if tile_xy[0] == 0:
            directions.remove((-1, 0))

        return directions

    def get_save_data(self) -> dict[str, list|dict]:
        return {
            'xy': list(self.rect.topleft),
            'map slice': self.map_slice.tolist(),
            'ore data': self.ore_data,
            'target ore': self.target_ore,
            'num ore available': self.num_ore_available,
            'ore col': self.ore_col,
            'ore row': self.ore_row,
            'output': self.output
        }

    def get_active_state(self) -> bool:
        if not self.active:
            if self.target_ore and self.fuel_input['item'] and self.output['amount'] < self.max_capacity['output']:
                self.active = True
        elif not (self.fuel_input['item'] and self.output['amount'] < self.max_capacity['output']):
            self.active = False
            self.timers.clear()

        return self.active
    
    def update(self, dt: float) -> None:
        self.ui.update('drill')
        if self.get_active_state():
            if self.timers['extract'].running: 
                self.timers['extract'].update()
            else:
                self.timers['extract'].start()


class BurnerDrill(Drill):
    def __init__(
        self, 
        xy: tuple[int, int], 
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
        item_transport_map: np.ndarray,
        gen_outline: callable,
        gen_bg: callable,
        rect_in_sprite_radius: callable,
        render_item_amount: callable,
        save_data: dict[str, any],
        tile_ids: dict[str, int],
        tile_id_name_map: dict[int, str]
    ):  
        self.speed_factor = 1
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
            item_transport_map,
            gen_outline,
            gen_bg,
            rect_in_sprite_radius,
            render_item_amount,
            save_data,
            tile_ids,
            tile_id_name_map
        )
        self.variant = 'burner'
        self.fuel_sources = {'wood': {'capacity': 99, 'burn speed': 3000}, 'coal': {'capacity': 99, 'burn speed': 6000}}
        self.max_capacity = {'fuel': 50, 'output': 99}
        self.init_ui(DrillUI)


class ElectricDrill(Drill):
    def __init__(
        self, 
        xy: tuple[int, int], 
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
        item_transport_map: np.ndarray,
        gen_outline: callable,
        gen_bg: callable,
        rect_in_sprite_radius: callable,
        render_item_amount: callable,
        save_data: dict[str, any],
        tile_ids: dict[str, int],
        tile_id_name_map: dict[int, str]
    ):  
        self.speed_factor = 1.5
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
            item_transport_map,
            gen_outline,
            gen_bg,
            rect_in_sprite_radius,
            render_item_amount,
            save_data,
            tile_ids,
            tile_id_name_map
        )
        self.variant = 'electric'
        self.fuel_sources = {'electric poles'}
        self.init_ui(DrillUI)  