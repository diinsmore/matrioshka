RES = (1280, 720)
FPS = 60

MAP_SIZE = (2500, 400) 
BIOME_WIDTH = 500

TILE_SIZE = 16
CHUNK_SIZE = 24
CELL_SIZE = 10

Z_LAYERS = {
    'clouds': 0,
    'bg': 1,
    'main': 2,
    'player': 3,
}

TILES = {
    'air': {'hardness': 0},
    'dirt': {'hardness': 10},
    'stone': {'hardness': 45},
    'sandstone': {'hardness': 30}, 
    'ice': {'hardness': 20},
    'coal': {'hardness': 50}, 
    'obsidian': {'hardness': 100},
    'hellstone': {'hardness': 90},
    'copper': {'ore': True, 'hardness': 35},
    'iron': {'ore': True, 'hardness': 75},
    'silver': {'ore': True, 'hardness': 55},
    'gold': {'ore': True, 'hardness': 60},
}

# ordered from left-right
# since pygame's coordinate system starts in the topleft, higher elevation values = lower in the world
# TODO: the highlands & tundra noise parameters are especially in need of fine-tuning
BIOMES = {
    'highlands': {
        'noise params': {'scale': 325, 'octaves': 5, 'persistence': 1.6, 'lacunarity': 2.1},
        'elevation': {'top': 30, 'bottom': 130}, 
        'tile probs': {'obsidian': 2, 'coal': 5, 'copper': 7, 'iron': 8, 'silver': 8, 'gold': 5},
        'liquid probs': {'water': 3, 'lava': 5}  
    }, 

    'desert': {
        'noise params': {'scale': 400, 'octaves': 4, 'persistence': 0.9, 'lacunarity': 1.4},
        'elevation': {'top': 130, 'bottom': 180},
        'tile probs': {'coal': 3, 'copper': 7, 'iron': 6, 'silver': 6, 'gold': 2},
        'liquid probs': {'oil': 7, 'lava': 5},
    },
    
    'forest': {
        'noise params': {'scale': 450, 'octaves': 3, 'persistence': 1.2, 'lacunarity': 2.0},
        'elevation': {'top': 150, 'bottom': 190},
        'tile probs': {'coal': 7, 'copper': 4, 'iron': 5, 'silver': 3, 'gold': 3},
        'liquid probs': {'water': 7, 'lava': 2}  
    },
    
    'taiga': {
        'noise params': {'scale': 400, 'octaves': 4, 'persistence': 1.3, 'lacunarity': 1.6},
        'elevation': {'top': 110, 'bottom': 160},
        'tile probs': {'coal': 5, 'copper': 3, 'iron': 6, 'silver': 5, 'gold': 4},
        'liquid probs': {'water': 5, 'lava': 1}  
    },
    
    'tundra': {
        'noise params': {'scale': 500, 'octaves': 3, 'persistence': 0.8, 'lacunarity': 1.3},
        'elevation': {'top': 170, 'bottom': 200},
        'tile probs': {'coal': 4, 'copper': 6, 'iron': 5, 'silver': 6, 'gold': 3},
        'liquid probs': {'water': 5, 'oil': 7} 
    }, 

    'underworld': {
        'noise params': {'scale': 300, 'octaves': 6, 'persistence': 1.7, 'lacunarity': 2.0},
        'elevation': {'top': 400, 'bottom': MAP_SIZE[1]},
        'tile probs': {'hellstone': 7, 'obsidian': 6, 'coal': 8, 'copper': 8, 'iron': 8, 'silver': 5, 'gold': 4},
        'liquid probs': {'oil': 6, 'lava': 9} 
    },
}

# 'producers' specifies who/what can craft a given item
TOOLS = {
    'pickaxe': {
        'stone': {'recipe': {'wood': 2, 'stone': 2}, 'strength': 5, 'producers': {'player', 'workbench', 'anvil', 'assembler'}},
        'iron': {'recipe': {'wood': 2, 'iron bar': 2}, 'strength': 25, 'producers': {'player', 'workbench', 'anvil', 'assembler'}},
        'copper': {'recipe': {'wood': 2, 'copper bar': 2}, 'strength': 10, 'producers': {'player', 'workbench', 'anvil', 'assembler'}},
        'silver': {'recipe': {'wood': 2, 'silver bar': 2}, 'strength': 15, 'producers': {'player', 'workbench', 'anvil', 'assembler'}},
        'gold': {'recipe': {'wood': 2, 'gold bar': 2}, 'strength': 20, 'producers': {'player', 'workbench', 'anvil', 'assembler'}},
    }
}