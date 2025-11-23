from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from inventory import Inventory
    from input_manager import Mouse, Keyboard
    from sprite_manager import SpriteManager
    from player import Player
    from sprite_base import SpriteBase

import pygame as pg
import numpy as np
from math import ceil
from collections import defaultdict

from settings import MAP_SIZE, TILE_SIZE, TILES, RAMP_TILES, TILE_REACH_RADIUS, Z_LAYERS, OBJ_ITEMS, MACHINES, PIPE_TRANSPORT_DIRS

class ItemPlacement:
    def __init__(
        self,
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        tile_map: np.ndarray,
        tile_IDs: dict[str, int],
        collision_map: dict[tuple[int, int], pg.Rect],
        inventory: Inventory,
        sprite_mgr: SpriteManager,
        mouse: Mouse,
        keyboard: Keyboard,
        player: Player,
        assets: dict[str, dict[str, any]],
        gen_outline: callable, 
        gen_bg: callable, 
        rect_in_sprite_radius: callable, 
        render_item_amount: callable, 
        items_init_when_placed: dict[str, type[SpriteBase]],
        save_data: dict[str, any] | None
    ):
        self.screen = screen
        self.cam_offset = cam_offset
        self.tile_map = tile_map
        self.tile_IDs = tile_IDs
        self.collision_map = collision_map
        self.inventory = inventory
        self.sprite_mgr = sprite_mgr
        self.mouse = mouse
        self.keyboard = keyboard
        self.player = player
        self.graphics = assets['graphics']
        self.gen_outline = gen_outline, 
        self.gen_bg = gen_bg, 
        self.rect_in_sprite_radius = rect_in_sprite_radius, 
        self.render_item_amount = render_item_amount, 
        self.items_init_when_placed = items_init_when_placed
        self.save_data = save_data
       
        self.obj_map = np.full(MAP_SIZE, None, dtype=object) # stores every tile an object overlaps with (tile_map only stores the topleft since it controls rendering)
        self.machine_ids = {self.tile_IDs[m] for m in MACHINES if 'pipe' not in m} | {self.tile_IDs['item extended']}
        self.pipe_ids = {self.tile_IDs[f'pipe {i}'] for i in range(len(PIPE_TRANSPORT_DIRS))}

    def place_item(self, sprite: pg.sprite.Sprite, tile_xy: tuple[int, int], old_pipe_idx: int=None) -> None:
        surf = self.graphics[sprite.item_holding]
        if surf.size[0] <= TILE_SIZE and surf.size[1] <= TILE_SIZE:
            if self.valid_placement(tile_xy, sprite):
                self.place_single_tile_item(tile_xy, sprite, old_pipe_idx)
        else:
            tile_xy_list = self.get_tile_xy_list(tile_xy, surf)
            if self.valid_placement(tile_xy_list, sprite):
                self.place_multi_tile_item(tile_xy_list, surf, sprite)
    
    def valid_placement(self, tile_xy: tuple[int, int] | list[tuple[int, int]], sprite: pg.sprite.Sprite) -> bool:
        if isinstance(tile_xy, tuple):
            x, y = tile_xy
            valid = all((
                self.can_reach_tile(x, y, sprite.rect.center),
                self.tile_map[x, y] == self.tile_IDs['air'],
                self.valid_item_border(x, y, single_tile=True) if 'pipe' not in sprite.item_holding else self.valid_pipe_border(x, y, int(sprite.item_holding[-1]))
            ))
        else:
            grounded = all((self.valid_item_border(*xy, multi_tile=True) for xy in self.get_ground_coords(tile_xy)))
            valid = grounded and all((self.can_reach_tile(*xy, sprite.rect.center) and self.tile_map[xy] == self.tile_IDs['air'] for xy in tile_xy))
        return valid
        
    def can_reach_tile(self, x: int, y: int, sprite_xy_world: tuple[int, int]) -> bool:
        sprite_tile_xy = pg.Vector2(sprite_xy_world) // TILE_SIZE
        return abs(x - sprite_tile_xy.x) <= TILE_REACH_RADIUS and abs(y - sprite_tile_xy.y) <= TILE_REACH_RADIUS 
    
    @staticmethod
    def get_ground_coords(tile_xy: tuple[int, int]) -> list[tuple[int, int]]:
        max_y = max([xy[1] for xy in tile_xy])
        return [xy for xy in tile_xy if xy[1] == max_y]

    def valid_item_border(self, x: int, y: int, single_tile: bool=False, multi_tile: bool=False) -> bool:
        tile_IDs = {self.tile_IDs[name] for name in list(TILES.keys())}
        if single_tile:
            for name in RAMP_TILES:
                tile_IDs.add(name)
            return any(self.tile_map[xy] in tile_IDs for xy in [(x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)]) # TODO: update the ramp tile checks to prevent placing tiles that only attach to the slanted side
        else:
            return self.tile_map[x, y + 1] in tile_IDs

    def valid_pipe_border(self, x: int, y: int, pipe_idx: int) -> bool:
        pipe_data = PIPE_TRANSPORT_DIRS[pipe_idx]
        for dx, dy in pipe_data if pipe_idx <= 5 else (pipe_data['horizontal'] + pipe_data['vertical']):
            if 0 <= x + dx < MAP_SIZE[0] and 0 <= y + dy < MAP_SIZE[1] and self.tile_map[x + dx, y + dy] in (self.machine_ids | self.pipe_ids):
                return True
        return False

    def place_single_tile_item(self, tile_xy: tuple[int, int], sprite: pg.sprite.Sprite, old_pipe_idx: int=None) -> None: # passing the item name if a class needs to be initialized
        self.tile_map[tile_xy] = self.tile_IDs[sprite.item_holding]
        self.collision_map.update_map(tile_xy, add_tile=True)
        sprite.inventory.remove_item(sprite.item_holding if old_pipe_idx is None else f'pipe {old_pipe_idx}')
        if sprite.item_holding in OBJ_ITEMS:
            self.init_obj(sprite.item_holding, [tile_xy])  

    def place_multi_tile_item(self, tile_xy_list: list[tuple[int, int]], surf: pg.Surface, sprite: pg.sprite.Sprite) -> None:
        obj = sprite.item_holding in OBJ_ITEMS
        for i, xy in enumerate(tile_xy_list):
            if i == 0:
                self.tile_map[xy] = self.tile_IDs[sprite.item_holding] # only store the topleft as the item ID to avoid rendering multiple surfaces
                if obj:
                    self.init_obj(sprite.item_holding, tile_xy_list)
            else:
                self.tile_map[xy] = self.tile_IDs['item extended'] 
            self.collision_map.update_map(xy, add_tile=True)
        sprite.inventory.remove_item(sprite.item_holding)
        sprite.item_holding = None

    def get_tile_xy_list(self, tile_xy: tuple[int, int], image: pg.Surface) -> list[tuple[int, int]]:
        '''return a list of tile map coordinates to update when placing items that cover >1 tile'''
        coords = []
        tile_span_x = ceil(image.get_width() / TILE_SIZE)
        tile_span_y = ceil(image.get_height() / TILE_SIZE)
        for x in range(tile_span_x):
            for y in range(tile_span_y):
                coords.append((tile_xy[0] + x, tile_xy[1] + y))
        return coords

    def render_ui(self, icon_image: pg.Surface, icon_rect: pg.Rect, tile_xy: tuple[int, int], player: Player) -> None:
        '''add a slight tinge of color to the image to signal whether it can be placed at the current location'''
        tiles_covered = ceil(icon_image.width / TILE_SIZE)
        if tiles_covered == 1:
            valid = self.valid_placement(tile_xy, player)
        else:
            coords_list = self.get_tile_xy_list(tile_xy, icon_image)
            valid = self.valid_placement(coords_list, player)
      
        tint_image = pg.Surface(icon_image.get_size())
        tint_image.fill('green' if valid else 'red')
        tint_image.set_alpha(25)
        self.screen.blit(tint_image, tint_image.get_rect(topleft=icon_rect.topleft))

    def init_obj(self, name: str, tiles_covered: list[tuple[int, int]]) -> None:
        obj = self.items_init_when_placed[name if 'pipe' not in name else name.split(' ')[0]]
        obj_instance = obj(**self.sprite_mgr.get_init_params(name, tiles_covered)) # don't add the pipe index here, they all use the same Pipe class
        for xy in tiles_covered:
            self.obj_map[xy] = obj_instance