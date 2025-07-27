import pygame as pg
import numpy as np

from settings import MAP_SIZE, TILE_SIZE

class MiniMap:
    def __init__(
        self, 
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        tile_map: np.ndarray, 
        tile_IDs: dict[str, int],
        tile_IDs_to_names: dict[int, str], 
        make_outline: callable,
        get_tile_material: callable
    ):
        self.screen = screen
        self.cam_offset = cam_offset
        self.tile_map = tile_map
        self.tile_IDs = tile_IDs
        self.tile_IDs_to_names = tile_IDs_to_names
        self.make_outline = make_outline
        self.get_tile_material = get_tile_material
        
        self.visited_tiles = np.full(MAP_SIZE, False, dtype = bool)
        
        self.tiles_x, self.tiles_y = 80, 80
        self.tile_px_w, self.tile_px_h = 2, 2
        self.outline_w = self.tiles_x * self.tile_px_w
        self.outline_h = self.tiles_y * self.tile_px_h
        self.padding = 5
        self.topleft = pg.Vector2(self.padding, self.padding)
        self.render = True
        
        self.border_dist_x = self.tiles_x // 2
        self.border_dist_y = self.tiles_y // 2

        self.RGBs = {
            'air': (178, 211, 236),
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
            'obsidian': (32, 23, 43),
            'tree': (74, 54, 47)
        }

        self.non_tiles = {'air', 'tree base'}
        self.tree_px_height = 8
        self.branch_y = self.tree_px_height // 2

    def render_outline(self) -> None:
        if self.render:
            base_rect = pg.Rect(*self.topleft, self.outline_w, self.outline_h)
            outline1 = self.make_outline(base_rect, draw = False, return_outline = True)
            outline2 = self.make_outline(outline1, draw = True)
            pg.draw.rect(self.screen, 'black', outline1, 1)

    def render_tiles(self) -> None:
        tile_map = self.get_map_slice()
        cols, rows = tile_map.shape
        for y in range(rows): # keep y first otherwise tree branches to the right get blitted over by the following x index
            for x in range(cols):
                image = pg.Surface((self.tile_px_w, self.tile_px_h))
                tile_ID = tile_map[x, y]
                tile_name = self.tile_IDs_to_names[tile_ID]
                
                if tile_name in self.non_tiles:
                    match tile_name:
                        case 'air': # not in the TILES dictionary from settings
                            tile_color = self.RGBs['air']

                        case 'tree base':
                            tile_color = self.RGBs['tree']
                            self.render_tree(image, tile_color, x, y)
                else:
                    tile_color = self.RGBs[self.get_tile_material(tile_ID)]

                image.fill(tile_color)
                rect = image.get_rect(topleft = self.topleft + (x * self.tile_px_w, y * self.tile_px_h))
                self.screen.blit(image, rect)

    def render_tree(self, image: pg.Surface, tile_color: str, x: int, y: int) -> None:
        image.fill(tile_color)
        for i in range(self.tree_px_height):
            rect = image.get_rect(topleft = self.topleft + (x * self.tile_px_w, (y - i) * self.tile_px_h))
            self.screen.blit(image, rect)
            if i == self.branch_y:
                left_branch = image.get_rect(topleft = self.topleft + ((x - 1) * self.tile_px_w, (y - i) * self.tile_px_h))
                right_branch = image.get_rect(topleft = self.topleft + ((x + 1) * self.tile_px_w, (y - i) * self.tile_px_h))
                self.screen.blit(image, left_branch)
                self.screen.blit(image, right_branch)

    def get_map_slice(self) -> np.ndarray:
        tile_offset_x = int(self.cam_offset.x / TILE_SIZE)
        tile_offset_y = int(self.cam_offset.y / TILE_SIZE)
        
        left_edge = max(0, tile_offset_x - self.border_dist_x)
        right_edge = min(self.tile_map.shape[0], tile_offset_x + self.border_dist_x)
        top_edge_default = tile_offset_y - self.border_dist_y # keeping the default in case it's negative so the top/bottom row calculation can be adjusted accordingly
        top_edge = max(0, top_edge_default)
        bottom_edge = min(self.tile_map.shape[1], tile_offset_y + self.border_dist_y)
        if top_edge_default < 0:
            bottom_edge += abs(top_edge_default) # prevents rows below from being occluded when the camera offset is negative 
        
        map_slice = self.tile_map[left_edge:right_edge, top_edge:bottom_edge]
        full_slice = np.full((self.tiles_x, self.tiles_y), self.tile_IDs['air'], dtype = np.uint8) # fill any gaps with air if the map's edge is reached
        start_y = max(0, self.border_dist_y - (tile_offset_y - top_edge)) # not needed for the x axis since movement is constrained to within the tile map's left/right borders
        # determine how many cols/rows represent the tile map vs empty space outside the map
        cols, rows = map_slice.shape
        map_cols = min(cols, self.tiles_x) 
        map_rows = min(rows, self.tiles_y - start_y)
        
        full_slice[:map_cols, :start_y + map_rows] = map_slice[:map_cols, :start_y + map_rows]
        return full_slice

    def update(self) -> None:
        self.render_outline()
        self.render_tiles()