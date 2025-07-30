import pygame as pg

from settings import BIOMES, TREE_BIOMES, TILES, RAMP_TILES, TOOLS, MACHINES
from file_import_functions import *

class AssetManager:
    def __init__(self):
        self.assets = {
            'graphics': {
                'clouds': load_folder(join('..', 'graphics', 'weather', 'clouds')),
                'materials': load_folder(join('..', 'graphics', 'materials')),
                'icons': load_folder(join('..', 'graphics', 'ui', 'icons')),
                'research': load_folder(join('..', 'graphics', 'research')),
                'storage': load_folder(join('..', 'graphics', 'storage')),
                'ramps': load_folder(join('..', 'graphics', 'terrain', 'tiles', 'ramps')),
                'consumables': load_subfolders(join('..', 'graphics', 'consumables')),
                'minerals': load_subfolders(join('..', 'graphics', 'minerals')),
                'decor': load_subfolders(join('..', 'graphics', 'decor'))
            },
        
            'fonts': {
                'default': pg.font.Font(join('..', 'graphics', 'fonts', 'Good Old DOS.ttf')),
                'craft menu category': pg.font.Font(join('..', 'graphics', 'fonts', 'C&C.ttf'), size = 14),
                'item label': pg.font.Font(join('..', 'graphics', 'fonts', 'C&C.ttf'), size = 16),
                'number': pg.font.Font(join('..', 'graphics', 'fonts', 'PKMN RBYGSC.ttf'), size = 8)
            },
        
            'colors': {
                'outline bg': 'gray18',
                'text': 'ivory4'
            }, 
        }
        
        self.load_remaining_graphics()

    def load_biome_graphics(self) -> None:
        for biome in BIOMES:
            self.assets['graphics'][biome] = {
                'landscape': load_folder(join('..', 'graphics', 'backgrounds', biome, 'landscape')), 
                'underground': load_folder(join('..', 'graphics', 'backgrounds', biome, 'underground'))
            }
            if biome in TREE_BIOMES:
                self.assets['graphics'][biome]['trees'] = load_folder(join('..', 'graphics', 'terrain', 'trees', biome))

    def load_tile_graphics(self) -> None:
        for tile in TILES.keys():
            self.assets['graphics'][tile] = load_image(join('..', 'graphics', 'terrain', 'tiles', f'{tile}.png'))

        for tile in RAMP_TILES:
            for direction in ('right', 'left'):
                self.assets['graphics'][f'{tile} ramp {direction}'] = load_image(
                    join('..', 'graphics', 'terrain', 'tiles', 'ramps', f'{tile} ramp {direction}.png')
                )

    def load_tool_graphics(self) -> None:
        for tool in TOOLS.keys():
            self.assets['graphics'][tool] = load_folder(join('..', 'graphics', 'tools', f'{tool}s'))

    def load_machine_graphics(self) -> None:
        no_category = {'assembler', 'boiler', 'steam engine', 'electric pole', 'solar panel', 'belt'} # not stored in a folder of related graphics
        for machine in MACHINES:
            if machine in no_category:
                self.assets['graphics'][machine] = load_image(join('..', 'graphics', 'machines', f'{machine}.png'))
            else:
                category = machine.split()[-1] + 's'
                if category not in self.assets['graphics'].keys():
                    self.assets['graphics'][category] = load_folder(join('..', 'graphics', 'machines', category))
                self.assets['graphics'][machine] = self.assets['graphics'][category][machine]

    def load_remaining_graphics(self) -> None:
        self.load_biome_graphics()
        self.load_tile_graphics()
        self.load_tool_graphics()
        self.load_machine_graphics()