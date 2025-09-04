from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from drills import BurnerDrill, ElectricDrill
    from input_manager import Mouse, Keyboard
    from player import Player

import pygame as pg
from machine_ui import MachineUI, UIDimensions, MachineUIHelpers

class DrillUI(MachineUI):
    def __init__(
        self, 
        drill: BurnerDrill|ElectricDrill,
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        mouse: Mouse, 
        keyboard: Keyboard,
        player: Player,
        assets: dict[str, dict[str, any]],
        dimensions: UIDimensions,
        helpers: MachineUIHelpers
    ):
        super().__init__(drill, screen, cam_offset, mouse, keyboard, player, assets, dimensions, helpers)