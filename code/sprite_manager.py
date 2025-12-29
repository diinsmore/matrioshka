from __future__ import annotations
from typing import Sequence
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
from settings import TILE_SIZE, TILES, TILE_REACH_RADIUS, TOOLS, MACHINES, FPS, Z_LAYERS, MAP_SIZE, RES, TREE_BIOMES
from player import Player
from alarm import Alarm
from nature_sprites import Tree, Cloud
from furnaces import BurnerFurnace, ElectricFurnace
from drills import BurnerDrill, ElectricDrill
from pipe import Pipe
from inserter import BurnerInserter, ElectricInserter, LongHandedInserter
from assembler import Assembler

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
        self.human_sprites = pg.sprite.Group()
        self.mech_sprites = pg.sprite.Group()
        self.transport_sprites = pg.sprite.Group()
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
                BurnerFurnace, 
                ElectricFurnace, 
                BurnerDrill, 
                ElectricDrill, 
                Pipe, 
                BurnerInserter, 
                ElectricInserter, 
                Assembler
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
                    self.tree_map, 
                    xy,
                    self.graphics['wood'], 
                    [self.all_sprites, self.active_sprites, self.nature_sprites, self.item_sprites],
                    self.sprite_movement,
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

   # def init_placed_items(self) -> None:
      #  for item, xy_list in self.item_placement.____.items(): 
          #  for xy in xy_list:
               # self.items_init_when_placed[item](**self.get_cls_init_params(name, xy))

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

    def get_machine_init_params(self, name: str, tiles_covered: list[tuple[int, int]] | tuple[int, int], save_idx: int=None) -> dict[str, any]:
        tile_x, tile_y = tiles_covered if isinstance(tiles_covered, tuple) else tiles_covered[0] # only extract the topleft coordinate for multi-tile items
        params = {
            'xy': (tile_x * TILE_SIZE, tile_y * TILE_SIZE), 'image': self.assets['graphics'][name], 
            'z': Z_LAYERS['main'], 
            'sprite_groups': [self.all_sprites, self.active_sprites, self.mech_sprites], 'screen': self.screen, 
            'cam_offset': self.cam_offset, 
            'input_manager': self.input_manager,
            'player': self.player, 
            'assets': self.assets, 
            'tile_map': self.tile_map, 
            'obj_map': self.item_placement.obj_map,
            'gen_outline': self.ui.gen_outline, 
            'gen_bg': self.ui.gen_bg, 
            'rect_in_sprite_radius': self.rect_in_sprite_radius, 
            'render_item_amount': self.ui.render_item_amount,
            'save_data': self.save_data['sprites'][name][save_idx] if self.save_data else None
        }
        if 'drill' in name:
            params.update([('names_to_ids', self.names_to_ids), ('ids_to_names', self.ids_to_names)])
        elif 'pipe' in name or 'inserter' in name:
            params = dict(islice(params.items(), 11))
            if 'pipe' in name:
                params.update([('names_to_ids', self.names_to_ids), ('variant_idx', int(name[-1]))])
                params['sprite_groups'].append(self.transport_sprites)
        return params

    def update(self, player: pg.sprite.Sprite, dt: float) -> None:
        for sprite in self.active_sprites:
            sprite.update(dt)
        self.mining.update(self.keyboard.held_keys, player, self.mouse.tile_xy)
        self.wood_gathering.update(player, self.mouse.buttons_held, self.mouse.world_xy)
        self.init_clouds(player)


