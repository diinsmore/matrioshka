from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player

import pygame as pg
from math import ceil

from settings import MACHINES, LOGISTICS, ELECTRICITY, MATERIALS, STORAGE, RESEARCH 
from machine_ui import MachineUI
from sprite_bases import InvSlot

class AssemblerUI(MachineUI):
    def __init__(
        self, machine: pg.sprite.Sprite, screen: pg.Surface, cam_offset: pg.Vector2, mouse: Mouse, keyboard: Keyboard, player: Player, 
        assets: dict[str, dict[str, any]], gen_outline: callable, gen_bg: callable, rect_in_sprite_radius: callable, render_item_amount: callable
    ):
        super().__init__(machine, screen, cam_offset, mouse, keyboard, player, assets, gen_outline, gen_bg, rect_in_sprite_radius, render_item_amount)
        self.category_names = list(self.machine.item_category_data.keys())
        self.category_cols = 3
        self.category_rows = ceil(len(self.category_names) / self.category_cols)
        self.category_rect = None
        self.item_rows, self.item_cols = None, None
        self.icon_scale = self.box_len * 0.6
        self.category_icons = self.get_icons(self.graphics['icons'], self.category_names)
        self.machine_icons, self.item_surf = None, None
        self.inv_box_len = 30
        self.update_bg_dimensions()

    def get_icons(self, folder: dict[str, pg.Surface], keys: list[str], scale: int=None) -> dict[str, pg.Surface]:
        if scale is None:
            scale = self.icon_scale
        return {k: pg.transform.scale(surf.copy(), (scale, scale)) for k, surf in folder.items() if k in keys}

    def update_bg_dimensions(self) -> None:
        if not self.machine.item_category:
            self.bg_w = (self.category_cols * self.box_len) + ((self.category_cols + 1) * self.padding)
            self.bg_h = (self.category_rows * self.box_len) + ((self.category_rows + 1) * self.padding)
            self.update_bg_rect()
        elif not self.machine.item:
            num_icons = max(1, len(self.machine_icons)) # TODO: remove the max when you have all the graphics
            self.item_cols = min(5, num_icons)
            self.item_rows = ceil(num_icons / self.item_cols)
            self.bg_w = (self.item_cols * self.inv_box_len) + ((self.item_cols + 1) * self.padding)
            self.bg_h = (self.item_rows * self.inv_box_len) + ((self.item_rows + 1) * self.padding) + self.padding + self.box_len # last 2 additions to save room for the category rect
        else:
            num_slots = len(self.machine.recipe) + 1 # plus the output slot
            self.bg_w = (num_slots * self.inv_box_len) + (self.padding * ((num_slots % self.item_cols) + 1))
            self.bg_h = self.inv_box_len + self.category_rect.height + (self.padding * (self.item_rows + 1))

    def render_item_categories(self) -> None:
        if not self.machine.item_category:
            for x in range(self.category_cols):
                for y in range(self.category_rows):
                    outline = pg.Rect(
                        self.bg_rect.topleft + pg.Vector2((self.padding * (x + 1)) + (x * self.box_len), (self.padding * (y + 1)) + (y * self.box_len)), 
                        (self.box_len, self.box_len)
                    )
                    self.gen_bg(outline, self.colors['ui bg highlight'] if outline.collidepoint(self.mouse.screen_xy) else 'black') 
                    self.gen_outline(outline)
                    category = self.category_names[x + (y * self.category_cols)]
                    icon = self.icons[category]
                    self.screen.blit(icon, icon.get_rect(center=outline.center))
                    self.get_category_input(outline, category)
        elif not self.machine.item:
            self.category_rect = pg.Rect(self.bg_rect.topleft + pg.Vector2((self.bg_w // 2) - (self.box_len // 2), self.padding), (self.box_len, self.box_len))
            self.screen.blit(self.icons[self.machine.item_category], self.category_rect)
            self.render_item_options()
        else:
            self.category_rect = pg.Rect(self.bg_rect.topleft + pg.Vector2((self.bg_w // 2) - (self.box_len // 2), self.padding), (self.box_len, self.box_len))
            self.screen.blit(self.item_surf, self.category_rect)
            self.render_inv(slot_preview=True)
    
    def get_category_input(self, input_box: pg.Rect, category: str) -> None:
        if input_box.collidepoint(self.mouse.screen_xy) and self.mouse.buttons_pressed['left']:
            self.machine.item_category = category
            self.machine_icons = self.get_icons(self.graphics, self.machine.item_category_data[category].keys())
            self.update_bg_dimensions() 

    def render_item_options(self) -> None:
        icons = list(self.machine_icons.values())
        y = self.category_rect.bottom - self.bg_rect.top
        for i in range(len(icons)):
            row, col = divmod(i, self.item_cols)
            outline = pg.Rect(
                self.bg_rect.topleft + pg.Vector2((self.padding * (col + 1)) + (col * self.inv_box_len), y + (self.padding * (row + 1)) + (row * self.inv_box_len)), 
                (self.inv_box_len, self.inv_box_len)
            )
            if outline.collidepoint(self.mouse.screen_xy):
                color = self.colors['ui bg highlight']
                if self.mouse.buttons_pressed['left']:
                    self.machine.assign_item(i)
                    self.item_surf = pg.transform.scale(self.graphics[self.machine.item].copy(), self.category_rect.size)
                    self.update_bg_dimensions()
            else:
                color = 'black'
            self.gen_bg(outline, color) 
            self.gen_outline(outline)
            icon = icons[i]
            self.screen.blit(icon, icon.get_rect(center=outline.center))

    def update_inv_rects(self) -> None:
        y = self.padding + self.category_rect.bottom - self.bg_rect.top
        for i, item in enumerate(self.machine.recipe):
            rect = pg.Rect(self.bg_rect.topleft + pg.Vector2((self.padding * (i + 1)) + (i * self.inv_box_len), y), (self.inv_box_len, self.inv_box_len))
            if item not in self.machine.inv.input_slots:
                self.inv.input_slots[item] = InvSlot(item, rect, valid_inputs={item})
            else:
                self.inv.input_slots[item].rect = rect

    def undo_selection(self) -> None:
        if self.keyboard.pressed_keys[pg.K_x] and self.machine.rect.collidepoint(self.mouse.world_xy):
            self.machine.item_category, self.machine_icons = None, None
            self.update_bg_dimensions()
            
    def render_interface(self) -> None:
        self.update_bg_rect()
        self.gen_bg(self.bg_rect, transparent=True)
        self.gen_outline(self.bg_rect)
        self.render_item_categories()
        self.undo_selection()