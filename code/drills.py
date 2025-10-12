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

from sprite_base import MachineSpriteBase
from settings import TILE_SIZE, TILE_ORE_RATIO, MAP_SIZE, RES

class Drill(MachineSpriteBase):
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
        save_data: dict[str, any],
        tile_map: np.ndarray,
        tile_IDs: dict[str, int],
        tile_IDs_to_names: dict[int, str]
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
            gen_outline, 
            gen_bg, 
            rect_in_sprite_radius, 
            render_item_amount, 
            save_data
        )
        self.tile_map = tile_map
        self.tile_IDs = tile_IDs
        self.tile_IDs_to_names = tile_IDs_to_names
        self.map_slice = save_data['map slice'] if save_data else self.get_map_slice()
        self.available_ores = self.get_available_ores()
        self.target_ore = save_data['target ore'] if save_data else None
        self.num_ore_available = 0
        self.num_ore_output = save_data['available ore'] if save_data else 0
        self.ore_xy = save_data['ore xy'] if save_data else None
        self.ore_idx = save_data['ore idx'] if save_data else 0
        self.max_ore_idx = save_data['max ore idx'] if save_data else None
        self.ore_row = save_data['ore row'] if save_data else 1
        self.extract_time_factor = 1.05 # extraction times increase as the drill moves deeper into the ground

        self.timers = {
            'extract': Timer(
                length=500 * self.speed_factor * (self.extract_time_factor ** (self.ore_row - 1)), 
                function=self.extract, 
                auto_start=False, 
                loop=True
            )
        }
        self.has_inv = True

    def get_map_slice(self) -> np.ndarray:
        top = self.rect.bottom // TILE_SIZE
        return self.tile_map[self.rect.left // TILE_SIZE:self.rect.right // TILE_SIZE, top:top + min(MAP_SIZE[1] - top, RES[1] // 4)]

    def get_available_ores(self) -> dict[str, int]:
        idxs, amounts = np.unique(self.map_slice, return_counts=True)
        return dict(zip([self.tile_IDs_to_names[i] for i in idxs if i not in (self.tile_IDs['air'], self.tile_IDs['item extended'])], amounts))

    def calc_ore_nums(self) -> None:
        target_ID = self.tile_IDs[self.target_ore]
        ore_xy_rel_slice = np.argwhere(map_slice == target_ID)
        self.ore_xy = ore_xy_rel_slice + np.array([top, left]) # relative to the full tile map now
        self.max_ore_idx = len(self.ore_xy)
        self.num_ore_available = self.max_ore_idx * TILE_ORE_RATIO

    def select_target_ore(self) -> None:
        pass

    def extract(self) -> None:
        self.available_ore -= 1
        if self.available_ore % TILE_ORE_RATIO == 0: # all ore in this tile has been extracted
            self.ore_idx += 1
            self.convert_tile()

        if not self.output['item']:
            self.output['item'] = self.target_ore
        self.output['amount'] += 1

        if self.ore_idx % self.reach_radius[0] == 0:
            self.ore_row += 1
            self.timers['extract'].length *= self.extract_time_factor

        if self.ore_idx == self.max_ore_idx:
            del self.timers['extract']

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
            'map slice': self.map_slice.tolist(),
            'xy': list(self.rect.topleft),
            'target ore': self.target_ore,
            'ore num': self.ore_num,
            'ore xy': self.ore_xy.tolist(),
            'max ore idx': self.max_ore_idx,
            'ore idx': self.ore_idx,
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
            self.extract()


class BurnerDrill(Drill):
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
        save_data: dict[str, any],
        tile_map: np.ndarray,
        tile_IDs: dict[str, int],
        tile_IDs_to_names: dict[int, str]
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
            gen_outline, 
            gen_bg, 
            rect_in_sprite_radius, 
            render_item_amount, 
            save_data, 
            tile_map, 
            tile_IDs, 
            tile_IDs_to_names
        )
        self.variant = 'burner'
        self.fuel_sources = {'wood': {'capacity': 99, 'burn speed': 3000}, 'coal': {'capacity': 99, 'burn speed': 6000}}
        self.init_ui(DrillUI)


class ElectricDrill(Drill):
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
        save_data: dict[str, any],
        tile_map: np.ndarray,
        tile_IDs: dict[str, int],
        tile_IDs_to_names: dict[int, str]
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
            gen_outline, 
            gen_bg, 
            rect_in_sprite_radius, 
            render_item_amount, 
            save_data, 
            tile_map, 
            tile_IDs, 
            tile_IDs_to_names
        )
        self.variant = 'electric'
        self.fuel_sources = {'electric poles'}
        self.init_ui(DrillUI)  