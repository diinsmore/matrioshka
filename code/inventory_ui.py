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
        player: Player,
        sprite_manager: SpriteManager,
        screen: pg.Surface,
        camera_offset: pg.Vector2,
        assets: dict[str, dict[str, any]], 
        top: int,
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
        self.render = True
        self.expand = False
        self.outline = pg.Rect(self.padding, self.top, self.total_width, self.total_height)

        self.drag = False
        self.image_to_drag, self.rect_to_drag = None, None
    
    def update_dimensions(self) -> None:
        # the number of columns is static
        self.num_rows = 2 if not self.expand else self.num_slots // self.num_cols
        self.total_height = self.box_height * self.num_rows

    def render_bg(self) -> None:
        rect = pg.Rect(self.padding, self.top, self.total_width, self.total_height)
        outline = self.make_outline(rect)
        self.make_transparent_bg(rect)
        
    def render_slots(self) -> None:
        for x in range(self.num_cols):
            for y in range(self.num_rows):
                box = pg.Rect(
                    (self.padding, self.top) + pg.Vector2(x * self.box_width, y * self.box_height), 
                    (self.box_width - 1, self.box_height - 1) # -1 for a slight gap between boxes
                )
                pg.draw.rect(self.screen, 'black', box, 1)

    def render_icons(self, click_states: dict[str, bool], mouse_coords: tuple[int, int]) -> None:
        contents = self.inventory.contents.items()
        for item_name, item_data in contents:
            try:
                icon_image = self.get_icon_image(item_name)
                # determine the slot an item corresponds to
                col = item_data['index'] % self.num_cols
                row = item_data['index'] // (self.num_rows if self.expand else self.num_slots // self.num_cols)
                
                # render at the center of the inventory slot
                x = self.outline.left + (col * self.box_width) + (icon_image.get_width() // 2)
                y = self.outline.top + (row * self.box_height) + (icon_image.get_height() // 2)

                icon_rect = icon_image.get_rect(topleft = (x, y))
                self.screen.blit(icon_image, icon_rect)

                self.render_item_amount(item_data['amount'], (x, y))
                self.render_item_name(icon_rect, item_name)

                self.drag_item(click_states, mouse_coords, item_name, icon_rect)
            except KeyError:
                pass

    def get_icon_image(self, item_name: str) -> pg.Surface:
        image = self.graphics[item_name]
        target_size = (TILE_SIZE, TILE_SIZE)
        if image.get_size() != target_size:
            image = self.get_scaled_image(image, item_name, *target_size)
        return image

    def render_item_amount(self, amount: int, coords: tuple[int, int]) -> None:
        amount_image = self.assets['fonts']['number'].render(str(amount), False, self.assets['colors']['text'])
        
        # move the text 5 pixels further to the right for each digit > 2
        num_digits = len(str(amount))
        x_offset = 5 * (num_digits - 2) if num_digits > 2 else 0

        amount_rect = amount_image.get_rect(center = coords + pg.Vector2(x_offset, -2))
        self.make_transparent_bg(amount_rect)
        self.screen.blit(amount_image, amount_rect)
    
    def drag_item(self, click_states: dict[str, bool], mouse_coords: tuple[int, int], item_name: str, icon_rect: pg.Rect):
        if click_states['left']:
            mouse_rel_screen = pg.mouse.get_pos() # the mouse_coords parameter is relative to the world-space | TODO: fix the naming convention for the mouse coordinates 
            self.drag = self.update_drag_state(item_name, icon_rect)
            if self.drag: # starting to drag
                if not self.image_to_drag:
                    self.image_to_drag = self.graphics[self.player.item_holding]
                    self.rect_to_drag = self.image_to_drag.get_rect(center = mouse_rel_screen)
            else: # end by placing the item
                tile_coords = (mouse_coords[0] // TILE_SIZE, mouse_coords[1] // TILE_SIZE) # not converting to a vector2 since the values need to be ints to index the tile map
                self.sprite_manager.item_placement.place_item(item_name, self.rect_to_drag, tile_coords)
                self.image_to_drag, self.rect_to_drag = None, None
        else: # continue dragging until a left click is detected
            if self.drag:
                mouse_rel_screen = pg.mouse.get_pos()
                self.rect_to_drag.center = mouse_rel_screen
                self.screen.blit(self.image_to_drag, self.rect_to_drag)
            
    def update_drag_state(self, item_name: str, icon_rect: pg.Rect) -> bool: 
        '''start/stop dragging'''
        if not self.drag and icon_rect.collidepoint(pg.mouse.get_pos()): # not using mouse_coords since i'd have to convert it to screen-space
            self.player.item_holding = list(self.inventory.contents)[self.get_inventory_item_index(item_name)]
            return True
        return False

    def get_inventory_item_index(self, item_name: str) -> int:
        for name, data in self.inventory.contents.items():
            if name == item_name:
                return data['index']

    def update(self, click_states: dict[str, bool], mouse_coords: tuple[int, int]) -> None:
        if self.render:
            self.update_dimensions()
            self.render_bg()
            self.render_slots()
            self.render_icons(click_states, mouse_coords)