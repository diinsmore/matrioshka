from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from inventory import Inventory

import pygame as pg

from settings import TILE_SIZE

class InvUI:
    def __init__(
        self, 
        inv: Inventory, 
        screen: pg.Surface, 
        assets: dict[str, dict[str, any]], 
        top: int,
        get_outline: callable
    ):
        self.inv = inv
        self.screen = screen
        self.assets = assets
        self.padding = 5
        self.top = top + self.padding
        self.get_outline = get_outline

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
                icon_image = self.graphics[name]
                
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
        amount_image = self.assets['fonts']['number'].render(str(amount), False, self.assets['colors']['text'])
        amount_rect = amount_image.get_rect(center = coords - pg.Vector2(0, 2))
        self.screen.blit(amount_image, amount_rect)

    def render_item_name(self, icon_rect: pg.Rect, name: str) -> None:
        if pg.mouse.get_rel():
            # render when the mouse hovers over the icon
            if icon_rect.collidepoint(pg.mouse.get_pos()):
                font = self.assets['fonts']['label'].render(name, True, self.assets['colors']['text'])
                font_rect = font.get_rect(topleft = icon_rect.bottomright)
                self.screen.blit(font, font_rect)

    def update(self) -> None:
        if self.render:
            self.update_dimensions()
            self.render_bg()
            self.render_slots()
            self.render_icons()