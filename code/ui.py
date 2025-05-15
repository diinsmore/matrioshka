from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from inventory import Inventory

import pygame as pg
import math

from settings import TILE_SIZE, RES, MACHINES, POTIONS

class UI:
    def __init__(
        self,
        screen: pg.Surface,
        camera_offset: pg.Vector2,
        assets: dict[str, dict[str, any]],
        inv: Inventory
    ):
        self.screen = screen
        self.camera_offset = camera_offset
        self.assets = assets
        self.inv = inv

        self.mini_map = MiniMap(self.screen, self.assets, self.make_outline)

        self.inv_ui = InvUI(
            self.inv, 
            self.screen, 
            self.assets,
            self.mini_map.height + self.mini_map.padding, 
            self.make_outline,
            self.make_transparent_bg
        )

        self.craft_window = CraftWindow(
            self.screen, 
            self.assets, 
            self.inv_ui, 
            self.get_craft_window_height(), 
            self.camera_offset,
            self.make_outline,
            self.make_transparent_bg
        )

        self.HUD = HUD(
            self.screen, 
            self.assets, 
            self.craft_window.outline.right, 
            self.make_outline, 
            self.make_transparent_bg
        )

        self.mouse_grid = MouseGrid(self.screen, self.camera_offset)

    def get_craft_window_height(self) -> int:
        inv_grid_max_height = self.inv_ui.box_height * (self.inv.slots // self.inv_ui.cols)
        return inv_grid_max_height + self.mini_map.height + self.mini_map.padding

    def make_outline(
        self,
        rect: pg.Rect,
        color: str|tuple[int, int, int] = None,
        width: int = 1,
        padding: int = 1,
        radius: int = 0,
        draw: bool = True, # if multiple rects are used, this gives more flexibility for their layering
        return_outline: bool = False
    ) -> None|pg.Rect:

        # avoids evaluating 'self' prematurely when set as a default parameter
        if color is None:
            color = self.assets['colors']['outline bg']

        outline = pg.Rect(
                    rect.topleft - pg.Vector2(padding, padding), 
                    (rect.width + (padding * 2), rect.height + (padding * 2))
                )
        if draw:
            pg.draw.rect(self.screen, color, outline, width, radius)

        if return_outline: # use the outline as the base rect for creating another outline
            return outline

    def make_transparent_bg(
        self, 
        rect: pg.Rect, 
        color: str|tuple[int, int, int] = 'black', 
        alpha: int = 100
    ) -> None:

        bg_image = pg.Surface(rect.size)
        bg_image.fill(color)
        bg_image.set_alpha(alpha)
        bg_rect = bg_image.get_rect(topleft = rect.topleft)
        self.screen.blit(bg_image, bg_rect)

    def update(self, mouse_coords: tuple[int, int], mouse_moving: bool, left_click: bool) -> None:
        self.mouse_grid.update(mouse_coords, mouse_moving, left_click)
        self.HUD.update()
        self.mini_map.update()
        self.craft_window.update(mouse_coords) # keep above the inventory ui otherwise item names may be rendered behind the window
        self.inv_ui.update()
        

class MouseGrid:
    '''a grid around the mouse position to guide block placement'''
    def __init__(self, screen: pg.Surface, camera_offset: pg.Vector2):
        self.screen = screen
        self.camera_offset = camera_offset

    def render_grid(self, mouse_coords: tuple[int, int], mouse_moving: bool, left_click: bool) -> None:
        tiles_x, tiles_y = 3, 3
        if mouse_moving or left_click:
            topleft = self.get_grid_coords(tiles_x, tiles_y, mouse_coords)
            for x in range(tiles_x):
                for y in range(tiles_y):
                    cell_surf = pg.Surface((TILE_SIZE, TILE_SIZE), pg.SRCALPHA)
                    cell_surf.fill((0, 0, 0, 0))
                    pg.draw.rect(cell_surf, (255, 255, 255, 10), (0, 0, TILE_SIZE, TILE_SIZE), 1) # (0, 0) is relative to the topleft of cell_surf
                    cell_rect = cell_surf.get_rect(topleft = (topleft + pg.Vector2(x * TILE_SIZE, y * TILE_SIZE)))
                    self.screen.blit(cell_surf, cell_rect)

    def get_grid_coords(self, width: int, height: int, mouse_coords: tuple[int, int]) -> pg.Vector2:
        '''align the grid with the tile map and return its topleft point'''
        width, height = width // 2, height // 2

        x = int(mouse_coords[0] // TILE_SIZE) * TILE_SIZE
        y = int(mouse_coords[1] // TILE_SIZE) * TILE_SIZE

        topleft = pg.Vector2(x - (width * TILE_SIZE), y - (height * TILE_SIZE))
        return pg.Vector2(topleft.x - self.camera_offset.x, topleft.y - self.camera_offset.y)

    def update(self, mouse_coords: tuple[int, int], mouse_moving, left_click: bool) -> None:
        self.render_grid(mouse_coords, mouse_moving, left_click)


class HUD:
    def __init__(
        self, 
        screen: pg.Surface, 
        assets: dict[str, dict[str, any]], 
        craft_window_right: int,
        make_outline: callable,
        make_transparent_bg: callable,
    ):
        self.screen = screen
        self.assets = assets
        self.craft_window_right = craft_window_right
        self.make_outline = make_outline
        self.make_transparent_bg = make_transparent_bg

        self.colors = self.assets['colors']
        self.fonts = self.assets['fonts']

        self.height = TILE_SIZE * 3
        self.width = RES[0] // 2
        self.shift_right = False
        self.render = True

    def render_bg(self) -> None:
        self.image = pg.Surface((self.width, self.height))
        self.rect = self.image.get_rect(topleft = (self.get_left_point(), 0))
        self.make_transparent_bg(self.rect)
        
        outline1 = self.make_outline(self.rect, draw = False, return_outline = True)
        outline2 = self.make_outline(outline1, draw = True)
        pg.draw.rect(self.screen, 'black', outline1, 1)

    def get_left_point(self) -> int:
        default = (RES[0] // 2) - (self.width // 2)
        if not self.shift_right:
            return default
        else:
            # center between the craft window's right border and the screen's right border
            padding = (RES[0] - self.craft_window_right) - self.width
            return self.craft_window_right + (padding // 2)
        
    def update(self) -> None:
        if self.render:
            self.render_bg()


class MiniMap:
    def __init__(
        self, 
        screen: pg.Surface, 
        assets: dict[str, dict[str, any]], 
        make_outline: callable
    ):
        self.screen = screen
        self.assets = assets
        self.make_outline = make_outline

        self.colors = self.assets['colors']
        self.fonts = self.assets['fonts']

        self.width, self.height = TILE_SIZE * 10, TILE_SIZE * 10
        self.padding = 5
        self.render = True

    def render_outline(self) -> None:
        if self.render:
            base_rect = pg.Rect(self.padding, self.padding, self.width, self.height)
            outline1 = self.make_outline(base_rect, draw = False, return_outline = True)
            outline2 = self.make_outline(outline1, draw = True)
            pg.draw.rect(self.screen, 'black', outline1, 1)

    def update(self) -> None:
        self.render_outline()


class InvUI:
    def __init__(
        self, 
        inv: Inventory, 
        screen: pg.Surface, 
        assets: dict[str, dict[str, any]], 
        top: int,
        make_outline: callable,
        make_transparent_bg: callable
    ):
        self.inv = inv
        self.screen = screen
        self.assets = assets
        self.padding = 5
        self.top = top + self.padding
        self.make_outline = make_outline
        self.make_transparent_bg = make_transparent_bg

        self.graphics = self.assets['graphics']
        self.fonts = self.assets['fonts']
        self.colors = self.assets['colors']

        self.slots = self.inv.slots
        self.cols = 5
        self.rows = 2
        self.box_width, self.box_height = TILE_SIZE * 2, TILE_SIZE * 2
        self.total_width = self.box_width * self.cols
        self.total_height = self.box_height * self.rows
        self.render = True
        self.expand = False
        self.outline = pg.Rect(self.padding, self.top, self.total_width, self.total_height)
    
    def update_dimensions(self) -> None:
        # the number of columns is static
        self.rows = 2 if not self.expand else self.slots // self.cols
        self.total_height = self.box_height * self.rows

    def render_bg(self) -> None:
        rect = pg.Rect(self.padding, self.top, self.total_width, self.total_height)
        outline = self.make_outline(rect)
        self.make_transparent_bg(rect)
        
    def render_slots(self) -> None:
        for x in range(self.cols):
            for y in range(self.rows):
                box = pg.Rect(
                    (self.padding, self.top) + pg.Vector2(x * self.box_width, y * self.box_height), 
                    (self.box_width - 1, self.box_height - 1) # -1 for a slight gap between boxes
                )
                pg.draw.rect(self.screen, 'black', box, 1)

    def render_icons(self) -> None:
        contents = self.inv.contents.items()
        if contents:
            for name, data in contents:
                # will have to update this path depending on the particular item type
                icon_image = self.graphics[name]
                
                # determine the slot an item corresponds to
                col = data['index'] % self.cols
                row = data['index'] // (self.rows if self.expand else self.slots // self.cols)
                
                # render at the center of the inventory slot
                x = self.outline.left + (col * self.box_width) + (icon_image.get_width() // 2)
                y = self.outline.top + (row * self.box_height) + (icon_image.get_height() // 2)
                icon_rect = icon_image.get_rect(topleft = (x, y))
                self.screen.blit(icon_image, icon_rect)

                self.render_item_amount(data['amount'], (x, y))
                self.render_item_name(icon_rect, name)

    def render_item_amount(self, amount: int, coords: tuple[int, int]) -> None:
        amount_image = self.assets['fonts']['number'].render(str(amount), False, self.assets['colors']['text'])
        
        # move the text 5 pixels further to the right for each digit > 2
        num_digits = len(str(amount))
        x_offset = 5 * (num_digits - 2) if num_digits > 2 else 0

        amount_rect = amount_image.get_rect(center = coords + pg.Vector2(x_offset, -2))
        self.render_amount_bg(amount_rect)
        self.screen.blit(amount_image, amount_rect)

    def render_amount_bg(self, rect: pg.Rect) -> None:
        '''adds a slightly transparent surface behind the text to aid in readability'''
        bg_image = pg.Surface(rect.size)
        bg_image.fill('black')
        bg_image.set_alpha(100)
        bg_rect = bg_image.get_rect(topleft = rect.topleft)
        self.screen.blit(bg_image, bg_rect)

    def render_item_name(self, icon_rect: pg.Rect, name: str) -> None:
        if pg.mouse.get_rel():
            # render when the mouse hovers over the icon
            if icon_rect.collidepoint(pg.mouse.get_pos()):
                font = self.assets['fonts']['item label'].render(name, True, self.assets['colors']['text'])
                font_rect = font.get_rect(topleft = icon_rect.bottomright)
                self.screen.blit(font, font_rect)

    def update(self) -> None:
        if self.render:
            self.update_dimensions()
            self.render_bg()
            self.render_slots()
            self.render_icons()


class CraftWindow:
    def __init__(
        self, 
        screen: pg.Surface, 
        assets: dict[str, dict[str, any]], 
        inv_ui: InvUI, 
        height: int, 
        camera_offset: pg.Vector2,
        make_outline: callable,
        make_transparent_bg: callable
    ):
        self.screen = screen
        self.assets = assets
        self.inv_ui = inv_ui
        self.height = height
        self.camera_offset = camera_offset
        self.make_outline = make_outline
        self.make_transparent_bg = make_transparent_bg

        self.graphics = self.assets['graphics']
        self.fonts = self.assets['fonts']
        self.colors = self.assets['colors']

        self.width = int(self.inv_ui.outline.width * 1.3)
        self.padding = 5
        # defining the outline as a class attribute to allow the HUD and potentially other ui elements to access its location
        self.outline = pg.Rect(self.inv_ui.outline.right + self.padding, self.padding, self.width, self.height)

        self.categories = {
            'tools': {
                'material gathering': ['pickaxe', 'axe', 'chainsaw'], 
                'defense': ['sword', 'bow', 'arrow', 'pistol', 'shotgun'], 
                'explosives': ['bomb', 'dynamite']
            },

            'materials': [
                {'bars': ['copper bar', 'iron bar', 'silver bar', 'gold bar']}, 
                'iron gear', 'circuit', 'glass', 
            ],

            'infrastructure': {
                'machines': {**MACHINES},
                'research': ['lab', 'research cores'],
                'decor': {
                    'walls': {'materials': ['wood', 'stone', 'iron', 'copper', 'silver', 'gold']},
                    'doors': {'materials': ['wood', 'glass', 'stone', 'iron']},
                    'tables': {'materials': ['wood', 'glass', 'sandstone', 'ice']},
                    'chairs': {'materials': ['wood', 'glass', 'ice']},
                },
                'storage': {
                    'chest': {'materials': ['wood', 'glass', 'stone', 'iron']},
                    'energy': ['battery', 'accumulator']
                },
            },
    
            'consumables': {
                # TODO: add more potions and potentially 'craftable' food/drink items?
                'potions': POTIONS,
            },
        }
        self.open = False
        self.selected_category = None
        self.open_subcategory = False
        self.category_keys = list(self.categories.keys()) # just here to avoid calling .keys() every time they need to be referenced
        self.num_categories = len(self.category_keys)

        self.num_cols = 2
        self.num_rows = self.num_categories // self.num_cols
        self.col_width = self.outline.width // self.num_cols
        self.row_height = (self.outline.height // 3) // self.num_rows

        self.cell_borders = {'x': [], 'y': []}
        self.precompute_cell_borders()

    def precompute_cell_borders(self) -> None:
        '''
        store the coordinates of each column/row comprising the grid to 
        reference when searching for the current cell being hovered over
        '''
        for col in range(self.num_cols):
            padding = 2 # without this offset, an error is thrown when you move within the menu's borders from the topleft side, presumably due to the outline
            self.cell_borders['x'].append((self.outline.left, self.outline.left + (self.col_width * (col + 1)) + padding))
        
        for row in range(self.num_rows):
            self.cell_borders['y'].append((self.outline.top, self.outline.top + (self.row_height * (row + 1))))

    def render_outline(self) -> None:
        pg.draw.rect(self.screen, 'black', self.outline, 1, 2)
        self.make_transparent_bg(pg.Rect(self.outline.topleft, self.outline.size))

    def split_into_sections(self) -> None:
        for col in range(self.num_cols):
            left = self.outline.left + (self.col_width * col)
            col_rect = pg.Rect(left, self.outline.top, self.col_width, self.row_height * self.num_rows)
            col_outline = self.make_outline(col_rect)
            pg.draw.rect(self.screen, 'black', col_rect, 1)

            for row in range(self.num_rows):
                top = self.outline.top + (self.row_height * row)
                row_rect = pg.Rect(self.outline.left, top, self.outline.width - 2, self.row_height)
                pg.draw.rect(self.screen, 'black', row_rect, 1)
                
                category_index = col + (row * self.num_cols)
                label = self.category_keys[category_index]
                self.render_labels((left, top), label)
                self.render_preview_images(label, col, row)
                
    def render_labels(self, topleft: tuple[int, int], label: str) -> None:
        padding = 2
        text = self.fonts['craft menu label'].render(label, True, self.colors['text'])
        border = pg.Rect(topleft + pg.Vector2(padding, padding), text.size + pg.Vector2(padding * 2, padding * 2))
        self.make_transparent_bg(border)
        text_rect = text.get_rect(topleft = topleft + pg.Vector2(padding * 2, padding * 2))
        self.screen.blit(text, text_rect)

        border_outline = self.make_outline(border, color = 'black')

    def render_preview_images(self, label: str, col: int, row: int) -> None:
        '''render an item relating to a given crafting category'''
        image = self.get_label_image(label)
        if label != self.selected_category:
            image.set_alpha(200)
        
        # get the space between the border of the image and the cell containing it
        padding_x = self.col_width - image.get_width()
        padding_y = self.row_height - image.get_height()

        # center the image within a given cell
        label_padding = 10  # account for the category label at the top 
        offset = pg.Vector2(
            (col * self.col_width) + (padding_x // 2), 
            (row * self.row_height) + (padding_y // 2) + label_padding
        ) 
        
        image_rect = image.get_rect(topleft = self.outline.topleft + offset)
        # add a slightly transparent black background
        bg_rect = pg.Rect(
            image_rect.topleft - pg.Vector2(self.padding, self.padding), 
            image_rect.size + pg.Vector2(self.padding * 2, self.padding * 2)
        )
        self.make_transparent_bg(bg_rect, alpha = 100 if label != self.selected_category else 255)
        self.make_outline(bg_rect)

        self.screen.blit(image, image_rect)

    def get_label_image(self, label: str) -> pg.Surface:
        scale = 1.2
        match label:
            case 'tools':
                image = self.graphics['pickaxes']['stone pickaxe']

            case 'materials':
                image = self.graphics['minerals']['bars']['iron bar']
                scale = 1.3
                
            case 'infrastructure':
                image = self.graphics['machines']['steam engine']
                scale = 0.8

            case 'consumables':
                image = self.graphics['consumables']['potions']['reduced fall speed']

        image = pg.transform.scale(image, (image.width * scale, image.height * scale))
        return image

    def select_category(self, mouse_coords: tuple[int, int]) -> None:
        mouse_coords -= self.camera_offset # convert from world-space to screen-space
        if self.open and self.mouse_within_borders(mouse_coords):
            cell_index = self.get_category_overlap(mouse_coords)
            col, row = cell_index[0], cell_index[1]
            self.selected_category = self.category_keys[col + (row * self.num_cols)]
            self.render_items()
        else:
            self.selected_category = None

    def mouse_within_borders(self, mouse_coords: pg.Vector2) -> bool:
        return self.outline.left < mouse_coords[0] < self.outline.right and \
                self.outline.top < mouse_coords[1] < self.outline.top + (self.num_rows * self.row_height)
    
    def get_category_overlap(self, mouse_coords: pg.Vector2) -> int:
        '''determine which category within the grid is being hovered over by the mouse'''
        cell_coords = []
        # column index
        for index, x_range in enumerate(self.cell_borders['x']):
            if mouse_coords.x in range(x_range[0], x_range[1]):
                cell_coords.append(index)
                break
        # row index
        for index, y_range in enumerate(self.cell_borders['y']):
            if mouse_coords.y in range(y_range[0], y_range[1]):
                cell_coords.append(index)
                return cell_coords
    
    def render_items(self) -> None:
        num_slots = self.count_category_slots(self.categories[self.selected_category])
        
        top = self.outline.top + (self.row_height * self.num_rows)
        cell_width, cell_height = int(TILE_SIZE * 2.5), int(TILE_SIZE * 2.5)
        x_cells = self.outline.width // cell_width
        y_cells = math.ceil(num_slots / x_cells)

        num_boxes = 0 # keeping this counter to prevent drawing a full row if only a partial row is needed
        for x in range(x_cells):
            for y in range(y_cells):
                num_boxes += 1
                if num_boxes <= num_slots:
                    cell = pg.Rect(
                        self.outline.left + (cell_width * x), 
                        top + (cell_height * y), 
                        cell_width, 
                        cell_height
                    )
                    pg.draw.rect(self.screen, 'black', cell, 1)
    
    @staticmethod
    def count_category_slots(item_data: dict[list|str, dict]) -> int:
        '''
        if the items in a given category aren't divided into subcategories, 
        then each item can be given its own slot in the crafting window. 
        otherwise just devote a slot to each subcategory and display the
        items within the subcategory only when it's selected
        '''
        if isinstance(item_data, list):
            return len(item_data)

        elif isinstance(item_data, dict):

            return len(item_data.keys())

    def update(self, mouse_coords: pg.Vector2) -> None:
        if self.open:
            self.render_outline()
            self.split_into_sections()
            self.select_category(mouse_coords)