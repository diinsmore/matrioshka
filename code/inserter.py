from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player

import pygame as pg
from settings import TILE_SIZE, MAP_SIZE, TRANSPORT_DIRS
from sprite_bases import TransportSpriteBase
from pipe import Pipe
from furnaces import Furnace

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
        obj_map: np.ndarray,
        item_transport_map: np.ndarray,
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
            item_transport_map,
            gen_outline, 
            gen_bg, 
            rect_in_sprite_radius, 
            render_item_amount, 
            save_data
        )
        self.tile_borders = {
            'x axis': [(self.tile_xy[0] + dx, self.tile_xy[1]) for dx in (-1, 1) if 0 <= self.tile_xy[0] + dx < MAP_SIZE[0]],
            'y axis': [(self.tile_xy[0], self.tile_xy[1] + dy) for dy in (-1, 1) if 0 <= self.tile_xy[1] + dy < MAP_SIZE[1]],
        }
        self.receive_dir, self.send_dir = None, None
        self.adj_sprites = {dxy: None for dxy in self.tile_borders}
        self.transport_idx = 0 # which index to take from the TRANSPORT_DIRS dictionary
        self.num_valid_configs = len([k for k in TRANSPORT_DIRS if isinstance(TRANSPORT_DIRS[k], list)]) # ignore the indexes only meant for handling junction pipes
        self.item_holding = None
        
    def config_transport_dir(self) -> None:
        if self.keyboard.pressed_keys[pg.K_LSHIFT] and self.rect.collidepoint(self.mouse.world_xy):
            self.transport_idx = (self.transport_idx + 1) % self.num_valid_configs
            self.receive_dir, self.send_dir = TRANSPORT_DIRS[self.transport_idx]
            print(self.receive_dir, self.send_dir)

    def insert(self, item_name: str) -> None:
        if all(self.obj_map[dxy] is not None for dxy in (self.receive_dir, self.send_dir)):
            if self.item_holding:
                receiving_obj = self.obj_map + self.send_dir
                # TODO: will have to make this more modular depending on whether the receiving object is a furnace/inserter/lab/etc.
                if not isinstance(receiving_obj, Pipe): # the pipe class handles the sending/receiving of items to/from a pipe
                    if receiving_obj.fuel_input['item'] in {None, self.item_holding}:
                        if receiving_obj.fuel_input['item'] is None:
                            receiving_obj.fuel_input['item'] = self.item_holding
                        receiving_obj.fuel_input['amount'] += 1
                        self.item_holding = None  
            else:
                sending_obj = self.obj_map + self.receive_dir
                if not isinstance(receiving_obj, Pipe) and (item := sending_obj.output['item']):
                    self.item_holding = item
                    sending_obj.output['amount'] -= 1
                    if not sending_obj.output['amount']:
                        sending_obj.output['item'] = None
    
    def render_transport_ui(self) -> None:
        if self.receive_dir and self.send_dir:
            dirs = self.xy_to_cardinal[self.transport_idx]
            receive_dir_surf = self.dir_surfs[dirs[self.receive_dir]]
            self.screen.blit(receive_dir_surf, receive_dir_surf.get_frect(center=self.rect.midtop - self.cam_offset))
            send_dir_surf = self.dir_surfs[dirs[self.send_dir]]
            self.screen.blit(send_dir_surf, send_dir_surf.get_frect(center=self.rect.midbottom - self.cam_offset))

    def update(self, dt: float) -> None:
        self.config_transport_dir()
        self.render_transport_ui()


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
        obj_map: np.ndarray,
        item_transport_map: np.ndarray,
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
            item_transport_map,
            gen_outline, 
            gen_bg, 
            rect_in_sprite_radius, 
            render_item_amount, 
            save_data
        )
        self.tile_reach_radius = 1
        self.speed_factor = 1
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
        obj_map: np.ndarray,
        item_transport_map: np.ndarray,
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
            item_transport_map,
            gen_outline, 
            gen_bg, 
            rect_in_sprite_radius, 
            render_item_amount, 
            save_data
        )
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
        obj_map: np.ndarray,
        item_transport_map: np.ndarray,
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
            item_transport_map,
            gen_outline, 
            gen_bg, 
            rect_in_sprite_radius, 
            render_item_amount, 
            save_data
        )
        self.tile_reach_radius = 2
        self.speed_factor = 1.25
        self.fuel_sources = {'electricity': {}}