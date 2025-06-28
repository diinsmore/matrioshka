import pygame as pg
import os
from os.path import join
import json

from settings import Z_LAYERS, MAP_SIZE, MAP_SIZE, TILE_SIZE
from procgen import ProcGen
from camera import Camera
from player import Player
from inventory import Inventory
from graphics_engine import GraphicsEngine
from asset_manager import AssetManager
from chunk_manager import ChunkManager
from physics_engine import PhysicsEngine
from sprite_manager import SpriteManager
from input_manager import InputManager
from ui import UI
from file_import_functions import load_subfolders

class Engine:
    def __init__(self, screen: pg.Surface):
        self.screen = screen
        
        self.saved_data = self.get_saved_data()

        self.camera = Camera(self.saved_data['sprites']['player']['coords'] if self.saved_data else (pg.Vector2(MAP_SIZE) * TILE_SIZE) // 2)

        self.proc_gen = ProcGen(screen, self.camera.offset, self.saved_data)
        self.tile_map = self.proc_gen.tile_map
        self.tile_IDs = self.proc_gen.tile_IDs
        self.tree_map = self.proc_gen.tree_map
        self.cave_map = self.proc_gen.cave_map

        self.inventory = Inventory(self.saved_data['sprites']['player']['inventory'] if self.saved_data else None) # TODO: once other human sprites are introduced, they'll need their own data passed
        self.asset_manager = AssetManager()
        
        self.physics_engine = PhysicsEngine(self.tile_map, self.tile_IDs)
        
        self.sprite_manager = SpriteManager(
            self.screen,
            self.camera.offset,
            self.asset_manager, 
            self.tile_map,
            self.tile_IDs,
            self.physics_engine,
            self.tree_map,
            self.inventory,
            self.proc_gen.tile_IDs_to_names,
            self.saved_data
        )

        self.player = Player( 
            self.saved_data['sprites']['player']['coords'] if self.saved_data else self.proc_gen.player_spawn_point,
            load_subfolders(join('..', 'graphics', 'player')), 
            Z_LAYERS['player'],
            [
                self.sprite_manager.all_sprites, 
                self.sprite_manager.player_sprite, 
                self.sprite_manager.human_sprites, 
                self.sprite_manager.animated_sprites
            ],
            self.tile_map,
            self.tile_IDs,
            self.proc_gen.biome_order,
            self.physics_engine,
            self.inventory
        )
        self.sprite_manager.player = self.player

        self.ui = UI(self.screen, self.camera.offset, self.asset_manager.assets, self.inventory, self.sprite_manager, self.player)
        self.sprite_manager.ui = self.ui

        self.input_manager = InputManager(self.physics_engine, self.sprite_manager, self.ui, self.player)

        self.chunk_manager = ChunkManager(self.camera.offset)
        
        self.graphics_engine = GraphicsEngine(
            self.screen,
            self.camera,
            self.asset_manager.assets['graphics'],
            self.ui,
            self.proc_gen,
            self.sprite_manager,
            self.chunk_manager,
            self.input_manager,
            self.player
        )
    
        self.sprite_manager.init_active_items() # keep this line below the sprite instances

    def make_save(self, file: str) -> None:
        data = {
            'tile map': self.tile_map.tolist(),
            'tree map': [list(coord) for coord in self.tree_map],
            'cave map': self.cave_map.tolist(),
            'biome order': self.proc_gen.biome_order,
            'current biome': self.player.current_biome,
            'sprites': {}
        }
        for sprite in self.sprite_manager.all_sprites:
            sprite_data = {'coords': list(sprite.rect.center)}
            if hasattr(sprite, 'inventory'):
                sprite_data['inventory'] = sprite.inventory.contents
            data['sprites'][sprite.__class__.__name__.lower()] = sprite_data

        with open(file, 'w') as f:
            json.dump(data, f)

    def get_saved_data(self) -> dict[str, any] | None:
        saved_data = None
        if os.path.exists('save.json'):
            with open('save.json', 'r') as f:
                saved_data = json.load(f)
        return saved_data

    def update(self, dt: float) -> None:
        self.input_manager.update(self.camera.offset, dt)
        self.graphics_engine.update(
            self.input_manager.mouse.coords, 
            self.input_manager.mouse.moving, 
            self.input_manager.mouse.click_states, 
            dt
        )
        self.camera.update(pg.Vector2(self.player.rect.x, self.player.rect.y))
        self.proc_gen.current_biome = self.sprite_manager.current_biome = self.player.current_biome