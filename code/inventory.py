from collections import defaultdict

from settings import TILES, TOOLS

class Inventory:
    def __init__(self):
        self.num_slots = 50
        self.slot_capacity = defaultdict(lambda: 999)
        self.set_slot_capacity()
        self.contents = {'stone': {'amount': 1000, 'index': 0}, 'wood': {'amount': 1000, 'index': 1}, 'torch': {'amount': 1000, 'index': 2}} # values are just for testing the crafting system
        
    def add_item(self, item: str) -> None:
        if item not in self.contents.keys():
            num_slots_taken = len([k for k in self.contents.keys()])
            if num_slots_taken < self.num_slots:
                self.contents[item] = {'amount': 1, 'index': num_slots_taken}
        else:
            if self.contents[item]['amount'] + 1 <= self.slot_capacity[item]:
               self.contents[item]['amount'] += 1

    def remove_item(self, item: str, amount: int) -> None:
        if self.contents[item]['amount'] - amount >= 1:
            self.contents[item]['amount'] -= amount
        else:
            del self.contents[item]
            
    def set_slot_capacity(self) -> None:
        for tile in TILES.keys():
            self.slot_capacity[tile] = 9999 

        for tool in TOOLS.keys():
            self.slot_capacity[tool] = 99