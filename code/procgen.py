import pygame as pg
import numpy as np
import noise
from random import randint, choice

from settings import TILES, TILE_SIZE, MAP_SIZE, CELL_SIZE, BIOMES, BIOME_WIDTH, Z_LAYERS, MACHINES, STORAGE
from timer import Timer
from file_import_functions import load_image

# TODO: refine the ore distribution to generate clusters of a particular gemstone rather than randomized for each tile 
class ProcGen:
    def __init__(self, screen: pg.Surface, camera_offset: pg.Vector2, saved_data: dict[str, any] | None):
        self.screen = screen
        self.camera_offset = camera_offset
        self.saved_data = saved_data
        
        self.tile_IDs = self.get_tile_IDs()
        self.tile_IDs_to_names = {v: k for k, v in self.tile_IDs.items()}
        
        if self.saved_data:
            self.load_saved_data()
        else:
            self.biome_order = self.order_biomes()
            self.current_biome = 'forest'

            self.terrain_gen = TerrainGen(self.tile_IDs, self.biome_order, self.current_biome, self.tile_IDs_to_names)
            self.tile_map = self.terrain_gen.tile_map
            self.height_map = self.terrain_gen.height_map
            self.cave_map = self.terrain_gen.cave_map

            self.tree_gen = TreeGen(self.tile_map, self.tile_IDs, self.height_map, self.valid_spawn_point, self.biome_order)
            self.tree_map = self.tree_gen.tree_map

            self.gen_world()
            self.player_spawn_point = self.get_player_spawn_point()

    def load_saved_data(self) -> None:
        self.tile_map = np.array(self.saved_data['tile map'], dtype = np.uint8)
        self.tree_map = set(tuple(coord) for coord in self.saved_data['tree map'])
        self.cave_map = np.array(self.saved_data['cave map'], dtype = bool)
        self.biome_order = self.saved_data['biome order']
        self.player_spawn_point = self.saved_data['sprites']['player']['coords']
        self.current_biome = self.saved_data['current biome']

    @staticmethod
    def get_tile_IDs() -> dict[str, int]:
        '''give each tile a unique number to store at its locations within the tile map'''
        id_map = {}
        world_objects = {**TILES, **MACHINES, **STORAGE}
        id_map.update((obj, index) for index, obj in enumerate(world_objects.keys()))
        id_map['obj extended'] = len(id_map)
        id_map['tree base'] = id_map['obj extended'] + 1
        id_map['left ramp'] = id_map['tree base'] + 1
        id_map['right ramp'] = id_map['left ramp'] + 1
        return id_map

    @staticmethod
    def order_biomes() -> dict[str, int]:
        # TODO: randomize this sequence
        order = {'highlands': 0, 'desert': 1, 'forest': 2, 'taiga': 3, 'tundra': 4}
        return order

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
        left_tile = self.tile_map[x - 1, y]
        center_tile = self.tile_map[x, y]
        right_tile = self.tile_map[x + 1, y]

        topleft_tile = self.tile_map[x - 1, y - 1]
        topcenter_tile = self.tile_map[x, y - 1]
        topright_tile = self.tile_map[x + 1, y - 1]
        
        air = self.tile_IDs['air'] 
        return all(tile != air for tile in (left_tile, center_tile, right_tile)) and \
               all(tile == air for tile in (topleft_tile, topcenter_tile, topright_tile))

    def gen_world(self) -> None:
        self.terrain_gen.run()
        self.tree_gen.get_tree_locations()


