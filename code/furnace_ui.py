from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player

import pygame as pg
from machine_ui import MachineUI
    
class FurnaceUI(MachineUI):
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
        self.y_offset = self.padding if self.machine.variant == 'burner' else (self.box_len // 2)
        self.progress_bar_height = 4
        self.right_arrow_surf = self.icons['right arrow'].convert()
        if self.machine.variant == 'burner':
            self.fuel_icon = self.icons['fuel'].convert()
            self.fuel_icon.set_colorkey((255, 255, 255))

    def update_inv_rects(self) -> None:
        self.machine.inv.input_slots['smelt'].rect = pg.Rect(self.bg_rect.topleft + pg.Vector2(self.padding, self.y_offset), (self.box_len, self.box_len))
        self.machine.inv.output_slot.rect = pg.Rect(self.bg_rect.midright - pg.Vector2(self.box_len + self.padding, self.box_len // 2), (self.box_len, self.box_len))
        if self.machine.variant == 'burner': 
            self.machine.inv.input_slots['fuel'].rect = pg.Rect(self.bg_rect.bottomleft - pg.Vector2(-self.padding, self.box_len + self.padding), (self.box_len, self.box_len))
        
    def render_interface(self) -> None:
        self.update_bg_rect()
        self.gen_bg(self.bg_rect, color='black', transparent=True) 
        self.gen_outline(self.bg_rect)
        self.render_inv()
        self.screen.blit(self.right_arrow_surf, self.right_arrow_surf.get_rect(center=self.bg_rect.center))
        if self.machine.variant == 'burner':
            offset = pg.Vector2(0, (self.machine.inv.input_slots['fuel'].rect.top - self.machine.inv.input_slots['smelt'].rect.bottom) // 2)
            self.screen.blit(self.fuel_icon, self.fuel_icon.get_rect(center=self.machine.inv.input_slots['smelt'].rect.midbottom + offset))
        if self.machine.active and 'smelt' in self.machine.timers:
            self.render_progress_bar(self.machine.inv.input_slots['smelt'].rect, self.machine.timers['smelt'].percent)
            if self.machine.variant == 'burner':
                self.render_progress_bar(self.machine.inv.input_slots['fuel'].rect, self.machine.timers['fuel'].percent)