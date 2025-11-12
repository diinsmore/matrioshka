import pygame as pg
from os.path import join

from settings import BIOMES, TREE_BIOMES, TILES, RAMP_TILES, TOOLS, MACHINES, LOGISTICS, MATERIALS, TRANSPORT_DIRS, TILE_SIZE
from helper_functions import load_image, load_folder, load_subfolders, load_frames

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
                'transport dirs': load_folder(join('..', 'graphics', 'ui', 'transport dirs'))
            },
        
            'fonts': {
                'default': pg.font.Font(join('..', 'graphics', 'fonts', 'Good Old DOS.ttf')),
                'craft menu category': pg.font.Font(join('..', 'graphics', 'fonts', 'C&C.ttf'), size=14),
                'item label': pg.font.Font(join('..', 'graphics', 'fonts', 'C&C.ttf'), size=16),
                'item label small': pg.font.Font(join('..', 'graphics', 'fonts', 'C&C.ttf'), size=13),
                'number': pg.font.Font(join('..', 'graphics', 'fonts', 'PKMN RBYGSC.ttf'), size=8)
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
            self.graphics[tile] = load_image(join('..', 'graphics', 'terrain', 'tiles', f'{tile}.png'))
        
        for tile in RAMP_TILES:
            self.graphics[tile] = load_image(join('..', 'graphics', 'terrain', 'tiles', 'ramps', f'{tile}.png'))

    def load_tool_graphics(self) -> None:
        for tool in TOOLS.keys():
            self.graphics[tool] = load_folder(join('..', 'graphics', 'tools', f'{tool}' + ('s' if tool != 'torch' else 'es')))
            for tool_type in self.graphics[tool]:
                self.graphics[tool_type] = self.graphics[tool][tool_type]

    def load_machine_graphics(self) -> None:
        self.graphics['machines'] = {}
        for name in MACHINES:
            if name in {'assembler', 'boiler', 'steam engine'}: # not stored in a folder of related graphics:
                self.graphics[name] = load_image(join('..', 'graphics', 'machines', f'{name}.png'))
            else:
                category = name.split()[-1] + 's'
                if category not in self.graphics['machines'].keys():
                    self.graphics['machines'][category] = load_folder(join('..', 'graphics', 'machines', category))
                self.graphics[name] = self.graphics['machines'][category][name]
            
    def load_logistics_graphics(self) -> None:
        self.graphics['logistics'] = {}
        for name in LOGISTICS:
            category = name.split()[-1] + 's'
            if category not in self.graphics['logistics'].keys():
                self.graphics['logistics'][category] = load_folder(join('..', 'graphics', 'logistics', category))
            if category != 'pipes':
                self.graphics[name] = self.graphics['logistics'][category][name]
            else:
                for i in range(len(TRANSPORT_DIRS)):
                    self.graphics[f'pipe {i}'] = self.graphics['logistics']['pipes'][f'pipe {i}']
                    self.graphics[f'pipe {i}'].set_colorkey(self.graphics[f'pipe {i}'].get_at((0, 0))) # not sure why the pipes are the only graphics convert_alpha() isn't working on...

    def load_material_graphics(self) -> None:
        for material in MATERIALS.keys():
            try:
                self.graphics[material] = load_image(join('..', 'graphics', 'materials', f'{material}.png'))
            except FileNotFoundError:
                pass

    def load_ui_graphics(self) -> None:
        self.graphics['transport dirs'] = load_folder(join('..', 'graphics', 'ui', 'transport directions'))
        for surf in self.graphics['transport dirs'].values():
            surf.set_alpha(100)
                
    def load_remaining_graphics(self) -> None:
        self.load_biome_graphics()
        self.load_tile_graphics()
        self.load_tool_graphics()
        self.load_machine_graphics()
        self.load_logistics_graphics()
        self.load_material_graphics()
        self.load_ui_graphics()