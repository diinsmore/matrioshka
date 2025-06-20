import pygame as pg
from os.path import join
import json

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
from file_import_functions import load_subfolders

class Engine:
    def __init__(self, screen: pg.Surface, saved_data: dict[str, any] | None):
        self.screen = screen
        self.saved_data = saved_data

        self.camera = Camera()

        self.proc_gen = ProcGen(screen, self.camera.offset, self.saved_data)
        self.tile_map = self.proc_gen.tile_map
        self.tile_IDs = self.proc_gen.tile_IDs
        self.tree_map = self.proc_gen.tree_map

        self.physics_engine = PhysicsEngine(self.tile_map, self.tile_IDs)

        self.asset_manager = AssetManager()
        
        inv_contents = self.saved_data['sprites']['player']['inventory'] if self.saved_data else None # TODO: once other human sprites are introduced, they'll need their own data passed
        self.inventory = Inventory(inv_contents)

        self.sprite_manager = SpriteManager(
            self.screen,
            self.camera.offset,
            self.asset_manager, 
            self.tile_map,
            self.tile_IDs,
            self.physics_engine,
            self.tree_map,
            self.inventory,
            self.proc_gen.tile_IDs_to_names
        )

        player_coords = self.saved_data['sprites']['player']['coords'] if self.saved_data else self.proc_gen.get_player_spawn_point()
        player_sprites = [
            self.sprite_manager.all_sprites, 
            self.sprite_manager.player_sprite, 
            self.sprite_manager.human_sprites, 
            self.sprite_manager.animated_sprites
        ]
        self.player = Player( 
            player_coords,
            load_subfolders(join('..', 'graphics', 'player')), 
            Z_LAYERS['player'],
            player_sprites,
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