class TerrainGen:
    def __init__(self, tile_IDs: dict[str, int], biome_order: dict[str, int], current_biome: str, tile_IDs_to_names: dict[int, str]):
        self.tile_IDs = tile_IDs
        self.biome_order = biome_order
        self.current_biome = current_biome
        self.tile_IDs_to_names = tile_IDs_to_names
        
        self.seed = 2285 # TODO: add the option to enter a custom seed
        self.tile_map = np.zeros((MAP_SIZE[0], MAP_SIZE[1]), dtype = np.uint8)
        self.height_map = self.gen_height_map()
        self.cave_gen = CaveGen(self.tile_map, self.height_map, self.seed)
        self.cave_map = self.cave_gen.map
        
    def gen_height_map(self) -> np.ndarray:
        '''generates a height map for every biome using 1d perlin noise'''
        height_map = np.zeros(MAP_SIZE[0], dtype = np.float32)
        lerp_range = BIOME_WIDTH // 5 # how far to extend the linear interpolation on noise parameters when generating biome transitions
        biome_names = list(self.biome_order.keys())
        second_to_last_idx = len(biome_names) - 1
        for idx, biome in enumerate(biome_names):
            start = idx * BIOME_WIDTH
            end = start + BIOME_WIDTH
            map_slice = np.arange(start, end) # represents the section of the height map local to the current biome
            elevs = self.get_biome_elevations(map_slice, biome)
            
            if idx < second_to_last_idx: # another biome lies to the right
                next_biome_elevs = self.get_biome_elevations(map_slice, biome_names[idx + 1])
            else:
                next_biome_elevs = None

            for biome_x, world_x in enumerate(map_slice):
                if biome_x < BIOME_WIDTH - lerp_range or next_biome_elevs is None: # outside the transition zone
                    height_map[world_x] = elevs[biome_x]
                else:
                    rel_pos = (biome_x - (BIOME_WIDTH - lerp_range)) / lerp_range # what % of the way x is to the end of the biome transition zone
                    height_map[world_x] = ((1 - rel_pos) * elevs[biome_x]) + (rel_pos * next_biome_elevs[biome_x]) # lerp for a smoother biome transition
                    
        return height_map

    def get_biome_elevations(self, map_slice: np.ndarray, biome: str) -> np.ndarray:
        biome_data = BIOMES[biome]
        noise_params = biome_data['height map']
        elev_params = biome_data['elevation']
        top, bottom = elev_params['top'], elev_params['bottom']
        elev_range = bottom - top

        n = np.array([
            noise.pnoise1(
                x / noise_params['scale'], 
                noise_params['octaves'], 
                noise_params['persistence'], 
                noise_params['lacunarity'], 
                repeat = -1, 
                base = self.seed
            ) 
            for x in map_slice
        ], dtype = np.float32)

        half_elev = elev_range // 2
        return top + half_elev + (n * half_elev)

    def place_tiles(self) -> None:
        for x in range(MAP_SIZE[0]):
            surface_level = int(self.height_map[x])
            for y in range(MAP_SIZE[1]): 
                if y < surface_level: 
                    self.tile_map[x, y] = self.tile_IDs['air'] 

                elif y == surface_level:
                    # TODO: add sand tiles for the desert, snow for the taiga, etc.
                    self.tile_map[x, y] = self.tile_IDs['dirt']
                    if 0 < x < MAP_SIZE[0] - 1:
                        self.add_ramps(x, y, self.tile_IDs_to_names[self.tile_map[x, y]])
                        
                else:
                    if self.cave_map[x, y]:
                        self.tile_map[x, y] = self.tile_IDs['air']
                    else:
                        rel_depth = (y - surface_level) / MAP_SIZE[1] # calculate the tile's depth relative to the height of the map
                        if rel_depth < 0.1:
                            self.tile_map[x, y] = self.tile_IDs['dirt']
                        
                        elif rel_depth < 0.2:
                            self.tile_map[x, y] = self.tile_IDs['stone' if randint(0, 100) <= 33 else 'dirt'] 
                        
                        elif rel_depth < 0.4:
                            if randint(0, 100) <= 25:
                                self.tile_map[x, y] = choice((self.tile_IDs['sandstone'], self.tile_IDs['ice']))
                            else:
                                self.tile_map[x, y] = self.tile_IDs['stone' if randint(0, 100) < 60 else 'dirt']  
                        else:
                            self.place_ores(x, y, self.current_biome)          
    
    def add_ramps(self, x: int, y: int, tile_type: str) -> None: # TODO: implement the tile types once more ramp graphics are uploaded
        air = self.tile_IDs['air']
        if self.tile_map[x - 1, y] == air:
            self.tile_map[x - 1, y] = self.tile_IDs['left ramp']
        
        if self.tile_map[x + 1, y] == air:
            self.tile_map[x + 1, y] = self.tile_IDs['right ramp']

    def place_ores(self, x: int, y: int, biome: str) -> None:
        '''
        Distribute ore tiles based on the biome's probability of containing such a tile.
        If no ore is selected, fill the space with a tile common to the biome.
        '''
        ores = [tile for tile in self.tile_IDs if self.tile_IDs['copper'] <= self.tile_IDs[tile] <= self.tile_IDs['gold']]
        
        non_ores = [tile for tile in self.tile_IDs if self.tile_IDs['dirt'] <= self.tile_IDs[tile] <= self.tile_IDs[
                    'obsidian' if biome != 'underworld' else 'hellstone']]

        if randint(1, 10) == 1:
            ore_selected = self.calc_tile_prob(ores, x, y, biome)
            if not ore_selected:
                # select a random non-ore tile
                tile = choice(non_ores)
                self.tile_map[x, y] = self.tile_IDs[tile] 
        else:
            tile = choice(non_ores)
            self.tile_map[x, y] = self.tile_IDs[tile] 
                        
    def calc_tile_prob(self, tiles: list[str], x: int, y: int, biome: str) -> bool:
        '''randomly determine which tile (if any) should be placed at the given coordinate'''
        tiles = sorted(tiles, key = lambda tile: BIOMES[biome]['tile probs'][tile], reverse=True)
        for index, tile in enumerate(tiles):
            if randint(0, 10) <= BIOMES[biome]['tile probs'][tile]:
                self.tile_map[x, y] = self.tile_IDs[tile] 
                return True
            else:
                if index < len(tiles) - 1:
                    continue
                return False

    def run(self) -> None:
        self.gen_height_map()
        self.place_tiles()


