from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player
    from furnaces import BurnerFurnace, ElectricFurnace
    from machine_ui import MachineUIDimensions

import pygame as pg
from machine_ui import MachineUI

class FurnaceUI(MachineUI):
    def __init__(
        self, 
        machine: BurnerFurnace|ElectricFurnace,
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
        self.bg_width = self.bg_height = 150
        self.box_w = self.box_h = 40
        self.progress_bar_w, self.progress_bar_h = self.box_w, 4
        self.padding = 10
        self.right_arrow_surf = self.icons['right arrow']
        if machine.variant == 'burner':
            self.fuel_icon = self.icons['fuel'].convert()
            self.fuel_icon.set_colorkey((255, 255, 255))

    def get_inv_box_rects(self) -> tuple[pg.Rect, pg.Rect|None, pg.Rect]:
        y_offset = self.padding if self.machine.variant == 'burner' else (self.box_h // 2)
        smelt_box = pg.Rect(self.bg_rect.topleft + pg.Vector2(self.padding, y_offset), (self.box_w, self.box_h))
        fuel_box = None
        if self.machine.variant == 'burner': 
            fuel_box = smelt_box.copy() 
            fuel_box.bottomleft = self.bg_rect.bottomleft + pg.Vector2(self.padding, -self.padding)
        output_box = smelt_box.copy() 
        output_box.midright = self.bg_rect.midright - pg.Vector2(self.padding, 0)
        return smelt_box, fuel_box, output_box 
    
    def get_inv_box_data(self) -> dict[str, dict]:
        self.smelt_box, self.fuel_box, self.output_box = self.get_inv_box_rects()
        data = {
            'smelt': {'contents': self.machine.smelt_input, 'valid inputs': self.machine.can_smelt.keys(), 'rect': self.smelt_box}, 
            'output': {'contents': self.machine.output, 'valid inputs': self.machine.output['item'], 'rect': self.output_box}
        }
        if self.machine.variant == 'burner':
            data['fuel'] = {'contents': self.machine.fuel_input, 'valid inputs': self.machine.fuel_sources, 'rect': self.fuel_box}
        return data
 
    def render_interface(self) -> None:
        self.bg_rect = self.get_bg_rect()
        if self.rect_in_sprite_radius(self.player, self.bg_rect):
            self.bg_rect.topleft -= self.cam_offset # converting to screen-space now to not mess with the radius check above
            self.gen_bg(self.bg_rect, color='black', transparent=True) 
            self.gen_outline(self.bg_rect)
            self.render_boxes()
            self.screen.blit(self.right_arrow_surf, self.right_arrow_surf.get_rect(center=self.bg_rect.center))

            if self.machine.variant == 'burner':
                self.screen.blit(self.fuel_icon, self.fuel_icon.get_rect(
                    center=self.smelt_box.midbottom + pg.Vector2(0, (self.fuel_box.top - self.smelt_box.bottom) // 2))
                )
            
            if self.machine.active:
                self.render_progress_bar(self.smelt_box, self.machine.timers['smelt'].progress_percent)
                if self.machine.variant == 'burner':
                    self.render_progress_bar(self.fuel_box, self.machine.timers['fuel'].progress_percent)
        else:
            self.render = False