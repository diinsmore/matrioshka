from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import numpy as np
    
import pygame as pg
from math import ceil
from collections import defaultdict

from settings import MAP_SIZE, TILE_SIZE, CELL_SIZE, WORLD_EDGE_RIGHT, WORLD_EDGE_BOTTOM

class PhysicsEngine:
    def __init__(self, tile_map: np.ndarray, tile_IDs: dict[str, int]):
        self.tile_map = tile_map
        self.tile_IDs = tile_IDs
        
        self.collision_map = CollisionMap(self.tile_map, self.tile_IDs)
        self.collision_detection = CollisionDetection(self.collision_map)
        self.sprite_movement = SpriteMovement(self.collision_detection, self.tile_map, self.tile_IDs)


class CollisionMap:
    def __init__(self, tile_map: np.ndarray, tile_IDs: dict[str, int]):
        self.tile_map = tile_map
        self.tile_IDs = tile_IDs

        self.map = defaultdict(list)
        self.generate_map()

    def generate_map(self) -> None:
        '''precompute rects with the coordinates of solid tiles'''
        for x in range(MAP_SIZE[0]):
            for y in range(MAP_SIZE[1]):
                if self.tile_map[x, y] != self.tile_IDs['air']: 
                    cell_coords = (x // CELL_SIZE, y // CELL_SIZE)
                    self.map[cell_coords].append(pg.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))

    def search_map(self, sprite: pg.sprite.Sprite) -> list[pg.Rect]:
        '''extract the rects within the current cell for collision detection'''
        rects = []
        # determine which collision map cell(s) the player is within
        min_tile_x = sprite.rect.left // TILE_SIZE
        max_tile_x = sprite.rect.right // TILE_SIZE

        min_tile_y = sprite.rect.top // TILE_SIZE
        max_tile_y = sprite.rect.bottom // TILE_SIZE

        min_cell_x = min_tile_x // CELL_SIZE
        max_cell_x = max_tile_x // CELL_SIZE

        min_cell_y = min_tile_y // CELL_SIZE
        max_cell_y = max_tile_y // CELL_SIZE
        
        for cell_x in range(min_cell_x, max_cell_x + 1):
            for cell_y in range(min_cell_y, max_cell_y + 1): 
                if (cell_x, cell_y) in self.map:
                    rects.extend(self.map[(cell_x, cell_y)])

        return rects

    # update tiles that have been mined/placed, will also have to account for the use of explosives and perhaps weather altering the terrain
    def update_map(self, tile_coords: tuple[int, int], add_tile: bool = False, remove_tile: bool = False) -> None:
        cell_coords = (tile_coords[0] // CELL_SIZE, tile_coords[1] // CELL_SIZE)
        rect = pg.Rect(tile_coords[0] * TILE_SIZE, tile_coords[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE)    
        if cell_coords in self.map: # false if you're up in the stratosphere
            if add_tile and rect not in self.map[cell_coords]:
                self.map[cell_coords].append(rect)
            
            elif remove_tile and rect in self.map[cell_coords]:
                # sprites could occasionally pass through tiles whose graphic was still being rendered
                # removing the associated rectangle only after the tile ID update is confirmed appears to fix the issue
                if self.tile_map[tile_coords[0], tile_coords[1]] == self.tile_IDs['air']:
                    self.map[cell_coords].remove(rect)
        

class CollisionDetection:
    def __init__(self, collision_map: CollisionMap):
        self.collision_map = collision_map

    def tile_collision_update(self, sprite: pg.sprite.Sprite, axis: str, step_over_tile: callable) -> None:
        '''adjust movement/positioning upon detecting a tile collision'''
        tiles_near = self.collision_map.search_map(sprite)
        if not tiles_near: # surrounded by air
            sprite.grounded = False
            sprite.state = 'jumping' # the jumping graphic applies to both jumping/falling
            return
        
        for tile in tiles_near:
            if sprite.rect.colliderect(tile):
                if axis == 'x' and sprite.direction.x:
                    self.tile_collision_x(sprite, tile, 'right' if sprite.direction.x > 0 else 'left', step_over_tile)

                elif axis == 'y' and sprite.direction.y:
                    self.tile_collision_y(sprite, tile, 'up' if sprite.direction.y < 0 else 'down')
        
    @staticmethod
    def tile_collision_x(sprite: pg.sprite.Sprite, tile: pg.Rect, direction: str, step_over_tile: callable) -> None:
        if not step_over_tile(sprite, tile.x // TILE_SIZE, tile.y // TILE_SIZE):
            if direction == 'right':
                sprite.rect.right = tile.left
            else:
                sprite.rect.left = tile.right

            sprite.state = 'idle'
        else:
            if sprite.grounded: # prevents some glitchy movement from landing on the side of a tile
                if direction == 'right':
                    sprite.rect.bottomright = tile.topleft
                else:
                    sprite.rect.bottomleft = tile.topright

        sprite.direction.x = 0

    @staticmethod
    def tile_collision_y(sprite: pg.sprite.Sprite, tile: pg.Rect, direction: str) -> None:
        if direction == 'up': 
            sprite.rect.top = tile.bottom
        
        elif direction == 'down':
            sprite.rect.bottom = tile.top
            if hasattr(sprite, 'grounded') and not sprite.grounded:
                sprite.grounded = True
            
            if hasattr(sprite, 'state') and sprite.state == 'jumping':
                sprite.state = 'idle'

        sprite.direction.y = 0


class SpriteMovement:
    def __init__(self, collision_detection: CollisionDetection, tile_map: np.ndarray, tile_IDs: dict[str, int]) -> None:
        self.collision_detection = collision_detection
        self.tile_map = tile_map
        self.tile_IDs = tile_IDs

        self.active_states = {'jumping', 'mining', 'chopping'} # TODO: revisit this line in case more relevant states are added

    def move_sprite(self, sprite: pg.sprite.Sprite, direction_x: int, dt: float) -> None:
        if direction_x:
            self.update_movement_x(sprite, direction_x, dt)  
        else:
            sprite.direction.x = 0
            if hasattr(sprite, 'state') and sprite not in self.active_states:
                sprite.state = 'idle'
                sprite.frame_index = 0
        
        self.collision_detection.tile_collision_update(sprite, 'x', self.step_over_tile)
        self.update_movement_y(sprite, dt) # always called since it handles gravity
        self.collision_detection.tile_collision_update(sprite, 'y', self.step_over_tile)

    @staticmethod
    def update_movement_x(sprite: pg.sprite.Sprite, direction_x: int, dt: float) -> None:
        sprite.direction.x = direction_x
        sprite.rect.x += sprite.direction.x * sprite.speed * dt
        sprite.rect.x = max(0, min(sprite.rect.x, WORLD_EDGE_RIGHT))

        if hasattr(sprite, 'state') and sprite.state == 'idle': # avoid overwriting an active state
            sprite.state = 'walking'
    
    @staticmethod
    def update_movement_y(sprite, dt: float) -> None:
        # getting the average of the downward velocity
        sprite.direction.y += (sprite.gravity // 2) * dt
        sprite.rect.y += sprite.direction.y * dt
        sprite.direction.y += (sprite.gravity // 2) * dt

        sprite.rect.y = min(sprite.rect.y, WORLD_EDGE_BOTTOM) # don't add a top limit until the space biome borders are set, if any
        
    def step_over_tile(self, sprite, tile_x, tile_y) -> bool:
        '''determine if the sprite can step over the colliding tile'''
        if sprite.direction.y == 0:
            above_tiles = []
            for i in range(1, ceil(sprite.rect.height / TILE_SIZE)): # check if the number of air tiles above the given tile is at least equal to the sprite's height
                above_tiles.append(self.tile_map[tile_x, tile_y - i])
            above_tiles.append(self.tile_map[tile_x - 1, tile_y - 2]) # also check if the tile above the player's head is air
            return all(tile_id == self.tile_IDs['air'] for tile_id in above_tiles)
        return False

    @staticmethod
    def jump(sprite: pg.sprite.Sprite) -> None:
        if sprite.grounded and sprite.state != 'jumping':
            sprite.direction.y -= sprite.jump_height
            sprite.grounded = False
            sprite.state = 'jumping'
            sprite.frame_index = 0