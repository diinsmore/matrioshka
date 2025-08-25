from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player

import pygame as pg

from sprite_base import SpriteBase
from settings import TILE_SIZE

class Drill(SpriteBase):
    def __init__(
        self, 
        coords: pg.Vector2, 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group],
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        mouse: Mouse,
        keyboard: Keyboard,
        player: Player,
        assets: dict[str, dict[str, any]],
        gen_outline: callable,
        gen_bg: callable,
        rect_in_sprite_radius: callable,
        render_item_amount: callable,
        save_data: dict[str, any]
    ):
        super().__init__(coords, image, z, sprite_groups, cam_offset, rect_in_sprite_radius)
        self.screen = screen
        self.cam_offset = cam_offset
        self.mouse = mouse
        self.keyboard = keyboard
        self.player = player
        self.assets = assets
        self.gen_outline = gen_outline
        self.gen_bg = gen_bg
        self.render_item_amount = render_item_amount

        self.target_ore = save_data['target ore'] if save_data else {} # key: ore, value: amount available
        self.output = save_data['output'] if save_data else {}
        self.reach_radius = ((image.width // TILE_SIZE) + 2, RES[1] // 5)

    def get_save_data(self) -> dict[str, list|dict]:
        return {
            'xy': list(self.rect.topleft),
            'target ore': self.target_ore,
            'output': self.output
        }