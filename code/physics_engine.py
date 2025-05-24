from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import numpy as np
    
import pygame as pg
import math

from settings import MAP_SIZE, TILE_SIZE, CELL_SIZE

class PhysicsEngine:
    def __init__(self, tile_map: np.ndarray,  tile_IDs: dict[str, dict[str, any]]):
        self.tile_map = tile_map
        self. tile_IDs =  tile_IDs 
        
        self.world_edge_right = (MAP_SIZE[0] * TILE_SIZE) - 19 # minus 19 to prevent going partially off-screen
        self.world_edge_bottom = MAP_SIZE[1] * TILE_SIZE

        self.collision_map = {}
        self.generate_collision_map()

    def move_sprite(self, sprite: pg.sprite.Sprite, direction_x: int, dt: float) -> None:
        sprite.direction.x = 0
        if direction_x:
            sprite.direction.x = direction_x
            sprite.rect.x += sprite.direction.x * sprite.speed * dt
            sprite.rect.x = max(0, min(sprite.rect.x, self.world_edge_right))

            if sprite.state == 'idle': # avoid overwriting an active state
                sprite.state = 'walking'
                
            self.tile_collision_detection(sprite, axis = 'x')
        else:
            # TODO: revisit this line in case more relevant states are added
            if sprite.state not in ('jumping', 'mining'):
                sprite.state = 'idle'
                sprite.frame_index = 0
                
        if not sprite.spawned: 
            # safeguard against a collision detection issue where the player falls through the map after being spawned
            # downward velocity is severely limited until the 1st player/tile collision is detected 
            sprite.direction.y = 10

        # getting the average of the downward velocity
        sprite.direction.y += sprite.gravity / 2 * dt
        sprite.rect.y += sprite.direction.y * dt
        sprite.direction.y += sprite.gravity / 2 * dt
      
        sprite.rect.y = min(sprite.rect.y, self.world_edge_bottom) # don't add a top limit until the space biome borders are set, if any
        self.tile_collision_detection(sprite, axis = 'y')     

    @staticmethod
    def jump(sprite: pg.sprite.Sprite) -> None:
        if sprite.grounded and sprite.state != 'jumping':
            sprite.direction.y -= sprite.jump_height
            sprite.state = 'jumping'
            sprite.frame_index = 0

    def generate_collision_map(self) -> None:
        '''precompute rects with the coordinates of solid tiles'''
        for x in range(MAP_SIZE[0]):
            for y in range(MAP_SIZE[1]):
                if self.tile_map[x, y] != self.tile_IDs['air']: 
                    cell_coords = (x // CELL_SIZE, y // CELL_SIZE)
                    if cell_coords not in self.collision_map:
                        self.collision_map[cell_coords] = []  
                    # store the rects that comprise the current cell
                    self.collision_map[cell_coords].append(pg.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))

    def search_collision_map(self, sprite: pg.sprite.Sprite) -> list[pg.Rect]:
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
                if (cell_x, cell_y) in self.collision_map:
                    rects.extend(self.collision_map[(cell_x, cell_y)])

        return rects
 
    def tile_collision_detection(self, sprite: pg.sprite.Sprite, axis: str) -> None:
        '''adjust movement/positioning upon detecting a collision'''
        colliding_tiles = self.search_collision_map(sprite)
        if colliding_tiles: 
            for tile in colliding_tiles:
                if sprite.rect.colliderect(tile):
                    if axis == 'x' and sprite.direction.x:
                        self.tile_collision_x(sprite, tile, direction = 'right' if sprite.direction.x > 0 else 'left')

                    elif axis == 'y' and sprite.direction.y:
                        self.tile_collision_y(sprite, tile, direction = 'up' if sprite.direction.y < 0 else 'down')
        else:
            sprite.grounded = False
            sprite.state = 'jumping' # technically falling but the jumping graphic can still be rendered

    def tile_collision_x(self, sprite: pg.sprite.Sprite, tile: pg.Rect, direction: str) -> None:
        if not self.step_over_tile(sprite, tile.x // TILE_SIZE, tile.y // TILE_SIZE):
            if direction == 'right':
                sprite.rect.right = tile.left
            else:
                sprite.rect.left = tile.right

            sprite.state = 'idle'
        else:
            if sprite.grounded: # prevents some glitchy movement from landing on the side of a tile
                if direction == 'right':
                    sprite.rect.bottomright = tile.topleft - pg.Vector2(0, 1) # subtracting 1 from the y-axis seems to give slightly more fluid movement 
                else:
                    sprite.rect.bottomleft = tile.topright

        sprite.direction.x = 0

    def step_over_tile(self, sprite, tile_x, tile_y) -> bool:
        '''determine if the sprite can step over the colliding tile'''
        above_tiles = []
        # check if the number of air tiles above the given tile is at least equal to the sprite's height
        if sprite.direction.y <= 0:
            for i in range(1, math.ceil(sprite.rect.height / TILE_SIZE)):
                above_tiles.append(self.tile_map[tile_x, tile_y - i])
            
            # also check if the tile above the player's head is air
            above_tiles.append(self.tile_map[tile_x - 1, tile_y - 2])

            return all(tile_id == self. tile_IDs['air']  for tile_id in above_tiles)

        return False

    @staticmethod
    def tile_collision_y(sprite: pg.sprite.Sprite, tile: pg.Rect, direction: str) -> None:
        if direction == 'up': 
            sprite.rect.top = tile.bottom
        else:
            sprite.rect.bottom = tile.top
            if not sprite.grounded:
                sprite.grounded = True

            if not sprite.spawned:
                sprite.spawned = True 
            
            if sprite.state == 'jumping':
                sprite.state = 'idle'

        sprite.direction.y = 0