class Mining:
    def __init__(
        self, 
        tile_map: np.ndarray, 
        names_to_ids: dict[str, int], 
        ids_to_names: dict[int, str], 
        key_mine: int, 
        update_map: callable, 
        get_tool_strength: callable,
        pick_up_item: callable, 
        get_tile_material: callable, 
        end_action: callable
    ):
        self.tile_map = tile_map
        self.names_to_ids = names_to_ids
        self.ids_to_names = ids_to_names
        self.key_mine = key_mine
        self.update_map = update_map
        self.get_tool_strength = get_tool_strength
        self.pick_up_item = pick_up_item
        self.get_tile_material = get_tile_material
        self.end_action = end_action
        
        self.mining_map = {} # {tile coords: {hardness: int, hits: int}}
        self.invalid_ids = {self.names_to_ids['air'], self.names_to_ids['tree base']} # can't be mined
    
    def run(self, sprite: pg.sprite.Sprite, mouse_tile_xy: tuple[int, int]) -> None:
        if sprite.item_holding and 'pickaxe' in sprite.item_holding:
            if self.valid_tile(sprite, mouse_tile_xy):
                sprite.state = 'mining'
                if mouse_tile_xy not in self.mining_map:
                    self.mining_map[mouse_tile_xy] = {
                        'hardness': TILES[self.get_tile_material(self.tile_map[mouse_tile_xy])]['hardness'], 
                        'hits': 0
                    }
                self.update_tile(sprite, mouse_tile_xy) 

    def valid_tile(self, sprite: pg.sprite.Sprite, mouse_tile_xy: tuple[int, int]) -> bool:
        sprite_coords = pg.Vector2(sprite.rect.center) // TILE_SIZE
        tile_distance = sprite_coords.distance_to(mouse_tile_xy)
        return tile_distance <= TILE_REACH_RADIUS and self.tile_map[mouse_tile_xy] not in self.invalid_ids
    
    # TODO: decrease the strength of the current tool as its usage accumulates    
    def update_tile(self, sprite: pg.sprite.Sprite, mouse_tile_xy: tuple[int, int]) -> bool:   
        data = self.mining_map[mouse_tile_xy]
        data['hits'] += 1 / FPS
        data['hardness'] = max(0, data['hardness'] - (self.get_tool_strength(sprite) * data['hits']))
        if self.mining_map[mouse_tile_xy]['hardness'] == 0:
            sprite.inventory.add_item(self.get_tile_material(self.tile_map[mouse_tile_xy]))
            self.tile_map[mouse_tile_xy] = self.names_to_ids['air']
            self.update_map(mouse_tile_xy, remove_tile = True)
            del self.mining_map[mouse_tile_xy]
    
    def update(self, held_keys: Sequence[bool], player: pg.sprite.Sprite, mouse_tile_xy: tuple[int, int]) -> None:
        if held_keys[self.key_mine]:
            self.run(player, mouse_tile_xy)
        else:
            if player.state == 'mining':
                self.end_action(player)


class Crafting:
    @staticmethod
    def craft_item(name: str, recipe: dict[str, int], sprite: pg.sprite.Sprite) -> None:
        inv = sprite.inventory
        recipe = recipe.items()
        if all(inv.contents.get(item, {}).get('amount', 0) >= amt for item, amt in recipe):
            for item, amt in recipe:
                inv.remove_item(item, amt)
            inv.add_item(name)


class WoodGathering:
    def __init__(
        self, 
        tile_map: np.ndarray, 
        names_to_ids: dict[str, int], 
        tree_sprites: pg.sprite.Group, 
        tree_map: list[tuple[int, int]], 
        cam_offset: pg.Vector2,
        get_tool_strength: callable, 
        pick_up_item: callable, 
        rect_in_sprite_radius: callable
    ):
        self.tile_map = tile_map
        self.names_to_ids = names_to_ids
        self.tree_sprites = tree_sprites
        self.tree_map = tree_map
        self.cam_offset = cam_offset
        self.get_tool_strength = get_tool_strength
        self.pick_up_item = pick_up_item
        self.rect_in_sprite_radius = rect_in_sprite_radius

        self.reach_radius = TILE_SIZE * 3

    def make_cut(self, sprite: pg.sprite.Sprite, mouse_button_held: dict[str, bool], mouse_world_xy: tuple[int, int]) -> None:
        if mouse_button_held['left']:
            if sprite.item_holding and sprite.item_holding.split()[-1] == 'axe':
                if tree := next((t for t in self.tree_sprites if self.rect_in_sprite_radius(sprite, t.rect) and t.rect.collidepoint(mouse_world_xy)), None):
                    tree.cut_down(sprite, self.get_tool_strength, self.pick_up_item)

    def update(self, player: pg.sprite.Sprite, mouse_button_held: dict[str, bool], mouse_world_xy: tuple[int, int]) -> None:
        self.make_cut(player, mouse_button_held, mouse_world_xy)