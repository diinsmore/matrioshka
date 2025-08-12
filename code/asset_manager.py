import pygame as pg

from settings import BIOMES, TREE_BIOMES, TILES, RAMP_TILES, TOOLS, MACHINES, MATERIALS
from file_import_functions import *

import pygame as pg

from settings import BIOMES, TREE_BIOMES, TILES, RAMP_TILES, TOOLS, MACHINES
from file_import_functions import *

class AssetManager:
    def __init__(self):
        self.assets = {
            'graphics': {
                'clouds': load_folder(join('..', 'graphics', 'weather', 'clouds')),
                'consumables': load_subfolders(join('..', 'graphics', 'consumables')),
                'decor': load_subfolders(join('..', 'graphics', 'decor')),
                'icons': load_folder(join('..', 'graphics', 'ui', 'icons')),
                'minerals': load_subfolders(join('..', 'graphics', 'minerals')),
                'ramps': load_folder(join('..', 'graphics', 'terrain', 'tiles', 'ramps')),
                'research': load_folder(join('..', 'graphics', 'research')),
                'storage': load_folder(join('..', 'graphics', 'storage')),
                'tools': load_folder(join('..', 'graphics', 'tools')),
                'ui': load_folder(join('..', 'graphics', 'ui')),
            },
        
            'fonts': {
                'default': pg.font.Font(join('..', 'graphics', 'fonts', 'Good Old DOS.ttf')),
                'craft menu category': pg.font.Font(join('..', 'graphics', 'fonts', 'C&C.ttf'), size = 14),
                'item label': pg.font.Font(join('..', 'graphics', 'fonts', 'C&C.ttf'), size = 16),
                'number': pg.font.Font(join('..', 'graphics', 'fonts', 'PKMN RBYGSC.ttf'), size = 8)
            },
        
            'colors': {
                'outline bg': 'gray18',
                'text': 'ivory4',
                'ui bg highlight': 'gray4'
            }, 
        }

        self.graphics = self.assets['graphics']
        self.load_remaining_graphics()

    def load_biome_graphics(self) -> None:
        for biome in BIOMES:
            self.graphics[biome] = {
                'landscape': load_folder(join('..', 'graphics', 'backgrounds', biome, 'landscape')), 
                'underground': load_folder(join('..', 'graphics', 'backgrounds', biome, 'underground'))
            }
            if biome in TREE_BIOMES:
                self.graphics[biome]['trees'] = load_folder(join('..', 'graphics', 'terrain', 'trees', biome))

    def load_tile_graphics(self) -> None:
        for tile in TILES.keys():
            self.graphics[tile] = load_image(join('..', 'graphics', 'terrain', 'tiles', f'{tile}.png') )
        
        for tile in RAMP_TILES:
            for direction in ('right', 'left'):
                self.graphics[f'{tile} ramp {direction}'] = load_image(
                    join('..', 'graphics', 'terrain', 'tiles', 'ramps', f'{tile} ramp {direction}.png')
                )

    def load_tool_graphics(self) -> None:
        for tool in TOOLS.keys():
            self.graphics[tool] = load_folder(join('..', 'graphics', 'tools', f'{tool}' + ('s' if tool != 'torch' else 'es')))
            for tool_type in self.graphics[tool]:
                self.graphics[tool_type] = self.graphics[tool][tool_type]

    def load_machine_graphics(self) -> None:
        self.graphics['machines'] = {}
        no_category = {'assembler', 'boiler', 'steam engine', 'electric pole', 'solar panel', 'belt'} # not stored in a folder of related graphics
        for machine in MACHINES:
            if machine in no_category:
                self.graphics[machine] = load_image(join('..', 'graphics', 'machines', f'{machine}.png'))
            else:
                category = machine.split()[-1] + 's'
                if category not in self.graphics['machines'].keys():
                    self.graphics['machines'][category] = load_folder(join('..', 'graphics', 'machines', category))
                self.graphics[machine] = self.graphics['machines'][category][machine]

    def load_material_graphics(self) -> None:
            for material in MATERIALS.keys():
                try:
                    self.graphics[material] = load_image(join('..', 'graphics', 'materials', f'{material}.png'))
                except FileNotFoundError:
                    pass

    def load_remaining_graphics(self) -> None:
        self.load_biome_graphics()
        self.load_tile_graphics()
        self.load_tool_graphics()
        self.load_machine_graphics()
        self.load_material_graphics()