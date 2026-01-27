from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import numpy as np
    from player import Player
    from physics_engine import PhysicsEngine
    from input_manager import InputManager
    from sprite_base import SpriteBase
    from procgen import ProcGen

import pygame as pg
from os.path import join
from random import choice, randint
from itertools import islice

from helper_functions import load_image, cls_name_to_str
from settings import TILE_SIZE, TILES, TILE_REACH_RADIUS, TOOLS, FPS, Z_LAYERS, MAP_SIZE, RES, TREE_BIOMES, PRODUCTION, LOGISTICS
from player import Player
from mining import Mining
from crafting import Crafting
from wood_gathering import WoodGathering
from nature_sprites import Tree, Cloud
from furnaces import BurnerFurnace, ElectricFurnace
from drills import BurnerDrill, ElectricDrill
from pipe import Pipe
from inserter import BurnerInserter, ElectricInserter, LongHandedInserter
from assembler import Assembler
from pump import Pump

class SpriteManager:
    def __init__(
        self, 
        screen: pg.Surface, 
        cam_offset: pg.Vector2, 
        assets: dict[str, dict[str, any]], 
        proc_gen: ProcGen,
        physics_engine: PhysicsEngine,
        input_manager: InputManager,
        save_data: dict[str, any] | None
    ):
        self.screen = screen
        self.cam_offset = cam_offset
        self.assets, self.graphics = assets, assets['graphics']
        self.tile_map = proc_gen.tile_map
        self.tree_map = proc_gen.tree_map
        self.height_map = proc_gen.height_map
        self.current_biome = proc_gen.current_biome
        self.names_to_ids, self.ids_to_names = proc_gen.names_to_ids, proc_gen.ids_to_names
        self.get_tile_material = proc_gen.get_tile_material
        self.sprite_movement = physics_engine.sprite_movement
        self.collision_map = physics_engine.collision_map
        self.input_manager = input_manager
        self.keyboard, self.mouse = input_manager.keyboard, input_manager.mouse
        self.save_data = save_data

        self.all_sprites = pg.sprite.Group()
        self.active_sprites = pg.sprite.Group() # has an update method
        self.animated_sprites = pg.sprite.Group()
        self.player_sprite = pg.sprite.GroupSingle()
        self.colonist_sprites = pg.sprite.Group()
        self.mech_sprites = pg.sprite.Group()
        self.logistics_sprites = pg.sprite.Group()
        self.nature_sprites = pg.sprite.Group()
        self.cloud_sprites = pg.sprite.Group()
        self.tree_sprites = pg.sprite.Group()
        self.item_sprites = pg.sprite.Group()
        self.all_groups = {k: v for k, v in vars(self).items() if isinstance(v, pg.sprite.Group)}
        
        self.mining = Mining(
            self.tile_map, 
            self.names_to_ids,
            self.ids_to_names,
            self.keyboard.key_bindings['mine'],
            self.collision_map.update_map,
            self.get_tool_strength, 
            self.pick_up_item,
            self.get_tile_material,
            self.end_action
        )
        self.crafting = Crafting()
        self.init_trees()
        self.items_init_when_placed = {
            cls_name_to_str(cls): cls for cls in (
                BurnerFurnace, ElectricFurnace, BurnerDrill, ElectricDrill, Pipe, BurnerInserter, ElectricInserter, Assembler, Pump
            )
        }
        self.ui, self.item_placement, self.player = None, None, None # not initialized until after the sprite manager
    
    def init_trees(self) -> None:
        if self.current_biome in TREE_BIOMES:
            image_folder = self.graphics[self.current_biome]['trees']
            tree_map = self.tree_map if not self.save_data else self.save_data['tree map']
            for i, xy in enumerate(tree_map): 
                Tree(
                    (pg.Vector2(xy) * TILE_SIZE) - self.cam_offset, 
                    choice(image_folder), 
                    Z_LAYERS['bg'], 
                    [self.all_sprites, self.nature_sprites, self.tree_sprites], 
                    xy,
                    self.graphics['wood'], 
                    self,
                    save_data=self.save_data['sprites']['tree'][i] if self.save_data else None
                )

        self.wood_gathering = WoodGathering(
            self.tile_map, 
            self.names_to_ids, 
            self.tree_sprites, 
            self.tree_map, 
            self.cam_offset, 
            self.get_tool_strength, 
            self.pick_up_item, 
            self.rect_in_sprite_radius
        )

    def init_clouds(self, player: pg.sprite.Sprite) -> None:
        if not self.cloud_sprites:
            surface_lvl = self.height_map[player.rect.x // TILE_SIZE]
            if player.rect.y // TILE_SIZE < surface_lvl:
                img_folder = self.graphics['clouds']
                for i in range(randint(10, 15)):
                    Cloud(
                        pg.Vector2(player.rect.x + RES[0] + (50 * (i + 1)), surface_lvl + randint(-2000, -1500)),
                        img_folder[randint(0, len(img_folder) - 1)],
                        Z_LAYERS['clouds'],
                        [self.all_sprites, self.nature_sprites, self.cloud_sprites],
                        randint(1, 3),
                        player,
                        self.rect_in_sprite_radius
                    )

    def init_placed_items(self) -> None:
        for item, tiles_covered in self.item_placement.items(): 
            for xy in tiles_covered:
               self.items_init_when_placed[item](**self.get_cls_init_params(name, xy))

    @staticmethod
    def get_tool_strength(sprite: pg.sprite.Sprite) -> int:
        if sprite.item_holding:
            material, tool = sprite.item_holding.split()
            return TOOLS[tool][material]['strength']
        return sprite.arm_strength
    
    @staticmethod
    def end_action(sprite: pg.sprite.Sprite) -> None:
        sprite.state = 'idle'
        idle_img = sprite.frames['idle'][0]
        sprite.image = idle_img if sprite.facing_left else pg.transform.flip(idle_img, True, False)

    def pick_up_item(self, obj: object, name: str, amount: int=1) -> None:
        for sprite in self.get_sprites_in_radius(obj.rect, self.human_sprites):
            inv = sprite.inventory
            if sprite.rect.colliderect(obj.rect) and not (name in inv.contents.keys() and inv.contents[name]['amount'] == inv.slot_capacity[name]):
                inv.add_item(name, amount)
                self.ui.render_new_item_name(name, obj.rect, amount)
                obj.kill()
                return

    def get_sprites_in_radius(self, rect: pg.Rect, group: pg.sprite.Group, x_dist: int=(RES[0] // 2), y_dist: int=(RES[1] // 2)) -> list[pg.sprite.Sprite]:
        return [spr for spr in group if self.rect_in_sprite_radius(spr, rect, x_dist, y_dist)]
    
    def rect_in_sprite_radius(
        self, 
        spr: pg.sprite.Sprite, 
        rect: pg.Rect, 
        x_dist: int=(RES[0] // 2), 
        y_dist: int=(RES[1] // 2), 
        spr_world_space: bool=True, 
        rect_world_space: bool=True
    ) -> bool:
        spr_xy = spr.rect.center if spr_world_space else spr.rect.center + self.cam_offset
        rect_xy = rect.center if rect_world_space else rect.center + self.cam_offset
        return abs(spr_xy[0] - rect_xy[0]) < x_dist and abs(spr_xy[1] - rect_xy[1]) < y_dist
    
    def get_sprite_groups(self, sprite: pg.sprite.Sprite) -> set[pg.sprite.Group]:
        return set(group for group in self.all_groups.values() if sprite in group)

    def get_cls_init_params(self, name: str, tiles_covered: list[tuple[int, int]] | tuple[int, int], save_idx: int=None) -> dict[str, any]:
        tile_x, tile_y = tiles_covered if isinstance(tiles_covered, tuple) else tiles_covered[0] # only extract the topleft coordinate for multi-tile items
        params = {
            'xy': (tile_x * TILE_SIZE, tile_y * TILE_SIZE), 
            'image': self.assets['graphics'][name], 
            'sprite_groups': [self.all_sprites, self.active_sprites, self.mech_sprites], 
            'screen': self.screen, 
            'cam_offset': self.cam_offset, 
            'input_manager': self.input_manager,
            'player': self.player, 
            'assets': self.assets, 
            'tile_map': self.tile_map, 
            'obj_map': self.item_placement.obj_map,
        }
        if name in PRODUCTION:
            params.update([
                ('ui', self.ui),
                ('rect_in_sprite_radius', self.rect_in_sprite_radius), 
                ('save_data', self.save_data['sprites'][name][save_idx] if self.save_data else None)
            ])
            if 'drill' in name:
                params.update([('names_to_ids', self.names_to_ids), ('ids_to_names', self.ids_to_names)])
        elif 'pipe' in name or name == 'pump':
            params.update([('names_to_ids', self.names_to_ids), ('variant_idx', int(name[-1]))] if 'pipe' in name else [('names_to_ids', self.names_to_ids)])
            params['sprite_groups'].append(self.logistics_sprites)
        return params

    def update(self, player: pg.sprite.Sprite, dt: float) -> None:
        for sprite in self.active_sprites:
            sprite.update(dt)
        self.mining.update(self.keyboard.held_keys, player, self.mouse.tile_xy)
        self.wood_gathering.update(player, self.mouse.buttons_held, self.mouse.world_xy)
        self.init_clouds(player)