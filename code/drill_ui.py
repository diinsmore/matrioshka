from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from drills import BurnerDrill, ElectricDrill
    from input_manager import Mouse, Keyboard
    from player import Player

import pygame as pg
from machine_ui import MachineUI

class DrillUI(MachineUI):
    def __init__(
        self, 
        machine: BurnerDrill|ElectricDrill,
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
        self.bg_w, self.bg_h = 100, 150
        self.box_w = self.box_h = 25
        self.progress_bar_w, self.progress_bar_h = self.box_w, 4
        self.bg_rect = self.get_bg_rect()

    def get_box_data(self) -> dict[str, dict]|None:
        self.fuel_box = pg.Rect(self.bg_rect.midbottom - pg.Vector2(self.box_w, (self.box_h * 2) + self.padding), (50, 50))
        return {'smelt': {'contents': self.machine.fuel_input, 'valid inputs': self.machine.fuel_sources, 'rect': self.fuel_box}}

    def render_boxes(self) -> None:
        if self.machine.variant == 'burner':
            data = self.get_box_data()
            for k in data:
                contents, rect = data[k]['contents'], data[k]['rect']
                self.gen_bg(rect, color=self.highlight_color if rect.collidepoint(self.mouse.screen_xy) else 'black', transparent=False) 
                self.gen_outline(rect)
                if contents['item']: 
                    self.render_box_contents(contents, rect)   
        
        if self.machine.target_ore:
            self.ore_surf_outline = pg.Rect(self.bg_rect.midtop, self.fuel_box.size) # a class attribute to access later in render_interface
            self.gen_outline(self.ore_surf_outline)
            ore_surf = self.graphics[self.machine.target_ore]
            self.screen.blit(ore_surf, ore_surf.get_rect(center=self.ore_surf_outline.center))

    def render_interface(self) -> None:
        self.bg_rect = self.get_bg_rect()
        if self.rect_in_sprite_radius(self.player, self.bg_rect):
            self.bg_rect.topleft -= self.cam_offset # converting to screen-space now to not mess with the radius check above
            self.gen_bg(self.bg_rect, color='black', transparent=True) 
            self.gen_outline(self.bg_rect)
            self.render_boxes()
            if self.machine.active:
                self.render_progress_bar(self.ore_surf_outline, self.machine.timers['extract'].progress_percent)
                if self.machine.variant == 'burner':
                    self.render_progress_bar(self.fuel_box, self.machine.timers['fuel'].progress_percent)
        else:
            self.render = False