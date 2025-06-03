from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from asset_manager import AssetManager
    import numpy as np
    from inventory import Inventory
    from player import Player

import pygame as pg
from os.path import join
import math

from settings import TILE_SIZE, TILES, TILE_REACH_RADIUS, TOOLS, MACHINES, FPS, Z_LAYERS
from player import Player
from timer import Timer
from mech_sprites import mech_sprite_dict

class SpriteManager:
    def __init__(
        self,
        screen: pg.Surface,
        camera_offset: pg.Vector2,
        asset_manager: AssetManager,
        tile_map: np.ndarray,
        tile_IDs: dict[str, int],
        collision_map: dict[tuple[int, int], pg.Rect],
        inventory: Inventory
    ):
        self.screen = screen
        self.camera_offset = camera_offset
        self.asset_manager = asset_manager
        self.tile_map = tile_map
        self.tile_IDs =  tile_IDs
        self.collision_map = collision_map
        self.inventory = inventory

        self.all_sprites = pg.sprite.Group()
        self.human_sprites = pg.sprite.Group()
        self.mech_sprites = pg.sprite.Group()
        self.cloud_sprites = pg.sprite.Group()
        self.animated_sprites = pg.sprite.Group()
        self.all_groups = {k: v for k, v in vars(self).items() if isinstance(v, pg.sprite.Group)}

        self.active_items = {} # block/tool currently held by a given sprite
         
        self.mining = Mining(
            self.tile_map, 
            self.tile_IDs, 
            self.collision_map, 
            self.get_tool_strength, 
            self.pick_up_item
        )

        self.crafting = Crafting(
            self.tile_map,
            self.tile_IDs,
            self.collision_map
        )

        self.item_placement = ItemPlacement(
            self.screen,
            self.camera_offset,
            self.tile_map,
            self.tile_IDs,
            self.collision_map,
            self.inventory,
            self.all_sprites,
            self.mech_sprites
        )

    # not doing a list comprehension in __init__ since sprites aren't 
    # assigned their groups until after SpriteManager is initialized
    def init_active_items(self) -> None:
        # TODO: update this for loop once a sprite group for mobs is added, unless you decide they can't hold items
        for sprite in self.human_sprites: 
            self.active_items[sprite] = sprite.item_holding
        
    @staticmethod
    def get_tool_strength(sprite: pg.sprite.Sprite) -> int:
        if sprite.item_holding:
            data = sprite.item_holding.split() # ['<material>', '<tool>']
            return TOOLS[data[1]][data[0]]['strength']
        return sprite.arm_strength
    
    @staticmethod
    def end_action(sprite: pg.sprite.Sprite) -> None:
        '''return a sprite to an idle state and update its graphic'''
        sprite.state = 'idle'
        #'sprite.frame_index = 0' defaults to rendering the first frame of the old animation state
        sprite.image = sprite.frames['idle'][0] if sprite.facing_left else pg.transform.flip(sprite.frames['idle'][0], True, False)

    def pick_up_item(self, sprite: pg.sprite.Sprite) -> None:
        pass

    def update(self, dt) -> None:
        for sprite in self.all_sprites:
            sprite.update(dt)


class Mining:
    def __init__(
        self, 
        tile_map: np.ndarray,
        tile_IDs: dict[str, int],
        collision_map: dict[tuple[int, int], pg.Rect],
        get_tool_strength: callable,
        pick_up_item: callable
    ):
        self.tile_map = tile_map
        self.tile_IDs =  tile_IDs
        self.collision_map = collision_map
        self.get_tool_strength = get_tool_strength
        self.pick_up_item = pick_up_item
        
        self.mining_map = {} # {tile coords: {hardness: int, hits: int}}

    def start(self, sprite: pg.sprite.Sprite, tile_coords: tuple[int, int]) -> None:
        if sprite.item_holding and 'pickaxe' in sprite.item_holding:
            if isinstance(sprite, Player): 
                if self.valid_tile(sprite, tile_coords):
                    sprite.state = 'mining'

                    if tile_coords not in self.mining_map:
                        self.init_tile(tile_coords)

                    self.update_tile(sprite, tile_coords) 
                    self.collision_map.update_map(tile_coords, remove_tile = True)
            else:
                pass
       
    def init_tile(self, tile_coords: tuple[int, int]) -> None:
        '''initialize a new key/value pair in the mining map'''
        tile_index = self.tile_map[tile_coords]
        self.mining_map[tile_coords] = {'hardness': TILES[self.get_tile_name(tile_index)]['hardness'], 'hits': 0}

    @staticmethod
    def get_tile_name(tile_index: int) -> str:
        for index, name in enumerate(TILES):
            if index == tile_index:
                return name

    def valid_tile(self, sprite: pg.sprite.Sprite, tile_coords: tuple[int, int]) -> bool:
        sprite_coords = pg.Vector2(sprite.rect.center) // TILE_SIZE
        tile_distance = sprite_coords.distance_to(tile_coords)
        return tile_distance <= TILE_REACH_RADIUS and self.tile_map[tile_coords] != self.tile_IDs['air']
    
    # TODO: decrease the strength of the current tool as its usage accumulates    
    def update_tile(self, sprite: pg.sprite.Sprite, tile_coords: tuple[int, int]) -> bool:
        tool_strength = self.get_tool_strength(sprite)     
        data = self.mining_map[tile_coords]
        data['hits'] += 1 / FPS
        data['hardness'] -= tool_strength * data['hits'] 
        
        if self.mining_map[tile_coords]['hardness'] <= 0:
            sprite.inventory.add_item(self.get_tile_name(self.tile_map[tile_coords]))
            self.tile_map[tile_coords] = self.tile_IDs['air']
            del self.mining_map[tile_coords]


