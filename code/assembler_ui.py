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
        self.cols = 3
        self.rows = self.machine.num_categories // self.cols
        self.box_len = 20

    def render_item_categories(self) -> None:
        for x in range(self.cols):
            for y in range(self.rows):
                category_rect = pg.Rect(
                    self.bg_rect.topleft + (pg.Vector2(self.padding + (x * self.box_len), self.padding + (y * self.box_len))), 
                    (self.bg_width, self.bg_height)
                )
                pg.draw.rect(self.screen, 'black', category_rect, 1)

    def render_interface(self) -> None:
        self.update_bg_rect()
        self.gen_bg(self.bg_rect, transparent=True)
        self.gen_outline(self.bg_rect)
        self.render_item_categories()