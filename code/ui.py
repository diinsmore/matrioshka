from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from asset_manager import AssetManager
    from inventory import Inventory

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

        self.assets = asset_manager.assets
        self.colors = self.assets['colors']
        self.fonts = self.assets['fonts']

        self.inv = inv

        self.HUD = HUD(self.screen)
        self.inv_grid = InvGrid(self.inv, self.screen, self.colors, self.fonts, self.HUD.height)
        self.mini_map = MiniMap(self.screen, self.HUD.height)
        self.mouse_grid = MouseGrid(self.screen, self.camera_offset)
        self.craft_window = CraftWindow(self.screen)

    def update(self, mouse_coords: tuple[int, int], left_click: bool) -> None:
        self.HUD.update()
        self.inv_grid.update()
        self.mini_map.update()
        self.mouse_grid.update(mouse_coords, left_click)
        self.craft_window.update()

class HUD:
    def __init__(self, screen: pg.Surface):
        self.screen = screen
        self.height = 20

    def render_bg(self) -> None:
        image = pg.Surface((RES[0], self.height))
        image.fill('black')
        image.set_alpha(225)
        rect = image.get_rect(topleft = (0, 0))
        self.screen.blit(image, rect)

    def update(self) -> None:
        self.render_bg()


class InvGrid:
    def __init__(
        self, 
        inv: Inventory, 
        screen: pg.Surface, 
        colors: dict[str, str], 
        fonts: dict[str, pg.font.Font], 
        hud_height: int
    ):
        self.inv = inv
        self.screen = screen
        self.colors = colors
        self.fonts = fonts
        self.hud_height = hud_height
        
    def render_inv_outline(self) -> None:
        left = RES[0] - self.inv.ui_width  
        self.inv_outline = pg.Rect(left, self.hud_height, self.inv.ui_width, self.inv.ui_height)
        pg.draw.rect(self.screen, 'black', self.inv_outline, 1)

        # filling in the outline
        bg_image = pg.Surface((self.inv.ui_width, self.inv.ui_height))
        bg_image.fill(self.colors['inv bg'])
        bg_image.set_alpha(225)
        bg_rect = bg_image.get_rect(topleft = (left, self.hud_height))
        self.screen.blit(bg_image, bg_rect)

        # individual boxes
        for x in range(self.inv.cols):
            for y in range(self.inv.rows):
                # TODO: the alignment is slightly off
                box = pg.Rect(
                    (left - 1, self.hud_height - 1) + pg.Vector2(x * self.inv.box_width, y * self.inv.box_height), 
                    (self.inv.box_width - 1, self.inv.box_height - 1) 
                )
                pg.draw.rect(self.screen, 'black', box, 1)

    def render_inv_icons(self) -> None:
        icons = {}
        for index, item_data in self.inv.data.items():
            if item_data: # ignore empty slots
                item = list(item_data.keys())[0]
                quantity = list(item_data.values())[0]
                if item not in icons:
                    # will have to update this path depending on the particular item type
                    icons[item] = self.asset_manager.load_image(join('..', 'graphics', 'terrain', 'tiles', f'{item}.png'))
                
                # determine the inventory slot an item corresponds to
                inv_col = index % self.cols
                inv_row = index // self.cols
                
                # render at the center of the inventory slot
                x = self.inv_outline.left + (inv_col * self.inv.box_width) + (icons[item].get_width() // 2)
                y = self.inv_outline.top + (inv_row * self.inv.box_height) + (icons[item].get_height() // 2)
                icon_rect = icons[item].get_frect(topleft = (x, y))
                self.screen.blit(pg.transform.scale(icons[item], (24, 24)), icon_rect)

                self.render_item_quantity(quantity, x, y)

    def render_item_quantity(self, x, y) -> None:
        bg_image = pg.Surface((16, 16))
        bg_image.fill(self.colors['inv bg'])
        bg_image.set_alpha(200)
        bg_rect = bg_image.get_rect(topleft = (x, y) - pg.Vector2(4, 5))
        self.screen.blit(bg_image, bg_rect)

        quant_image = self.assets['fonts']['label'].render(str(quantity), False, 'gray')
        quant_rect = quant_image.get_frect(bottomleft = bg_image.bottomleft + pg.Vector2(2, 2))
        self.screen.blit(pg.transform.scale(quant_image, bg_image.get_size()), quant_rect)

    def render_inv_label(self) -> None:
        image = self.fonts['label'].render('Inventory', False, self.colors['inv label'])
        rect = image.get_frect(center = self.inv_outline.midtop - pg.Vector2(0, self.inv_outline.top / 2))
        self.screen.blit(image, rect)

        # decorative lines to the left/right of the text
        pg.draw.line(
            self.screen, 
            self.colors['inv label'], 
            (self.inv_outline.left, rect.midleft[1]), 
            (rect.left - 4, rect.midleft[1])
        )

        pg.draw.line(
            self.screen, 
            self.colors['inv label'], 
            (self.inv_outline.left, rect.midleft[1]), 
            (self.inv_outline.left, self.inv_outline.top - 4)
        )
        
        padding = 3
        pg.draw.line(
            self.screen, 
            self.colors['inv label'], 
            (rect.right + padding, rect.midright[1]), 
            (self.inv_outline.right - padding, rect.midright[1])
            )

        pg.draw.line(
            self.screen, 
            self.colors['inv label'], 
            (self.inv_outline.right - padding, rect.midright[1]), 
            (self.inv_outline.right - padding, self.inv_outline.top - padding)
        )

    def update(self) -> None:
        self.render_inv_outline()
        self.render_inv_icons()
        self.render_inv_label()


class MiniMap:
    def __init__(self, screen: pg.Surface, HUD_height: int):
        self.screen = screen
        self.HUD_height = HUD_height

        self.width, self.height = 200, 200

    def render_outline(self) -> None:
        padding = 5
        outline = pg.Rect((padding, padding + self.HUD_height), (self.width, self.height))
        pg.draw.rect(self.screen, 'black', outline, 1, 2)
 
    def update(self) -> None:
        self.render_outline()


class MouseGrid:
    '''a grid around the mouse position to guide block placement'''
    def __init__(self, screen: pg.Surface, camera_offset: pg.Vector2):
        self.screen = screen
        self.camera_offset = camera_offset

    def render_grid(self, mouse_coords: tuple[int, int], left_click: bool) -> None:
        tiles_x, tiles_y = 4, 4
        if pg.mouse.get_rel()[0] != 0 or pg.mouse.get_rel()[1] != 0 or left_click:
            topleft = self.get_grid_coords(tiles_x, tiles_y, mouse_coords)
            for x in range(tiles_x):
                for y in range(tiles_y):
                    cell_surf = pg.Surface((TILE_SIZE, TILE_SIZE), pg.SRCALPHA)
                    cell_surf.fill((0, 0, 0, 0))
                    pg.draw.rect(cell_surf, (255, 255, 255, 20), (0, 0, TILE_SIZE, TILE_SIZE), 1) # position (0, 0) is relative to the Surface's topleft corner
                    cell_rect = cell_surf.get_rect(topleft = (topleft + pg.Vector2(x * TILE_SIZE, y * TILE_SIZE)))
                    self.screen.blit(cell_surf, cell_rect)
        print(left_click)
    def get_grid_coords(self, width: int, height: int, mouse_coords: tuple[int, int]) -> pg.Vector2:
        '''align the grid with the tile map and return its topleft point'''
        width, height = width // 2, height // 2

        x = int(mouse_coords[0] // TILE_SIZE) * TILE_SIZE
        y = int(mouse_coords[1] // TILE_SIZE) * TILE_SIZE

        topleft = pg.Vector2(x - (width * TILE_SIZE), y - (height * TILE_SIZE))
        return pg.Vector2(topleft.x - self.camera_offset.x, topleft.y - self.camera_offset.y)

    def update(self, mouse_coords: tuple[int, int], left_click: bool) -> None:
        self.render_grid(mouse_coords, left_click)


class CraftWindow:
    def __init__(self, screen: pg.Surface):
        self.screen = screen
        self.open = False

    def render(self) -> None:
        if self.open:
            width, height = self.inv.ui_width, 400
            outline = pg.Rect(self.inv_outline.left - 1, self.inv_outline.bottom + 1, width, height)
            pg.draw.rect(self.screen, 'black', outline, 1, 2)

    def update(self) -> None:
        self.render()