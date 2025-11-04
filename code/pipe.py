from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player

import pygame as pg
import numpy as np

from settings import MAP_SIZE, TILE_SIZE, PIPE_BORDERS
from sprite_bases import SpriteBase
from timer import Timer

class Pipe(SpriteBase):
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
        item_transport_map: np.ndarray,
        obj_map: np.ndarray,
        tile_IDs: dict[str, int],
        variant_idx: int
    ):
        super().__init__(xy, image, z, sprite_groups)
        self.screen = screen
        self.cam_offset = cam_offset
        self.mouse = mouse
        self.keyboard = keyboard
        self.player = player
        self.assets = assets
        self.tile_map = tile_map
        self.item_transport_map = item_transport_map
        self.obj_map = obj_map
        self.tile_IDs = tile_IDs
        self.variant_idx = variant_idx
        
        self.graphics = self.assets['graphics']
        self.tile_xy = (int(xy.x) // TILE_SIZE, int(xy.y) // TILE_SIZE)
        self.transport_item = None
        self.speed_factor = 1
        self.timers = {'move item': Timer(length=2000 * self.speed_factor, function=self.transport, auto_start=False, loop=False, store_progress=False)}
        self.connections = {}
        self.transport_direction = None
        self.xy_to_cardinal = {
            0: {(1, 0): 'E', (-1, 0): 'W'},
            1: {(0, -1): 'N', (0, 1): 'S'},
            2: {(1, 0): 'SE', (0, -1): 'WN'},
            3: {(0, -1): 'EN', (-1, 0): 'SW'},
            4: {(1, 0): 'NE', (0, 1): 'WS'},
            5: {(-1, 0): 'ES', (0, 1): 'NW'}
        }
        self.get_connected_objs()

    def get_connected_objs(self) -> None:
        pipe_data = PIPE_BORDERS[self.variant_idx]
        self.connections = {xy: None for xy in (pipe_data if self.variant_idx <= 5 else [xy for dirs in pipe_data.values() for xy in dirs])}
        self.borders = list(self.connections.keys()) if self.variant_idx <= 5 else dict(pipe_data.items()) # converting to a dict to avoid the error from calling .values() on a dict_items object
        x, y = self.tile_xy
        for dx, dy in self.borders if self.variant_idx <= 5 else [xy for dxy in pipe_data.values() for xy in dxy]:
            if (0 < x + dx < MAP_SIZE[0] and 0 < y + dy < MAP_SIZE[1]) and (obj := self.obj_map[x + dx, y + dy]):
                if isinstance(obj, Pipe):
                    if (dx * -1, dy * -1) in obj.borders if obj.variant_idx <= 5 else obj.borders.values(): # ensure the pipes are connected and not just adjacent
                        self.connections[dx, dy] = obj
                else:
                    self.connections[dx, dy] = obj # machines don't have a 'facing direction' so no need to check if they're only just adjacent
        self.transport_direction = self.borders[0] if self.variant_idx <= 5 else {'horizontal': pipe_data['horizontal'][0], 'vertical': pipe_data['vertical'][0]} # default to the 1st index

    def transport(self) -> None:
        if self.transport_item:
            if obj := self.obj_map[self.tile_xy[0] + self.transport_direction[0], self.tile_xy[1] + self.transport_direction[1]]: 
                if isinstance(obj, Pipe):
                    if not obj.transport_item:
                        obj.transport_item = self.transport_item
                        self.transport_item = None
                else:
                    pass
        else:
            for dxy in [xy for xy in self.connections if self.connections[xy] is not None]:
                obj = self.connections[dxy]                          
                if isinstance(obj, Pipe): # don't add the bottom 2 conditions to this line, it needs to be alone for the else condition to run without error
                    if obj.transport_item and (obj.xy // TILE_SIZE) + obj.transport_direction == self.tile_xy:
                        self.transport_item = obj.transport_item
                        obj.transport_item = None
                else:
                    if dxy == self.transport_direction:
                        pass # add to the machine's inventory
                    else:
                        if obj.output['amount'] > 0:
                            self.transport_item = obj.output['item']
                            obj.output['amount'] -= 1

    def render_transport_ui(self) -> None:
        if self.variant_idx <= 5: # TODO: add the junction pipes
            direction_surf = self.graphics['pipe directions'][self.xy_to_cardinal[self.variant_idx][self.transport_direction]]
            self.screen.blit(direction_surf, direction_surf.get_frect(center=self.rect.center - self.cam_offset))

        if self.transport_item:
            item_surf = self.graphics[self.transport_item]
            self.screen.blit(item_surf, item_surf.get_frect(center=self.rect.center - self.cam_offset))
        
    def update_rotation(self) -> None:
        if self.keyboard.pressed_keys[pg.K_r] and self.rect.collidepoint(self.mouse.world_xy) and not self.player.item_holding:
            self.variant_idx = (self.variant_idx + 1) % len(PIPE_BORDERS)
            self.image = self.graphics[f'pipe {self.variant_idx}']
            self.tile_map[self.tile_xy] = self.tile_IDs[f'pipe {self.variant_idx}']
            self.get_connected_objs()

    def update_transport_direction(self) -> None:
        if self.keyboard.pressed_keys[pg.K_LSHIFT] and self.rect.collidepoint(self.mouse.world_xy):
            if self.variant_idx <= 5:
                self.transport_direction = self.borders[0] if self.transport_direction == self.borders[1] else self.borders[1]
            else:
                if self.keyboard.pressed_keys[pg.K_h] or self.keyboard.pressed_keys[pg.K_v]:
                    axis = 'horizontal' if self.keyboard.pressed_keys[pg.K_h] else 'vertical'
                    if len(self.borders[axis]) > 1:
                        d0, d1 = self.borders[axis][0], self.borders[axis][1]
                        self.transport_direction[axis] = d1 if self.transport_direction[axis] == d0 else d0

    def update(self, dt: float) -> None:
        self.update_rotation()
        self.update_transport_direction()
        self.transport()
        self.render_transport_ui()