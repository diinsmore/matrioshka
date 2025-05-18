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
        'stone': {'recipe': {'wood': 2, 'stone': 6}, 'strength': 15, 'producers': {'player', 'workbench', 'anvil'}},
        'iron': {'recipe': {'wood': 2, 'iron bar': 4}, 'strength': 50, 'producers': {'player', 'workbench', 'anvil'}},
        'copper': {'recipe': {'wood': 2, 'copper bar': 4}, 'strength': 30, 'producers': {'player', 'workbench', 'anvil'}},
        'silver': {'recipe': {'wood': 2, 'silver bar': 4}, 'strength': 40, 'producers': {'player', 'workbench', 'anvil'}},
        'gold': {'recipe': {'wood': 2, 'gold bar': 4}, 'strength': 35, 'producers': {'player', 'workbench', 'anvil'}},
    },
    'axe': {
        'stone': {'recipe': {'wood': 3, 'stone': 4}, 'strength': 10, 'producers': {'player', 'workbench', 'anvil'}},
        'iron': {'recipe': {'wood': 3, 'iron bar': 2}, 'strength': 40, 'producers': {'player', 'workbench', 'anvil'}},
        'copper': {'recipe': {'wood': 3, 'stone': 2}, 'strength': 25, 'producers': {'player', 'workbench', 'anvil'}},
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

MACHINES = [
    'burner furnace', 'electric furnace',
    'belt', 'burner drill', 'electric drill', 'inserter', 'assembler', 'printing press',
    'electric pole', 'electric grid', 'boiler', 'steam engine', 'pump', 'solar panel',
    'belt', 'pipes' # TODO: add trains or maybe minecarts with similar functionality?
]

MATERIALS = [
    'iron gear', 'circuit', 'copper cable', 
    'copper plate', 'steel plate', 'iron rod', 'glass', 
    'copper bar', 'iron bar', 'silver bar', 'gold bar'
]

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
    'chest': {'materials': ['wood', 'glass', 'stone', 'iron']},
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