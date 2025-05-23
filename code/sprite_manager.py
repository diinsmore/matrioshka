from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from asset_manager import AssetManager
    import numpy as np

import pygame as pg
from os.path import join

from settings import TILE_SIZE, TILES, TOOLS, FPS
from player import Player
from timer import Timer

class SpriteManager:
    def __init__(
        self, 
        asset_manager: AssetManager,
        tile_map: np.ndarray,
        tile_IDs: dict[str, int],
        collision_map: dict[tuple[int, int], pg.Rect],
    ):
        self.asset_manager = asset_manager
        self.tile_map = tile_map
        self.tile_IDs =  tile_IDs
        self.collision_map = collision_map

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
            self.tile_map,
            self.tile_IDs,
            self.collision_map
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


class SpriteBase(pg.sprite.Sprite):
    def __init__(
        self, 
        coords: pg.Vector2,
        image: dict[str, dict[str, pg.Surface]], 
        z: dict[str, int],  
        sprite_groups: list[pg.sprite.Group]
    ):
        super().__init__(*sprite_groups)
        self.sprite_groups = sprite_groups
        self.image = image
        self.rect = self.image.get_rect(topleft = coords)
        self.z = z # layer to render on


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
        self.tile_reach_radius = 4

    def start(self, sprite: pg.sprite.Sprite, tile_coords: tuple[int, int], update_collision_map: callable) -> None:
        if sprite.item_holding and sprite.item_holding.split()[1] == 'pickaxe': # ignore the item's material if specified
            if isinstance(sprite, Player): 
                if self.valid_tile(sprite, tile_coords):
                    sprite.state = 'mining'

                    if tile_coords not in self.mining_map:
                        self.init_tile(tile_coords)

                    self.update_tile(sprite, tile_coords) 
                    update_collision_map(tile_coords, self.collision_map)
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
        return tile_distance <= self.tile_reach_radius and self.tile_map[tile_coords] != self.tile_IDs['air']
    
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
        tile_map: np.ndarray,
        tile_IDs: dict[str, int],
        collision_map: dict[tuple[int, int], pg.Rect]
    ):
        self.tile_map = tile_map
        self.tile_IDs = tile_IDs
        self.collision_map = collision_map  

    def place_item(self, tile_coords: tuple[int, int]) -> None:
        pass
        # if 0 <= tile_id < len(TILES.keys()): # placing a tile
             # self.tile_map[tile_coords] = self.tile_IDs[self.item_holding][tile_id]

       # coords = self.get_item_coords(rect)

       # for coords in tile_coords:
           # self.tile_map[coords] = self.tile_IDs['solid object']

    def get_item_coords(self, rect: pg.Rect) -> list[tuple[int, int]]:
        left, top = rect.left // TILE_SIZE, rect.top // TILE_SIZE
        coords = []
        for x in range(1, (rect.width // TILE_SIZE) + 1):
            for y in range(1, (rect.height // TILE_SIZE) + 1):
                coords.append((left + (x * TILE_SIZE), top + (y * TILE_SIZE)))