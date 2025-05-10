from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from asset_manager import AssetManager
    from inventory import Inventory

from os.path import join

import pygame as pg
from settings import RES, TILE_SIZE

class UI:
    def __init__(
        self, 
        screen: pg.Surface,
        camera_offset: pg.Vector2,
        asset_manager: AssetManager,
        inv: Inventory
    ):
        self.screen = screen
        self.camera_offset = camera_offset
        self.asset_manager = asset_manager
        self.assets = self.asset_manager.assets
        self.inv = inv

        self.mini_map = MiniMap(self.screen, self.assets, self.get_outline)
        self.inv_ui = InvUI(
            self.inv, 
            self.screen, 
            self.asset_manager, 
            self.mini_map.height + self.mini_map.padding, 
            self.get_outline
        )
        self.craft_window = CraftWindow(self.screen, self.inv_ui, self.get_craft_window_height(), self.get_outline)
        self.HUD = HUD(self.screen, self.assets, self.craft_window.outline.right, self.get_outline)
        self.mouse_grid = MouseGrid(self.screen, self.camera_offset)

    def get_craft_window_height(self) -> int:
        inv_grid_max_height = self.inv_ui.box_height * (self.inv.slots // self.inv_ui.cols)
        return inv_grid_max_height + self.mini_map.height + self.mini_map.padding

    def get_outline(
        self,
        rect: pg.Rect,
        color: str = None,
        width: int = 1, 
        radius: int = 0,
        draw: bool = True, # if multiple rects are used, this gives more flexibility for their layering
        return_outline: bool = False
    ) -> None|pg.Rect:

        # avoids evaluating 'self' prematurely when set as a default parameter
        if color is None:
            color = self.assets['colors']['outline bg']

        outline = pg.Rect(
                    rect.topleft - pg.Vector2(width, width), 
                    (rect.width + (width * 2), rect.height + (width * 2))
                )
        if draw:
            pg.draw.rect(self.screen, color, outline, width, radius)

        if return_outline: # use the new rect to create a second outline around it
            return outline

    def update(self, mouse_coords: tuple[int, int], mouse_moving: bool, left_click: bool) -> None:
        self.mouse_grid.update(mouse_coords, mouse_moving, left_click)
        self.HUD.update()
        self.mini_map.update()
        self.inv_ui.update()
        self.craft_window.update()


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
        get_outline: callable,
    ):
        self.screen = screen
        self.assets = assets
        self.craft_window_right = craft_window_right
        self.get_outline = get_outline

        self.colors = self.assets['colors']
        self.fonts = self.assets['fonts']
        self.height = TILE_SIZE * 3
        self.width = RES[0] // 2
        self.shift_right = False
        self.render = True

    def render_bg(self) -> None:
        self.image = pg.Surface((self.width, self.height))
        self.rect = self.image.get_rect(topleft = (self.get_left_point(), 0))
        self.image.fill('black')
        self.image.set_alpha(150)
        self.screen.blit(self.image, self.rect)
        
        outline1 = self.get_outline(self.rect, draw = False, return_outline = True)
        outline2 = self.get_outline(outline1, draw = True)
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
    def __init__(self, screen: pg.Surface, assets: dict[str, dict[str, any]], get_outline: callable):
        self.screen = screen
        self.assets = assets
        self.get_outline = get_outline

        self.colors = self.assets['colors']
        self.fonts = self.assets['fonts']
        self.width, self.height = TILE_SIZE * 10, TILE_SIZE * 10
        self.padding = 5
        self.render = True

    def render_outline(self) -> None:
        if self.render:
            base_rect = pg.Rect(self.padding, self.padding, self.width, self.height)
            outline1 = self.get_outline(base_rect, draw = False, return_outline = True)
            outline2 = self.get_outline(outline1, draw = True)
            pg.draw.rect(self.screen, 'black', outline1, 1)

    def update(self) -> None:
        self.render_outline()


class InvUI:
    def __init__(
        self, 
        inv: Inventory, 
        screen: pg.Surface, 
        asset_manager: AssetManager, 
        top: int,
        get_outline: callable
    ):
        self.inv = inv
        self.screen = screen
        self.asset_manager = asset_manager
        self.padding = 5
        self.top = top + self.padding
        self.get_outline = get_outline

        self.assets = self.asset_manager.assets
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
        image = pg.Surface((self.total_width, self.total_height))
        image.fill('black')
        image.set_alpha(100)
        rect = image.get_rect(topleft = (self.padding, self.top))
        outline = self.get_outline(rect)
        self.screen.blit(image, rect)

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
                icon_image = self.assets['graphics'][name]
                
                # determine the slot an item corresponds to
                col = data['index'] % self.cols
                row = data['index'] // self.rows
                
                # render at the center of the inventory slot
                x = self.outline.left + (col * self.box_width) + (icon_image.get_width() // 2)
                y = self.outline.top + (row * self.box_height) + (icon_image.get_height() // 2)
                icon_rect = icon_image.get_rect(topleft = (x, y))
                self.screen.blit(icon_image, icon_rect)

                self.render_item_amount(data['amount'], (x, y))
                self.render_item_name(icon_rect, name)

    def render_item_amount(self, amount: int, coords: tuple[int, int]) -> None:
        amount_image = self.assets['fonts']['number'].render(str(amount), False, 'gray')
        amount_rect = amount_image.get_rect(center = coords - pg.Vector2(0, 2))
        self.screen.blit(amount_image, amount_rect)

    def render_item_name(self, icon_rect: pg.Rect, name: str) -> None:
        if pg.mouse.get_rel():
            # render when the mouse hovers over the icon
            if icon_rect.collidepoint(pg.mouse.get_pos()):
                font = self.assets['fonts']['label'].render(name, True, 'azure4')
                font_rect = font.get_rect(topleft = icon_rect.bottomright)
                self.screen.blit(font, font_rect)

    def update(self) -> None:
        if self.render:
            self.update_dimensions()
            self.render_bg()
            self.render_slots()
            self.render_icons()


class CraftWindow:
    def __init__(self, screen: pg.Surface, inv_ui: InvUI, height: int, get_outline: callable):
        self.screen = screen
        self.inv_ui = inv_ui
        self.height = height
        self.get_outline = get_outline

        self.width = self.inv_ui.total_width * 2
        self.padding = 5
        # defining the outline as a class attribute to allow the HUD and potentially other ui elements to access its location
        self.outline = pg.Rect(self.inv_ui.outline.right + self.padding, self.padding, self.width, self.height)
        self.open = False

    def render_outline(self) -> None:
        if self.open:
            pg.draw.rect(self.screen, 'black', self.outline, 1, 2)
            bg = self.get_outline(self.outline)

    def update(self) -> None:
        self.render_outline()