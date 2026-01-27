from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from drills import BurnerDrill, ElectricDrill
    from input_manager import InputManager
    from player import Player
    from ui import UI

import pygame as pg

from machine_ui import MachineUI
from dataclasses import dataclass
from settings import TILE_SIZE

@dataclass
class OreSelectUI:
    available_ores: dict
    rect: pg.Rect=None
    amount: int=0
    box_len: int=(TILE_SIZE * 2) + 2
    idx: int=0


class DrillUI(MachineUI):
    def __init__(
        self, 
        machine: BurnerDrill | ElectricDrill, 
        screen: pg.Surface, 
        cam_offset: pg.Vector2, 
        input_manager: InputManager, 
        player: Player, 
        assets: dict[str, dict[str, any]], 
        ui: UI, 
        rect_in_sprite_radius: callable, 
    ):
        super().__init__(machine, screen, cam_offset, input_manager, player, assets, ui, rect_in_sprite_radius)
        self.bg_width, self.bg_height = 200, 150
        self.box_len = 40
        self.ore_names = list(self.machine.ore_data.keys())
        self.num_ores = len(self.ore_names)
        self.ore_surfs = {k: pg.transform.scale2x(self.graphics[k]) for k in self.ore_names}
        self.select_ui = OreSelectUI(dict(zip(self.machine.ore_data.keys(), [self.machine.ore_data[k]['amount'] for k in self.machine.ore_data])))

    def update_inv_rects(self) -> None:
        if self.machine.variant == 'burner':
            self.machine.inv.input_slots['fuel'].rect = pg.Rect(self.bg_rect.bottomleft + pg.Vector2(self.padding, -(self.padding + self.box_len)), (self.box_len, self.box_len))
            self.machine.inv.output_slot.rect = pg.Rect(
                self.bg_rect.bottomright - pg.Vector2(self.box_len + self.padding, self.box_len + self.padding), (self.box_len, self.box_len)
            )
        else:
            self.machine.inv.output_slot.rect = pg.Rect(self.bg_rect.midbottom - pg.Vector2(0, self.padding), (self.box_len, self.box_len))
        self.select_ui.rect = pg.Rect(self.bg_rect.midtop - pg.Vector2(self.select_ui.box_len // 2, -self.padding), (self.select_ui.box_len, self.select_ui.box_len))

    def render_ore_select_ui(self) -> None:
        self.gen_outline(self.select_ui.rect)
        name = self.ore_names[self.select_ui.idx]
        if not self.machine.target_ore:
            self.update_target_ore() 
        elif not self.machine.inv.output_slot.amount: # fade in a preview of the ore as it's extracted for the 1st time
            ore_preview_surf = self.graphics[name].copy()
            ore_preview_surf.set_alpha(155 + int(self.machine.alarms['extract'].pct))
            self.screen.blit(ore_preview_surf, ore_preview_surf.get_rect(center=self.machine.inv.output_slot.rect.center))
        ore_surf = self.ore_surfs[name] 
        self.screen.blit(ore_surf, ore_surf.get_rect(center=self.select_ui.rect.center))
        name_surf = self.fonts['item label small'].render(name, True, self.colors['text'])
        name_rect = name_surf.get_rect(midtop=self.select_ui.rect.midbottom + pg.Vector2(0, self.padding // 2))
        self.screen.blit(name_surf, name_rect) 
        amount_surf = self.fonts['item label small'].render(f'available: {self.machine.ore_data[name]["amount"]}', True, self.colors['text'])
        self.screen.blit(amount_surf, amount_surf.get_rect(midtop=name_rect.midbottom))

    def update_target_ore(self) -> None:
        if self.keyboard.pressed_keys[pg.K_RIGHT]:
            self.select_ui.idx = (self.select_ui.idx + 1) % self.num_ores
        elif self.keyboard.pressed_keys[pg.K_LEFT]:
            self.select_ui.idx = (self.select_ui.idx - 1) % self.num_ores 
        elif self.keyboard.pressed_keys[pg.K_RETURN]:
            ore = self.ore_names[self.select_ui.idx]
            self.machine.target_ore = ore
            self.machine.num_ore_available = self.machine.ore_data[ore]['amount']

    def render_interface(self) -> None:
        self.update_bg_rect()
        if self.rect_in_sprite_radius(self.player, self.bg_rect, rect_world_space=False):
            self.gen_bg(self.bg_rect, color='black', transparent=True) 
            self.gen_outline(self.bg_rect)
            self.render_inv()
            self.render_ore_select_ui()
            if self.machine.target_ore:
                self.render_progress_bar(self.machine.inv.output_slot.rect, self.machine.alarms['extract'].pct, color=self.colors['progress bar'])
                if self.machine.variant == 'burner':
                    self.render_progress_bar(self.machine.inv.input_slots['fuel'].rect, self.machine.alarms['burn fuel'].pct, color=self.colors['progress bar'])
        else:
            self.render = False