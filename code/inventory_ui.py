from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from inventory import Inventory
    from player import Player
    from sprite_manager import SpriteManager

import pygame as pg

from settings import TILE_SIZE

class InventoryUI:
    def __init__(
        self, 
        inventory: Inventory,
        screen: pg.Surface,
        camera_offset: pg.Vector2,
        assets: dict[str, dict[str, any]], 
        top: int,
        player: Player,
        sprite_manager: SpriteManager,
        make_outline: callable,
        make_transparent_bg: callable,
        render_item_name: callable,
        get_scaled_image: callable
    ):
        self.inventory = inventory
        self.player = player
        self.sprite_manager = sprite_manager
        self.screen = screen
        self.camera_offset = camera_offset
        self.assets = assets
        self.padding = 5
        self.top = top + self.padding
        self.make_outline = make_outline
        self.make_transparent_bg = make_transparent_bg
        self.render_item_name = render_item_name
        self.get_scaled_image = get_scaled_image

        self.graphics = self.assets['graphics']
        self.fonts = self.assets['fonts']
        self.colors = self.assets['colors']

        self.num_slots = self.inventory.num_slots
        self.num_cols = 5
        self.num_rows = 2
        self.box_width, self.box_height = TILE_SIZE * 2, TILE_SIZE * 2
        self.total_width = self.box_width * self.num_cols
        self.total_height = self.box_height * self.num_rows
        self.icon_size = (TILE_SIZE, TILE_SIZE)
        self.render = True
        self.expand = False
        self.outline = pg.Rect(self.padding, self.top, self.total_width, self.total_height)

        self.drag = False
        self.image_to_drag, self.rect_to_drag = None, None
    
    def update_dimensions(self) -> None:
        self.num_rows = 2 if not self.expand else self.num_slots // self.num_cols
        self.total_height = self.box_height * self.num_rows

    def render_bg(self) -> None:
        rect = pg.Rect(self.padding, self.top, self.total_width, self.total_height)
        self.make_outline(rect)
        self.make_transparent_bg(rect)
        
    def render_slots(self) -> None:
        for x in range(self.num_cols):
            for y in range(self.num_rows):
                box = pg.Rect(
                    (self.padding, self.top) + pg.Vector2(x * self.box_width, y * self.box_height), 
                    (self.box_width - 1, self.box_height - 1)  # -1 for a slight gap between boxes
                )
                pg.draw.rect(self.screen, 'black', box, 1)

    def render_icons(self) -> None:
        contents = list(self.inventory.contents.items()) # storing in a list to avoid the 'dictionary size changed during iteration' error when removing placed items
        for item_name, item_data in contents:
            try:
                icon_image = self.get_icon_image(item_name)
                # determine the slot an item corresponds to
                col = item_data['index'] % self.num_cols
                row = item_data['index'] // self.num_cols
        
                left = self.outline.left + (col * self.box_width)
                top = self.outline.top + (row * self.box_height)
                # center the icon within the inventory slot
                padding_x = (self.box_width - icon_image.get_width()) // 2
                padding_y = (self.box_height - icon_image.get_height()) // 2

                blit_x = left + padding_x
                blit_y = top + padding_y

                icon_rect = icon_image.get_rect(topleft = (blit_x, blit_y))
                self.screen.blit(icon_image, icon_rect)

                self.render_item_amount(item_data['amount'], (blit_x, blit_y))
                self.render_item_name(icon_rect, item_name)
            except KeyError:
                pass

    def get_icon_image(self, item_name: str) -> pg.Surface:
        image = self.graphics[item_name] 
        return image if image.get_size() == self.icon_size else self.get_scaled_image(image, item_name, *self.icon_size)

    def render_item_amount(self, amount: int, coords: tuple[int, int]) -> None:
        image = self.fonts['number'].render(str(amount), False, self.assets['colors']['text'])
        
        num_digits = len(str(amount))
        x_offset = 5 * (num_digits - 2) if num_digits > 2 else 0 # move 3+ digit values to the left by 5px for every remaining digit 

        rect = image.get_rect(center = (coords[0] + x_offset, coords[1] - 2))
        self.make_transparent_bg(rect)
        self.screen.blit(image, rect)
    
    def check_drag(self, left_click: bool) -> None:
        if left_click:
            if not self.drag:
                item = self.get_clicked_item()
                if item:
                    self.player.item_holding = item
                    self.drag = True
                    self.start_drag()
            else:
                self.end_drag(pg.mouse.get_pos())
        else:
            if self.drag: 
                # continue dragging
                self.rect_to_drag.center = self.get_grid_aligned_coords(self.rect_to_drag.size)
                self.screen.blit(self.image_to_drag, self.rect_to_drag)
                tile_coords = (self.rect_to_drag.topleft + self.camera_offset) // TILE_SIZE # assigning the rect's center results in an off by 1 error on the y-axis for objects >1 tile tall
                tile_coords = (int(tile_coords[0]), int(tile_coords[1])) # previously vector2 floats
                self.sprite_manager.item_placement.render_placement_ui(self.image_to_drag, self.rect_to_drag, tile_coords, self.player)
    
    def get_clicked_item(self) -> str | None:
        for item_name, item_data in self.inventory.contents.items():
            col = item_data['index'] % self.num_cols
            row = item_data['index'] // self.num_cols

            left = self.outline.left + (col * self.box_width)
            top = self.outline.top + (row * self.box_height)

            padding_x = (self.box_width - self.icon_size[0]) // 2
            padding_y = (self.box_height - self.icon_size[1]) // 2

            icon_rect = pg.Rect(left + padding_x, top + padding_y, *self.icon_size)
            if icon_rect.collidepoint(pg.mouse.get_pos()):
                return item_name
        return None

    def start_drag(self) -> None:
        self.image_to_drag = self.graphics[self.player.item_holding].copy() # a copy to not alter the alpha value of the original
        self.image_to_drag.set_alpha(150) # slightly transparent until it's placed
        self.rect_to_drag = self.image_to_drag.get_rect(center = pg.mouse.get_pos())
 
    def end_drag(self, mouse_screen_coords: tuple[int, int]) -> None:
        if self.player.item_holding:
            tile_coords = (
                int(mouse_screen_coords[0] + self.camera_offset[0]) // TILE_SIZE,
                int(mouse_screen_coords[1] + self.camera_offset[1]) // TILE_SIZE
            )
            self.sprite_manager.item_placement.place_item(self.player, self.graphics[self.player.item_holding], tile_coords)

        self.drag = False
        self.image_to_drag, self.rect_to_drag = None, None
        self.player.item_holding = None
        
    @staticmethod
    def get_grid_aligned_coords(item_size: tuple[int, int]) -> tuple[int, int]:
        x = round(pg.mouse.get_pos()[0] / TILE_SIZE) * TILE_SIZE 
        y = round(pg.mouse.get_pos()[1] / TILE_SIZE) * TILE_SIZE
        return (
            x + (item_size[0] % TILE_SIZE) + 2, # +2 to not overlap with the mouse grid outline
            y + (item_size[1] % TILE_SIZE) + 2, 
        )

    def update(self, click_states: dict[str, bool], mouse_coords: tuple[int, int]) -> None:
        if self.render:
            self.update_dimensions()
            self.render_bg()
            self.render_slots()
            self.render_icons()
            self.check_drag(click_states['left'])