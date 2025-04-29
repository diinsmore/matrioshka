import pygame as pg
from os import walk
from os.path import join

from settings import BIOMES, TILES

class AssetManager:
    def __init__(self, tile_id_map: dict[str, dict[str, any]]):
        self.assets = {
            'graphics': {
                'clouds': self.load_folder(join('..', 'graphics', 'weather', 'clouds')),
                'walls': self.load_folder(join('..', 'graphics',  'backgrounds', 'walls')),
            },
        
            'fonts': {
                'default': pg.font.Font(join('..', 'graphics', 'fonts', 'Good Old DOS.ttf')),
                'label': pg.font.Font(join('..', 'graphics', 'fonts', 'Good Old DOS.ttf'), size = 15),
                'number': pg.font.Font(join('..', 'graphics', 'fonts', 'MinecraftStandardBold.otf'), size = 10)
            },
        
            'colors': {
                'inv label': 'mistyrose4',
                'inv bg': 'lightsteelblue4'
            }
        }
        self.tile_id_map = tile_id_map
        self.load_biome_graphics()
        self.load_tile_graphics(self.tile_id_map)

    @staticmethod
    def load_image(dir_path: str) -> pg.Surface:
        return pg.image.load(dir_path).convert_alpha()

    def load_folder(self, dir_path: str) -> dict[str, pg.Surface]:
        images = {}
        for path, _, files in walk(dir_path):    
            for file_name in files:
                key = file_name.split('.')[0] # not reassigning 'file_name' because it needs the file extension when passed to load_image()
                images[int(key) if key.isnumeric() else key] = self.load_image(join(path, file_name))

        return images
 
    def load_subfolders(self, dir_path: str) -> dict[str, dict[str, pg.Surface]]:
        '''load folders stored in a given parent folder'''
        images = {}
        for _, subfolders, __ in walk(dir_path):
            for folder in subfolders:
                path = join(dir_path, folder)
                images[folder] = self.load_folder(path)
                
        return images

    def load_frames(self, dir_path: str) -> list[pg.Surface]:
        '''load the individual frames of an animation (numeric file names)'''
        frames = []
        # remove the file extension to sort from 0 to n
        for path, _, files in walk(dir_path):   
            for file in sorted(files, key = lambda name: int(name.split('.')[0])): 
                frames.append(self.load_image(join(path, file)))

    def load_biome_graphics(self) -> None:
        for biome in BIOMES:
            self.assets['graphics'][biome] = {
                'landscape': self.load_image(join('..', 'graphics', 'backgrounds', f'{biome} landscape.png')), 
                'underground': self.load_image(join('..', 'graphics', 'backgrounds', f'{biome} underground.png'))
            }
            
            if biome in ('forest', 'taiga', 'desert'):
                self.assets['graphics'][biome]['trees'] = self.load_image(join('..', 'graphics', 'terrain', 'trees', f'{biome} tree.png'))

    def load_tile_graphics(self, tile_id_map) -> None:
        for tile in TILES.keys():
            if tile != 'air':
                self.assets['graphics'][tile] = self.load_image(join('..', 'graphics', 'terrain', 'tiles', f'{tile}.png'))