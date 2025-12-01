from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player

import pygame as pg

from settings import MACHINES, LOGISTICS, ELECTRICITY, MATERIALS, STORAGE, RESEARCH 
from machine_ui import MachineUI
from sprite_bases import InvSlot

class AssemblerUI(MachineUI):
    def __init__(
        self, 
        machine: pg.sprite.Sprite,
        screen: pg.Surface, 
        cam_offset: pg.Vector2,
        mouse: Mouse, 
        keyboard: Keyboard,
        player: Player,
        assets: dict[str, dict[str, any]],
        gen_outline: callable,
        gen_bg: callable,
        rect_in_sprite_radius: callable,
        render_item_amount: callable
    ):
        super().__init__(machine, screen, cam_offset, mouse, keyboard, player, assets, gen_outline, gen_bg, rect_in_sprite_radius, render_item_amount)
        self.cols = 3
        self.rows = len(self.machine.item_category_data) // self.cols
        self.category_names = list(self.machine.item_category_data.keys())
        self.category_rect = None
        self.icon_scale = self.box_len * 0.6
        self.category_icons = self.get_icons(self.assets['graphics']['icons'], self.category_names)
        self.machine_icons = None

    def get_icons(self, folder: dict[str, pg.Surface], keys: list[str]) -> dict[str, pg.Surface]:
        return {k: pg.transform.scale(surf.copy(), (self.icon_scale, self.icon_scale)) for k, surf in folder.items() if k in keys}

    def render_item_categories(self) -> None:
        if not self.machine.item_category:
            for x in range(self.cols):
                for y in range(self.rows):
                    outline = pg.Rect(
                        self.bg_rect.topleft + pg.Vector2(self.padding + (x * self.box_len), self.padding + (y * self.box_len)), 
                        (self.box_len, self.box_len)
                    )
                    self.gen_bg(outline, self.colors['ui bg highlight'] if outline.collidepoint(self.mouse.screen_xy) else 'black') 
                    self.gen_outline(outline)
                    category = self.category_names[x + (y * self.cols)]
                    icon = self.icons[category]
                    self.screen.blit(icon, icon.get_rect(center=outline.center))
                    self.get_category_input(outline, category)
        elif not self.machine.item_crafting:
            self.category_rect = pg.Rect(
                self.bg_rect.topleft + pg.Vector2((self.bg_width // 2) - (self.box_len // 2), self.padding), 
                (self.box_len, self.box_len)
            )
            self.screen.blit(self.icons[self.machine.item_category], self.category_rect)
            self.render_item_options()
        else:
            self.render_inv()
    
    def get_category_input(self, input_box: pg.Rect, category: str) -> None:
        if input_box.collidepoint(self.mouse.screen_xy) and self.mouse.buttons_pressed['left']:
            self.machine.item_category = category
            self.machine_icons = self.get_icons(self.assets['graphics'], self.machine.item_category_data[category].keys())

    def render_item_options(self) -> None:
        for i in range(len(self.machine_icons)):
            x, y = divmod(i, self.cols)
            outline = pg.Rect(
                self.bg_rect.topleft + pg.Vector2(self.padding + (x * self.box_len), self.padding + (self.category_rect.bottom - self.bg_rect.top) + (y * self.box_len)), 
                (self.box_len, self.box_len)
            )
            if outline.collidepoint(self.mouse.screen_xy):
                color = self.colors['ui bg highlight']
                if self.mouse.buttons_pressed['left']:
                    category_data = self.machine.item_category_data[self.machine.item_category]
                    print(category_data)
                    self.machine.item_crafting = list(category_data.keys())[i]
                    self.machine.craft_recipe = list(category_data.values())[i]['recipe']
            else:
                color = 'black'
            self.gen_bg(outline, color) 
            self.gen_outline(outline)
            icon = list(self.machine_icons.values())[i]
            self.screen.blit(icon, icon.get_rect(center=outline.center))

    def update_inv_rects(self) -> None:
        for i, item in enumerate(self.machine.craft_recipe):
            rect = pg.Rect(
                self.bg_rect.topleft + pg.Vector2(self.padding + (i * self.box_len), self.padding + (self.category_rect.bottom - self.bg_rect.top)), 
                (self.box_len, self.box_len)
            )
            if item not in self.machine.inv.input_slots:
                self.machine.inv.input_slots[item] = InvSlot(rect=rect, valid_inputs=item)
            else:
                self.machine.inv.input_slots[item].rect = rect
            
    def render_interface(self) -> None:
        self.update_bg_rect()
        self.gen_bg(self.bg_rect, transparent=True)
        self.gen_outline(self.bg_rect)
        self.render_item_categories()