class Crafting:
    def __init__(
        self, 
        tile_map: np.ndarray,
        tile_IDs: dict[str, int],
        collision_map: dict[tuple[int, int], pg.Rect]
    ):
        self.tile_map = tile_map
        self.tile_IDs = tile_IDs
        self.collision_map = collision_map

    def craft_item(self, name: str, recipe: dict[str, int], sprite: pg.sprite.Sprite) -> None:
        if self.can_craft_item(sprite.inventory.contents, recipe):
            for item, amount in recipe.items():
                sprite.inventory.remove_item(item, amount)
            sprite.inventory.add_item(name)

    @staticmethod
    def can_craft_item(inventory_contents: dict[str, dict[str, int]], recipe: dict[str, int]) -> bool:
        # first check if the recipe items are available, then check if the quantity of them item are enough
        return all(inventory_contents.get(item, {}).get('amount', 0) >= amount_needed for item, amount_needed in recipe.items())


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
        if image.get_size() == (TILE_SIZE, TILE_SIZE):
            self.place_single_tile_object(tile_coords, player) 
        else:
            self.place_multiple_tile_object(tile_coords, image, player)

    def place_single_tile_object(self, tile_coords: tuple[int, int], player: Player) -> None:
        if self.can_place_item(tile_coords, player.rect.center):
            self.tile_map[tile_coords] = self.get_tile_id(player.item_holding)
            self.collision_map.update_map(tile_coords, add_tile = True)
                
            self.inventory.remove_item(player.item_holding, 1)
            player.item_holding = None

    def place_multiple_tile_object(self, tile_coords: tuple[int, int], image: pg.Surface, player: Player) -> None:
        tile_coords_list = self.get_tile_coords_list(tile_coords, image)
        tiles_available = [self.can_place_item(tile, player.rect.center) for tile in tile_coords_list]
        
        if self.object_grounded_check(tile_coords_list) and False not in tiles_available:
            image_topleft = tile_coords_list[0]
            self.tile_map[image_topleft] = self.get_tile_id(player.item_holding) # only store the topleft to prevent rendering multiple images
            for coord in tile_coords_list[1:]: 
                self.tile_map[coord] = self.tile_IDs['obj extended'] # update the remaining tiles covered with a separate ID to be ignored by the renderer

            if player.item_holding in mech_sprite_dict.keys():
                world_space_coords = pg.Vector2(image_topleft) * TILE_SIZE
                self.instantiate_item_placed(player.item_holding, world_space_coords, image)

            self.inventory.remove_item(player.item_holding, 1)
            player.item_holding = None
    
    def can_place_item(self, tile_coords: tuple[int, int], player_coords: tuple[int, int]) -> bool:
        x_dist = tile_coords[0] - (player_coords[0] // TILE_SIZE)
        y_dist = tile_coords[1] - (player_coords[1] // TILE_SIZE)
        in_reach = abs(x_dist) <= TILE_REACH_RADIUS and abs(y_dist) <= TILE_REACH_RADIUS

        empty_tile = self.tile_map[tile_coords] == self.tile_IDs['air']
        
        return in_reach and empty_tile

    def get_tile_coords_list(self, tile_coords: tuple[int, int], image: pg.Surface) -> list[tuple[int, int]]:
        '''return a list of tile map coordinates to update when placing items that cover >1 tile'''
        coords = []
        tile_span_x = math.ceil(image.get_width() / TILE_SIZE)
        tile_span_y = math.ceil(image.get_height() / TILE_SIZE)
        for x in range(tile_span_x):
            for y in range(tile_span_y):
                coords.append((tile_coords[0] + x, tile_coords[1] + y))
        return coords

    def get_tile_id(self, tile_name: str) -> int:
        for name, id_num in self.tile_IDs.items():
            if name == tile_name:
                return id_num
    
    def object_grounded_check(self, tile_coords_list: list[tuple[int, int]]) -> None:
        '''for objects of heights > 1 tile, get their southernmost tiles to check if they border the ground'''
        max_y = max([xy[1] for xy in tile_coords_list])
        ground_coords = [xy for xy in tile_coords_list if xy[1] == max_y]
        on_ground = all([self.tile_map[xy[0], xy[1] + 1] != self.tile_IDs['air'] for xy in ground_coords]) 
        return on_ground

    def instantiate_item_placed(self, item: str, coords: tuple[int, int], image: pg.Surface) -> None:
        '''create an instance of the item's class if applicable (e.g non-terrain tile objects)'''
        item_class = mech_sprite_dict[item]
        sprite_groups = [self.all_sprites, self.mech_sprites]
        item = item_class(coords, image, Z_LAYERS['main'], sprite_groups, self.camera_offset)