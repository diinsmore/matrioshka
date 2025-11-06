from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player

import pygame as pg
import numpy as np

from settings import MAP_SIZE, TILE_SIZE, PIPE_BORDERS
from sprite_bases import SpriteBase, MachineSpriteBase
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
        self.transport_dir = None
        self.xy_to_cardinal = {
            0: {(1, 0): 'E', (-1, 0): 'W'},
            1: {(0, -1): 'N', (0, 1): 'S'},
            2: {(1, 0): 'SE', (0, -1): 'WN'},
            3: {(0, -1): 'EN', (-1, 0): 'SW'},
            4: {(1, 0): 'NE', (0, 1): 'WS'},
            5: {(-1, 0): 'NW', (0, 1): 'ES'},
            6: {(1, 0): 'E', (-1, 0): 'W', (0, -1): 'N', (0, 1): 'S'},
            7: {(1, 0): 'E', (0, -1): 'N', (0, 1): 'S'},
            8: {(0, -1): 'N', (0, 1): 'S', (-1, 0): 'W'},
            9: {(1, 0): 'E', (-1, 0): 'W', (0, -1): 'N'},
            10: {(1, 0): 'E', (-1, 0): 'W', (0, 1): 'S'}
        }
        self.get_connected_objs()

    def get_connected_objs(self) -> None:
        pipe_data = PIPE_BORDERS[self.variant_idx]
        self.connections = {xy: None for xy in (pipe_data if self.variant_idx <= 5 else [xy for dirs in pipe_data.values() for xy in dirs])}
        x, y = self.tile_xy
        for dx, dy in self.connections if self.variant_idx <= 5 else [xy for dirs in pipe_data.values() for xy in dirs]:
            if (0 < x + dx < MAP_SIZE[0] and 0 < y + dy < MAP_SIZE[1]) and (obj := self.obj_map[x + dx, y + dy]):
                if isinstance(obj, Pipe):
                    if (dx * -1, dy * -1) in obj.connections: # ensure the pipes are connected and not just adjacent
                        self.connections[dx, dy] = obj
                else:
                    self.connections[dx, dy] = obj # machines don't have a 'facing direction' so no need to check if they're only just adjacent
        
        self.transport_dir = list(self.connections.keys())[0] if self.variant_idx <= 5 else {
            'horizontal': pipe_data['horizontal'][0], 'vertical': pipe_data['vertical'][0] # default to the 1st index
        } 

    def update_rotation(self) -> None:
            if self.keyboard.pressed_keys[pg.K_r] and self.rect.collidepoint(self.mouse.world_xy) and not self.player.item_holding:
                self.variant_idx = (self.variant_idx + 1) % len(PIPE_BORDERS)
                self.image = self.graphics[f'pipe {self.variant_idx}']
                self.tile_map[self.tile_xy] = self.tile_IDs[f'pipe {self.variant_idx}']
                self.get_connected_objs()

    def transport(self) -> None:
        for dxy in [xy for xy in self.connections if self.connections[xy] is not None]:
            if obj := self.connections[dxy]:                         
                if self.transport_item:
                    if dxy == self.transport_dir: 
                        if isinstance(obj, Pipe):
                            if not obj.transport_item:
                                obj.transport_item = self.transport_item
                                self.transport_item = None
                        else:
                            self.send_item_to_machine(obj)
                else:
                    if isinstance(obj, Pipe): # don't add the bottom conditions to this line, it needs to be alone for the else condition to run without error
                        if self.variant_idx == 5:
                            print(self.transport_dir)
                        obj_dir = obj.transport_dir if obj.variant_idx <= 5 else obj.transport_dir['horizontal' if dxy[0] != 0 else 'vertical']
                        if obj.transport_item and dxy == (obj_dir[0] * -1, obj_dir[1] * -1) and \
                        (self.tile_xy[0] + self.transport_dir[0], self.tile_xy[1] + self.transport_dir[1]) != obj.tile_xy:
                            self.transport_item = obj.transport_item
                            obj.transport_item = None
                    else:
                        if dxy != self.transport_dir and obj.output['amount'] > 0:
                            self.transport_item = obj.output['item']
                            obj.output['amount'] -= 1

    def send_item_to_machine(self, obj: pg.sprite.Sprite) -> None: # TODO: will have to update this to account for inserting items other than fuel, e.g parts to an assembler
        if obj.fuel_input['item'] in (None, self.transport_item):
            obj.fuel_input['amount'] += 1
            self.transport_item = None
        
    def update_transport_direction(self) -> None:
        if self.keyboard.pressed_keys[pg.K_LSHIFT] and self.rect.collidepoint(self.mouse.world_xy):
            if self.variant_idx <= 5:
                dirs = list(self.connections.keys())
                self.transport_dir = dirs[1] if self.transport_dir == dirs[0] else dirs[0]
            else:
                if self.keyboard.pressed_keys[pg.K_h] or self.keyboard.pressed_keys[pg.K_v]:
                    axis = 'horizontal' if self.keyboard.pressed_keys[pg.K_h] else 'vertical'
                    dx, dy = self.transport_dir[axis]
                    self.transport_dir[axis] = (dx * -1, dy * -1)

    def render_transport_ui(self) -> None:
        if self.variant_idx <= 5:
            dir_surf = self.graphics['pipe directions'][self.xy_to_cardinal[self.variant_idx][self.transport_dir]]
            self.screen.blit(dir_surf, dir_surf.get_frect(center=self.rect.center - self.cam_offset))
        else:
            for axis in ('horizontal', 'vertical'):
                dir_surf = self.graphics['pipe directions'][self.xy_to_cardinal[self.variant_idx][self.transport_dir[axis]]]
                self.screen.blit(dir_surf, dir_surf.get_rect(center=self.rect.center - self.cam_offset))

        if self.transport_item:
            item_surf = self.graphics[self.transport_item]
            self.screen.blit(item_surf, item_surf.get_rect(center=self.rect.center - self.cam_offset))

    def extract_item(self) -> None:
        if self.mouse.buttons_pressed['left'] and self.mouse.tile_xy == self.tile_xy and (not self.player.item_holding or self.player.item_holding == self.transport_item):
            self.player.inventory.add_item(self.transport_item)
            self.player.item_holding = self.transport_item
            self.transport_item = None

    def update_timers(self) -> None:
        for t in self.timers.values():
            if not t.running:
                t.start()
            t.update()

    def update(self, dt: float) -> None:
        self.update_timers()
        self.render_transport_ui()
        self.update_rotation()
        self.update_transport_direction()
        self.extract_item()