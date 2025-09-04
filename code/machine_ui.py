from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sprite_base import SpriteBase

import pygame as pg
from dataclasses import dataclass

class MachineUI:
    def __init__(
        self,
        machine: SpriteBase,
        screen: pg.Surface, 
        cam_offset: pg.Vector2,
        mouse: Mouse, 
        keyboard: Keyboard,
        player: Player,
        assets: dict[str, dict[str, any]],
        helpers: MachineUIHelpers
    ):
        self.machine = machine
        self.screen = screen
        self.cam_offset = cam_offset
        self.mouse = mouse
        self.keyboard = keyboard
        self.player = player
        self.assets = assets
        self.helpers = helpers

        self.graphics = self.assets['graphics']
        self.render = False
        self.highlight_color = self.assets['colors']['ui bg highlight']
        self.machine_mask = pg.mask.from_surface(machine.image)
        self.machine_mask_surf = self.machine_mask.to_surface(setcolor=(20, 20, 20, 255), unsetcolor=(0, 0, 0, 0))

        self.key_close_ui = self.keyboard.key_bindings['close ui window']

@dataclass
class MachineUIHelpers:
    gen_outline: callable
    gen_bg: callable
    rect_in_sprite_radius: callable
    render_item_amount: callable