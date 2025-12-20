from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player

import pygame as pg

from sprite_bases import MachineSpriteBase, Inventory, InvSlot
from settings import MACHINES, LOGISTICS, ELECTRICITY, MATERIALS, STORAGE, RESEARCH 
from assembler_ui import AssemblerUI

class Assembler(MachineSpriteBase):
    def __init__(
        self, xy: tuple[int, int], image: dict[str, dict[str, pg.Surface]], z: dict[str, int], sprite_groups: list[pg.sprite.Group], screen: pg.Surface, 
        cam_offset: pg.Vector2, mouse: Mouse, keyboard: Keyboard, player: Player, assets: dict[str, dict[str, any]], tile_map: np.ndarray, obj_map: np.ndarray, 
        gen_outline: callable, gen_bg: callable, rect_in_sprite_radius: callable, render_item_amount: callable, save_data: dict[str, any]
    ):
        super().__init__(
            xy, image, z, sprite_groups, screen, cam_offset, mouse, keyboard, player, assets, tile_map, obj_map, gen_outline, gen_bg, rect_in_sprite_radius, 
            render_item_amount, save_data
        )
        self.inv = Inventory(input_slots={})
        self.item_category, self.item, self.recipe = None, None, None
        self.item_category_data = {'machines': MACHINES, 'logistics': LOGISTICS, 'electricity': ELECTRICITY, 'materials': MATERIALS, 'storage': STORAGE, 'research': RESEARCH}
        self.init_ui(AssemblerUI)

    def assign_item(self, idx: int) -> None:
        data = self.item_category_data[self.item_category]
        self.item = list(data.keys())[idx]
        self.recipe = list(data.values())[idx]['recipe']
        self.inv.input_slots.clear()
        for item in self.recipe:
            self.inv.input_slots[item] = InvSlot(item, valid_inputs={item}) # assigning the rect in the ui class
 
    def update(self, dt=None) -> None:
        self.ui.update()