import pygame as pg

from settings import BIOMES, TILES, TOOLS, MACHINES
from file_import_functions import *

class AssetManager:
    def __init__(self):
        self.assets = {
            'graphics': {
                'clouds': load_folder(join('..', 'graphics', 'weather', 'clouds')),
                'minerals': load_subfolders(join('..', 'graphics', 'minerals')),
                'decor': load_subfolders(join('..', 'graphics', 'decor')),
                'research': load_folder(join('..', 'graphics', 'research')),
                'storage': load_folder(join('..', 'graphics', 'storage')),
                'consumables': load_subfolders(join('..', 'graphics', 'consumables'))
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
                'landscape': load_image(join('..', 'graphics', 'backgrounds', f'{biome} landscape.png')), 
                'underground': load_image(join('..', 'graphics', 'backgrounds', f'{biome} underground.png'))
            }
            
            if biome in ('forest', 'taiga', 'desert'):
                self.assets['graphics'][biome]['trees'] = load_folder(join('..', 'graphics', 'terrain', 'trees', biome))

    def load_tile_graphics(self) -> None:
        for tile in TILES.keys():
            if tile != 'air':
                self.assets['graphics'][tile] = load_image(join('..', 'graphics', 'terrain', 'tiles', f'{tile}.png'))

    def load_tool_graphics(self) -> None:
        for tool in TOOLS.keys():
            self.assets['graphics'][tool] = load_folder(join('..', 'graphics', 'tools', f'{tool}s'))

    def load_machine_graphics(self) -> None:
        animated = {'assembler', 'belt', 'inserter'}
        for machine in MACHINES:
            if machine in animated: 
                self.assets['graphics'][machine] = load_folder(join('..', 'graphics', 'machinery', machine))
            else:
                if machine in {'steam engine', 'burner furnace', 'burner drill', 'electric drill', 'inserter'}: # don't have the others yet
                    self.assets['graphics'][machine] = load_image(join('..', 'graphics', 'machinery', f'{machine}.png'))

    def load_remaining_graphics(self) -> None:
        self.load_biome_graphics()
        self.load_tile_graphics()
        self.load_tool_graphics()
        self.load_machine_graphics()