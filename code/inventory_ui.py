from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player
    
import pygame as pg

from settings import TILE_SIZE
from item_drag import ItemDrag

class InventoryUI:
    def __init__(
        self, screen: pg.Surface, cam_offset: pg.Vector2, assets: dict[str, dict[str, any]], mouse: Mouse, keyboard: Keyboard, top: int, player: Player, 
        mech_sprites: pg.sprite.Group, gen_outline: callable, gen_bg: callable, render_inv_item_name: callable, get_scaled_img: callable, get_grid_xy: callable,
        get_sprites_in_radius: callable, render_item_amount: callable
    ):  
        self.screen = screen
        self.cam_offset = cam_offset
        self.assets = assets
        self.mouse = mouse
        self.keyboard = keyboard
        self.padding = 5
        self.top = top + self.padding
        self.player = player
        self.mech_sprites = mech_sprites
        self.gen_outline = gen_outline
        self.gen_bg = gen_bg
        self.render_inv_item_name = render_inv_item_name
        self.get_scaled_img = get_scaled_img
        self.get_grid_xy = get_grid_xy
        self.get_sprites_in_radius = get_sprites_in_radius
        self.render_item_amount = render_item_amount
        
        self.graphics, self.fonts, self.colors = self.assets['graphics'], self.assets['fonts'], self.assets['colors']
        self.num_cols, self.num_rows = 5, 2
        self.slot_len = TILE_SIZE * 2
        self.outline_width, self.outline_height = self.slot_len * self.num_cols, self.slot_len * self.num_rows
        self.icon_size = pg.Vector2(TILE_SIZE, TILE_SIZE)
        self.icon_padding = ((self.slot_len, self.slot_len) - self.icon_size) // 2
        self.outline = pg.Rect(self.padding, self.top, self.outline_width, self.outline_height)
        self.render = True
        self.expand = False
        self.item_drag = ItemDrag(
            screen, cam_offset, self.graphics, player, mouse, keyboard, self.player.inventory, self.outline, self.slot_len, self.num_cols, self.num_rows, 
            pg.Rect(self.icon_padding, self.icon_size), self.mech_sprites, self.get_grid_xy, self.get_sprites_in_radius
        )
        self.item_placement = None # not initialized yet

    def update_dimensions(self) -> None:
        self.num_rows = 2 if not self.expand else (self.player.inventory.num_slots // self.num_cols)
        self.outline_height = self.slot_len * self.num_rows
        self.outline = pg.Rect(self.padding, self.top, self.outline_width, self.outline_height)

    def render_bg(self) -> None:
        self.gen_bg(self.outline, transparent=True)
        self.gen_outline(self.outline)

    def render_slots(self) -> None:
        selected_idx = self.player.inventory.index
        for x in range(self.num_cols):
            for y in range(self.num_rows):
                box = pg.Rect((self.padding, self.top) + pg.Vector2(x * self.slot_len, y * self.slot_len), (self.slot_len - 1, self.slot_len - 1))
                pg.draw.rect(self.screen, 'black', box, 1)
                if self.player.item_holding and (y * (self.num_rows - 1) * self.num_cols) + x == selected_idx:
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
                surf = self.get_item_surf(item_name)
                row, col = divmod(item_data['index'], self.num_cols) # determine the slot an item corresponds to
                topleft = self.outline.topleft + pg.Vector2(col * self.slot_len, row * self.slot_len)
                padding = (pg.Vector2(self.slot_len, self.slot_len) - surf.get_size()) // 2
                rect = surf.get_rect(topleft=topleft + padding)
                self.screen.blit(surf, rect)
                self.render_item_amount(item_data['amount'], topleft + padding)
                self.render_inv_item_name(rect, item_name)
            except KeyError:
                pass

    def get_item_surf(self, name: str) -> pg.Surface:
        surf = self.graphics[name] 
        return surf if surf.get_size() == self.icon_size else self.get_scaled_img(surf, name, *self.icon_size)

    def update(self) -> None:
        if self.render:
            self.render_bg()
            self.render_slots()
            self.render_icons()
            self.item_drag.update()