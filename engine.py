import pygame as pg
pg.init()
from os.path import join

from settings import Z_LAYERS, MAP_SIZE
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

class Engine:
    def __init__(self, screen: pg.Surface) -> None:
        self.proc_gen = ProcGen()
        tile_map = self.proc_gen.tile_map
        tile_data = self.proc_gen.tile_data

        self.physics_engine = PhysicsEngine(tile_map, tile_data)

        self.camera = Camera() # added later
        
        asset_manager = AssetManager(tile_data)
        self.sprite_manager = SpriteManager( 
            asset_manager, 
            tile_map, 
            tile_data, 
            self.physics_engine.collision_map
        )
        self.input_manager = InputManager(self.physics_engine, self.sprite_manager, self.camera.offset)
        self.chunk_manager = ChunkManager(self.camera.offset)
        
        self.inv = Inventory()

        ui = UI(screen, self.camera.offset, asset_manager, self.inv)
        self.graphics_engine = GraphicsEngine(
            screen,
            self.camera,
            asset_manager.assets['graphics'],
            ui,
            self.proc_gen,
            self.sprite_manager,
            self.chunk_manager
        )
        
        self.player = Player( 
            coords = self.proc_gen.get_player_spawn_point(), 
            frames = asset_manager.load_subfolders(join('..', 'graphics', 'player')), 
            z = Z_LAYERS['player'],
            sprite_groups = [self.sprite_manager.all_sprites], # passing a list since more groups will likely be added
            tile_map = tile_map,
            tile_data = tile_data,
            biome_order = self.proc_gen.biome_order,
            physics_engine = self.physics_engine,
            inventory = self.inv
        )
        
    def update(self, dt: float) -> None:
        self.input_manager.update(self.player, self.proc_gen.update_map, dt)
        self.graphics_engine.update(self.input_manager.mouse_coords, self.input_manager.clicks['left'], dt)
        self.camera.update(pg.Vector2(self.player.rect.x, self.player.rect.y))
        self.inv.update()
        
        self.proc_gen.current_biome = self.player.current_biome