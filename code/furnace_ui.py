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
        self.inv = self.machine.inv
        self.box_len = 40
        self.bg_width, self.bg_height = 150, 150
        self.padding = 10 
        self.y_offset = self.padding if self.machine.variant == 'burner' else (self.box_len // 2)
        self.progress_bar_width, self.progress_bar_height = self.box_len, 4
        self.right_arrow_surf = self.icons['right arrow'].convert()
        if self.machine.variant == 'burner':
            self.fuel_icon = self.icons['fuel'].convert()
            self.fuel_icon.set_colorkey((255, 255, 255))

    def update_inv_rects(self) -> None:
        self.inv.smelt.rect = pg.Rect(self.bg_rect.topleft + pg.Vector2(self.padding, self.y_offset), (self.box_len, self.box_len))
        self.inv.output.rect = self.inv.smelt.rect.copy() 
        self.inv.output.rect.midright = self.bg_rect.midright - pg.Vector2(self.padding, 0)
        if self.machine.variant == 'burner': 
            self.inv.fuel.rect = self.inv.smelt.rect.copy() 
            self.inv.fuel.rect.bottomleft = self.bg_rect.bottomleft + pg.Vector2(self.padding, -self.padding)
 
    def render_interface(self) -> None:
        self.update_bg_rect()
        self.bg_rect.topleft -= self.cam_offset # converting to screen-space now to not mess with the radius check above
        self.gen_bg(self.bg_rect, color='black', transparent=True) 
        self.gen_outline(self.bg_rect)
        self.render_inv()
        self.screen.blit(self.right_arrow_surf, self.right_arrow_surf.get_rect(center=self.bg_rect.center))
        if self.machine.variant == 'burner':
            self.screen.blit(self.fuel_icon, self.fuel_icon.get_rect(
                center=self.inv.smelt.rect.midbottom + pg.Vector2(0, (self.inv.fuel.rect.top - self.inv.smelt.rect.bottom) // 2)
            ))
        if self.machine.active and 'smelt' in self.machine.timers:
            self.render_progress_bar(self.inv.smelt.rect, self.machine.timers['smelt'].percent)
            if self.machine.variant == 'burner':
                self.render_progress_bar(self.inv.fuel.rect, self.machine.timers['fuel'].percent)