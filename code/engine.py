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

        self.cam = Camera(self.saved_data['sprites']['player']['coords'] if self.saved_data else (pg.Vector2(MAP_SIZE) * TILE_SIZE) // 2)

        self.proc_gen = ProcGen(screen, self.cam.offset, self.saved_data)
    
        self.inventory = Inventory(self.saved_data['sprites']['player']['inventory'] if self.saved_data else None) # TODO: once other human sprites are introduced, they'll need their own data passed
        
        self.asset_mgr = AssetManager()
        
        self.physics_engine = PhysicsEngine(self.proc_gen)
        
        self.sprite_mgr = SpriteManager(
            self.screen, 
            self.cam.offset, 
            self.asset_mgr.assets['graphics'], 
            self.physics_engine.sprite_movement,
            self.physics_engine.collision_map,
            self.proc_gen.tile_map,
            self.proc_gen.tile_IDs,
            self.proc_gen.tile_IDs_to_names,
            self.proc_gen.tree_map,
            self.proc_gen.current_biome,
            self.inventory, 
            self.saved_data,
            self.get_tile_material
        )
      
        self.player = Player( 
            self.saved_data['sprites']['player']['coords'] if self.saved_data else self.proc_gen.player_spawn_point,
            load_subfolders(join('..', 'graphics', 'player')), 
            Z_LAYERS['player'],
            [self.sprite_mgr.all_sprites, self.sprite_mgr.player_sprite, self.sprite_mgr.human_sprites, self.sprite_mgr.animated_sprites], 
            self.proc_gen.tile_map,
            self.proc_gen.tile_IDs,
            self.proc_gen.current_biome,
            self.proc_gen.biome_order,
            self.inventory
        )
        self.sprite_mgr.player = self.player

        self.ui = UI(
            self.screen, 
            self.cam.offset, 
            self.asset_mgr.assets, 
            self.inventory, 
            self.sprite_mgr, 
            self.player, 
            self.proc_gen.tile_map,
            self.proc_gen.tile_IDs,
            self.proc_gen.tile_IDs_to_names
        )
        self.sprite_mgr.ui = self.ui

        self.input_mgr = InputManager(self.physics_engine, self.sprite_mgr, self.ui, self.player)

        self.chunk_mgr = ChunkManager(self.cam.offset)
        
        self.graphics_engine = GraphicsEngine(
            self.screen, 
            self.cam,
            self.asset_mgr.assets['graphics'], 
            self.ui, 
            self.sprite_mgr, 
            self.chunk_mgr, 
            self.input_mgr, 
            self.player,
            self.proc_gen.tile_map,
            self.proc_gen.tile_IDs,
            self.proc_gen.tile_IDs_to_names,
            self.proc_gen.current_biome,
            self.proc_gen.biome_order
        )
    
        self.sprite_mgr.init_active_items() # keep this line below the sprite instances

    def make_save(self, file: str) -> None:
        data = {
            'tile map': self.proc_gen.tile_map.tolist(),
            'tree map': [list(coord) for coord in self.proc_gen.tree_map],
            'cave maps': {biome: cave_map.tolist() for biome, cave_map in self.proc_gen.cave_maps.items()},
            'biome order': self.proc_gen.biome_order,
            'current biome': self.player.current_biome,
            'sprites': {}
        }
        for sprite in self.sprite_mgr.all_sprites:
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

    def get_tile_material(self, tile_ID: int) -> str:
        tile_name = self.proc_gen.tile_IDs_to_names[tile_ID]
        return tile_name.split(' ')[0] if tile_ID in self.proc_gen.ramp_IDs else tile_name

    def update(self, dt: float) -> None:
        self.input_mgr.update(self.cam.offset, dt)
        self.graphics_engine.update(
            self.input_mgr.mouse.coords, 
            self.input_mgr.mouse.moving, 
            self.input_mgr.mouse.click_states, 
            self.player.current_biome, 
            dt
        )
        self.cam.update(pg.Vector2(self.player.rect.x, self.player.rect.y))