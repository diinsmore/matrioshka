from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import InputManager
    import numpy as np
    from machine_ui import MachineUI
    from ui import UI

import pygame as pg
from dataclasses import dataclass, field
from abc import ABC

from settings import Z_LAYERS, GRAVITY, TILE_SIZE, BIOME_WIDTH, TILE_SIZE
from sprite_base_classes import Sprite

@dataclass(slots=True)
class MachineInventorySlot:
    item: str=None
    rect: pg.Rect=None
    valid_inputs: set=None
    amount: int=0
    max_capacity: int=99

@dataclass
class MachineInventory:
    input_slots: dict[str, MachineInventorySlot]=None
    output_slot: MachineInventorySlot=field(default_factory=MachineInventorySlot)

    def __iter__(self):
        if self.input_slots:
            for slot in self.input_slots.values():
                yield slot
        yield self.output_slot


class Machine(Sprite, ABC):
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
        ui: UI=None,
        rect_in_sprite_radius: callable=None, 
        save_data: dict[str, any]=None
    ):
        super().__init__(xy, image, Z_LAYERS['main'], sprite_groups)
        self.screen = screen
        self.cam_offset = cam_offset
        self.keyboard, self.mouse = input_manager.keyboard, input_manager.mouse
        self.player = player
        self.assets, self.graphics = assets, assets['graphics']
        self.tile_map = tile_map
        self.obj_map = obj_map
        if ui:
            self.gen_outline, self.gen_bg, self.render_item_amount = ui.gen_outline, ui.gen_bg, ui.render_item_amount
            self.rect_in_sprite_radius = rect_in_sprite_radius
            _vars = vars()
            self.ui_params = {k: _vars[k] for k in ('screen', 'cam_offset', 'input_manager', 'player', 'assets', 'ui', 'rect_in_sprite_radius')}
            self.fuel_input = save_data['fuel input'] if save_data else {'item': None, 'amount': 0}
            self.output = save_data['output'] if save_data else {'item': None, 'amount': 0}
            self.pipe_connections = {}
            
        self.active = False

    def init_ui(self, ui_cls: MachineUI) -> None:
        self.ui = ui_cls(machine=self, **self.ui_params) # not initializing self.ui until the machine variant (burner/electric) is determined