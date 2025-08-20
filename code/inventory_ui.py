from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from inventory import Inventory
    from player import Player
    from item_placement import ItemPlacement
    from input_manager import Mouse

import pygame as pg

from settings import TILE_SIZE, PLACEABLE_ITEMS

class InventoryUI:
    def __init__(
        self,
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        assets: dict[str, dict[str, any]], 
        mouse: Mouse,
        top: int,
        player: Player,
        item_placement: ItemPlacement,
        mech_sprites: pg.sprite.Group,
        gen_outline: callable,
        gen_bg: callable,
        render_inventory_item_name: callable,
        get_scaled_image: callable,
        get_grid_xy: callable,
        get_sprites_in_radius: callable
    ):  
        self.screen = screen
        self.cam_offset = cam_offset
        self.assets = assets
        self.mouse = mouse
        self.padding = 5
        self.top = top + self.padding
        self.player = player
        self.item_placement = item_placement
        self.mech_sprites = mech_sprites
        self.gen_outline = gen_outline
        self.gen_bg = gen_bg
        self.render_inventory_item_name = render_inventory_item_name
        self.get_scaled_image = get_scaled_image
        self.get_grid_xy = get_grid_xy
        self.get_sprites_in_radius = get_sprites_in_radius
        
        self.graphics = self.assets['graphics']
        self.fonts = self.assets['fonts']
        self.colors = self.assets['colors']

        self.inventory = self.player.inventory
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
        self.gen_outline(rect)
        self.gen_bg(rect, transparent=True)
        
    def render_slots(self) -> None:
        selected_idx = self.inventory.index
        for x in range(self.num_cols):
            for y in range(self.num_rows):
                box = pg.Rect(
                    (self.padding, self.top) + pg.Vector2(x * self.box_width, y * self.box_height), 
                    (self.box_width - 1, self.box_height - 1)  # -1 for a slight gap between boxes
                )
                pg.draw.rect(self.screen, 'black', box, 1)

                if (y * (self.num_rows - 1) * self.num_cols) + x == selected_idx:
                    self.highlight_slot(box)

    def highlight_slot(self, slot: pg.Rect) -> None:
        hl_surf = pg.Surface(slot.size - pg.Vector2(2, 2)) # -2 to not overlap with the 1px borders
        hl_surf.fill('gray')
        hl_surf.set_alpha(50)
        hl_rect = hl_surf.get_rect(topleft = slot.topleft)
        self.screen.blit(hl_surf, hl_rect)
        
    def render_icons(self) -> None:
        for item_name, item_data in list(self.player.inventory.contents.items()): # storing in a list to avoid the 'dictionary size changed during iteration' error when removing placed items
            try:
                icon_image = self.get_icon_image(item_name)

                row, col = divmod(item_data['index'], self.num_cols) # determine the slot an item corresponds to
                
                left = self.outline.left + (col * self.box_width)
                top = self.outline.top + (row * self.box_height)
                
                padding_x = (self.box_width - icon_image.get_width()) // 2
                padding_y = (self.box_height - icon_image.get_height()) // 2

                blit_x = left + padding_x
                blit_y = top + padding_y

                icon_rect = icon_image.get_rect(topleft = (blit_x, blit_y))
                self.screen.blit(icon_image, icon_rect)

                self.render_item_amount(item_data['amount'], (blit_x, blit_y))
                self.render_inventory_item_name(icon_rect, item_name)
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
        self.gen_bg(rect, transparent=True)
        self.screen.blit(image, rect)
    
    def check_drag(self) -> None:
        if self.mouse.click_states['left']:
            if self.drag:
                for machine in self.get_sprites_in_radius(self.player.rect, self.mech_sprites):
                    if machine.ui.render and self.player.item_holding:
                        machine.ui.check_input()
                        if machine.ui.inputting_item:
                            machine.ui.input_item(self.player.item_holding)
                            self.end_drag(machine_input=True)
                            return
                self.end_drag()
            else:
                item = self.get_clicked_item()
                if item:
                    self.player.item_holding = item
                    self.player.inventory.index = self.player.inventory.contents[item]['index']  
                    self.start_drag(item)       
        else:
            if self.drag: 
                item = self.player.item_holding
                self.rect_to_drag.topleft = self.get_grid_xy()
                self.screen.blit(self.image_to_drag, self.rect_to_drag)
                if item in PLACEABLE_ITEMS:
                    item_xy_world = (pg.Vector2(self.rect_to_drag.topleft) + self.cam_offset) // TILE_SIZE
                    self.item_placement.render_ui(
                        self.image_to_drag, 
                        self.rect_to_drag, 
                        (int(item_xy_world.x), int(item_xy_world.y)),
                        self.player
                    )
                            
    def get_clicked_item(self) -> str:
        for item_name, item_data in self.inventory.contents.items():
            col = item_data['index'] % self.num_cols
            row = item_data['index'] // self.num_cols

            left = self.outline.left + (col * self.box_width)
            top = self.outline.top + (row * self.box_height)

            padding_x = (self.box_width - self.icon_size[0]) // 2
            padding_y = (self.box_height - self.icon_size[1]) // 2

            icon_rect = pg.Rect(left + padding_x, top + padding_y, *self.icon_size)
            if icon_rect.collidepoint(self.mouse.screen_xy):
                return item_name

    def start_drag(self, item: str) -> None:
        self.drag = True
        self.image_to_drag = self.graphics[item].copy() # a copy to not alter the alpha value of the original
        self.image_to_drag.set_alpha(150) # slightly transparent until it's placed
        self.rect_to_drag = self.image_to_drag.get_rect(center=self.mouse.world_xy)
 
    def end_drag(self, machine_input: bool = False) -> None: 
        if not machine_input:
            self.item_placement.place_item(
                self.player, 
                self.graphics[self.player.item_holding], 
                (self.mouse.world_xy[0] // TILE_SIZE, self.mouse.world_xy[1] // TILE_SIZE)
            )
        self.drag = False
        self.image_to_drag = self.rect_to_drag = self.player.item_holding = None

    def update(self) -> None:
        if self.render:
            self.update_dimensions()
            self.render_bg()
            self.render_slots()
            self.render_icons()
            self.check_drag()