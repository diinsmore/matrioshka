import pygame as pg
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
    def __init__(self, screen: pg.Surface):
        self.proc_gen = ProcGen()
        tile_map = self.proc_gen.tile_map
        tile_IDs = self.proc_gen.tile_IDs

        self.physics_engine = PhysicsEngine(tile_map, tile_IDs)

        self.camera = Camera()
        
        self.asset_manager = AssetManager(tile_IDs)

        self.sprite_manager = SpriteManager( 
            self.asset_manager, 
            tile_map, 
            tile_IDs, 
            self.physics_engine.collision_map,
        )

        self.inv = Inventory()

        self.ui = UI(screen, self.camera.offset, self.asset_manager, self.inv)

        self.input_manager = InputManager(self.physics_engine, self.sprite_manager, self.ui)
        
        self.chunk_manager = ChunkManager(self.camera.offset)
        
        self.graphics_engine = GraphicsEngine(
            screen,
            self.camera,
            self.asset_manager.assets['graphics'],
            self.ui,
            self.proc_gen,
            self.sprite_manager,
            self.chunk_manager,
        )
        
        self.player = Player( 
            coords = self.proc_gen.get_player_spawn_point(), 
            frames = self.asset_manager.load_subfolders(join('..', 'graphics', 'player')), 
            z = Z_LAYERS['player'],
            sprite_groups = [
                self.sprite_manager.all_sprites, 
                self.sprite_manager.human_sprites,
                self.sprite_manager.animated_sprites
            ],
            tile_map = tile_map,
            tile_IDs = tile_IDs,
            biome_order = self.proc_gen.biome_order,
            physics_engine = self.physics_engine,
            inventory = self.inv
        )
        
        # keep this line below the sprite instances
        self.sprite_manager.init_active_items()
        
    def update(self, dt: float) -> None:
        self.input_manager.update(self.player, self.camera.offset, self.proc_gen.update_collision_map, dt)
        self.graphics_engine.update(
            self.input_manager.mouse_coords, 
            self.input_manager.mouse_moving, 
            self.input_manager.clicks['left'], 
            dt
        )
        self.camera.update(pg.Vector2(self.player.rect.x, self.player.rect.y))
        self.inv.update()
        self.proc_gen.current_biome = self.player.current_biome