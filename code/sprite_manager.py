from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import numpy as np
    from inventory import Inventory
    from player import Player
    from physics_engine import CollisionMap

import pygame as pg
from os.path import join
from random import choice, randint
from file_import_functions import load_image

from settings import TILE_SIZE, TILES, TILE_REACH_RADIUS, TOOLS, MACHINES, FPS, Z_LAYERS, MAP_SIZE, RES, TREE_BIOMES
from player import Player
from timer import Timer
from mech_sprites import mech_sprite_dict
from nature_sprites import Tree, Cloud
from item_placement import ItemPlacement

class SpriteManager:
    def __init__(
        self,
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        graphics: dict[str, pg.Surface],
        sprite_movement: callable,
        collision_map: CollisionMap,
        tile_map: np.ndarray,
        tile_IDs: dict[str, int],
        tile_IDs_to_names: dict[str, int],
        tree_map: list[tuple[int, int]],
        current_biome: str,
        inventory: Inventory,
        saved_data: dict[str, any]
    ):
        self.screen = screen
        self.cam_offset = cam_offset
        self.graphics = graphics
        self.sprite_movement = sprite_movement
        self.collision_map = collision_map
        self.tile_map = tile_map
        self.tile_IDs = tile_IDs
        self.tile_IDs_to_names = tile_IDs_to_names
        self.tree_map = tree_map
        self.current_biome = current_biome
        
        self.inventory = inventory
        self.saved_data = saved_data

        self.all_sprites = pg.sprite.Group()
        self.animated_sprites = pg.sprite.Group()
        self.player_sprite = pg.sprite.GroupSingle()
        self.human_sprites = pg.sprite.Group()
        self.mech_sprites = pg.sprite.Group()
        self.nature_sprites = pg.sprite.Group()
        self.cloud_sprites = pg.sprite.Group()
        self.tree_sprites = pg.sprite.Group()
        self.item_sprites = pg.sprite.Group()
        self.all_groups = {k: v for k, v in vars(self).items() if isinstance(v, pg.sprite.Group)}

        self.player = None # not initialized until after the sprite manager

        self.active_items = {} # block/tool currently held by a given sprite
         
        self.mining = Mining(
            self.tile_map, 
            self.tile_IDs,
            self.tile_IDs_to_names,
            self.collision_map, 
            self.get_tool_strength, 
            self.pick_up_item 
        )

        self.crafting = Crafting(self.tile_map, self.tile_IDs, self.collision_map)

        self.item_placement = ItemPlacement(
            self.screen,
            self.cam_offset,
            self.tile_map,
            self.tile_IDs,
            self.collision_map,
            self.inventory,
            self.all_sprites,
            self.mech_sprites
        )

        self.wood_gathering = WoodGathering(
            self.tile_map, 
            self.tile_IDs, 
            self.tree_sprites, 
            self.tree_map, 
            self.cam_offset, 
            self.get_tool_strength,
            self.pick_up_item
        )
        
        self.ui = None # passed in engine.py after the UI class is initialized

        self.init_trees()
                
    # not doing a list comprehension in __init__ since sprites aren't 
    # assigned their groups until after the class is initialized
    def init_active_items(self) -> None:
        # TODO: update this for loop once a sprite group for mobs is added, unless you decide they can't hold items
        for sprite in self.human_sprites:
            self.active_items[sprite] = sprite.item_holding
        
    @staticmethod
    def get_tool_strength(sprite: pg.sprite.Sprite) -> int:
        if sprite.item_holding:
            data = sprite.item_holding.split()
            material, tool = data[0], data[1]
            return TOOLS[tool][material]['strength']
        return sprite.arm_strength
    
    @staticmethod
    def end_action(sprite: pg.sprite.Sprite) -> None:
        '''return a sprite to an idle state and update its graphic'''
        sprite.state = 'idle'
        sprite.image = sprite.frames['idle'][0] if sprite.facing_left else pg.transform.flip(sprite.frames['idle'][0], True, False)

    def pick_up_item(self, item: object, item_name: str, item_rect: pg.Rect) -> None:
        for sprite in self.get_sprites_in_radius(item_rect, self.human_sprites):
            if sprite.rect.colliderect(item_rect):
                sprite.inventory.add_item(item_name)
                self.ui.render_new_item_name(item_name, item_rect)
                item.kill()
                return

    @staticmethod
    def get_sprites_in_radius(
        target: pg.Rect, 
        group: pg.sprite.Group, 
        x_dist: int = (RES[0] // 2) + 100, 
        y_dist: int = (RES[1] // 2) + 100
    ) -> list[pg.sprite.Group]:
        return [
            sprite for sprite in group if 
            abs(sprite.rect.centerx - target.centerx) < x_dist and \
            abs(sprite.rect.centery - target.centery) < y_dist
        ]

    def init_clouds(self) -> None:
        if not self.cloud_sprites:
            x, y = self.player.rect.midtop
            image_folder = self.graphics['clouds']
            for cloud in range(randint(10, 15)):
                Cloud(
                    coords = pg.Vector2(x, y) + pg.Vector2(randint(1000, 2000), randint(-2000, -1500)),
                    image = image_folder[randint(0, len(image_folder) - 1)],
                    z = Z_LAYERS['clouds'],
                    sprite_groups = [self.all_sprites, self.nature_sprites, self.cloud_sprites],
                    speed = randint(1, 3),
                    player = self.player
                )
    
    def init_trees(self) -> None:
        if self.current_biome in TREE_BIOMES:
            image_folder = self.graphics[self.current_biome]['trees']
            tree_map = self.tree_map if not self.saved_data else self.saved_data['tree map']
            for xy in tree_map: 
                Tree(
                    coords = (pg.Vector2(xy) * TILE_SIZE) - self.cam_offset, 
                    image = choice(image_folder), 
                    z = Z_LAYERS['bg'],
                    sprite_groups = [self.all_sprites, self.nature_sprites, self.tree_sprites], 
                    tree_map = self.tree_map, 
                    tree_map_coords = xy,
                    sprite_movement = self.sprite_movement,
                    wood_image = self.graphics['materials']['wood'],
                    wood_sprites = [self.all_sprites, self.nature_sprites, self.item_sprites]
                )
            
    def update(self, dt) -> None:
        for sprite in self.all_sprites:
            sprite.update(dt)

        self.init_clouds()


class Mining:
    def __init__(
        self, 
        tile_map: np.ndarray,
        tile_IDs: dict[str, int],
        tile_IDs_to_names: dict[int, str],
        collision_map: dict[tuple[int, int], pg.Rect],
        get_tool_strength: callable,
        pick_up_item: callable
    ):
        self.tile_map = tile_map
        self.tile_IDs = tile_IDs
        self.tile_IDs_to_names = tile_IDs_to_names
        self.collision_map = collision_map
        self.get_tool_strength = get_tool_strength
        self.pick_up_item = pick_up_item
        
        self.mining_map = {} # {tile coords: {hardness: int, hits: int}}
        self.invalid_IDs = {self.tile_IDs['air'], self.tile_IDs['tree base']} # can't be mined
        self.ramp_IDs = [self.tile_IDs[name] for name in self.tile_IDs.keys() if 'ramp' in name]
    
    def run(self, sprite: pg.sprite.Sprite, tile_coords: tuple[int, int]) -> None:
        if sprite.item_holding and 'pickaxe' in sprite.item_holding:
            if self.valid_tile(sprite, tile_coords):
                sprite.state = 'mining'
                if tile_coords not in self.mining_map:
                    self.mining_map[tile_coords] = {
                        'hardness': TILES[self.get_tile_material(self.tile_map[tile_coords])]['hardness'], 
                        'hits': 0
                    }
                self.update_tile(sprite, tile_coords) 

    def valid_tile(self, sprite: pg.sprite.Sprite, tile_coords: tuple[int, int]) -> bool:
        sprite_coords = pg.Vector2(sprite.rect.center) // TILE_SIZE
        tile_distance = sprite_coords.distance_to(tile_coords)
        return tile_distance <= TILE_REACH_RADIUS and self.tile_map[tile_coords] not in self.invalid_IDs
    
    # TODO: decrease the strength of the current tool as its usage accumulates    
    def update_tile(self, sprite: pg.sprite.Sprite, tile_coords: tuple[int, int]) -> bool:   
        data = self.mining_map[tile_coords]
        data['hits'] += 1 / FPS
        data['hardness'] = max(0, data['hardness'] - (self.get_tool_strength(sprite) * data['hits']))
        if self.mining_map[tile_coords]['hardness'] == 0:
            sprite.inventory.add_item(self.get_tile_material(self.tile_map[tile_coords]))
            self.tile_map[tile_coords] = self.tile_IDs['air']
            self.collision_map.update_map(tile_coords, remove_tile = True)
            del self.mining_map[tile_coords]
    
    def get_tile_material(self, tile_ID: int) -> str:
        if tile_ID in self.ramp_IDs:
            return self.tile_IDs_to_names[tile_ID].split(' ')[0] # just extract the material name
        else:
            return self.tile_IDs_to_names[tile_ID]


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


class WoodGathering:
    def __init__(
        self, 
        tile_map: np.ndarray,
        tile_IDs: dict[str, int],
        tree_sprites: pg.sprite.Group(),
        tree_map: list[tuple[int, int]],
        cam_offset: pg.Vector2,
        get_tool_strength: callable,
        pick_up_item: callable
    ):
        self.tile_map = tile_map
        self.tile_IDs = tile_IDs
        self.tree_sprites = tree_sprites
        self.tree_map = tree_map
        self.cam_offset = cam_offset
        self.get_tool_strength = get_tool_strength
        self.pick_up_item = pick_up_item

    def make_cut(self, sprite: pg.sprite.Sprite) -> None:
        if isinstance(sprite, Player):
            if sprite.item_holding and sprite.item_holding.split()[-1] == 'axe':
                nearby_trees = [tree for tree in self.tree_sprites if self.in_reach(sprite, tree.rect)]
                for tree in nearby_trees:
                    if tree.rect.collidepoint(pg.mouse.get_pos() + self.cam_offset):
                        tree.cut_down(sprite, self.get_tool_strength, self.pick_up_item)
                        break # avoid cutting multiple trees at once
        else:
            pass

    @staticmethod
    def in_reach(sprite: pg.sprite.Sprite, tree_rect: pg.Rect) -> bool:
        px_dist = abs(sprite.rect.x - tree_rect.x)
        tile_dist = px_dist // TILE_SIZE
        return tile_dist <= 3