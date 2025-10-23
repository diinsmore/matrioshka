RES = (1500, 750)
FPS = 60

TILE_SIZE = 16
CHUNK_SIZE = 24
CELL_SIZE = 10
MAP_SIZE = (3000, 200)
# since pygame's coordinate system starts in the topleft, higher elevation values = lower in the world
BIOMES = { # TODO: the highlands & snow noise parameters are especially in need of fine-tuning
    'highlands': {
        'height map': {'scale': 325, 'octaves': 5, 'persistence': 1.6, 'lacunarity': 2.1},
        'cave map': {'scale': 30.0, 'octaves': 5, 'persistence': 2.0, 'lacunarity': 2.3, 'threshold': 0.4},
        'elevation': {'top': 0, 'bottom': 70}, 
        'tile probs': {'stone': 40, 'dirt': 20, 'coal': 15, 'tin': 3, 'iron': 13, 'copper': 10},
        'liquid probs': {'water': 3, 'lava': 5},
    }, 

    'desert': {
        'height map': {'scale': 425, 'octaves': 4, 'persistence': 0.9, 'lacunarity': 1.4},
        'cave map': {'scale': 60.0, 'octaves': 3, 'persistence': 0.7, 'lacunarity': 0.9, 'threshold': 0.6},
        'elevation': {'top': 50, 'bottom': 90},
        'tile probs': {'sand': 40, 'sandstone': 20, 'clay': 3, 'dirt': 10, 'desert fossil': 3, 'copper': 12, 'iron': 8},
        'liquid probs': {'oil': 7, 'lava': 5},
    },

    'forest': {
        'height map': {'scale': 400, 'octaves': 3, 'persistence': 1.2, 'lacunarity': 2.0},
        'cave map': {'scale': 30.0, 'octaves': 4, 'persistence': 1.6, 'lacunarity': 1.3, 'threshold': 0.55},
        'elevation': {'top': 70, 'bottom': 110},
        'tile probs': {'dirt': 35, 'stone': 25, 'clay': 7, 'tin': 5, 'coal': 9, 'iron': 11, 'copper': 8},
        'liquid probs': {'water': 7, 'lava': 2},
        'tree probs': 30
    },
    
    'taiga': {
        'height map': {'scale': 375, 'octaves': 4, 'persistence': 1.3, 'lacunarity': 1.6},
        'cave map': {'scale': 40.0, 'octaves': 4, 'persistence': 1.6, 'lacunarity': 1.9, 'threshold': 0.4},
        'elevation': {'top': 35, 'bottom': 90},
        'tile probs': {'stone': 35, 'dirt': 25, 'clay': 4, 'ice': 15, 'coal': 13, 'iron': 8},
        'liquid probs': {'water': 5},
        'tree probs': 20
    },
    
    'tundra': {
        'height map': {'scale': 450, 'octaves': 3, 'persistence': 1.2, 'lacunarity': 1.5},
        'cave map': {'scale': 70.0, 'octaves': 2, 'persistence': 0.6, 'lacunarity': 1.8, 'threshold': 0.35},
        'elevation': {'top': 90, 'bottom': 125},
        'tile probs': {'ice': 30, 'stone': 25, 'dirt': 15, 'tin': 2, 'coal': 11, 'copper': 6, 'iron': 11},
        'liquid probs': {'water': 5, 'oil': 7}
    }, 
    
    #'defiled': {
        #'height map': {'scale': 350, 'octaves': 4, 'persistence': 1.5, 'lacunarity': 2.0},
        #'cave map': {'scale': 60.0, 'octaves': 5, 'persistence': 1.8, 'lacunarity': 1.9, 'threshold': 0.45},
        #'elevation': {'top': 70, 'bottom': 110},
        #'tile probs': {'defiled stone': 35, 'dirt': 20, 'tin': 2, 'coal': 15, 'iron': 14, 'copper': 4},
        #'tiles at depth': {
            #0.1: ['defiled stone', 'dirt'],
            #0.2: ['defiled stone', 'dirt', 'tin'], 
            #0.3: ['defiled stone', 'dirt', 'tin', 'coal'], 
            #0.4: ['defiled stone', 'dirt', 'tin', 'coal', 'copper'],
            #0.5: ['defiled stone', 'dirt', 'tin', 'coal', 'copper', 'iron'],  
        #},
        #'liquid probs': {'oil': 9, 'lava': 6},
        #'tree probs': 20
    #},

    'underworld': {
        'height map': {'scale': 300, 'octaves': 6, 'persistence': 1.7, 'lacunarity': 2.0},
        'cave map': {'scale': 90.0, 'octaves': 6, 'persistence': 2.5, 'lacunarity': 2.4, 'threshold': 0.3},
        'elevation': {'top': 160, 'bottom': MAP_SIZE[1]},
        'tile probs': {'hellstone': 20, 'stone': 15, 'dirt': 5, 'coal': 15, 'copper': 15, 'iron': 15, 'obsidian': 15},
        'liquid probs': {'oil': 6, 'lava': 9},
    },  
}

