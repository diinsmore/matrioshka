from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player
    from inserter import Inserter

import pygame as pg
import numpy as np

from settings import MAP_SIZE, TILE_SIZE, TRANSPORT_DIRS
from sprite_bases import SpriteBase, TransportSpriteBase
from timer import Timer

class Pipe(TransportSpriteBase):
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
        
        self.speed_factor = 1
        self.timers = {'move item': Timer(length=2000 * self.speed_factor, function=self.transport, auto_start=False, loop=False, store_progress=False)}
        self.connections = {}
        self.transport_dir = None
        self.get_connected_objs()

    def get_connected_objs(self) -> None:
        pipe_data = TRANSPORT_DIRS[self.variant_idx]
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
            self.variant_idx = (self.variant_idx + 1) % len(TRANSPORT_DIRS)
            self.image = self.graphics[f'pipe {self.variant_idx}']
            self.tile_map[self.tile_xy] = self.tile_IDs[f'pipe {self.variant_idx}']
            self.get_connected_objs()

    def transport(self) -> None:
        for dxy in [xy for xy in self.connections if self.connections[xy] is not None]:
            transport_dir = self.transport_dir if self.variant_idx <= 5 else self.transport_dir['horizontal' if dxy[0] != 0 else 'vertical']
            if obj := self.connections[dxy]:                         
                if self.item_holding:
                    if dxy == transport_dir: 
                        if isinstance(obj, Pipe):
                            if not obj.item_holding:
                                obj.item_holding = self.item_holding
                                self.item_holding = None
                        else:
                            self.send_item_to_inserter(obj)
                else:
                    if isinstance(obj, Pipe): # don't add the bottom conditions to this line, it needs to be alone for the else condition to run without error
                        obj_dir = obj.transport_dir if obj.variant_idx <= 5 else obj.transport_dir['horizontal' if dxy[0] != 0 else 'vertical']
                        if obj.item_holding and dxy == (obj_dir[0] * -1, obj_dir[1] * -1) and \
                        (self.tile_xy[0] + transport_dir[0], self.tile_xy[1] + transport_dir[1]) != obj.tile_xy:
                            self.item_holding = obj.item_holding
                            obj.item_holding = None
                    else:
                        if dxy != transport_dir and obj.item_holding: # inserter sending item to pipe
                            self.item_holding = obj.item_holding
                            obj.item_holding = None

    def send_item_to_inserter(self, obj: Inserter) -> None:
        if not obj.item_holding:
            obj.item_holding = self.item_holding
            self.item_holding = None
        
    def config_transport_dir(self) -> None:
        if self.variant_idx <= 5:
            if self.keyboard.pressed_keys[pg.K_LSHIFT] and self.rect.collidepoint(self.mouse.world_xy):
                dirs = list(self.connections.keys())
                self.transport_dir = dirs[1] if self.transport_dir == dirs[0] else dirs[0]
        else:
            if (self.keyboard.pressed_keys[pg.K_LSHIFT] or self.keyboard.pressed_keys[pg.K_RSHIFT]) and self.rect.collidepoint(self.mouse.world_xy):
                axis = 'horizontal' if self.keyboard.pressed_keys[pg.K_LSHIFT] else 'vertical'
                dx, dy = self.transport_dir[axis]
                self.transport_dir[axis] = (dx * -1, dy * -1)

    def render_transport_ui(self) -> None:
        if self.variant_idx <= 5:
            dir_surf = self.dir_surfs[self.xy_to_cardinal[self.variant_idx][self.transport_dir]]
            self.screen.blit(dir_surf, dir_surf.get_frect(center=self.rect.center - self.cam_offset))
        else:
            for axis in ('horizontal', 'vertical'):
                dir_surf = self.dir_surfs[self.xy_to_cardinal[self.variant_idx][self.transport_dir[axis]]]
                self.screen.blit(dir_surf, dir_surf.get_rect(center=self.rect.center - self.cam_offset))

        if self.item_holding:
            item_surf = self.graphics[self.item_holding]
            self.screen.blit(item_surf, item_surf.get_rect(center=self.rect.center - self.cam_offset))

    def extract_item(self) -> None:
        if self.mouse.buttons_pressed['left'] and self.mouse.tile_xy == self.tile_xy and \
        (not self.player.item_holding or self.player.item_holding == self.item_holding):
            self.player.inventory.add_item(self.item_holding)
            self.player.item_holding = self.item_holding
            self.item_holding = None

    def update(self, dt: float) -> None:
        self.update_timers()
        self.render_transport_ui()
        self.update_rotation()
        self.config_transport_dir()
        self.extract_item()