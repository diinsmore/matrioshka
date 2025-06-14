from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from inventory_ui import InventoryUI
    from sprite_manager import SpriteManager
    from player import Player

import pygame as pg
import math

from settings import TILE_SIZE, TOOLS, MATERIALS, MACHINES, STORAGE, DECOR, RESEARCH

class CraftWindow:
    def __init__(
        self, 
        screen: pg.Surface, 
        camera_offset: pg.Vector2,
        assets: dict[str, dict[str, any]], 
        inventory_ui: InventoryUI,
        sprite_manager: SpriteManager,
        player: Player,
        height: int,
        make_outline: callable,
        make_transparent_bg: callable,
        render_inventory_item_name: callable,
        get_scaled_image: callable
    ):
        self.screen = screen
        self.camera_offset = camera_offset
        self.assets = assets
        self.inventory_ui = inventory_ui
        self.sprite_manager = sprite_manager
        self.player = player
        self.height = height
        self.make_outline = make_outline
        self.make_transparent_bg = make_transparent_bg
        self.render_inventory_item_name = render_inventory_item_name
        self.get_scaled_image = get_scaled_image

        self.graphics = self.assets['graphics']
        self.fonts = self.assets['fonts']
        self.colors = self.assets['colors']

        self.width = int(self.inventory_ui.outline.width * 1.3)
        self.padding = 5
        # defining the outline as a class attribute to allow the HUD and potentially other ui elements to access its location
        self.outline = pg.Rect(self.inventory_ui.outline.right + self.padding, self.padding, self.width, self.height)

        self.opened = False

        self.cell_height, self.cell_width = TILE_SIZE * 2, TILE_SIZE * 2 # for the grid of items comprising a given category

        self.category_grid = CategoryGrid(
            self.screen,
            self.camera_offset,
            self.outline, 
            self.graphics,
            self.fonts, 
            self.colors,
            self.padding,
            self.opened,
            self.make_outline, 
            self.make_transparent_bg, 
        )

        self.item_grid = ItemGrid(
            self.screen, 
            self.graphics,
            self.outline, 
            self.outline.top + (self.category_grid.row_height * self.category_grid.num_rows) + self.padding,
            self.category_grid.categories, 
            self.category_grid.selected_category,
            self.sprite_manager,
            self.player,
            self.make_outline, 
            self.render_inventory_item_name,
            self.get_scaled_image
        )

    def render_outline(self) -> None:
        self.make_outline(self.outline, color = 'black')
        self.make_transparent_bg(pg.Rect(self.outline.topleft, self.outline.size))

    def update(self, mouse_coords: pg.Vector2, left_click: bool) -> None:
        if self.opened:
            self.render_outline()

            self.category_grid.opened = self.opened
            self.category_grid.update(mouse_coords, left_click)
            
            self.item_grid.selected_category = self.category_grid.selected_category
            self.item_grid.update(left_click)


