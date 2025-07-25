import pygame as pg
import numpy as np

from settings import MAP_SIZE, TILE_SIZE

class MiniMap:
    def __init__(
        self, 
        screen: pg.Surface,
        camera_offset: pg.Vector2,
        tile_map: np.ndarray, 
        tile_IDs: dict[str, int],
        tile_IDs_to_names: dict[int, str], 
        make_outline: callable,
        get_tile_material: callable
    ):
        self.screen = screen
        self.camera_offset = camera_offset
        self.tile_map = tile_map
        self.tile_IDs = tile_IDs
        self.tile_IDs_to_names = tile_IDs_to_names
        self.make_outline = make_outline
        self.get_tile_material = get_tile_material
        
        self.visited_tiles = np.full(MAP_SIZE, False, dtype = bool)
        
        self.tiles_x, self.tiles_y = 100, 100
        self.tile_px_w, self.tile_px_h = 2, 2
        self.outline_w = self.tiles_x * self.tile_px_w
        self.outline_h = self.tiles_y * self.tile_px_h
        self.padding = 5
        self.render = True
        
        self.border_dist_x = self.tiles_x // 2
        self.border_dist_y = self.tiles_y // 2

        self.RGBs = {
            'dirt': (82, 71, 69),
            'ice': (137, 204, 234),
            'sand': (214, 188, 150),
            'clay': (192, 136, 119),
            'tin': (205, 206, 181),
            'defiled stone': (157, 157, 157),
            'stone': (100, 100, 100),
            'desert fossil': (173, 159, 139),
            'coal': (37, 40, 41),
            'sandstone': (162, 132, 88),
            'silver': (208, 213, 215),
            'copper': (158, 110, 61),
            'gold': (211, 178, 79),
            'iron': (146, 146, 146),
            'hellstone': (132, 34, 34),
            'obsidian': (32, 23, 43)
        }

        self.non_tiles = {'air', 'tree base'}

    def render_outline(self) -> None:
        if self.render:
            base_rect = pg.Rect(self.padding, self.padding, self.outline_w, self.outline_h)
            outline1 = self.make_outline(base_rect, draw = False, return_outline = True)
            outline2 = self.make_outline(outline1, draw = True)
            pg.draw.rect(self.screen, 'black', outline1, 1)

    def render_tiles(self) -> None:
        tiles = self.get_map_slice()
        rows, cols = tiles.shape
        for x in range(rows):
            for y in range(cols):
                image = pg.Surface((self.tile_px_w, self.tile_px_h))
                tile_ID = tiles[x, y]
                tile_name = self.tile_IDs_to_names[tile_ID]
                if tile_name in self.non_tiles:
                    tile_color = (178, 211, 236) if tile_name == 'air' else 'black'
                else:
                    tile_color = self.RGBs[self.get_tile_material(tile_ID)]
                image.fill(tile_color)
                rect = image.get_rect(topleft = pg.Vector2(self.padding, self.padding) + (x * self.tile_px_w, y * self.tile_px_h))
                self.screen.blit(image, rect)

    def get_map_slice(self) -> np.ndarray:
        tile_offset = self.camera_offset // TILE_SIZE
        left_edge = max(0, int(tile_offset.x - self.border_dist_x))
        right_edge = min(self.tile_map.shape[0], int(tile_offset.x + self.border_dist_x))
        top_edge = max(0, int(tile_offset.y - self.border_dist_y))
        bottom_edge = min(self.tile_map.shape[1], int(tile_offset.y + self.border_dist_y))
        return self.tile_map[left_edge:right_edge, top_edge:bottom_edge]

    def update(self) -> None:
        self.render_outline()
        self.render_tiles()