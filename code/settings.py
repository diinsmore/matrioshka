RES = (1280, 720)
FPS = 60

TILE_SIZE = 16
CHUNK_SIZE = 24
CELL_SIZE = 10
# TODO: any value larger on the x-axis will cause a glitch where the physics engine doesn't detect the player's initial contact with the ground in time and ends up spawning in a cave
MAP_SIZE = (1590, 200) 

BIOMES = {
    'highlands': {
        'height map': {'scale': 325, 'octaves': 5, 'persistence': 1.6, 'lacunarity': 2.1},
        'cave map': {'scale': 30.0, 'octaves': 5, 'persistence': 2.0, 'lacunarity': 2.3, 'threshold': 0.4},
        'elevation': {'top': 0, 'bottom': 70}, 
        'tile probs': {'obsidian': 2, 'coal': 5, 'copper': 7, 'iron': 8, 'silver': 8, 'gold': 5},
        'liquid probs': {'water': 3, 'lava': 5},
    }, 

    'desert': {
        'height map': {'scale': 400, 'octaves': 4, 'persistence': 0.9, 'lacunarity': 1.4},
        'cave map': {'scale': 60.0, 'octaves': 3, 'persistence': 0.7, 'lacunarity': 0.9, 'threshold': 0.6},
        'elevation': {'top': 50, 'bottom': 90},
        'tile probs': {'coal': 3, 'copper': 7, 'iron': 6, 'silver': 6, 'gold': 2},
        'liquid probs': {'oil': 7, 'lava': 5},
        
    },
    
    'forest': {
        'height map': {'scale': 400, 'octaves': 3, 'persistence': 1.2, 'lacunarity': 2.0},
        'cave map': {'scale': 30.0, 'octaves': 4, 'persistence': 1.6, 'lacunarity': 1.3, 'threshold': 0.55},
        'elevation': {'top': 70, 'bottom': 110},
        'tile probs': {'coal': 7, 'copper': 4, 'iron': 5, 'silver': 3, 'gold': 3},
        'liquid probs': {'water': 7, 'lava': 2},
        'tree coverage': 40
    },
    
    'taiga': {
        'height map': {'scale': 400, 'octaves': 4, 'persistence': 1.3, 'lacunarity': 1.6},
        'cave map': {'scale': 40.0, 'octaves': 4, 'persistence': 1.6, 'lacunarity': 1.9, 'threshold': 0.4},
        'elevation': {'top': 35, 'bottom': 90},
        'tile probs': {'coal': 5, 'copper': 3, 'iron': 6, 'silver': 5, 'gold': 4},
        'liquid probs': {'water': 5, 'lava': 1},
        'tree coverage': 30
    },
    
    'tundra': {
        'height map': {'scale': 450, 'octaves': 3, 'persistence': 1.2, 'lacunarity': 1.5},
        'cave map': {'scale': 70.0, 'octaves': 2, 'persistence': 0.6, 'lacunarity': 1.8, 'threshold': 0.35},
        'elevation': {'top': 90, 'bottom': 125},
        'tile probs': {'coal': 4, 'copper': 6, 'iron': 5, 'silver': 6, 'gold': 3},
        'liquid probs': {'water': 5, 'oil': 7},
    }, 

    'underworld': {
        'height map': {'scale': 300, 'octaves': 6, 'persistence': 1.7, 'lacunarity': 2.0},
        'cave map': {'scale': 90.0, 'octaves': 6, 'persistence': 2.5, 'lacunarity': 2.4, 'threshold': 0.3},
        'elevation': {'top': 160, 'bottom': MAP_SIZE[1]},
        'tile probs': {'hellstone': 7, 'obsidian': 6, 'coal': 8, 'copper': 8, 'iron': 8, 'silver': 5, 'gold': 4},
        'liquid probs': {'oil': 6, 'lava': 9},
    },
}

BIOME_WIDTH = MAP_SIZE[0] // (len(BIOMES) - 1) # -1 since the underworld spans the entire map

WORLD_EDGE_RIGHT = (MAP_SIZE[0] * TILE_SIZE) - 19 # minus 19 to prevent going partially off-screen
WORLD_EDGE_BOTTOM = MAP_SIZE[1] * TILE_SIZE
GRAVITY = 1200

Z_LAYERS = {
    'clouds': 0,
    'bg': 1,
    'main': 2,
    'player': 3,
}

TILES = {
    'air': {'hardness': 0},
    'dirt': {'hardness': 100},
    'stone': {'hardness': 400},
    'sandstone': {'hardness': 500}, 
    'ice': {'hardness': 200},
    'coal': {'hardness': 450},
    'obsidian': {'hardness': 1000},
    'hellstone': {'hardness': 900},
    'copper': {'ore': True, 'hardness': 350},
    'iron': {'ore': True, 'hardness': 750},
    'silver': {'ore': True, 'hardness': 550},
    'gold': {'ore': True, 'hardness': 600},
}

TILE_REACH_RADIUS = 5

# ordered from left-right
# since pygame's coordinate system starts in the topleft, higher elevation values = lower in the world
# TODO: the highlands & tundra noise parameters are especially in need of fine-tuning


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
    'chainsaw': {},
    'bow': {},
    'arrow': {},
    'pistol': {},
    'shotgun': {},
    'bomb': {},
    'dynamite': {}
}

MACHINES = {
    'burner furnace': {'recipe': {'stone': 7, 'wood': 2, 'torch': 1}}, 'electric furnace': {},
    'burner drill': {}, 'electric drill': {}, 'inserter': {}, 'assembler': {},
    'electric pole': {}, 'electric grid': {}, 'boiler': {}, 'steam engine': {}, 'pump': {}, 'solar panel': {},
    'belt': {}, 'pipes': {},  # TODO: add trains or maybe minecarts with similar functionality?
}

MATERIALS = {
    'iron gear': {}, 'circuit': {}, 'copper cable': {},
    'copper plate': {}, 'steel plate': {}, 'iron rod': {}, 'glass': {},
    'copper bar': {}, 'iron bar': {}, 'silver bar': {}, 'gold bar': {},
}

STORAGE = {
    'chest': {'materials': {'wood': {'capacity': 500}, 'iron': {'capacity': 1500}}},
    'accumulator': {},
}

RESEARCH = {
    'lab': {},
    'core': {}
}

DECOR = {
    'walls': {'materials': ['wood', 'stone', 'iron', 'copper', 'silver', 'gold']},
    'doors': {'materials': ['wood', 'glass', 'stone', 'iron']},
    'tables': {'materials': ['wood', 'glass', 'sandstone', 'ice']},
    'chairs': {'materials': ['wood', 'glass', 'ice']},
}

# TODO: everything below is unfinished
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