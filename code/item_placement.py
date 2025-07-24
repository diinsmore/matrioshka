from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from inventory import Inventory

import pygame as pg
from math import ceil

from settings import TILE_SIZE, TILES, TILE_REACH_RADIUS, Z_LAYERS
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
        mech_sprites: pg.sprite.Group
    ):
        self.screen = screen
        self.camera_offset = camera_offset
        self.tile_map = tile_map
        self.tile_IDs = tile_IDs
        self.collision_map = collision_map
        self.inventory = inventory
        self.all_sprites = all_sprites
        self.mech_sprites = mech_sprites

    def place_item(self, player: Player, image: pg.Surface, tile_coords: tuple[int, int]) -> None:
        self.place_single_tile_obj(tile_coords, player) if image.get_size() == (TILE_SIZE, TILE_SIZE) else self.place_multi_tile_obj(tile_coords, image, player)
        
    def place_single_tile_obj(self, tile_coords: tuple[int, int], player: Player) -> None:
        if self.valid_placement(tile_coords, player):
            self.tile_map[tile_coords] = self.tile_IDs[player.item_holding]
            self.collision_map.update_map(tile_coords, add_tile = True)
            
            self.inventory.remove_item(player.item_holding, 1)
            player.item_holding = None

    def place_multi_tile_obj(self, tile_coords: tuple[int, int], image: pg.Surface, player: Player) -> None:
        tile_coords_list = self.get_tile_coords_list(tile_coords, image)
        if self.valid_placement(tile_coords_list, player):
            image_topleft = tile_coords_list[0]
            self.tile_map[image_topleft] = self.tile_IDs[player.item_holding] # only store the topleft to prevent rendering multiple images
            self.collision_map.update_map(image_topleft, add_tile = True)
            for coord in tile_coords_list[1:]: 
                self.tile_map[coord] = self.tile_IDs['obj extended'] # update the remaining tiles covered with a separate ID to be ignored by the renderer
                self.collision_map.update_map(coord, add_tile = True)

            if player.item_holding in mech_sprite_dict.keys():
                world_space_coords = pg.Vector2(image_topleft) * TILE_SIZE
                self.instantiate_item(player.item_holding, world_space_coords, image)
            
            self.inventory.remove_item(player.item_holding, 1)
            player.item_holding = None
    
    def valid_placement(self, tile_coords: tuple[int, int] | list[tuple[int, int]], player: Player) -> bool:
        if isinstance(tile_coords, tuple):
            valid = self.can_reach_tile(tile_coords, player.rect.center) and \
                    self.tile_map[tile_coords] == self.tile_IDs['air'] and \
                    self.valid_obj_border(tile_coords, single_tile_obj = True)
        else:
            ground_coords = self.get_ground_coords(tile_coords)
            grounded = all((self.valid_obj_border(xy, multi_tile_obj = True) for xy in ground_coords))

            valid = grounded and all((
                self.can_reach_tile(xy, player.rect.center) and 
                self.tile_map[xy] == self.tile_IDs['air'] 
                for xy in tile_coords
            ))
        return valid

    @staticmethod
    def can_reach_tile(tile_coords: tuple[int, int], player_coords: tuple[int, int]) -> bool:
        x_dist = tile_coords[0] - (player_coords[0] // TILE_SIZE)
        y_dist = tile_coords[1] - (player_coords[1] // TILE_SIZE)
        return abs(x_dist) <= TILE_REACH_RADIUS and abs(y_dist) <= TILE_REACH_RADIUS 

    def get_tile_coords_list(self, tile_coords: tuple[int, int], image: pg.Surface) -> list[tuple[int, int]]:
        '''return a list of tile map coordinates to update when placing items that cover >1 tile'''
        coords = []
        tile_span_x = ceil(image.get_width() / TILE_SIZE)
        tile_span_y = ceil(image.get_height() / TILE_SIZE)
        for x in range(tile_span_x):
            for y in range(tile_span_y):
                coords.append((tile_coords[0] + x, tile_coords[1] + y))
        return coords

    def valid_obj_border(self, tile_coords: tuple[int, int], single_tile_obj: bool = False, multi_tile_obj: bool = False) -> bool:
        '''
        single tile objects: check for any solid tile bordering the tile selected
        multi-tile objects: check the bottom row of tiles to ensure the object is grounded
        '''
        tile_IDs = {self.tile_IDs[name] for name in list(TILES.keys())}
        if single_tile_obj:
            border_coords = [
                (tile_coords[0], tile_coords[1] - 1), # north
                (tile_coords[0] + 1, tile_coords[1]), # east
                (tile_coords[0], tile_coords[1] + 1), # south
                (tile_coords[0] - 1, tile_coords[1]), # west
            ]
            return any(self.tile_map[bc] in tile_IDs for bc in border_coords)
        else:
            return self.tile_map[tile_coords[0], tile_coords[1] + 1] in tile_IDs

    def render_placement_ui(self, icon_image: pg.Surface, icon_rect: pg.Rect, tile_coords: tuple[int, int], player: Player) -> None:
        '''add a slight tinge of color to the image to signal whether it can be placed at the current location'''
        mouse_world_coords = pg.mouse.get_pos() + self.camera_offset
        tiles_covered = ceil(icon_image.width / TILE_SIZE)
        if tiles_covered == 1:
            valid = self.valid_placement(tile_coords, player)
        else:
            coords_list = self.get_tile_coords_list(tile_coords, icon_image)
            valid = self.valid_placement(coords_list, player)

        tint_image = pg.Surface(icon_image.get_size())
        tint_image.fill('green' if valid else 'red')
        tint_image.set_alpha(25)
        tint_rect = tint_image.get_rect(topleft = icon_rect.topleft)
        self.screen.blit(tint_image, tint_rect)
            
    @staticmethod
    def get_ground_coords(tile_coords: tuple[int, int]) -> list[tuple[int, int]]:
        '''returns the tiles of an object that would be directly above the ground/surface that it's being placed on'''
        max_y = max([xy[1] for xy in tile_coords])
        return [xy for xy in tile_coords if xy[1] == max_y]

    def instantiate_item(self, item: str, coords: tuple[int, int], image: pg.Surface) -> None:
        '''create an instance of the item's class if applicable (e.g non-terrain tile objects)'''
        item_class = mech_sprite_dict[item]
        sprite_groups = [self.all_sprites, self.mech_sprites]
        item = item_class(coords, image, Z_LAYERS['main'], sprite_groups, self.camera_offset)