class CaveGen:
    def __init__(self, tile_map: np.ndarray, height_map: np.ndarray, seed: int):
        self.tile_map = tile_map
        self.height_map = height_map
        self.seed = seed
        self.map = self.gen_map()

    def gen_map(self) -> np.ndarray:
        cave_map = np.zeros(MAP_SIZE, dtype = bool)
        start_y = randint(25, 50)
        for x in range(MAP_SIZE[0]):
            params = BIOMES['forest']['cave map']
            surface_level = int(self.height_map[x])
            for y in range(surface_level + start_y, MAP_SIZE[1]):
                n = noise.pnoise2(
                    x / params['scale'],
                    y / params['scale'],
                    params['octaves'],
                    params['persistence'],
                    params['lacunarity'],
                    repeatx = -1,
                    repeaty = -1,
                    base = self.seed
                )
                cave_map[x, y] = (n + 1) / 2 > params['threshold'] # convert to a range of 0-1 before comparing
        return cave_map


class TreeGen:
    def __init__(
        self, 
        tile_map: np.ndarray, 
        tile_IDs: dict[str, int], 
        height_map: np.ndarray, 
        valid_spawn_point: callable, 
        biome_order: dict[str, int]
    ):
        self.tile_map = tile_map
        self.tile_IDs = tile_IDs
        self.height_map = height_map
        self.valid_spawn_point = valid_spawn_point
        self.biome_order = biome_order

        self.tree_map = set()
        self.biomes_covered = [{'name': name, 'idx': idx} for name, idx in self.biome_order.items() if 'tree coverage' in BIOMES[name].keys()]
        
    def get_tree_locations(self) -> None:
        for data in self.biomes_covered:
            start_x = data['idx'] * BIOME_WIDTH
            for x in range(start_x, start_x + BIOME_WIDTH):
                y = int(self.height_map[x]) # surface level
                if self.valid_spawn_point(x, y) and \
                not self.get_tree_neighbors(x, y, 1, True, True) and \
                randint(0, 100) <= self.get_tree_prob(data['name'], x, y):
                    self.tree_map.add((x, y))
                    self.tile_map[x, y] = self.tile_IDs['tree base']
    
    def get_tree_prob(self, current_biome: str, x: int, y: int) -> int:
        '''
        checks the distribution of trees in the previous tiles.
        the probability of spawning a tree increases for every tree within the given range.
        i.e trees are more likely to spawn near existing trees
        '''
        default_prob = BIOMES[current_biome]['tree coverage']
        scale_factor = default_prob // 10
        return default_prob + scale_factor * self.get_tree_neighbors(x, y, 10, True, False)
        
    def get_tree_neighbors(self, x: int, y: int, sample_size: int, check_left: bool = True, check_right: bool = True) -> int:
        num_neighbors = 0
        if check_left: # search a given number of tiles left of the starting point
            num_neighbors += sum(1 for dx in range(1, sample_size + 1) if (x - dx, y) in self.tree_map)

        if check_right:
            num_neighbors += sum(1 for dx in range(1, sample_size + 1) if (x + dx, y) in self.tree_map)
        return num_neighbors    