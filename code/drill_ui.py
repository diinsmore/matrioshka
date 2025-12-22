from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from drills import BurnerDrill, ElectricDrill
    from input_manager import Mouse, Keyboard
    from player import Player

import pygame as pg

from machine_ui import MachineUI
from dataclasses import dataclass

@dataclass
class OrePreview:
    available_ores: dict
    rect: pg.Rect=None
    amount: int=0
    box_len: int=60
    idx: int=0


class DrillUI(MachineUI):
    def __init__(
        self, machine: BurnerDrill | ElectricDrill, screen: pg.Surface, cam_offset: pg.Vector2, mouse: Mouse, keyboard: Keyboard, player: Player, 
        assets: dict[str, dict[str, any]], gen_outline: callable, gen_bg: callable, rect_in_sprite_radius: callable, render_item_amount: callable
    ):
        super().__init__(machine, screen, cam_offset, mouse, keyboard, player, assets, gen_outline, gen_bg, rect_in_sprite_radius, render_item_amount)
        self.bg_width, self.bg_height = 200, 150
        self.box_len = 50
        self.ore_preview = OrePreview(dict(zip(self.machine.ore_data.keys(), [self.machine.ore_data[k]['amount'] for k in self.machine.ore_data])))
    
    def update_inv_rects(self) -> None:
        if self.machine.variant == 'burner':
            self.machine.inv.input_slots['fuel'].rect = pg.Rect(self.bg_rect.bottomleft + pg.Vector2(self.padding, -(self.padding + self.box_len)), (self.box_len, self.box_len))
            self.machine.inv.output_slot.rect = pg.Rect(
                self.bg_rect.bottomright - pg.Vector2(self.box_len + self.padding, self.box_len + self.padding), (self.box_len, self.box_len)
            )
        else:
            self.machine.inv.output_slot.rect = pg.Rect(self.bg_rect.midbottom - pg.Vector2(0, self.padding), (self.box_len, self.box_len))
        if not self.machine.target_ore:
            self.ore_preview.rect = pg.Rect(self.bg_rect.midtop - pg.Vector2(self.box_len // 2, -self.padding), (self.box_len, self.box_len))

    def render_ore_preview(self) -> None:  
        self.gen_outline(pg.Rect(self.bg_rect.midtop - pg.Vector2(self.ore_preview.rect.width / 2, -self.padding), self.ore_preview.rect.size))
        if self.machine.target_ore:
            self.gen_bg(self.ore_preview.rect, transparent=True)
            self.gen_outline(self.ore_preview.rect)
            ore_surf = self.graphics[self.machine.target_ore]
            self.screen.blit(ore_surf, ore_surf.get_rect(center=self.ore_preview.rect.center))
        else:
            self.render_ore_options()
        
    def render_ore_options(self) -> None:
        ore_names = list(self.ore_preview.available_ores.keys())
        self.update_target_ore(ore_names)
        name = ore_names[self.ore_preview.idx]
        ore_surf = self.graphics[name]
        self.screen.blit(ore_surf, ore_surf.get_rect(center=self.ore_preview.rect.center))
        name_surf = self.fonts['item label small'].render(name, True, self.colors['text'])
        name_rect = name_surf.get_rect(midtop=self.ore_preview.rect.midbottom)
        self.screen.blit(name_surf, name_rect) 
        amount_surf = self.fonts['item label small'].render(f'available: {self.ore_preview.available_ores[name]}', True, self.colors['text'])
        self.screen.blit(amount_surf, amount_surf.get_rect(midtop=name_rect.midbottom))

    def update_target_ore(self, ore_names: list[str]) -> None:
        num_names = len(ore_names)
        if self.keyboard.pressed_keys[pg.K_RIGHT]:
            self.ore_preview.idx = (self.ore_preview.idx + 1) % num_names
        elif self.keyboard.pressed_keys[pg.K_LEFT]:
            self.ore_preview.idx = (self.ore_preview.idx - 1) % num_names 
        elif self.keyboard.pressed_keys[pg.K_RETURN]:
            ore = ore_names[self.ore_preview.idx]
            self.machine.target_ore = ore
            self.machine.num_ore_available = self.machine.ore_data[ore]['amount']

    def render_interface(self) -> None:
        self.update_bg_rect()
        if self.rect_in_sprite_radius(self.player, self.bg_rect, rect_world_space=False):
            self.gen_bg(self.bg_rect, color='black', transparent=True) 
            self.gen_outline(self.bg_rect)
            self.render_inv()
            self.render_ore_preview()
            if self.machine.target_ore:
                self.render_progress_bar(self.ore_preview.rect, self.machine.alarms['extract'].pct)
            if self.machine.variant == 'burner':
                self.render_progress_bar(self.machine.inv.input_slots['fuel'].rect, self.machine.alarms['burn fuel'].pct)
        else:
            self.render = False