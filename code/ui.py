from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from inventory import Inventory
    from sprite_manager import SpriteManager
    from player import Player
    import numpy as np

import pygame as pg

from settings import TILE_SIZE, RES
from mini_map import MiniMap
from craft_window import CraftWindow
from inventory_ui import InventoryUI
from timer import Timer

class UI:
    def __init__(
        self,
        screen: pg.Surface,
        camera_offset: pg.Vector2,
        assets: dict[str, dict[str, any]],
        inventory: Inventory,
        sprite_manager: SpriteManager,
        player: Player,
        tile_map: np.ndarray,
        tile_IDs: dict[str, int],
        tile_IDs_to_names: dict[int, str],
        saved_data: dict[str, any] | None
    ):
        self.screen = screen
        self.camera_offset = camera_offset
        self.assets = assets
        self.inventory = inventory
        self.sprite_manager = sprite_manager
        self.player = player
        self.tile_map = tile_map
        self.tile_IDs = tile_IDs
        self.tile_IDs_to_names = tile_IDs_to_names
        self.saved_data = saved_data

        self.mini_map = MiniMap(
            self.screen, 
            self.camera_offset, 
            self.tile_map,
            self.tile_IDs,
            self.tile_IDs_to_names, 
            self.make_outline,
            self.sprite_manager.mining.get_tile_material,
            self.saved_data
        )
        
        self.mouse_grid = MouseGrid(self.screen, self.camera_offset, self.get_grid_xy)

        self.inventory_ui = InventoryUI(
            self.screen,
            self.camera_offset,
            self.assets,
            self.mini_map.outline_h + self.mini_map.padding,
            self.player,
            self.sprite_manager,
            self.make_outline,
            self.make_transparent_bg,
            self.render_inventory_item_name,
            self.get_scaled_image,
            self.get_grid_xy
        )

        self.craft_window = CraftWindow(
            self.screen,
            self.camera_offset,
            self.assets, 
            self.inventory_ui, 
            self.sprite_manager,
            self.player,
            self.get_craft_window_height(),
            self.make_outline,
            self.make_transparent_bg,
            self.render_inventory_item_name,
            self.get_scaled_image
        )

        self.HUD = HUD(
            self.screen, 
            self.assets, 
            self.craft_window.outline.right, 
            self.make_outline, 
            self.make_transparent_bg
        )

        self.active_item_names = []

    def get_craft_window_height(self) -> int:
        inv_grid_max_height = self.inventory_ui.box_height * (self.inventory.num_slots // self.inventory_ui.num_cols)
        return inv_grid_max_height + self.mini_map.outline_h + self.mini_map.padding

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

    def render_inventory_item_name(self, rect: pg.Rect, name: str) -> None:
        if rect.collidepoint(pg.mouse.get_pos()):
            font = self.assets['fonts']['item label'].render(name, True, self.assets['colors']['text'])
            self.screen.blit(font, font.get_rect(topleft = rect.bottomleft))

    def render_new_item_name(self, item_name: str, item_rect: pg.Rect) -> None:
        '''render the name of the item that was just picked up'''
        color = self.assets['colors']['text']
        item_total = self.inventory.contents[item_name]['amount']
        world_coords = pg.Vector2(item_rect.midtop)
        self.active_item_names.append(
            ItemName(
                name = item_name,
                color = color,
                alpha = 255,
                font = self.assets['fonts']['item label'].render(f'+1 {item_name} ({item_total})', True, color),
                screen = self.screen,
                camera_offset = self.camera_offset,
                world_coords = world_coords,
                timer = Timer(length = 2000)
            )
        )

    def update_item_name_data(self) -> None:
        for index, cls in enumerate(self.active_item_names):
            cls.update(index)
        
        self.active_item_names = [cls for cls in self.active_item_names if cls.timer.running]

    def get_scaled_image(self, image: pg.Surface, item_name: str, width: int, height: int, padding: int = 0) -> pg.Surface:
        '''returns an image scaled to a given size while accounting for its aspect ratio'''
        bounding_box = (width - (padding * 2), height - (padding * 2))
        aspect_ratio = min(image.width / bounding_box[0], image.height / bounding_box[1]) # avoid stretching an image too wide/tall
        scale = (min(bounding_box[0], image.width * aspect_ratio), min(bounding_box[1], image.height * aspect_ratio))
        return pg.transform.scale(self.assets['graphics'][item_name], scale)

    def get_grid_xy(self, mouse_coords: tuple[int, int], item_size: tuple[int, int], multi_tile: bool = False) -> pg.Vector2:
        x, y = (mouse_coords[0] // TILE_SIZE) * TILE_SIZE, (mouse_coords[1] // TILE_SIZE) * TILE_SIZE
        
        if multi_tile:
            x_offset, y_offset = (item_size[0] // 2) * TILE_SIZE, (item_size[1] // 2) * TILE_SIZE
        else:
            x_offset, y_offset = 0, 0
        
        topleft = pg.Vector2(x - x_offset, y - y_offset)
        return topleft - self.camera_offset

    def update(self, mouse_xy: tuple[int, int], mouse_moving: bool, click_states: dict[str, dict[str, bool]]) -> None:
        self.mouse_grid.update(mouse_xy, mouse_moving, click_states)
        self.HUD.update()
        self.mini_map.update()
        self.craft_window.update(mouse_xy, click_states['left']) # keep above the inventory ui otherwise item names may be rendered behind the window
        self.inventory_ui.update(click_states, mouse_xy)
        self.update_item_name_data()
        

class MouseGrid:
    '''a grid around the mouse position to guide block placement'''
    def __init__(self, screen: pg.Surface, camera_offset: pg.Vector2, get_grid_xy: callable):
        self.screen = screen
        self.camera_offset = camera_offset
        self.get_grid_xy = get_grid_xy

        self.tile_w, self.tile_h = 3, 3

    def render_grid(self, mouse_xy: tuple[int, int], mouse_moving: bool, left_click: bool) -> None:
        if mouse_moving or left_click:
            topleft = self.get_grid_xy(mouse_xy, (self.tile_w, self.tile_h), True)
            for x in range(self.tile_w):
                for y in range(self.tile_h):
                    cell_surf = pg.Surface((TILE_SIZE, TILE_SIZE), pg.SRCALPHA)
                    cell_surf.fill((0, 0, 0, 0))
                    pg.draw.rect(cell_surf, (255, 255, 255, 10), (0, 0, TILE_SIZE, TILE_SIZE), 1) # (0, 0) is relative to the topleft of cell_surf 
                    cell_rect = cell_surf.get_rect(topleft = topleft + pg.Vector2(x * TILE_SIZE, y * TILE_SIZE))
                    self.screen.blit(cell_surf, cell_rect)

    def update(self, mouse_xy: tuple[int, int], mouse_moving, left_click: bool) -> None:
        self.render_grid(mouse_xy, mouse_moving, left_click)


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


class ItemName:
    def __init__(
        self, 
        name: str, 
        color: str, 
        alpha: int,
        font: pg.Font, 
        screen: pg.Surface,
        camera_offset: pg.Vector2,
        world_coords: tuple[int, int],
        timer: Timer
    ):
        self.name = name
        self.color = color
        self.alpha = alpha
        self.font = font
        self.screen = screen
        self.camera_offset = camera_offset
        self.world_coords = world_coords
        self.timer = timer

    def update(self, index: int) -> None:
        if not self.timer.running:
            self.timer.start()
            return
            
        self.timer.update()    
        
        self.alpha = max(0, self.alpha - 2)
        self.font.set_alpha(self.alpha)
        screen_coords = self.world_coords - self.camera_offset
        self.screen.blit(self.font, self.font.get_rect(midbottom = screen_coords))
        self.world_coords[1] -= index + 1 # move north across the screen