from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from inventory import Inventory
    from input_manager import Mouse, Keyboard
    from sprite_manager import SpriteManager
    from player import Player
    from sprite_base import SpriteBase
    from machine_ui import MachineUIHelpers

import pygame as pg
from math import ceil
from collections import defaultdict

from settings import MAP_SIZE, TILE_SIZE, TILES, TILE_REACH_RADIUS, Z_LAYERS, MACHINES

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
        helpers: MachineUIHelpers,
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
        self.helpers = helpers
        self.machine_cls_map = machine_cls_map
        self.save_data = save_data
       
        self.machine_map = defaultdict(list, self.save_data['machine map']) if self.save_data else defaultdict(list)
        self.machine_names = list(MACHINES.keys()) 
        self.tile_names = list(tile_IDs.keys())

    def place_item(self, sprite: pg.sprite.Sprite, tile_xy: tuple[int, int]) -> None:
        surf = self.assets['graphics'][sprite.item_holding]
        if surf.get_size() == (TILE_SIZE, TILE_SIZE):
            if self.valid_placement(tile_xy, sprite):
                self.place_single_tile_item(tile_xy, sprite)
        else:
            tile_xy_list = self.get_tile_xy_list(tile_xy, surf)
            if self.valid_placement(tile_xy_list, sprite):
                self.place_multi_tile_item(tile_xy_list, surf, sprite)
    
    def valid_placement(self, tile_xy: tuple[int, int] | list[tuple[int, int]], sprite: pg.sprite.Sprite) -> bool:
        if isinstance(tile_xy, tuple):
            valid = all((
                self.can_reach_tile(tile_xy, sprite.rect.center),
                self.tile_map[tile_xy] == self.tile_IDs['air'],
                self.valid_item_border(tile_xy, single_tile=True),
                sprite.item_holding in self.tile_names
            ))
        else:
            grounded = all((self.valid_item_border(xy, multi_tile=True) for xy in self.get_ground_coords(tile_xy)))
            valid = grounded and all((
                self.can_reach_tile(xy, sprite.rect.center) and 
                self.tile_map[xy] == self.tile_IDs['air'] 
                for xy in tile_xy
            ))
        return valid
        
    def can_reach_tile(self, tile_xy_world: tuple[int, int], sprite_xy_world: tuple[int, int]) -> bool:
        tile_world_px = pg.Vector2(tile_xy_world) * TILE_SIZE
        px_dist = (tile_world_px - pg.Vector2(sprite_xy_world)).length() 
        return px_dist // TILE_SIZE <= TILE_REACH_RADIUS

    def valid_item_border(self, tile_xy: tuple[int, int], single_tile: bool = False, multi_tile: bool = False) -> bool:
        '''
        single tile items: check for any solid tile bordering the tile selected
        multi-tile items: check the bottom row of tiles to ensure the object is grounded
        '''
        tile_IDs = {self.tile_IDs[name] for name in list(TILES.keys())}
        if single_tile:
            return any(self.tile_map[xy] in tile_IDs for xy in [
                (tile_xy[0], tile_xy[1] - 1), # north
                (tile_xy[0] + 1, tile_xy[1]), # east
                (tile_xy[0], tile_xy[1] + 1), # south
                (tile_xy[0] - 1, tile_xy[1]), # west
            ])
        else:
            return self.tile_map[tile_xy[0], tile_xy[1] + 1] in tile_IDs

    def place_single_tile_item(self, tile_xy: tuple[int, int], sprite: pg.sprite.Sprite) -> None:
        self.tile_map[tile_xy] = self.tile_IDs[sprite.item_holding]
        self.collision_map.update_map(tile_xy, add_tile=True)
        sprite.inventory.remove_item(sprite.item_holding)
        sprite.item_holding = None

    def place_multi_tile_item(self, tile_xy_list: list[tuple[int, int]], surf: pg.Surface, sprite: pg.sprite.Sprite) -> None:
        surf_topleft = tile_xy_list[0]
        item = sprite.item_holding
        self.tile_map[surf_topleft] = self.tile_IDs[item] # only store the topleft to prevent rendering multiple images
        self.collision_map.update_map(surf_topleft, add_tile=True)
        for xy in tile_xy_list[1:]: 
            self.tile_map[xy] = self.tile_IDs['item extended'] # update the remaining tiles covered with a separate ID to be ignored by the renderer
            self.collision_map.update_map(xy, add_tile=True)
        
        if item in self.machine_names:
            self.machine_map[item].append(surf_topleft)
            self.init_machine_class(item, surf_topleft)

        sprite.inventory.remove_item(item)
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

    def init_machine_class(self, item: str, img_topleft: tuple[int, int]) -> None:
        self.machine_cls_map[item](
            coords=pg.Vector2(img_topleft[0] * TILE_SIZE, img_topleft[1] * TILE_SIZE),
            image=self.assets['graphics'][item],
            z=Z_LAYERS['main'],
            sprite_groups=[self.sprite_mgr.all_sprites, self.sprite_mgr.active_sprites, self.sprite_mgr.mech_sprites],
            screen=self.screen,
            cam_offset=self.cam_offset,
            mouse=self.mouse,
            keyboard=self.keyboard,
            player=self.player,
            assets=self.assets,
            helpers=self.helpers,
            save_data=self.save_data['sprites'][item] if self.save_data else None
        )