from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from camera import Camera
    from ui import UI
    from procgen import ProcGen
    from sprite_manager import SpriteManager
    from chunk_manager import ChunkManager
    
import pygame as pg
from os import walk
from os.path import join
import math

from settings import *
from weather import Weather

class GraphicsEngine:
    def __init__(
        self, 
        screen: pg.Surface,
        camera: Camera,
        graphics: dict[str, list[pg.Surface]],
        ui: UI,
        proc_gen: ProcGen, 
        sprite_manager: SpriteManager,
        chunk_manager: ChunkManager
    ):
        self.screen = screen
        self.camera = camera
        self.camera_offset = camera.offset
        self.graphics = graphics
        self.ui = ui
        self.proc_gen = proc_gen
        self.sprite_manager = sprite_manager
        self.chunk_manager = chunk_manager

        self.tile_map = proc_gen.tile_map
        self.tile_id_map = proc_gen.tile_id_map
        self.biome_order = proc_gen.biome_order

        self.all_sprites = sprite_manager.all_sprites
        self.cloud_sprites = sprite_manager.cloud_sprites
        
        self.weather = Weather(screen)
     
    # world
    def render_bg_images(self, bg_type: str) -> None:
        '''render the current biome's landscape & underground graphics''' 
        if bg_type != 'terrain wall':
            image = self.graphics[self.proc_gen.current_biome][bg_type]
        else:
            image = self.graphics['walls'][' '.join([self.get_terrain_type(), 'wall'])]

        elev_data = self.get_elevation_data()

        for x in range((BIOME_WIDTH * TILE_SIZE) // image.get_width()): 
            left = (image.get_width() * x) + self.get_biome_offset()
            if bg_type == 'landscape': # has a static y-axis
                top = elev_data['landscape base'] - image.get_height()
                self.screen.blit(image, (left, top) - self.camera_offset)
            else: 
                # underground graphics
                for y in range(elev_data['underground span'] // image.get_height() + 1): 
                    top = elev_data['underground start' if bg_type == 'underground' else 'landscape base']
                    top += image.get_height() * y
                    self.screen.blit(image, (left, top) - self.camera_offset)

    def get_terrain_type(self) -> str:
        '''just for getting a specific wall variant but could become more modular'''
        match self.proc_gen.current_biome:
            case 'highlands':
                return 'stone'

            case 'forest' | 'taiga' | 'tundra':
                return 'dirt'

            case 'desert':
                return 'sandstone'
                
            case 'underworld':
                return 'magma'

    def get_elevation_data(self) -> dict[str, int]:
        elev_params = BIOMES[self.proc_gen.current_biome]['elevation']
        elev_data = {
            'range': (elev_params['bottom'] - elev_params['top']) * TILE_SIZE,
            'underground span': (MAP_SIZE[1] * TILE_SIZE) - (elev_params['bottom'] * TILE_SIZE), # minimum number of tiles from the bottom of the map to the surface
            'underground start': elev_params['bottom'] * TILE_SIZE 
        }
        # approximate midpoint between the biome's highest/lowest elevation
        elev_data['landscape base'] = elev_data['underground start'] - (elev_data['range'] // 2) 
        return elev_data

    def get_biome_offset(self) -> int:
        '''return the current biome's distance (in pixels) from the left edge of the screen'''
        return self.proc_gen.biome_order[self.proc_gen.current_biome] * (BIOME_WIDTH * TILE_SIZE)

    def render_tiles(self) -> None:
        visible_chunks = self.chunk_manager.update()
        for coords in visible_chunks: # all visible tile coordinates
            for (x, y) in coords: # individual tile coordinates
                # ensure that the tile is within the map borders & is a solid tile
                if 0 <= x < MAP_SIZE[0] and 0 <= y < MAP_SIZE[1] \
                and self.tile_map[x, y] != self.tile_id_map['air']:
                    # match the tile to its graphic
                    for tile in self.tile_id_map.keys():
                        if self.tile_id_map[tile]  == self.tile_map[x, y]:
                            # convert from tile to pixel coordinates
                            px_x = (x * TILE_SIZE) - self.camera_offset.x
                            px_y = (y * TILE_SIZE) - self.camera_offset.y 
                            self.screen.blit(self.graphics[tile], (px_x, px_y))


    # sprites
    def animate(self, sprite: pg.sprite.Sprite, dt: float) -> None:
        if sprite.state not in ('idle', 'jumping'):
            sprite.frame_index += sprite.animation_speed[sprite.state] * dt
            if self.update_flip(sprite):
                sprite.facing_left = not sprite.facing_left
            sprite.image = pg.transform.flip(
                sprite.frames[sprite.state][int(sprite.frame_index % len(sprite.frames[sprite.state]))],
                not sprite.facing_left,
                False
            )
    
    @staticmethod
    def update_flip(sprite: pg.sprite.Sprite) -> bool:
        '''signals when the sprite's facing & movement directions misalign'''
        return sprite.facing_left and sprite.direction.x > 0 or not sprite.facing_left and sprite.direction.x < 0
        
    def render_sprites(self) -> None:
        for sprite in sorted(self.all_sprites, key = lambda sprite: sprite.z): # layer graphics by their z-level
            self.screen.blit(sprite.image, sprite.rect.topleft - self.camera_offset)

    def update(self, mouse_coords: tuple[int, int], mouse_moving: bool, left_click: bool, dt: float) -> None:
        self.sprite_manager.update(dt)
        self.weather.update()

        for bg in ('landscape', 'terrain wall', 'underground'):
            self.render_bg_images(bg)
        self.render_tiles()
        self.render_sprites()
        self.ui.update(mouse_coords, mouse_moving, left_click)

        for sprite in self.sprite_manager.all_sprites:
            self.animate(sprite, dt)