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
        self.bg_w, self.bg_h = 200, 150
        self.box_w = self.box_h = 50
        self.progress_bar_w, self.progress_bar_h = self.box_w, 4
        self.ore_select_idx = 0
        self.bg_rect = self.get_bg_rect()

    def get_box_data(self) -> dict[str, dict]|None:
        self.output_rect = pg.Rect(self.bg_rect.bottomright - pg.Vector2(self.box_w + self.padding, self.box_h + self.padding), (self.box_w, self.box_h))
        box_data = {'output': {'contents': {'item': None, 'amount': None}, 'rect': self.output_rect}}
        
        if self.machine.variant == 'burner':
            self.fuel_box = pg.Rect(self.bg_rect.bottomleft + pg.Vector2(self.padding, -(self.padding + self.box_h)), (self.box_w, self.box_h))
            box_data['fuel'] = {'contents': self.machine.fuel_input, 'valid inputs': self.machine.fuel_sources, 'rect': self.fuel_box}
        
        if self.machine.target_ore:
            pass
        else:
            ores = self.machine.available_ores
            box_data['available ores'] = {
                'contents': {'names': ores.keys(), 'amount': ores.values()}, 
                'rect': pg.Rect(self.bg_rect.midtop + pg.Vector2(-(self.box_w // 2), self.padding), (self.box_w, self.box_h))
            }
        return box_data

    def render_boxes(self) -> None:
        data = self.get_box_data()
        for k in data:
            contents, rect = data[k]['contents'], data[k]['rect']
            self.gen_bg(rect, color=self.highlight_color if rect.collidepoint(self.mouse.screen_xy) else 'black', transparent=False) 
            self.gen_outline(rect)
            if k != 'available ores':
                if contents['item']: 
                    self.render_box_contents(contents, rect)
            else:
                self.render_ore_options(contents, rect)   
        
        if self.machine.target_ore:
            self.ore_surf_outline = pg.Rect(self.bg_rect.midtop, self.fuel_box.size) # a class attribute to access later in render_interface
            self.gen_outline(self.ore_surf_outline)
            ore_surf = self.graphics[self.machine.target_ore]
            self.screen.blit(ore_surf, ore_surf.get_rect(center=self.ore_surf_outline.center))

    def render_ore_options(self, contents: dict[str, int], rect: pg.Rect) -> None:
        names = list(contents['names'])
        self.update_target_ore(names)
        name = names[self.ore_select_idx]

        ore_surf = self.graphics[name]
        self.screen.blit(ore_surf, ore_surf.get_rect(center=rect.center))

        name_surf = self.fonts['item label small'].render(name, True, self.assets['colors']['text'])
        name_rect = name_surf.get_rect(midtop=rect.midbottom)
        self.screen.blit(name_surf, name_rect) 
        amount_surf = self.fonts['item label small'].render(f'available: {list(contents["amount"])[self.ore_select_idx]}', True, self.assets['colors']['text'])
        self.screen.blit(amount_surf, amount_surf.get_rect(midtop=name_rect.midbottom))

    def update_target_ore(self, names: list[str]) -> None:
        num_names = len(names)
        if self.keyboard.pressed_keys[pg.K_RIGHT]:
            self.ore_select_idx = (self.ore_select_idx + 1) % num_names
        elif self.keyboard.pressed_keys[pg.K_LEFT]:
            self.ore_select_idx = (self.ore_select_idx - 1) % num_names
        elif self.keyboard.pressed_keys[pg.K_RETURN]:
            self.machine.target_ore = names[self.ore_select_idx]
            
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