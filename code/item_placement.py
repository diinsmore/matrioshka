from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from inventory import Inventory

import pygame as pg
from math import ceil
from collections import defaultdict

from settings import MAP_SIZE, TILE_SIZE, TILES, TILE_REACH_RADIUS, Z_LAYERS, MACHINES
from mech_sprites import mech_sprite_dict

class ItemPlacement:
    def __init__(
        self,
        screen: pg.Surface,
        camera_offset: pg.Vector2,
        tile_map: np.ndarray,
        tile_IDs: dict[str, int],
        collision_map: dict[tuple[int, int], pg.Rect],
        inventory: Inventory,
        all_sprites: pg.sprite.Group,
        mech_sprites: pg.sprite.Group,
        saved_data: dict[str, any] | None
    ):
        self.screen = screen
        self.camera_offset = camera_offset
        self.tile_map = tile_map
        self.tile_IDs = tile_IDs
        self.collision_map = collision_map
        self.inventory = inventory
        self.all_sprites = all_sprites
        self.mech_sprites = mech_sprites
        self.saved_data = saved_data
        
        self.machine_map = self.saved_data['machine map'] if self.saved_data else defaultdict(list)
        self.machine_names = set(MACHINES.keys())

    def place_item(self, sprite: pg.sprite.Sprite, image: pg.Surface, tile_xy: tuple[int, int]) -> None:
        if image.get_size() == (TILE_SIZE, TILE_SIZE):
            if self.valid_placement(tile_xy, sprite):
                self.place_single_tile_item(tile_xy, sprite)
        else:
            tile_xy_list = self.get_tile_xy_list(tile_xy, image)
            if self.valid_placement(tile_xy_list, sprite):
                self.place_multi_tile_item(tile_xy_list, image, sprite)
        
    def place_single_tile_item(self, tile_xy: tuple[int, int], sprite: pg.sprite.Sprite) -> None:
        item = sprite.item_holding
        self.tile_map[tile_xy] = self.tile_IDs[item]
        self.collision_map.update_map(tile_xy, add_tile = True)
        if item in self.machine_names:
            self.machine_map[item].append(tile_xy)
        
        sprite.inventory.remove_item(item)
        sprite.item_holding = None

    def place_multi_tile_item(self, tile_xy_list: list[tuple[int, int]], image: pg.Surface, sprite: pg.sprite.Sprite) -> None:
        image_topleft = tile_xy_list[0]
        item = sprite.item_holding
        self.tile_map[image_topleft] = self.tile_IDs[item] # only store the topleft to prevent rendering multiple images
        self.collision_map.update_map(image_topleft, add_tile = True)
        for coord in tile_xy_list[1:]: 
            self.tile_map[coord] = self.tile_IDs['item extended'] # update the remaining tiles covered with a separate ID to be ignored by the renderer
            self.collision_map.update_map(coord, add_tile = True)
        
        if item in self.machine_names:
            self.machine_map[item].append(image_topleft)

        sprite.inventory.remove_item(item)
        sprite.item_holding = None

    def valid_placement(self, tile_xy: tuple[int, int] | list[tuple[int, int]], sprite: pg.sprite.Sprite) -> bool:
        if isinstance(tile_xy, tuple):
            valid = self.can_reach_tile(tile_xy, sprite.rect.center) and \
                    self.tile_map[tile_xy] == self.tile_IDs['air'] and \
                    self.valid_item_border(tile_xy, single_tile_item = True)
        else:
            grounded = all((self.valid_item_border(xy, multi_tile_item = True) for xy in self.get_ground_coords(tile_xy)))
            valid = grounded and all((
                self.can_reach_tile(xy, sprite.rect.center) and 
                self.tile_map[xy] == self.tile_IDs['air'] 
                for xy in tile_xy
            ))
        return valid

    @staticmethod
    def can_reach_tile(tile_xy: tuple[int, int], sprite_xy: tuple[int, int]) -> bool:
        x_dist = tile_xy[0] - (sprite_xy[0] // TILE_SIZE)
        y_dist = tile_xy[1] - (sprite_xy[1] // TILE_SIZE)
        return abs(x_dist) <= TILE_REACH_RADIUS and abs(y_dist) <= TILE_REACH_RADIUS 

    def get_tile_xy_list(self, tile_xy: tuple[int, int], image: pg.Surface) -> list[tuple[int, int]]:
        '''return a list of tile map coordinates to update when placing items that cover >1 tile'''
        coords = []
        tile_span_x = ceil(image.get_width() / TILE_SIZE)
        tile_span_y = ceil(image.get_height() / TILE_SIZE)
        for x in range(tile_span_x):
            for y in range(tile_span_y):
                coords.append((tile_xy[0] + x, tile_xy[1] + y))
        return coords

    def valid_item_border(self, tile_xy: tuple[int, int], single_tile_item: bool = False, multi_tile_item: bool = False) -> bool:
        '''
        single tile items: check for any solid tile bordering the tile selected
        multi-tile items: check the bottom row of tiles to ensure the object is grounded
        '''
        tile_IDs = {self.tile_IDs[name] for name in list(TILES.keys())}
        if single_tile_item:
            border_xy = [
                (tile_xy[0], tile_xy[1] - 1), # north
                (tile_xy[0] + 1, tile_xy[1]), # east
                (tile_xy[0], tile_xy[1] + 1), # south
                (tile_xy[0] - 1, tile_xy[1]), # west
            ]
            return any(self.tile_map[bc] in tile_IDs for bc in border_xy)
        else:
            return self.tile_map[tile_xy[0], tile_xy[1] + 1] in tile_IDs

    def render_placement_ui(self, icon_image: pg.Surface, icon_rect: pg.Rect, tile_xy: tuple[int, int], player: Player) -> None:
        '''add a slight tinge of color to the image to signal whether it can be placed at the current location'''
        mouse_world_coords = pg.mouse.get_pos() + self.camera_offset
        tiles_covered = ceil(icon_image.width / TILE_SIZE)
        if tiles_covered == 1:
            valid = self.valid_placement(tile_xy, player)
        else:
            coords_list = self.get_tile_xy_list(tile_xy, icon_image)
            valid = self.valid_placement(coords_list, player)

        tint_image = pg.Surface(icon_image.get_size())
        tint_image.fill('green' if valid else 'red')
        tint_image.set_alpha(25)
        tint_rect = tint_image.get_rect(topleft = icon_rect.topleft)
        self.screen.blit(tint_image, tint_rect)
            
    @staticmethod
    def get_ground_coords(tile_xy: tuple[int, int]) -> list[tuple[int, int]]:
        '''returns the tiles of an object that would be directly above the ground/surface that it's being placed on'''
        max_y = max([xy[1] for xy in tile_xy])
        return [xy for xy in tile_xy if xy[1] == max_y]