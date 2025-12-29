from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import InputManager
    import numpy as np

import pygame as pg
from machine_sprite_base import Machine

class TransportSprite(Machine):
    def __init__(
        self, 
        xy: tuple[int, int], 
        image: pg.Surface, 
        z: int, 
        sprite_groups: list[pg.sprite.Group], 
        screen: pg.Surface, 
        cam_offset: pg.Vector2,
        input_manager: InputManager, 
        player: Player, 
        assets: dict[str, dict[str, any]], 
        tile_map: np.ndarray, 
        obj_map: np.ndarray, 
        save_data: dict[str, any]=None
    ):
        super().__init__(
            xy, 
            image, 
            z, 
            sprite_groups, 
            screen, 
            cam_offset, 
            input_manager, 
            player, 
            assets, 
            tile_map, 
            obj_map, 
            save_data=save_data
        )
        self.dir_ui = self.graphics['transport dirs']
        self.item_holding = None
        self.xy_to_cardinal = {
            0: {(1, 0): 'E', (-1, 0): 'W'},
            1: {(0, -1): 'N', (0, 1): 'S'},
            2: {(1, 0): 'SE', (0, -1): 'WN'},
            3: {(0, -1): 'EN', (-1, 0): 'SW'},
            4: {(1, 0): 'NE', (0, 1): 'WS'},
            5: {(-1, 0): 'NW', (0, 1): 'ES'},
            6: {(1, 0): 'E', (-1, 0): 'W', (0, -1): 'N', (0, 1): 'S'},
            7: {(1, 0): 'E', (0, -1): 'N', (0, 1): 'S'},
            8: {(0, -1): 'N', (0, 1): 'S', (-1, 0): 'W'},
            9: {(1, 0): 'E', (-1, 0): 'W', (0, -1): 'N'},
            10: {(1, 0): 'E', (-1, 0): 'W', (0, 1): 'S'}
        }

    def update_alarms(self) -> None:
        for alarm in self.alarms.values():
            alarm.update()