BIOME_WIDTH = MAP_SIZE[0] // (len(BIOMES) - 1) # -1 since the underworld spans the entire map
TREE_BIOMES = ['forest', 'taiga']

WORLD_EDGE_RIGHT = (MAP_SIZE[0] * TILE_SIZE) - 19 # minus 19 to prevent going partially off-screen
WORLD_EDGE_BOTTOM = MAP_SIZE[1] * TILE_SIZE

GRAVITY = 1200

Z_LAYERS = {'clouds': 0, 'bg': 1, 'main': 2, 'player': 3}

TILES = {
    'dirt': {'hardness': 100, 'rgb': (82, 71, 69)},
    'ice': {'hardness': 200, 'rgb': (82, 71, 69)},
    'sand': {'hardness': 100, 'rgb': (214, 188, 150)},
    'clay': {'hardness': 150, 'rgb': (192, 136, 119)},
    'tin': {'ore': True, 'hardness': 200, 'rgb': (205, 206, 181)},
    'defiled stone': {'hardness': 250, 'rgb': (157, 157, 157)},
    'stone': {'hardness': 300, 'rgb': (100, 100, 100)},
    'desert fossil': {'hardness': 400, 'rgb': (173, 159, 139)},
    'coal': {'hardness': 450, 'rgb': (37, 40, 41)},
    'sandstone': {'hardness': 500, 'rgb': (162, 132, 88)},
    'silver': {'ore': True, 'hardness': 500, 'rgb': (208, 213, 215)},
    'copper': {'ore': True, 'hardness': 550, 'rgb': (158, 110, 61)},
    'gold': {'ore': True, 'hardness': 600, 'rgb': (211, 178, 79)},
    'iron': {'ore': True, 'hardness': 750, 'rgb': (146, 146, 146)},
    'hellstone': {'hardness': 950, 'rgb': (132, 34, 34)},
    'obsidian': {'hardness': 1000, 'rgb': (32, 23, 43)},
}

ramp_materials = ['dirt', 'sand', 'stone', 'ice']
RAMP_TILES = []
for m in ramp_materials:
    RAMP_TILES.append(f'{m} ramp right')
    RAMP_TILES.append(f'{m} ramp left')

TILE_REACH_RADIUS = 5
TILE_ORE_RATIO = 50 # amount of ore 1 tile is worth

# 'producers' specifies who/what can craft a given item
TOOLS = {
    'pickaxe': {
        'stone': {'recipe': {'wood': 2, 'stone': 6}, 'strength': 15, 'producers': {'player', 'workbench', 'anvil'}},
        'iron': {'recipe': {'wood': 2, 'iron bar': 4}, 'strength': 50, 'producers': {'player', 'workbench', 'anvil'}},
        'copper': {'recipe': {'wood': 2, 'copper bar': 4}, 'strength': 30, 'producers': {'player', 'workbench', 'anvil'}},
        'silver': {'recipe': {'wood': 2, 'silver bar': 4}, 'strength': 40, 'producers': {'player', 'workbench', 'anvil'}},
        'gold': {'recipe': {'wood': 2, 'gold bar': 4}, 'strength': 35, 'producers': {'player', 'workbench', 'anvil'}},
    },
    'axe': {
        'stone': {'recipe': {'wood': 3, 'stone': 4}, 'strength': 10, 'producers': {'player', 'workbench', 'anvil'}},
        'iron': {'recipe': {'wood': 3, 'iron bar': 2}, 'strength': 25, 'producers': {'player', 'workbench', 'anvil'}},
        'copper': {'recipe': {'wood': 3, 'stone': 2}, 'strength': 10, 'producers': {'player', 'workbench', 'anvil'}},
    },
    'sword': {
        'stone': {'recipe': {'stone': 12}, 'strength': 40, 'producers': {'player', 'workbench', 'anvil'}},
        'iron': {'recipe': {'iron bar': 9}, 'strength': 40, 'producers': {'player', 'workbench', 'anvil'}},
        'copper': {'recipe': {'copper bar': 9}, 'strength': 25, 'producers': {'player', 'workbench', 'anvil'}},
    },
    'torch': {
        'wood': {'recipe': {'wood': 1}, 'producers': {'player', 'workbench'}}
    },
    'chainsaw': {},
    'bow': {},
    'arrow': {},
    'pistol': {},
    'shotgun': {},
    'bomb': {},
    'dynamite': {}
}

