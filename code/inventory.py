from __future__ import annotations
from typing import Sequence
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import pygame as pg
    from input_manager import Keyboard
from collections import defaultdict

from settings import TILES, TOOLS
from player import Player

class Inventory:
    def __init__(self, save_data: dict[str, any], default_contents: dict[str, dict[str, int]]=None):
        if save_data:
            self.contents = save_data['contents']
        else:
            self.contents = default_contents if default_contents else {}
        if self.contents:
            for i, item in enumerate(self.contents):
                self.contents[item]['index'] = i

        self.index = save_data['index'] if save_data else 0
        self.num_slots = 50
        self.slot_capacity = defaultdict(lambda: 999)
        self.set_slot_capacity()
        
    def set_slot_capacity(self) -> None:
        for tile in TILES.keys():
            self.slot_capacity[tile] = 9999 

        for tool in TOOLS.keys():
            self.slot_capacity[tool] = 99   

    def add_item(self, item: str, amount: int=1) -> None:
        items = self.contents.keys()
        if item not in items:
            num_slots_taken = len(items)
            if num_slots_taken < self.num_slots:
                self.contents[item] = {'amount': amount, 'index': num_slots_taken}
        else:
            max_amount = amount
            if item in self.slot_capacity.keys():
                max_amount = min(amount, self.slot_capacity['item'] - self.contents[item]['amount'])
            self.contents[item]['amount'] += max_amount
            
    def remove_item(self, item: str, amount: int=1) -> None:
        if self.contents[item]['amount'] - amount >= 1:
            self.contents[item]['amount'] -= amount
        else:
            del self.contents[item]
            for i, (name, data) in enumerate(self.contents.items()):
                data['index'] = i


class PlayerInventory(Inventory):
    def __init__(self, save_data: dict[str, any]):
        super().__init__(save_data, default_contents=None if save_data else {
            'stone': {'amount': 100}, 
            'wood': {'amount': 100}, 
            'wood torch': {'amount': 100},
            'stone axe': {'amount': 10}, 
            'stone pickaxe': {'amount': 10},
            'pipe 0': {'amount': 100},
            'copper': {'amount': 100},
            'burner inserter': {'amount': 50}
        })
         
    def get_idx_selection(self, keyboard: Keyboard, player: pg.sprite.Sprite) -> None:
        for key in keyboard.num_keys:
            if keyboard.pressed_keys[key]:
                player.inventory.index = keyboard.key_map[key]
                items = list(self.contents.keys())
                player.item_holding = items[player.inventory.index] if player.inventory.index < len(items) else None
                return