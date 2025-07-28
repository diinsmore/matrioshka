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
        get_tile_material: callable,
        saved_data: dict[str, any] | None
    ):
        self.screen = screen
        self.cam_offset = cam_offset
        self.tile_map = tile_map
        self.tile_IDs = tile_IDs
        self.tile_IDs_to_names = tile_IDs_to_names
        self.make_outline = make_outline
        self.get_tile_material = get_tile_material
        self.saved_data = saved_data
        
        self.visited_tiles = np.array(self.saved_data['visited tiles']) if self.saved_data else np.full(MAP_SIZE, False, dtype = bool)
        self.update_radius = 6

        self.tiles_x, self.tiles_y = 80, 80
        self.tile_px_w, self.tile_px_h = 2, 2
        self.outline_w = self.tiles_x * self.tile_px_w
        self.outline_h = self.tiles_y * self.tile_px_h
        self.border_dist_x = self.tiles_x // 2
        self.border_dist_y = self.tiles_y // 2
        self.padding = 5
        self.topleft = pg.Vector2(self.padding, self.padding)
        self.render = True
        
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
        tile_map, visited_map = self.get_map_slices()
        cols, rows = tile_map.shape
        for y in range(rows): # keep y first otherwise tree branches to the right get blitted over by the following x index
            for x in range(cols):
                image = pg.Surface((self.tile_px_w, self.tile_px_h))
                if visited_map[x, y]:
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
                else:
                    tile_color = 'black'
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

    def get_map_slices(self) -> tuple[np.ndarray, np.ndarray]:
        '''returns the slice of the tile map to display & the updated visited tiles map'''
        screen_w = self.screen.get_width() // 2
        screen_h = self.screen.get_height() // 2
        tile_offset_x = int((self.cam_offset.x + screen_w) / TILE_SIZE) # not using int division since the camera offset is a vector2
        tile_offset_y = int((self.cam_offset.y + screen_h) / TILE_SIZE)

        left = max(0, tile_offset_x - self.border_dist_x)
        right = min(self.tile_map.shape[0], tile_offset_x + self.border_dist_x)
        top_default = tile_offset_y - self.border_dist_y # keeping the default in case it's negative so the top/bottom row calculation can be adjusted
        top = max(0, top_default)
        bottom = min(self.tile_map.shape[1], tile_offset_y + self.border_dist_y)
        if top_default < 0:
            bottom += abs(top_default) # prevents rows below from being occluded when the camera offset is negative 
        
        left_visited = max(0, tile_offset_x - self.update_radius)
        right_visited = min(self.tile_map.shape[0], tile_offset_x + self.update_radius)
        top_default = tile_offset_y - self.update_radius
        top_visited = max(0, tile_offset_y - self.update_radius)
        bottom_visited = min(self.tile_map.shape[1], tile_offset_y + self.update_radius)
        if top_default < 0:
            bottom_visited += abs(top_default)
        self.visited_tiles[left_visited:right_visited, top_visited:bottom_visited] = True
        
        start_x = max(0, self.border_dist_x - (tile_offset_x - left))
        start_y = max(0, self.border_dist_y - (tile_offset_y - top))
        
        map_slice = self.tile_map[left:right, top:bottom]
        map_cols, map_rows = map_slice.shape
        cols = min(map_cols, self.tiles_x - start_x) 
        rows = min(map_rows, self.tiles_y - start_y)

        full_slice = np.full((self.tiles_x, self.tiles_y), self.tile_IDs['air'], dtype = np.uint8)
        full_slice[start_x:start_x + map_cols, start_y:start_y + map_rows] = map_slice[start_x:start_x + map_cols, start_y:start_y + map_rows]
        
        visited_slice = np.full((self.tiles_x, self.tiles_y), False, dtype = bool)
        visited_slice[start_x:start_x + cols, start_y:start_y + rows] = self.visited_tiles[left:left + cols, top:top + rows]
        
        return full_slice, visited_slice

    def update(self) -> None:
        self.render_outline()
        self.render_tiles()