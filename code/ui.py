from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from inventory import Inventory

import pygame as pg
from settings import RES, TILE_SIZE
from mini_map import MiniMap
from inventory_ui import InvUI
from craft_window import CraftWindow
from mouse_grid import MouseGrid
from hud import HUD

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

        self.mini_map = MiniMap(self.screen, self.assets, self.get_outline)
        self.inv_ui = InvUI(
            self.inv, 
            self.screen, 
            self.assets,
            self.mini_map.height + self.mini_map.padding, 
            self.get_outline
        )
        self.craft_window = CraftWindow(
            self.screen, 
            self.assets, 
            self.inv_ui, 
            self.get_craft_window_height(), 
            self.get_outline
        )
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