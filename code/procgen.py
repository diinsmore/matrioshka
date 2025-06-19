import pygame as pg
import numpy as np
import noise
import random
from os.path import join

from settings import TILES, TILE_SIZE, MAP_SIZE, CELL_SIZE, BIOMES, BIOME_WIDTH, Z_LAYERS, MACHINES, STORAGE
from timer import Timer
from file_import_functions import load_image
import camera

# TODO: refine the ore distribution to generate clusters of a particular gemstone rather than randomized for each tile 

class ProcGen:
    def __init__(self, screen: pg.Surface, camera_offset: pg.Vector2, saved_data: dict[str, any] | None):
        self.screen = screen
        self.camera_offset = camera_offset
        self.saved_data = saved_data

        self.tile_IDs = self.get_tile_IDs()
        self.tile_IDs_to_names = {v: k for k, v in self.tile_IDs.items()}
        self.biome_order = self.order_biomes()
        
        if self.saved_data:
            self.load_saved_data()
        else:
            self.tile_map = np.zeros((MAP_SIZE[0], MAP_SIZE[1]), dtype = np.uint8)
            self.height_map = np.zeros(MAP_SIZE[0], dtype = np.float32)
            self.tree_map = [] # store the coordinates of each tree's base to avoid looping through the entire tile map
            self.current_biome = 'forest'
            self.generate_terrain()
    
    def load_saved_data(self) -> None:
        self.tile_map = np.array(self.saved_data['tile map'], dtype = np.uint8)
        self.tree_map = [tuple(coord) for coord in self.saved_data['tree map']]
        self.player_spawn_point = self.saved_data['sprites']['player']['coords']
        self.current_biome = self.saved_data['current biome']

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
    def get_tile_IDs() -> dict[str, int]:
        '''give each tile a unique number to store at its locations within the tile map'''
        id_map = {}
        world_objects = {**TILES, **MACHINES, **STORAGE}
        id_map.update((obj, index) for index, obj in enumerate(world_objects.keys()))
        id_map['obj extended'] = len(id_map)
        id_map['tree base'] = id_map['obj extended'] + 1
        return id_map
    
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
        self.place_tiles()
        self.place_trees()

    def place_tiles(self) -> None:
        for x in range(MAP_SIZE[0]):
            surface_level = int(self.height_map[x])
            for y in range(MAP_SIZE[1]): 
                if y < surface_level: 
                    self.tile_map[x, y] = self.tile_IDs['air'] 

                elif y == surface_level:
                    self.tile_map[x, y] = self.tile_IDs['dirt']

                else:
                    # calculate the tile's depth relative to the height of the map
                    rel_depth = (y - surface_level) / MAP_SIZE[1]
                    if rel_depth < 0.1:
                        self.tile_map[x, y] = self.tile_IDs['dirt']

                    elif rel_depth < 0.2:
                        self.tile_map[x, y] = self.tile_IDs['stone' if random.randint(0, 100) <= 33 else 'dirt'] 
                    
                    elif rel_depth < 0.4:
                        if random.randint(0, 100) <= 25:
                            self.tile_map[x, y] = random.choice((self.tile_IDs['sandstone'], self.tile_IDs['ice']))
                        else:
                            self.tile_map[x, y] = self.tile_IDs['stone' if random.randint(0, 100) < 60 else 'dirt']  
                    
                    else:
                        self.ore_distribution(x, y, self.current_biome)

    def place_trees(self) -> None:
        for x in range(MAP_SIZE[0]):
            y = int(self.height_map[x]) # surface level
            current_biome = list(BIOMES.keys())[x // BIOME_WIDTH]
            # don't use any() here or an error will be thrown from the biomes missing 'tree prob'
            if current_biome in {'forest', 'taiga', 'desert'} and \
            random.randint(0, 100) <= BIOMES[current_biome]['tree prob'] and \
            self.valid_spawn_point(x, y):
                self.tree_map.append((x, y))
                self.tile_map[x, y] = self.tile_IDs['tree base']
    
    def ore_distribution(self, x: int, y: int, biome: str) -> None:
        '''
        Distribute ore tiles based on the biome's probability of containing such a tile.
        If no ore is selected, fill the space with a tile common to the biome.
        '''
        ores = [tile for tile in self.tile_IDs if self.tile_IDs['copper']  <= self.tile_IDs[tile]  <= self.tile_IDs['gold'] ]
        
        non_ores = [tile for tile in self.tile_IDs if self.tile_IDs['dirt']  <= self.tile_IDs[tile]  <= self.tile_IDs[
                    'obsidian' if biome != 'underworld' else 'hellstone'] ]

        if random.random() < 0.1:
            ore_selected = self.calc_tile_prob(ores, x, y, biome)
            if not ore_selected:
                # select a random non-ore tile
                tile = random.choice(non_ores)
                self.tile_map[x, y] = self.tile_IDs[tile] 
        else:
            tile = random.choice(non_ores)
            self.tile_map[x, y] = self.tile_IDs[tile] 
                        
    def calc_tile_prob(self, tiles: list[str], x: int, y: int, biome: str) -> bool:
        '''randomly determine which tile (if any) should be placed at the given coordinate'''
        tiles = sorted(tiles, key = lambda tile: BIOMES[biome]['tile probs'][tile], reverse=True)
        for index, tile in enumerate(tiles):
            if random.randint(0, 10) <= BIOMES[biome]['tile probs'][tile]:
                self.tile_map[x, y] = self.tile_IDs[tile] 
                return True
            else:
                if index < len(tiles) - 1:
                    continue
                return False
        
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
                    if self.valid_spawn_point(*xy):
                        valid_coords.append(xy)

                if valid_coords:
                    # select the coordinate nearest to the map's center-x
                    spawn_point = min(valid_coords, key = lambda coord: abs(coord[0] - center_x))
                    return (spawn_point[0] * TILE_SIZE, spawn_point[1] * TILE_SIZE)
                else:
                    # default to the center-x
                    return (center_x * TILE_SIZE, y * TILE_SIZE)

    def valid_spawn_point(self, x: int, y: int) -> bool:
        current_tile = self.tile_map[x, y]
        left_tile = self.tile_map[x - 1, y]
        right_tile = self.tile_map[x + 1, y]

        topleft_tile = self.tile_map[x - 1, y - 1]
        topcenter_tile = self.tile_map[x, y - 1]
        topright_tile = self.tile_map[x + 1, y - 1]
        
        air = self.tile_IDs['air'] 
        return all(tile != air for tile in (current_tile, left_tile, right_tile)) and \
               all(tile == air for tile in (topleft_tile, topcenter_tile, topright_tile))