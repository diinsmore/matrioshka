from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import InputManager
    from player import Player

import pygame as pg

from machine_sprite_base import Machine, MachineInventory, MachineInventorySlot
from settings import PRODUCTION, LOGISTICS, ELECTRICITY, MATERIALS, STORAGE, RESEARCH 
from assembler_ui import AssemblerUI
from alarm import Alarm

class Assembler(Machine):
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
        gen_outline: callable, 
        gen_bg: callable, 
        rect_in_sprite_radius: callable, 
        render_item_amount: callable, 
        save_data: dict[str, any]
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
            gen_outline,
            gen_bg, 
            rect_in_sprite_radius, 
            render_item_amount, 
            save_data
        )
        self.inv = MachineInventory(input_slots={})
        self.item_category, self.item, self.recipe = None, None, None
        self.item_category_data = {
            'production': PRODUCTION, 
            'logistics': LOGISTICS, 
            'electricity': ELECTRICITY, 
            'materials': MATERIALS, 
            'storage': STORAGE, 
            'research': RESEARCH
        }
        self.assemble_progress = {}
        self.alarms = {}
        self.init_ui(AssemblerUI)

    def assign_item(self, idx: int) -> None:
        data = self.item_category_data[self.item_category]
        self.item = list(data.keys())[idx]
        self.inv.output_slot.valid_inputs = {self.item}
        self.recipe = list(data.values())[idx]['recipe']
        for dct in (self.inv.input_slots, self.alarms, self.assemble_progress):
            dct.clear()
        for item in self.recipe:
            self.assemble_progress[item] = 0
            self.inv.input_slots[item] = MachineInventorySlot(item, valid_inputs={item}) # assigning the rect in the ui class
            self.alarms[item] = Alarm(2500, self.update_slot, loop=True, track_pct=True, slot=self.inv.input_slots[item]) # TODO: have alarm length vary by material
        self.alarms[self.item] = Alarm(max(self.recipe.values()) * 2500, loop=True, track_pct=True, slot=self.inv.output_slot)
    
    def update_slot(self, slot: InvSlot) -> None:
        slot.amount -= 1
        self.assemble_progress[slot.item] += 1
        if not slot.amount:
            slot.item = None

    def assemble(self) -> None:
        if self.inv.input_slots and all(slot.amount > 0 for slot in self.inv.input_slots.values()):
            for alarm in self.alarms.values():
                if not alarm.running:
                    alarm.start()
                else:
                    alarm.update()
            if all(self.assemble_progress[item] >= self.recipe[item] for item in self.recipe):
                if not self.inv.output_slot.item:
                    self.inv.output_slot.item = self.item
                self.inv.output_slot.amount += 1
                for item in self.recipe:
                    self.assemble_progress[item] = 0

    def update(self, dt=None) -> None:
        self.assemble()
        self.ui.update()