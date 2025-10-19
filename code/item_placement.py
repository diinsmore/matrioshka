from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from inventory import Inventory
    from input_manager import Mouse, Keyboard
    from sprite_manager import SpriteManager
    from player import Player
    from sprite_base import SpriteBase

import pygame as pg
from math import ceil
from collections import defaultdict

from settings import MAP_SIZE, TILE_SIZE, TILES, RAMP_TILES, TILE_REACH_RADIUS, Z_LAYERS, MACHINES

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
        machine_cls_map: dict[str, type[SpriteBase]],
        save_data: dict[str, any]|None
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
        self.assets = assets
        self.gen_outline = gen_outline, 
        self.gen_bg = gen_bg, 
        self.rect_in_sprite_radius = rect_in_sprite_radius, 
        self.render_item_amount = render_item_amount, 
        self.machine_cls_map = machine_cls_map
        self.save_data = save_data
       
        self.machine_map = defaultdict(list, save_data['machine map']) if save_data else defaultdict(list)
        self.machine_names = list(MACHINES.keys()) + ['pipe']
        self.tile_names = list(tile_IDs.keys())

    def place_item(self, sprite: pg.sprite.Sprite, tile_xy: tuple[int, int]) -> None:
        surf = self.assets['graphics'][sprite.item_holding]
        if surf.size[0] <= TILE_SIZE and surf.size[1] <= TILE_SIZE:
            if self.valid_placement(tile_xy, sprite):
                self.place_single_tile_item(tile_xy, sprite, item_name)
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

    def valid_item_border(self, x: int, y: int, single_tile: bool=False, multi_tile: bool=False) -> bool:
        tile_IDs = {self.tile_IDs[name] for name in list(TILES.keys())}
        if single_tile:
            for name in RAMP_TILES:
                tile_IDs.add(name)
            return any(self.tile_map[xy] in tile_IDs for xy in [(x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)])
        else:
            return self.tile_map[x, y + 1] in tile_IDs

    def valid_pipe_border(self, x: int, y: int, pipe_idx: int) -> bool:
        machine_ids = {self.tile_IDs[m] for m in MACHINES} | {self.tile_IDs['item extended']}
        match pipe_idx:
            case 0:
                valid = any((
                    self.tile_map[x + 1, y] in {self.tile_IDs['pipe 0'], self.tile_IDs['pipe 3'], self.tile_IDs['pipe 5'], *machine_ids},
                    self.tile_map[x - 1, y] in {self.tile_IDs['pipe 0'], self.tile_IDs['pipe 2'], self.tile_IDs['pipe 4'], *machine_ids}
                ))
            case 1:
                valid = any((
                    self.tile_map[x, y - 1] in {self.tile_IDs['pipe 1'], self.tile_IDs['pipe 4'], self.tile_IDs['pipe 5'], *machine_ids},
                    self.tile_map[x, y + 1] in {self.tile_IDs['pipe 1'], self.tile_IDs['pipe 2'], self.tile_IDs['pipe 3'], *machine_ids}
                ))
            case 2:
                valid = any((
                    self.tile_map[x + 1, y] in {self.tile_IDs['pipe 0'], self.tile_IDs['pipe 3'], self.tile_IDs['pipe 5'], *machine_ids},
                    self.tile_map[x, y - 1] in {self.tile_IDs['pipe 1'], self.tile_IDs['pipe 4'], self.tile_IDs['pipe 5'], *machine_ids}
                ))
            case 3:
                valid = any((
                    self.tile_map[x - 1, y] in {self.tile_IDs['pipe 0'], self.tile_IDs['pipe 2'], self.tile_IDs['pipe 4'], *machine_ids},
                    self.tile_map[x, y - 1] in {self.tile_IDs['pipe 1'], self.tile_IDs['pipe 4'], self.tile_IDs['pipe 5'], *machine_ids}
                ))
            case 4:
                valid = any((
                    self.tile_map[x + 1, y] in {self.tile_IDs['pipe 0'], self.tile_IDs['pipe 3'], self.tile_IDs['pipe 5'], *machine_ids},
                    self.tile_map[x, y + 1] in {self.tile_IDs['pipe 1'], self.tile_IDs['pipe 2'], self.tile_IDs['pipe 3'], *machine_ids}
                ))
            case 5:
                valid = any((
                    self.tile_map[x - 1, y] in {self.tile_IDs['pipe 0'], self.tile_IDs['pipe 2'], self.tile_IDs['pipe 4'], *machine_ids},
                    self.tile_map[x, y + 1] in {self.tile_IDs['pipe 1'], self.tile_IDs['pipe 2'], self.tile_IDs['pipe 3'], *machine_ids}
                ))
        return valid

    def place_single_tile_item(self, tile_xy: tuple[int, int], sprite: pg.sprite.Sprite, item_name: str=None) -> None: # passing the item name if a class needs to be initialized
        self.tile_map[tile_xy] = self.tile_IDs[sprite.item_holding]
        self.collision_map.update_map(tile_xy, add_tile=True)
        sprite.inventory.remove_item(sprite.item_holding)
        sprite.item_holding = None
        if item_name:
            if item_name in self.machine_names:
                self.init_machine_cls(item_name, tile_xy)
            else:
                pass     

    def place_multi_tile_item(self, tile_xy_list: list[tuple[int, int]], surf: pg.Surface, sprite: pg.sprite.Sprite) -> None:
        surf_topleft = tile_xy_list[0]
        item_name = sprite.item_holding
        self.tile_map[surf_topleft] = self.tile_IDs[item_name] # only store the topleft to prevent rendering multiple images
        self.collision_map.update_map(surf_topleft, add_tile=True)
        for xy in tile_xy_list[1:]: 
            self.tile_map[xy] = self.tile_IDs['item extended'] # update the remaining tiles covered with a separate ID to be ignored by the renderer
            self.collision_map.update_map(xy, add_tile=True)
        
        if item_name in self.machine_names:
            self.machine_map[item_name].append(surf_topleft)
            self.init_machine_cls(item_name, surf_topleft)

        sprite.inventory.remove_item(item_name)
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
            
    @staticmethod
    def get_ground_coords(tile_xy: tuple[int, int]) -> list[tuple[int, int]]:
        '''returns the tiles of an object that would be directly above the ground/surface that it's being placed on'''
        max_y = max([xy[1] for xy in tile_xy])
        return [xy for xy in tile_xy if xy[1] == max_y]

    def init_machine_cls(self, name: str, surf_topleft: tuple[int, int], sprite_idx: int=None) -> None:
        self.machine_cls_map[name](**self.sprite_mgr.get_machine_params(name, surf_topleft, sprite_idx))