MACHINES = {
    'burner furnace': {'recipe': {'stone': 7, 'wood torch': 1}, 'rgb': (47, 15, 15)}, 
    'electric furnace': {'recipe': {'iron plate': 7, 'circuit': 4}, 'rgb': (49, 63, 71)},
    'steel furnace': {'recipe': {'steel': 7, 'circuit': 4}, 'rgb': (84, 84, 84)},
    'burner drill': {'recipe': {'iron plate': 7, 'iron gear': 5, 'burner furnace': 1}, 'rgb': (137, 126, 126),},
    'electric drill': {'recipe': {'iron plate': 7, 'circuit': 5, 'electric furnace': 1}, 'rgb': (111, 122, 112),},
    'burner inserter': {'recipe': {'iron plate': 5, 'iron gear': 3, 'wood torch': 1}, 'rgb': (47, 29, 29),}, 
    'electric inserter': {'recipe': {'iron plate': 5, 'circuit': 3}, 'rgb': (118, 107, 107),}, 
    'assembler': {'recipe': {'iron plate': 10, 'iron gear': 5, 'circuit': 4}, 'rgb': (80, 74, 73),},
    'boiler': {'recipe': {'iron plate': 8, 'pipe': 4, 'burner furnace': 1}, 'rgb': (38, 33, 31),}, 
    'steam engine': {'recipe': {'iron plate': 12, 'pipe': 7}, 'rgb': (59, 35, 27),},
}

LOGISTICS = {
    'inlet pump': {'recipe': {'iron plate': 6, 'iron gear': 3, 'pipe': 4}, 'rgb': (87, 95, 104),},
    'outlet pump': {'recipe': {'iron plate': 6, 'iron gear': 3, 'pipe': 4}, 'rgb': (87, 95, 104),},
    'pipe': {'recipe': {'iron plate': 3}, 'rgb': (72, 92, 93),}, 
    
}
PIPE_TRANSPORT_DIRECTIONS = [(0, 1), (1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]

ELECTRICITY = {
    'electric pole': {'recipe': {'wood': 10, 'circuit': 2}, 'rgb': (90, 71, 64),}, 
    'solar panel': {'recipe': {'copper plate': 4, 'glass': 4, 'circuit': 13}, 'rgb': (20, 52, 77),},
}

MATERIALS = {
    'wood': {'recipe': None},
    'iron gear': {'recipe': {'iron plate': 2}},
    'iron plate': {'recipe': {'iron ore': 3}}, 
    'iron rod': {'recipe': {'iron plate': 2}}, 
    'copper cable': {'recipe': {'copper plate': 1}},
    'copper plate': {'recipe': {'copper ore': 3}},
    'circuit': {'recipe': {'copper cable': 1, 'iron plate': 1}}, 
    'steel plate': {'recipe': {'iron plate': 7}}, 
    'glass': {'recipe': {'sand': 6}},
}

STORAGE = {
    'chest': {
        'materials': {
            'wood': {
                'recipe': {'wood': 10}, 
                'capacity': 500,
                'rgb': (63, 54, 52)
            }, 
            'iron': {
                'recipe': {'iron plate': 10},
                'capacity': 1500,
                'rgb': (71, 70, 69)
            },
        },
    },
}

RESEARCH = {
    'lab': {'recipe': {'glass': 8, 'iron rod': 6, 'circuit': 9, 'belt': 4}, 'rgb': (139, 154, 167)},
    'automation science': {'recipe': {'circuit:': 1, 'gear': 1, 'glass': 1}},
    'logistic science': {'recipe': {'electric inserter': 1, 'belt': 1, 'glass': 1}},
}

DECOR = {
    'walls': {'materials': ['wood', 'stone', 'iron', 'copper', 'silver', 'gold']},
    'doors': {'materials': ['wood', 'glass', 'stone', 'iron']},
    'tables': {'materials': ['wood', 'glass', 'sandstone', 'ice']},
    'chairs': {'materials': ['wood', 'glass', 'ice']},
}

PLACEABLE_ITEMS = [
    *TILES, *MACHINES, *[l for l in LOGISTICS if l != 'pipe'], *[f'pipe {i}' for i in range(len(PIPE_TRANSPORT_DIRECTIONS))], 
    *[f'{m} chest' for m in STORAGE['chest']['materials']], 'glass', 'lab'
]

OBJ_ITEMS = [item for item in PLACEABLE_ITEMS if item not in {*TILES, 'glass'}] # has a class to instantiate after placement

FOOD = {
    'fruits': [
        'apple', 'orange', 'banana', 'cherry', 'grapes', 'coconut', 'grapefruit', 'lemon', 
        'mango', 'peach', 'plum', 'pineapple', 'pomegranate', 'starfruit', 'fruit salad'
    ],
    'fish': ['salmon', 'tuna', 'trout'],
    'roasts': ['roasted bird', 'roasted duck'],  
    'desserts': ['apple pie', 'pumpkin pie', 'banana split', 'cookie', 'ice cream'],
}

DRINKS = ['apple juice', 'grape juice', 'soda', 'beer', 'milkshake']

POTIONS = ['invisibility', 'night vision', 'health regeneration', 'gravity reversal']