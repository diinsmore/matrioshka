from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player

import pygame as pg
from machine_ui import MachineUI

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
        self.bg_width, self.bg_height = int(self.machine.rect.width * 1.2), int(self.machine.rect.height * 1.2)
        self.option_cols = 3
        self.option_rows = self.machine.num_categories // self.cols

    def render_item_categories(self) -> None:
        self.gen_outline()
        for x in range(self.cols):
            for y in range(self.rows):
                pass