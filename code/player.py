from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import numpy as np
    from input_manager import InputManager

import pygame as pg
import numpy as np

from settings import Z_LAYERS, RES
from sprite_bases import Colonist
from inventory import PlayerInventory

class Player(Colonist):
    def __init__(
        self, 
        screen: pg.Surface,
        xy: tuple[int, int],
        cam_offset: pg.Vector2, 
        frames: dict[str, pg.Surface], 
        sprite_groups: list[pg.sprite.Group], 
        input_manager: InputManager, 
        tile_map: np.ndarray, 
        current_biome: str,
        biome_order: dict[str, int], 
        assets: dict[str, any],
        save_data: dict[str, any] | None
    ):
        super().__init__(screen, xy, cam_offset, frames, sprite_groups, input_manager, tile_map, current_biome, biome_order, assets, save_data)
        self.z = Z_LAYERS['player']
        self.inventory = PlayerInventory(parent_sprite=self, save_data=save_data)
        self.heart_surf = self.graphics['icons']['heart']
        self.heart_width = self.heart_surf.get_width()
    
    def render_hearts(self) -> None:
        for i in range(self.hearts):
            self.screen.blit(self.heart_surf, (RES[0] - (5 + self.heart_width + (25 * i)), 5))

    def respawn(self) -> None:
        pass

    def update(self, dt: float) -> None:
        self.get_current_biome()
        self.inventory.get_idx_selection(self.keyboard)
        self.render_hearts()
        self.update_oxygen_level()