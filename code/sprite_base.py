from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player

import pygame as pg

class SpriteBase(pg.sprite.Sprite):
    def __init__(
        self, 
        xy: pg.Vector2,
        image: pg.Surface,
        z: dict[str, int],  
        sprite_groups: list[pg.sprite.Group]
    ):
        super().__init__(*sprite_groups)
        self.xy = xy
        self.image = image
        self.rect = self.image.get_rect(topleft=self.xy)
        self.z = z # layer to render on


class MachineSpriteBase(SpriteBase):
    def __init__(
        self, 
        xy: pg.Vector2,
        image: pg.Surface,
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
        super().__init__(xy, image, z, sprite_groups)
        self.ui_params = { # not initializing self.ui until the machine variant (burner/electric) is determined
            'screen': screen,
            'cam_offset': cam_offset,
            'mouse': mouse,
            'keyboard': keyboard,
            'player': player,
            'assets': assets,
            'gen_outline': gen_outline,
            'gen_bg': gen_bg,
            'rect_in_sprite_radius': rect_in_sprite_radius,
            'render_item_amount': render_item_amount
        }

        self.active = False
        self.timers = {}
        self.fuel_input = save_data['fuel input'] if save_data else {'item': None, 'amount': 0}
        self.output = save_data['output'] if save_data else {'item': None, 'amount': 0}
        self.max_capacity = {'fuel': 50, 'output': 99}

    def init_ui(self, ui_cls: any) -> None:
        self.ui = ui_cls(machine=self, **self.ui_params)