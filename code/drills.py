from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player
    from machine_ui import MachineUIHelpers

import pygame as pg

from sprite_base import MachineSpriteBase
from settings import TILE_SIZE

class Drill(MachineSpriteBase):
    def __init__(
        self, 
        xy: pg.Vector2, 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group],
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        mouse: Mouse,
        keyboard: Keyboard,
        player: Player,
        assets: dict[str, dict[str, any]],
        helpers: MachineUIHelpers,
        save_data: dict[str, any]
    ):
        super().__init__(xy, image, z, sprite_groups, screen, cam_offset, mouse, keyboard, player, assets, helpers, save_data)
        self.target_ore = save_data['target ore'] if save_data else {} # key: ore, value: amount available
        self.reach_radius = ((image.width // TILE_SIZE) + 2, RES[1] // 5)

    def get_save_data(self) -> dict[str, list|dict]:
        return {
            'xy': list(self.rect.topleft),
            'target ore': self.target_ore,
            'output': self.output
        }


class BurnerDrill(Drill):
    def __init__(
        self, 
        xy: pg.Vector2, 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group],
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        mouse: Mouse,
        keyboard: Keyboard,
        player: Player,
        assets: dict[str, dict[str, any]],
        helpers: MachineUIHelpers,
        save_data: dict[str, any]
    ):
        super().__init__(xy, image, z, sprite_groups, screen, cam_offset, mouse, keyboard, player, assets, helpers, save_data)


class ElectricDrill(Drill):
    def __init__(
        self, 
        xy: pg.Vector2, 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group],
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        mouse: Mouse,
        keyboard: Keyboard,
        player: Player,
        assets: dict[str, dict[str, any]],
        helpers: MachineUIHelpers,
        save_data: dict[str, any]
    ):
        super().__init__(xy, image, z, sprite_groups, screen, cam_offset, mouse, keyboard, player, assets, helpers, save_data)