class CategoryGrid:
    def __init__(
        self, 
        screen: pg.Surface, 
        camera_offset: pg.Vector2,
        window_outline: pg.Rect, 
        graphics: dict[str, dict[str, any]],
        fonts: dict[str, pg.font.Font],
        colors: dict[str, str],
        padding: int,
        opened: bool,
        make_outline: callable, 
        make_transparent_bg: callable
    ):
        self.screen = screen
        self.camera_offset = camera_offset
        self.window_outline = window_outline
        self.graphics = graphics
        self.fonts = fonts
        self.colors = colors
        self.padding = padding
        self.opened = opened
        self.make_outline = make_outline
        self.make_transparent_bg = make_transparent_bg

        self.categories = {
            'tools': {**TOOLS},
            'materials': {**MATERIALS},
            'machines': {**MACHINES},
            'research': {**RESEARCH},
            'decor': {**DECOR},
            'storage': {**STORAGE}
        }

        self.selected_category = None
        self.open_subcategory = False

        self.category_keys = list(self.categories.keys()) # just here to avoid calling .keys() every time they need to be referenced
        self.num_categories = len(self.category_keys)

        self.num_cols = 2
        self.num_rows = self.num_categories // self.num_cols

        self.col_width = self.window_outline.width // self.num_cols
        self.row_height = (self.window_outline.height // 2) // self.num_rows

        self.borders = {'x': [], 'y': []}
        self.precompute_borders()

    def precompute_borders(self) -> None:
        '''store the coordinates of each column/row to reference when searching for the current cell being hovered over'''
        for col in range(1, self.num_cols + 1):
            padding = 2 # without this offset, an error is thrown when you move within the menu's borders from the topleft side, presumably due to the outline
            self.borders['x'].append((self.window_outline.left, self.window_outline.left + (self.col_width * col) + padding))
        
        for row in range(1, self.num_rows + 1):
            self.borders['y'].append((self.window_outline.top, self.window_outline.top + (self.row_height * row) + padding))

    def make_grid(self) -> None:
        for col in range(self.num_cols):
            left = self.window_outline.left + (self.col_width * col)
            col_rect = pg.Rect(left, self.window_outline.top, self.col_width, self.row_height * self.num_rows)
            self.make_outline(col_rect)
            pg.draw.rect(self.screen, 'black', col_rect, 1)

            for row in range(self.num_rows):
                top = self.window_outline.top + (self.row_height * row)
                row_rect = pg.Rect(self.window_outline.left, top, self.window_outline.width - 2, self.row_height)
                pg.draw.rect(self.screen, 'black', row_rect, 1)
                
                category_index = col + (row * self.num_cols)
                category = self.category_keys[category_index]
                self.render_category_images(category, col, row)
                self.render_category_names((left, top), category)

    def render_category_images(self, category: str, col: int, row: int) -> None:
        '''render a graphic relating to a given crafting category'''
        image = self.get_category_image(category)
        if category != self.selected_category:
            image.set_alpha(150)
        
        # get the space between the border of the image and the cell containing it
        padding_x = self.col_width - image.get_width()
        padding_y = self.row_height - image.get_height()

        # center the image within a given cell
        category_padding = 10 # account for the category label at the top 
        offset = pg.Vector2(
            (col * self.col_width) + (padding_x // 2), 
            (row * self.row_height) + (padding_y // 2) + category_padding
        ) 
        
        image_rect = image.get_rect(topleft = self.window_outline.topleft + offset)
        self.screen.blit(image, image_rect)

    def render_category_names(self, topleft: tuple[int, int], category: str) -> None:
        padding = 2
        text = self.fonts['craft menu category'].render(category, True, self.colors['text'])
        border = pg.Rect(topleft + pg.Vector2(padding, padding), text.size + pg.Vector2(padding * 2, padding * 2))
        self.make_transparent_bg(border)
        self.make_outline(border, color = 'black')
        text_rect = text.get_rect(topleft = topleft + pg.Vector2(padding * 2, padding * 2))
        self.screen.blit(text, text_rect)

    def get_category_image(self, category: str) -> pg.Surface:
        scale = 0.8
        match category:
            case 'tools':
                image = self.graphics['pickaxe']['stone pickaxe']
                scale = 1.2

            case 'materials':
                image = self.graphics['minerals']['bars']['iron bar']
                scale = 1.3
                
            case 'machines':
                image = self.graphics['steam engine']

            case 'research':
                image = self.graphics['research']['lab']

            case 'decor':
                image = self.graphics['decor']['paintings']['creation']

            case 'storage':
                image = self.graphics['storage']['wood chest']
                scale = 1.2

        image = pg.transform.scale(image, (image.width * scale, image.height * scale))
        return image

    def select_category(self, mouse_coords: tuple[int, int], left_click: bool) -> None:
        if self.opened:
            mouse_coords -= self.camera_offset # convert from world-space to screen-space
            if self.mouse_on_grid(mouse_coords) and left_click:
                cell_index = self.get_category_overlap(mouse_coords)
                col, row = cell_index[0], cell_index[1]
                self.selected_category = self.category_keys[col + (row * self.num_cols)]
        else:
            self.selected_category = None
    
    def mouse_on_grid(self, mouse_coords: pg.Vector2) -> bool:
        return self.window_outline.left < mouse_coords[0] < self.window_outline.right and \
                self.window_outline.top < mouse_coords[1] < self.window_outline.top + (self.num_rows * self.row_height)

    def get_category_overlap(self, mouse_coords: pg.Vector2) -> int:
        '''determine which category is being hovered over by the mouse'''
        cell_coords = []
        # column index
        for index, x_range in enumerate(self.borders['x']):
            if mouse_coords.x in range(x_range[0], x_range[1]):
                cell_coords.append(index)
                break
        # row index
        for index, y_range in enumerate(self.borders['y']):
            if mouse_coords.y in range(y_range[0], y_range[1]):
                cell_coords.append(index)
                return cell_coords

    def update(self, mouse_coords: tuple[int, int], left_click: bool) -> None:
        self.make_grid()
        self.select_category(mouse_coords, left_click)


class ItemGrid:
    def __init__(
        self, 
        screen: pg.Surface, 
        graphics: dict[str, dict[str, any]],
        window_outline: pg.Surface,
        top: int, 
        categories: dict[str, list[str]],
        selected_category: str,
        sprite_manager: SpriteManager,
        player: Player,
        make_outline: callable,
        render_item_name: callable,
        get_scaled_image: callable,
    ):
        self.screen = screen
        self.graphics = graphics
        self.window_outline = window_outline
        self.top = top
        self.categories = categories
        self.selected_category = selected_category
        self.sprite_manager = sprite_manager
        self.player = player
        self.make_outline = make_outline
        self.render_item_name = render_item_name
        self.get_scaled_image = get_scaled_image
        
        self.cell_width, self.cell_height = TILE_SIZE * 2, TILE_SIZE * 2
        self.x_cells = self.window_outline.width // self.cell_width
        self.left_padding = (self.window_outline.width - (self.x_cells * self.cell_width)) // 2
        self.left = self.window_outline.left + self.left_padding

    def render_item_slots(self, left_click: bool) -> None:
        # not defining these in __init__ since they rely on the selected category
        self.num_slots = len(self.categories[self.selected_category])
        self.y_cells = math.ceil(self.num_slots / self.x_cells)
        for x in range(self.x_cells):
            for y in range(self.y_cells):
                index = x + (y * self.x_cells)
                if index < self.num_slots:
                    cell = pg.Rect(
                        self.left + (self.cell_width * x), 
                        self.top + (self.cell_height * y), 
                        self.cell_width - 1, 
                        self.cell_height - 1
                    )
                    rect = pg.draw.rect(self.screen, 'black', cell, 1)
                    self.render_item_images(index, x, y, left_click)

    def render_item_images(self, index: int, x: int, y: int, left_click: bool) -> None:
        item_name = list(self.categories[self.selected_category].keys())[index]
        try:
            if not isinstance(self.graphics[item_name], dict):
                image = self.graphics[item_name]
                padding = 2
                scaled_image = self.get_scaled_image(image, item_name, self.cell_width, self.cell_height, padding)
                rect = scaled_image.get_rect(center = (
                    self.left + (self.cell_width * x) + (self.cell_width // 2), 
                    self.top + (self.cell_height * y) + (self.cell_height // 2)
                ))
                self.screen.blit(scaled_image, rect)

                self.render_item_name(rect, item_name)
                self.get_selected_item(rect, item_name, left_click)
        except KeyError:
            pass
    
    def get_selected_item(self, rect: pg.Rect, item_name: str, left_click: bool) -> None:
        if rect.collidepoint(pg.mouse.get_pos()) and left_click:
            item_data = self.categories[self.selected_category][item_name]
            self.sprite_manager.crafting.craft_item(item_name, item_data['recipe'], self.player)

    def update(self, left_click: bool) -> None:
        if self.selected_category:
            self.render_item_slots(left_click)