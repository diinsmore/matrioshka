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
        self.bg_width, self.bg_height = 200, 150
        self.box_width = self.box_height = 50
        self.progress_bar_width, self.progress_bar_height = self.box_width, 4
        self.ore_selection_idx = 0
        self.ore_box_outline_dims = pg.Vector2(self.box_width, self.box_height) * 1.2

    def get_inv_box_data(self) -> dict[str, dict]:
        data = {
            'output': {
                'contents': {
                    'item': self.machine.target_ore, 'amount': self.machine.num_ore_output,
                },
            },
        }
        if self.machine.variant == 'burner':
            data['fuel'] = {
                'contents': self.machine.fuel_input, 
                'valid inputs': self.machine.fuel_sources,
                'rect': pg.Rect(self.bg_rect.bottomleft + pg.Vector2(self.padding, -(self.padding + self.box_height)), (self.box_width, self.box_height))
            }
            data['output']['rect'] = pg.Rect(
                self.bg_rect.bottomright - pg.Vector2(self.box_width + self.padding, self.box_height + self.padding), 
                (self.box_width, self.box_height)
            )
        else:
            data['output']['rect'] = pg.Rect(self.bg_rect.midbottom - pg.Vector2(0, self.padding), (self.box_width, self.box_height))

        return data

    def get_ore_preview_box_data(self) -> dict[str, dict]:
        rect = pg.Rect(self.bg_rect.midtop - pg.Vector2(self.box_width // 2, -self.padding), (self.box_width, self.box_height))
        if self.machine.target_ore:
            return {'contents': {'item': self.machine.target_ore, 'amount': self.machine.num_ore_available}, 'rect': rect}
        else:
            ores = self.machine.available_ores
            return {'contents': {'names': ores.keys(), 'amount': ores.values()}, 'rect': rect}

    def render_ore_preview_box(self) -> None:  
        data = self.get_ore_preview_box_data()

        outline = pg.Rect(self.bg_rect.midtop - pg.Vector2(self.ore_box_outline_dims.x / 2, -self.padding), self.ore_box_outline_dims)
        self.gen_outline(outline)

        if ore := self.machine.target_ore:
            self.render_box_contents(ore, self.machine.num_ore_available, data['rect'])
        else:
            self.render_ore_options(data['contents'], data['rect'])
        
    def render_ore_options(self, ore_data: dict[str, any], rect: pg.Rect) -> None:
        names = list(ore_data['names'])
        self.update_target_ore(names)

        name = names[self.ore_selection_idx]
        ore_surf = self.graphics[name]
        self.screen.blit(ore_surf, ore_surf.get_rect(center=rect.center))

        name_surf = self.fonts['item label small'].render(name, True, self.assets['colors']['text'])
        name_rect = name_surf.get_rect(midtop=rect.midbottom)
        self.screen.blit(name_surf, name_rect) 

        amount_surf = self.fonts['item label small'].render(f'available: {list(ore_data["amount"])[self.ore_selection_idx]}', True, self.assets['colors']['text'])
        self.screen.blit(amount_surf, amount_surf.get_rect(midtop=name_rect.midbottom))

    def update_target_ore(self, names: list[str]) -> None:
        num_names = len(names)
        if self.keyboard.pressed_keys[pg.K_RIGHT]:
            self.ore_selection_idx = (self.ore_selection_idx + 1) % num_names
        elif self.keyboard.pressed_keys[pg.K_LEFT]:
            self.ore_selection_idx = (self.ore_selection_idx - 1) % num_names
        elif self.keyboard.pressed_keys[pg.K_RETURN]:
            self.machine.target_ore = names[self.ore_selection_idx]    

    def render_interface(self) -> None:
        self.bg_rect = self.get_bg_rect()
        if self.rect_in_sprite_radius(self.player, self.bg_rect):
            self.bg_rect.topleft -= self.cam_offset # converting to screen-space now to not mess with the radius check above
            self.gen_bg(self.bg_rect, color='black', transparent=True) 
            self.gen_outline(self.bg_rect)
            self.render_boxes(self.get_inv_box_data)
            self.render_ore_preview_box() # render_boxes() can't be re-used for the ore preview box since it doesn't account for the ore selection process
            if self.machine.active:
                self.render_progress_bar(self.ore_surf_outline, self.machine.timers['extract'].progress_percent)
                if self.machine.variant == 'burner':
                    self.render_progress_bar(self.fuel_box, self.machine.timers['fuel'].progress_percent)
        else:
            self.render = False