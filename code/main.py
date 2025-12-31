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
from inventory import SpriteInventory, PlayerInventory
from graphics_engine import GraphicsEngine, Camera
from asset_manager import AssetManager
from chunk_manager import ChunkManager
from physics_engine import PhysicsEngine
from sprite_manager import SpriteManager
from input_manager import InputManager
from ui import UI
from item_placement import ItemPlacement
from helper_functions import load_subfolders, cls_name_to_str

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

        self.cam = Camera(center=player_xy if save_data else (pg.Vector2(MAP_SIZE) * TILE_SIZE) // 2)
        offset = self.cam.offset

        self.input_manager = InputManager()

        self.proc_gen = ProcGen(screen, self.cam.offset, save_data)
        
        self.asset_manager = AssetManager()
        assets = self.asset_manager.assets

        self.physics_engine = PhysicsEngine(self.proc_gen, self.cam.offset, self.input_manager.keyboard)
        
        self.sprite_manager = SpriteManager(screen, offset, assets, self.proc_gen, self.physics_engine, self.input_manager, save_data)

        self.player = Player( 
            player_xy if save_data else self.proc_gen.player_spawn_point,
            offset,
            load_subfolders(join('..', 'graphics', 'player')),
            assets,
            screen,
            self.sprite_manager,
            [getattr(self.sprite_manager, group) for group in (
                'all_sprites', 'player_sprite', 'active_sprites', 'human_sprites', 'animated_sprites'
            )],
            self.proc_gen,
            self.input_manager.keyboard,
            player_data if save_data else None
        )
        self.sprite_manager.player = self.player

        self.ui = UI(screen, offset, assets, self.input_manager, self.sprite_manager, self.player, self.proc_gen, save_data)
        self.sprite_manager.ui = self.ui

        self.item_placement = ItemPlacement(
            screen, 
            offset, 
            self.proc_gen,
            self.physics_engine.collision_map, 
            self.sprite_manager, 
            self.input_manager,
            self.player, 
            assets, 
            self.ui,
            save_data
        )
        self.sprite_manager.item_placement = self.item_placement
        self.ui.inventory_ui.item_placement = self.item_placement
        self.ui.inventory_ui.item_drag.item_placement = self.item_placement

        self.chunk_manager = ChunkManager(self.cam.offset)

        self.graphics_engine = GraphicsEngine(
            screen, 
            self.cam, 
            assets['graphics'], 
            self.ui, 
            self.sprite_manager, 
            self.chunk_manager, 
            self.input_manager.keyboard.key_map, 
            self.player, 
            self.proc_gen,
            save_data
        )

        def make_save(self, file: str) -> None:
            visited_tiles = self.ui.mini_map.visited_tiles
            data = defaultdict(list, {
                **self.proc_gen.make_save(), 
                'current biome': self.player.current_biome, 
                'visited tiles': visited_tiles if isinstance(visited_tiles, list) else visited_tiles.tolist(), 
                'weather': self.graphics_engine.weather.sky.make_save(), 
                'sprites': defaultdict(list) 
            })
            self.load_sprite_data(data)
            with open(file, 'w') as f:
                json.dump(data, f)

    def load_sprite_data(self, data: dict[str, list]) -> None:
        for sprite in [s for s in self.sprite_mgr.all_sprites if hasattr(s, 'get_save_data')]:
            data['sprites'][cls_name_to_str(sprite)].append(sprite.get_save_data())

    def get_save_data(self) -> dict[str, list|dict] | None:
        data = None
        if os.path.exists('save.json'):
            with open('save.json', 'r') as f:
                data = json.load(f)
        return data
    
    def update(self, dt: float) -> None:
        self.input_manager.update(self.cam.offset)
        self.physics_engine.update(self.player, dt)
        self.graphics_engine.update(dt) 
        self.sprite_manager.update(self.player, dt) # keep below the graphics engine otherwise the ui for machines will be rendered over
        self.graphics_engine.terrain.render_water()
        self.proc_gen.current_biome = self.player.current_biome

    def run(self) -> None:
        while self.running:
            for event in pg.event.get():
                if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                 #   self.make_save('save.json')
                    pg.quit()
                    sys.exit()
            self.update(self.clock.tick(FPS) / 1000)
            pg.display.flip()
             
if __name__ == '__main__':
    main = Main()
    main.run()