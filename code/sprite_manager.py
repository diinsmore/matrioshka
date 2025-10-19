from __future__ import annotations
from typing import Sequence
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import numpy as np
    from player import Player
    from physics_engine import CollisionMap
    from input_manager import Mouse, Keyboard
    from sprite_base import SpriteBase

import pygame as pg
from os.path import join
from random import choice, randint
from itertools import islice

from helper_functions import load_image, cls_name_to_str
from settings import TILE_SIZE, TILES, TILE_REACH_RADIUS, TOOLS, MACHINES, FPS, Z_LAYERS, MAP_SIZE, RES, TREE_BIOMES, PIPE_TRANSPORT_DIRECTIONS
from player import Player
from timer import Timer
from nature_sprites import Tree, Cloud
from furnaces import BurnerFurnace, ElectricFurnace
from drills import BurnerDrill, ElectricDrill
from pipe import Pipe

class SpriteManager:
    def __init__(
        self,
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        assets: dict[str, dict[str, any]],
        tile_map: np.ndarray,
        tile_IDs: dict[str, int],
        tile_IDs_to_names: dict[str, int],
        tree_map: set[tuple[int, int]],
        height_map: np.ndarray,
        current_biome: str,
        get_tile_material: callable,
        sprite_movement: callable,
        collision_map: CollisionMap,
        mouse: Mouse,
        keyboard: Keyboard,
        save_data: dict[str, any] | None
    ):
        self.screen = screen
        self.cam_offset = cam_offset
        self.assets = assets
        self.tile_map = tile_map
        self.tile_IDs = tile_IDs
        self.tile_IDs_to_names = tile_IDs_to_names
        self.tree_map = tree_map
        self.height_map = height_map
        self.current_biome = current_biome
        self.get_tile_material = get_tile_material
        self.sprite_movement = sprite_movement
        self.collision_map = collision_map
        self.mouse = mouse
        self.keyboard = keyboard
        self.save_data = save_data

        self.all_sprites = pg.sprite.Group()
        self.active_sprites = pg.sprite.Group() # has an update method
        self.animated_sprites = pg.sprite.Group()
        self.player_sprite = pg.sprite.GroupSingle()
        self.human_sprites = pg.sprite.Group()
        self.mech_sprites = pg.sprite.Group()
        self.nature_sprites = pg.sprite.Group()
        self.cloud_sprites = pg.sprite.Group()
        self.tree_sprites = pg.sprite.Group()
        self.item_sprites = pg.sprite.Group()
        self.all_groups = {k: v for k, v in vars(self).items() if isinstance(v, pg.sprite.Group)}
        
        self.mining = Mining(
            self.tile_map, 
            self.tile_IDs,
            self.tile_IDs_to_names,
            self.keyboard.key_bindings['mine'],
            self.collision_map.update_map,
            self.get_tool_strength, 
            self.pick_up_item,
            self.get_tile_material,
            self.end_action
        )

        self.crafting = Crafting()

        self.init_trees()
        self.machine_cls_map = self.get_machine_cls_map()

        self.ui = self.item_placement = self.player = None # not initialized until after the sprite manager
        
    @staticmethod
    def get_tool_strength(sprite: pg.sprite.Sprite) -> int:
        if sprite.item_holding:
            material, tool = sprite.item_holding.split()
            return TOOLS[tool][material]['strength']
        return sprite.arm_strength
    
    @staticmethod
    def end_action(sprite: pg.sprite.Sprite) -> None:
        '''return a sprite to an idle state and update its graphic'''
        sprite.state = 'idle'
        idle_img = sprite.frames['idle'][0]
        sprite.image = idle_img if sprite.facing_left else pg.transform.flip(idle_img, True, False)

    def pick_up_item(self, obj: object, name: str, rect: pg.Rect) -> None:
        for sprite in self.get_sprites_in_radius(rect, self.human_sprites):
            inv = sprite.inventory
            if sprite.rect.colliderect(rect) and not (name in inv.contents.keys() and inv.contents[name]['amount'] == inv.slot_capacity[name]):
                inv.add_item(name)
                self.ui.render_new_item_name(name, rect)
                obj.kill()
                return

    @staticmethod
    def rect_in_sprite_radius(
        sprite: pg.sprite.Sprite, 
        rect: pg.Rect, 
        x_dist: int = (RES[0] // 2) + 5, 
        y_dist: int = (RES[1] // 2) + 5
    ) -> bool:
        return abs(sprite.rect.centerx - rect.centerx) < x_dist and abs(sprite.rect.centery - rect.centery) < y_dist

    def get_sprites_in_radius(
        self, 
        rect: pg.Rect, 
        group: pg.sprite.Group, 
        x_dist: int = (RES[0] // 2),  
        y_dist: int = (RES[1] // 2) 
    ) -> list[pg.sprite.Sprite]:
        return [sprite for sprite in group if self.rect_in_sprite_radius(sprite, rect, x_dist, y_dist)]

    def get_sprite_groups(self, sprite: pg.sprite.Sprite) -> set[pg.sprite.Group]:
        return set(group for group in self.all_groups.values() if sprite in group)

    def init_clouds(self, player: pg.sprite.Sprite) -> None:
        half_screen_w = RES[0] // 2
        if not self.cloud_sprites:
            player_x = player.rect.x
            surface_lvl = self.height_map[player_x // TILE_SIZE]
            if player.rect.y // TILE_SIZE < surface_lvl:
                img_folder = self.assets['graphics']['clouds']
                num_imgs = len(img_folder) - 1
                for i in range(randint(10, 15)):
                    Cloud(
                        coords=pg.Vector2(player_x + RES[0] + (50 * (i + 1)), surface_lvl + randint(-2000, -1500)),
                        image=img_folder[randint(0, num_imgs)],
                        z=Z_LAYERS['clouds'],
                        sprite_groups=[self.all_sprites, self.nature_sprites, self.cloud_sprites],
                        speed=randint(1, 3),
                        player=player,
                        rect_in_sprite_radius=self.rect_in_sprite_radius
                    )
    
    def init_trees(self) -> None:
        if self.current_biome in TREE_BIOMES:
            image_folder = self.assets['graphics'][self.current_biome]['trees']
            tree_map = self.tree_map if not self.save_data else self.save_data['tree map']
            for i, xy in enumerate(tree_map): 
                Tree(
                    xy=(pg.Vector2(xy) * TILE_SIZE) - self.cam_offset, 
                    image=choice(image_folder), 
                    z=Z_LAYERS['bg'],
                    sprite_groups=[self.all_sprites, self.nature_sprites, self.tree_sprites], 
                    tree_map=self.tree_map, 
                    tree_map_xy=xy,
                    sprite_movement=self.sprite_movement,
                    wood_image=self.assets['graphics']['wood'],
                    wood_sprites=[self.all_sprites, self.active_sprites, self.nature_sprites, self.item_sprites],
                    save_data=self.save_data['sprites']['tree'][i] if self.save_data else None
                )
        
        self.wood_gathering = WoodGathering(
            self.tile_map, 
            self.tile_IDs, 
            self.tree_sprites, 
            self.tree_map, 
            self.cam_offset, 
            self.get_tool_strength,
            self.pick_up_item,
            self.rect_in_sprite_radius
        )

    @staticmethod
    def get_machine_cls_map() -> dict[str, type[SpriteBase]]:
        machine_cls_map = {}
        for cls in [BurnerFurnace, ElectricFurnace, BurnerDrill, ElectricDrill, Pipe]:
            machine_cls_map[cls_name_to_str(cls)] = cls
        return machine_cls_map

    def init_machines(self) -> None:
        for name, xy_list in self.item_placement.machine_map.items(): 
            for i, xy in enumerate(xy_list):
                self.machine_cls_map[name](**self.get_machine_params(name, xy, i))

    def get_machine_params(self, name: str, xy: tuple[int, int], sprite_idx: int=None) -> dict[str, any]:
        params = {
            'xy': pg.Vector2(xy[0] * TILE_SIZE, xy[1] * TILE_SIZE),
            'image': self.assets['graphics'][name if pipe_idx is None else name + f' {pipe_idx}'],
            'z': Z_LAYERS['main'],
            'sprite_groups': [self.all_sprites, self.active_sprites, self.mech_sprites],
            'screen': self.screen,
            'cam_offset': self.cam_offset,
            'mouse': self.mouse,
            'keyboard': self.keyboard,
            'player': self.player,
            'assets': self.assets,
            'gen_outline': self.ui.gen_outline,
            'gen_bg': self.ui.gen_bg,
            'rect_in_sprite_radius': self.rect_in_sprite_radius,
            'render_item_amount': self.ui.render_item_amount,
            'save_data': self.save_data['sprites'][name][sprite_idx] if sprite_idx and self.save_data else None
        }
        if 'drill' in name:
            params.update([('tile_map', self.tile_map), ('tile_IDs', self.tile_IDs), ('tile_IDs_to_names', self.tile_IDs_to_names)])
        elif name == 'pipe':
            params = dict(islice(params.items(), 10))
            params.update([('idx', int(name[-1])), ('tile_map', self.tile_map), ('tile_IDs', self.tile_IDs)])
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
        tile_IDs: dict[str, int],
        tile_IDs_to_names: dict[int, str],
        key_mine: int,
        update_map: callable,
        get_tool_strength: callable,
        pick_up_item: callable,
        get_tile_material: callable,
        end_action: callable
    ):
        self.tile_map = tile_map
        self.tile_IDs = tile_IDs
        self.tile_IDs_to_names = tile_IDs_to_names
        self.key_mine = key_mine
        self.update_map = update_map
        self.get_tool_strength = get_tool_strength
        self.pick_up_item = pick_up_item
        self.get_tile_material = get_tile_material
        self.end_action = end_action
        
        self.mining_map = {} # {tile coords: {hardness: int, hits: int}}
        self.invalid_IDs = {self.tile_IDs['air'], self.tile_IDs['tree base']} # can't be mined
    
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
        return tile_distance <= TILE_REACH_RADIUS and self.tile_map[mouse_tile_xy] not in self.invalid_IDs
    
    # TODO: decrease the strength of the current tool as its usage accumulates    
    def update_tile(self, sprite: pg.sprite.Sprite, mouse_tile_xy: tuple[int, int]) -> bool:   
        data = self.mining_map[mouse_tile_xy]
        data['hits'] += 1 / FPS
        data['hardness'] = max(0, data['hardness'] - (self.get_tool_strength(sprite) * data['hits']))
        if self.mining_map[mouse_tile_xy]['hardness'] == 0:
            sprite.inventory.add_item(self.get_tile_material(self.tile_map[mouse_tile_xy]))
            self.tile_map[mouse_tile_xy] = self.tile_IDs['air']
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
        tile_IDs: dict[str, int],
        tree_sprites: pg.sprite.Group(),
        tree_map: list[tuple[int, int]],
        cam_offset: pg.Vector2,
        get_tool_strength: callable,
        pick_up_item: callable,
        rect_in_sprite_radius: callable
    ):
        self.tile_map = tile_map
        self.tile_IDs = tile_IDs
        self.tree_sprites = tree_sprites
        self.tree_map = tree_map
        self.cam_offset = cam_offset
        self.get_tool_strength = get_tool_strength
        self.pick_up_item = pick_up_item
        self.rect_in_sprite_radius = rect_in_sprite_radius

        self.reach_radius = TILE_SIZE * 3

    def make_cut(self, sprite: pg.sprite.Sprite, mouse_button_held: dict[str, bool], mouse_world_xy: pg.Vector2) -> None:
        if mouse_button_held['left']:
            if sprite.item_holding and sprite.item_holding.split()[-1] == 'axe':
                if tree := next((t for t in self.tree_sprites if self.rect_in_sprite_radius(sprite, t.rect) and t.rect.collidepoint(mouse_world_xy)), None):
                    tree.cut_down(sprite, self.get_tool_strength, self.pick_up_item)

    def update(self, player: pg.sprite.Sprite, mouse_button_held: dict[str, bool], mouse_world_xy: pg.Vector2) -> None:
        self.make_cut(player, mouse_button_held, mouse_world_xy)