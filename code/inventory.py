from collections import defaultdict

from settings import TILES, TOOLS

class Inventory:
    def __init__(self):
        self.slots = 50
        self.slot_capacity = defaultdict(lambda: 999)
        self.set_slot_capacity()
        self.contents = {}
        self.current_index = 0
        
    def add_item(self, item: str) -> None:
        if item not in self.contents.keys():
            num_slots_taken = len([k for k in self.contents.keys()])
            if num_slots_taken < self.slots:
                self.contents[item] = {'amount': 1, 'index': num_slots_taken}
        else:
            if self.contents[item]['amount'] + 1 <= self.slot_capacity[item]:
               self.contents[item]['amount'] += 1
            
    def set_slot_capacity(self) -> None:
        for tile in TILES.keys():
            self.slot_capacity[tile] = 9999 

        for tool in TOOLS.keys():
            self.slot_capacity[tool] = 99