from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player

import pygame as pg
import math

from settings import TILE_SIZE, MAP_SIZE, TRANSPORT_DIRS
from sprite_bases import TransportSpriteBase
from pipe import Pipe
from furnaces import Furnace
from timer import Timer

class Inserter(TransportSpriteBase):
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
        obj_map: np.ndarray
    ):
        super().__init__(xy, image, z, sprite_groups, screen, cam_offset, mouse, keyboard, player, assets, tile_map, obj_map)
        self.tile_borders = {
            'x axis': [(self.tile_xy[0] + dx, self.tile_xy[1]) for dx in (-1, 1) if 0 <= self.tile_xy[0] + dx < MAP_SIZE[0]],
            'y axis': [(self.tile_xy[0], self.tile_xy[1] + dy) for dy in (-1, 1) if 0 <= self.tile_xy[1] + dy < MAP_SIZE[1]],
        }
        self.receive_dir, self.send_dir = None, None
        self.rotated_over = False
        self.adj_sprites = {dxy: None for dxy in self.tile_borders}
        self.transport_idx = 0 # which index to take from the TRANSPORT_DIRS dictionary
        self.num_valid_configs = len([k for k in TRANSPORT_DIRS if isinstance(TRANSPORT_DIRS[k], list)]) # ignore the indexes only meant for handling junction pipes
        self.item_holding = None
        self.rotate_speed = 1500 
        self.speed_factor = 1
        self.rotate_dir = None
        self.original_img = self.image.copy()
        self.timers = {
            'check insert': Timer(length=self.rotate_speed/self.speed_factor, function=self.check_insert, auto_start=True, loop=True),
            'receive item': Timer(length=(self.rotate_speed/4)/self.speed_factor, function=None, auto_start=False, loop=False),
            'send item': Timer(length=(self.rotate_speed/4)/self.speed_factor, function=None, auto_start=False, loop=False),
        }
        
    def config_transport_dir(self) -> None:
        if self.keyboard.pressed_keys[pg.K_LSHIFT] and self.rect.collidepoint(self.mouse.world_xy):
            self.transport_idx = (self.transport_idx + 1) % self.num_valid_configs
            self.receive_dir, self.send_dir = TRANSPORT_DIRS[self.transport_idx]
   
    def check_insert(self) -> None: # TODO: will have to make this more modular depending on whether the receiving object is a furnace/inserter/lab/etc.
        x, y = self.tile_xy
        if self.receive_dir and self.send_dir and all(self.obj_map[x + dx, y + dy] is not None for dx, dy in (self.receive_dir, self.send_dir)):
            if not self.item_holding:
                sending_obj = self.obj_map[x + self.send_dir[0], y + self.send_dir[1]] 
                if not self.rotated_over:
                    self.rotate(sending_obj)
                    self.rotated_over = True
                    self.timers['receive item'].start()
                elif not self.timers['receive item'].running:
                    if not isinstance(sending_obj, Pipe):
                        if hasattr(sending_obj, 'output') and sending_obj.output['item']:
                            self.item_holding = sending_obj.output['item']
                            sending_obj.output['amount'] -= 1
                            if not sending_obj.output['amount']:
                                sending_obj.output['item'] = None
                            self.rotate(sending_obj, reset=True)
                            self.rotated_over = False
                    else:
                        if sending_obj.item_holding:
                            self.item_holding = sending_obj.item_holding
                            sending_obj.item_holding = None
                            self.rotate(sending_obj, reset=True)
                            self.rotated_over = False
            else:
                receiving_obj = self.obj_map[x + self.receive_dir[0], y + self.receive_dir[1]]
                if not self.rotated_over:
                    self.rotate(receiving_obj)
                    self.rotated_over = True
                    self.timers['send item'].start()
                elif not self.timers['send item'].running:
                    if not isinstance(receiving_obj, Pipe):
                        if receiving_obj.fuel_input['item'] in {None, self.item_holding}:
                            if receiving_obj.fuel_input['item'] is None:
                                receiving_obj.fuel_input['item'] = self.item_holding
                            receiving_obj.fuel_input['amount'] += 1
                            self.item_holding = None  
                            self.rotate(receiving_obj, reset=True)
                            self.rotated_over = False
                    else:
                        if not receiving_obj.item_holding:
                            receiving_obj.item_holding = self.item_holding
                            self.item_holding = None
                            self.rotate(receiving_obj, reset=True)
                            self.rotated_over = False
                    
    def rotate(self, target_obj: pg.sprite.Sprite, reset: bool=False) -> None:
        if not reset:
            dxy = pg.Vector2(self.rect.center) - pg.Vector2(target_obj.rect.center)
            angle = -math.degrees(math.atan2(dxy.y, dxy.x)) + 135 # negative since rotozoom rotates counterclockwise
            self.image = pg.transform.rotozoom(self.original_img, angle, 1) 
            center = self.rect.center # preserve the original center
            self.rect = self.image.get_rect(center=center)
        else:
            center = self.rect.center
            self.image = self.original_img
            self.rect = self.image.get_rect(center=center)

    def render_transport_ui(self) -> None:
        if self.receive_dir and self.send_dir:
            dirs = self.xy_to_cardinal[self.transport_idx]
            receive_dir_surf = self.dir_ui[dirs[self.receive_dir]]
            self.screen.blit(receive_dir_surf, receive_dir_surf.get_frect(midbottom=self.rect.midtop - self.cam_offset))
            send_dir_surf = self.dir_ui[dirs[self.send_dir]]
            self.screen.blit(send_dir_surf, send_dir_surf.get_frect(midtop=self.rect.midbottom - self.cam_offset))

        if self.item_holding:
            item_surf = self.graphics[self.item_holding]
            self.screen.blit(item_surf, item_surf.get_rect(center=self.rect.midtop - self.cam_offset))

    def update(self, dt: float) -> None:
        self.update_timers()
        self.render_transport_ui()
        self.config_transport_dir()


class BurnerInserter(Inserter):
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
        obj_map: np.ndarray
    ):
        super().__init__(xy, image, z, sprite_groups, screen, cam_offset, mouse, keyboard, player, assets, tile_map, obj_map)
        self.tile_reach_radius = 1
        self.fuel_sources = {'coal': {'capacity': 50, 'burn speed': 6000}}


class ElectricInserter(Inserter):
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
        obj_map: np.ndarray
    ):
        super().__init__(xy, image, z, sprite_groups, screen, cam_offset, mouse, keyboard, player, assets, tile_map, obj_map)
        self.tile_reach_radius = 1
        self.speed_factor = 1.5
        self.fuel_sources = {'electricity': {}}


class LongHandedInserter(Inserter):
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
        obj_map: np.ndarray
    ):
        super().__init__(xy, image, z, sprite_groups, screen, cam_offset, mouse, keyboard, player, assets, tile_map, obj_map)
        self.tile_reach_radius = 2
        self.speed_factor = 1.25
        self.fuel_sources = {'electricity': {}}