from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import InputManager
    import numpy as np
    from player import Player

import pygame as pg

from sprite_base_classes import Sprite
from settings import Z_LAYERS
from alarm import Alarm

class Pump(Sprite):
    def __init__(
        self, 
        xy: tuple[int, int], 
        image: pg.Surface, 
        sprite_groups: list[pg.sprite.Group], 
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        input_manager: InputManager,
        player: Player,
        assets: dict[str, dict[str, any]],
        tile_map: np.ndarray, 
        obj_map: np.ndarray,
        names_to_ids: dict[str, int],
        save_data: dict[str, any]=None
    ):
        super().__init__(xy, image, Z_LAYERS['main'], sprite_groups)
        self.tile_map = tile_map
        self.obj_map = obj_map
        self.water_id = names_to_ids['water']
        self.keyboard = input_manager.keyboard
        self.mouse = input_manager.mouse

        self.active = False if not save_data else save_data['active']
        self.direction = 'right' if not save_data else save_data['direction']
        self.liquid = None if not save_data else save_data['liquid']
        self.speed = {'water': 1200, 'lava': 2400}
        self.alarm = Alarm(None, self.pump_liquid, False, False, False)

    def pump_liquid(self) -> None:
        pass

    def flip_direction(self) -> None:
        if self.rect.collidepoint(self.mouse.world_xy) and self.keyboard.pressed_keys[pg.K_r]:
            self.image = pg.transform.flip(self.image, True)
            self.direction = 'left' if self.direction == 'right' else 'right'

    def update(self, dt: float=None) -> None:
        if self.active:
            if not self.alarm.running:
                speed = self.speed[self.liquid]
                if alarm.length != speed:
                    alarm.length = speed
                alarm.start()
            else:
                alarm.update()

    def get_save_data(self) -> dict[str, any]:
        return {'active': self.active, 'direction': self.direction, 'liquid': self.liquid}