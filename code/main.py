from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import numpy as np

import pygame as pg
import sys
import os
from os.path import join
import json
from collections import defaultdict
import re

from settings import RES, FPS, Z_LAYERS, MAP_SIZE, MAP_SIZE, TILE_SIZE
from procgen import ProcGen
from player import Player
from inventory import Inventory, PlayerInventory
from graphics_engine import GraphicsEngine, Camera
from asset_manager import AssetManager
from chunk_manager import ChunkManager
from physics_engine import PhysicsEngine
from sprite_manager import SpriteManager
from input_manager import InputManager
from ui import UI
from item_placement import ItemPlacement
from file_import_functions import load_subfolders

class Main:
    def __init__(self):
        pg.init()
        pg.display.set_caption('matrioshka')
        self.running = True
        self.clock = pg.time.Clock()
        screen = pg.display.set_mode(RES)
        save_data = self.get_save_data()
        if save_data:
            player_data = save_data['sprites']['player'][0] # index 0 to get the dictionary within the list
            player_xy = player_data['xy']

        self.cam = Camera(player_xy if save_data else (pg.Vector2(MAP_SIZE) * TILE_SIZE) // 2)
        
        self.input_mgr = InputManager()
        self.mouse = self.input_mgr.mouse
        self.keyboard = self.input_mgr.keyboard

        self.proc_gen = ProcGen(screen, self.cam.offset, save_data, player_xy if save_data else None)
        
        self.asset_mgr = AssetManager()
        assets = self.asset_mgr.assets

        self.physics_engine = PhysicsEngine(
            self.proc_gen.tile_map, 
            self.proc_gen.tile_IDs, 
            self.proc_gen.tile_IDs_to_names,
            self.keyboard.key_bindings
        )
        
        self.sprite_mgr = SpriteManager(
            screen, 
            self.cam.offset, 
            assets,
            self.proc_gen.tile_map,
            self.proc_gen.tile_IDs,
            self.proc_gen.tile_IDs_to_names,
            self.proc_gen.tree_map,
            self.proc_gen.height_map,
            self.proc_gen.current_biome,
            self.proc_gen.get_tile_material,
            self.physics_engine.sprite_movement,
            self.physics_engine.collision_map,
            self.mouse,
            self.keyboard,
            save_data
        )
        
        self.player_inv = PlayerInventory(player_data['inventory data'] if save_data else None)

        self.player = Player( 
            player_xy if save_data else self.proc_gen.player_spawn_point,
            load_subfolders(join('..', 'graphics', 'player')), 
            Z_LAYERS['player'],
            [self.sprite_mgr.all_sprites, self.sprite_mgr.active_sprites, self.sprite_mgr.player_sprite, 
            self.sprite_mgr.human_sprites, self.sprite_mgr.animated_sprites], 
            self.proc_gen.tile_map,
            self.proc_gen.tile_IDs,
            self.proc_gen.current_biome,
            self.proc_gen.biome_order,
            self.player_inv,
            save_data=player_data if save_data else None
        )
        self.sprite_mgr.player = self.player

        self.ui = UI(
            screen, 
            self.cam.offset,
            assets, 
            self.mouse,
            self.keyboard,
            self.player_inv, 
            self.sprite_mgr, 
            self.player, 
            self.proc_gen.tile_map,
            self.proc_gen.tile_IDs,
            self.proc_gen.tile_IDs_to_names,
            save_data
        )
        self.sprite_mgr.ui = self.ui

        self.item_placement = ItemPlacement(
            screen,
            self.cam.offset,
            self.proc_gen.tile_map,
            self.proc_gen.tile_IDs,
            self.physics_engine.collision_map,
            self.player_inv,
            self.sprite_mgr,
            self.mouse,
            self.keyboard,
            self.player,
            assets,
            self.ui.render_item_amount,
            self.ui.gen_outline,
            self.ui.gen_bg,
            save_data
        )
        self.sprite_mgr.item_placement = self.item_placement
        self.sprite_mgr.init_machines()
        self.ui.inventory_ui.item_placement = self.item_placement
        
        self.chunk_mgr = ChunkManager(self.cam.offset)
        
        self.graphics_engine = GraphicsEngine(
            screen, 
            self.cam,
            assets['graphics'], 
            self.ui, 
            self.sprite_mgr, 
            self.chunk_mgr,
            self.keyboard.key_map,
            self.player,
            self.proc_gen.tile_map,
            self.proc_gen.tile_IDs,
            self.proc_gen.tile_IDs_to_names,
            self.proc_gen.current_biome,
            self.proc_gen.biome_order, 
            save_data
        )

    def make_save(self, file: str) -> None:
        visited_tiles = self.ui.mini_map.visited_tiles
        data = defaultdict(list, {
            'tile map': self.proc_gen.tile_map.tolist(),
            'height map': self.proc_gen.height_map.tolist(),
            'tree map': [list(xy) for xy in self.proc_gen.tree_map],
            'cave maps': {
                biome: cave_map if isinstance(cave_map, list) else cave_map.tolist() 
                for biome, cave_map in self.proc_gen.cave_maps.items()
            },
            'machine map': self.item_placement.machine_map,
            'visited tiles': visited_tiles if isinstance(visited_tiles, list) else visited_tiles.tolist(),
            'biome order': self.proc_gen.biome_order,
            'current biome': self.player.current_biome,
            'weather': self.graphics_engine.weather.sky.make_save(),
            'sprites': defaultdict(list)
        })
        self.load_sprite_data(data)
        with open(file, 'w') as f:
            json.dump(data, f)

    def load_sprite_data(self, data:dict[str, list]) -> None:
        for sprite in [s for s in self.sprite_mgr.all_sprites if hasattr(s, 'get_save_data')]:
            data['sprites'][re.sub(r'(?<!^)(?=[A-Z])', ' ', sprite.__class__.__name__).lower()].append(sprite.get_save_data())

    def get_save_data(self) -> dict[str, list|dict]|None:
        data = None
        if os.path.exists('save.json'):
            with open('save.json', 'r') as f:
                data = json.load(f)
        return data
    
    def update(self, dt: float) -> None:
        self.input_mgr.update(self.cam.offset)
        self.physics_engine.update(self.player, self.keyboard.held_keys, self.keyboard.pressed_keys, dt)
        self.graphics_engine.update(self.player.current_biome, dt) 
        self.sprite_mgr.update(self.player, dt) # keep below the graphics engine otherwise the ui for machines will be rendered over
        self.player_inv.update_selected_index(self.keyboard, self.player)

    def run(self) -> None:
        while self.running:
            for event in pg.event.get():
                if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                    self.make_save('save.json')
                    pg.quit()
                    sys.exit()

            self.update(self.clock.tick(FPS) / 1000)
            pg.display.flip()
             
if __name__ == '__main__':
    main = Main()
    main.run()