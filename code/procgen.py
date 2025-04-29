import pygame as pg
import numpy as np
import noise
import random

from settings import TILES, TILE_SIZE, MAP_SIZE, CELL_SIZE, BIOMES, BIOME_WIDTH
from sprites import *
from timer import Timer

# TODO: refine the ore distribution to generate clusters of a particular gemstone rather than randomized for each tile 

class ProcGen:
    def __init__(self):
        self.tile_map = np.zeros((MAP_SIZE[0], MAP_SIZE[1]), dtype = np.uint8)
        self.height_map = np.zeros(MAP_SIZE[0], dtype = np.float32)
        self.biome_order = self.order_biomes()
        self.current_biome = 'forest'
        self.tile_id_map = self.get_tile_id_map()
        # stores the strength of tiles in the process of being mined
        self.mining_map = {}
       
        self.generate_terrain()

    # TODO: randomize the sequence
    @staticmethod
    def order_biomes() -> dict[str, int]:
        order = {}
        # excluding the underworld since it spans the entire map width
        biomes = [b for b in BIOMES.keys() if b != 'underworld']
        for index, biome in enumerate(biomes):
            order[biome] = index

        return order

    @staticmethod
    def get_tile_id_map() -> dict[str, int]:
        '''give each tile a unique number to store at its locations within the tile map'''
        tile_id_map = {}
        # key = tile type, value = tile index
        tile_id_map.update((tile, index) for index, tile in enumerate(TILES))
        return tile_id_map
    
    def generate_height_map(self) -> None:
        '''generates a height map for every biome using 1d perlin noise'''
        seed = 2285 # TODO: add the option to enter a custom seed
        # TODO: add more gradual transitions between biomes
        for biome, order_num in self.biome_order.items(): 
            elev_data = BIOMES[biome]['elevation']
            elev_range = elev_data['bottom'] - elev_data['top']
            
            noise_params = BIOMES[biome]['noise params']
            
            for x in range(order_num * BIOME_WIDTH, (order_num + 1) * BIOME_WIDTH):
                # generates a random float between -1/1
                num = noise.pnoise1(  
                    x / noise_params['scale'], 
                    octaves = noise_params['octaves'], 
                    persistence = noise_params['persistence'],
                    lacunarity = noise_params['lacunarity'],
                    repeat = -1, # don't repeat
                    base = seed
                )
                # convert the range from -1/1 to 0/1 to keep values positive (or zero, but rarely)
                range01 = (num + 1) / 2 
                self.height_map[x] = elev_data['top'] + range01 * elev_range

    def generate_terrain(self) -> None:
        self.generate_height_map()
        # TODO: add the underworld
        for x in range(MAP_SIZE[0]):
            surface_level = round(self.height_map[x])
            for y in range(MAP_SIZE[1]):
                if y < surface_level: 
                    self.tile_map[x, y] = self.tile_id_map['air'] 

                elif y == surface_level: 
                    self.tile_map[x, y] = self.tile_id_map['dirt'] 
                    
                else:
                    # calculate the tile's depth relative to the height of the map
                    rel_depth = (y - surface_level) / MAP_SIZE[1]
                    if rel_depth < 0.1:
                        self.tile_map[x, y] = self.tile_id_map['dirt'] 

                    elif rel_depth < 0.2:
                        self.tile_map[x, y] = self.tile_id_map['stone' if random.randint(0, 100) <= 33 else 'dirt'] 

                    elif rel_depth < 0.4:
                        if random.randint(0, 100) <= 25:
                            self.tile_map[x, y] = random.choice((self.tile_id_map['sandstone'] , self.tile_id_map['ice'] ))
                        else:
                            self.tile_map[x, y] = self.tile_id_map['stone' if random.randint(0, 100) < 60 else 'dirt']  
                    else:
                        self.ore_distribution(x, y, self.current_biome)  
    
    def ore_distribution(self, x: int, y: int, biome: str) -> None:
        '''
        Distribute ore tiles based on the biome's probability of containing such a tile.
        If no ore is selected, fill the space with a tile common to the biome.
        '''
        ores = [tile for tile in self.tile_id_map if self.tile_id_map['copper']  <= self.tile_id_map[tile]  <= self.tile_id_map['gold'] ]
        
        non_ores = [tile for tile in self.tile_id_map if self.tile_id_map['dirt']  <= self.tile_id_map[tile]  <= self.tile_id_map[
                    'obsidian' if biome != 'underworld' else 'hellstone'] ]

        if random.random() < 0.1:
            ore_selected = self.calc_tile_prob(ores, x, y, biome)
            if not ore_selected:
                # select a random non-ore tile
                tile = random.choice(non_ores)
                self.tile_map[x, y] = self.tile_id_map[tile] 
        else:
            tile = random.choice(non_ores)
            self.tile_map[x, y] = self.tile_id_map[tile] 
                        
    def calc_tile_prob(self, tiles: list[str], x: int, y: int, biome: str) -> bool:
        '''randomly determine which tile (if any) should be placed at the given coordinate'''
        tiles = sorted(tiles, key = lambda tile: BIOMES[biome]['tile probs'][tile], reverse=True)
        for index, tile in enumerate(tiles):
            if random.randint(0, 10) <= BIOMES[biome]['tile probs'][tile]:
                self.tile_map[x, y] = self.tile_id_map[tile] 
                return True
            else:
                if index < len(tiles) - 1:
                    continue
                return False

    def add_tree(self, coords: tuple[int, int], biome) -> None:
        image = load_image(join('..', 'graphics', 'terrain', 'trees', f'{biome} tree.png'))
        if TILE_SIZE < coords[0] < MAP_SIZE[0] - TILE_SIZE: # not positioned at the edge of the map
            center_tile = self.tile_map[coords[0] + 1, coords[1]]    
            left_tile = self.tile_map[coords[0] - 1, coords[1]]
            right_tile = self.tile_map[coords[0] + 1, coords[1]]
            # only spawn at coordinates where the x-axis is consistent for 3+ tiles (equal to the tree's width of 36px)
            if center_tile == 0 and left_tile == 0 and right_tile == 0: # dirt tiles
                Tree(
                    coords = (coords[0] * TILE_SIZE, coords[1] * TILE_SIZE - image.get_height()), 
                    image = image, 
                    z = Z_LAYERS['bg'], 
                    groups = self.all_sprites
                )

    def get_player_spawn_point(self) -> tuple[int, int]:
            '''spawn at the nearest flat surface (at least 3 solid tiles on the same y-axis) to the map's center-x'''
            center_x = MAP_SIZE[0] // 2
            y = int(self.height_map[center_x])
            # check for neighboring tiles being on the same y-axis and only having air tiles above them
            if self.valid_spawn_point(center_x, y): 
                return (center_x * TILE_SIZE, y * TILE_SIZE)
            else:
                valid_coords = []
                for x in range(1, MAP_SIZE[0] - 1):
                    xy = (x, int(self.height_map[x]))
                    if self.valid_spawn_point(xy[0], xy[1]):
                        valid_coords.append(xy)

                if valid_coords:
                    # select the coordinate nearest to the map's center-x
                    spawn_point = min(valid_coords, key = lambda coord: abs(coord[0] - center_x))
                    return (spawn_point[0] * TILE_SIZE, spawn_point[1] * TILE_SIZE)
                else:
                    # default to the center-x
                    return (center_x * TILE_SIZE, y * TILE_SIZE)

    def valid_spawn_point(self, x: int, y: int) -> bool:
        '''
        Determine whether a 3x3 horizontal line of tiles are all solid, 
        to find a suitable spawn point for the player (and maybe future entities)
        '''
        current_tile = self.tile_map[x, y]
        left_tile = self.tile_map[x - 1, y]
        right_tile = self.tile_map[x + 1, y]

        topleft_tile = self.tile_map[x - 1, y - 1]
        topcenter_tile = self.tile_map[x, y - 1]
        topright_tile = self.tile_map[x + 1, y - 1]
        
        air = self.tile_id_map['air'] 
        return all(tile != air for tile in (current_tile, left_tile, right_tile)) and \
               all(tile == air for tile in (topleft_tile, topcenter_tile, topright_tile))

    # update tiles that have been mined, will also have to account for the use of explosives and perhaps weather altering the terrain
    def update_map(self, tile_coords: tuple[int, int], collision_map: dict[tuple[int, int], pg.Rect]) -> None:
        cell_coords = (
            tile_coords[0] // CELL_SIZE, 
            tile_coords[1] // CELL_SIZE
        )
        if cell_coords in collision_map: # false if you're up in the stratosphere
            rect = pg.Rect(tile_coords[0] * TILE_SIZE, tile_coords[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            if rect in collision_map[cell_coords]:
                # sprites could occasionally pass through tiles whose graphic was still being rendered
                # removing the associated rectangle only after the tile id's update is confirmed appears to fix the issue
                if self.tile_map[tile_coords[0], tile_coords[1]] == self.tile_id_map['air'] :
                    collision_map[cell_coords].remove(rect)