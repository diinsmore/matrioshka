from collections import defaultdict

from settings import TILE_SIZE, TILES, TOOLS

class Inventory:
    def __init__(self):
        self.slots = 50
        self.contents = {}
        self.cols = 10
        self.rows = 1
        self.box_width, self.box_height = TILE_SIZE * 2, TILE_SIZE * 2
        self.ui_width = self.box_width * self.cols
        self.ui_height = self.box_height * self.rows
        
        self.index = 0
        self.expand = False
        self.slot_capacity = defaultdict(lambda: 999)
        self.set_slot_capacity()
        
    def add_item(self, item: str) -> None:
        if item not in self.contents.keys():
            num_slots_taken = len([k for k in self.contents.keys()])
            if num_slots_taken < self.slots - 1:
                self.contents[item] = {'amount': 1, 'index': num_slots_taken + 1 if num_slots_taken > 0 else 0}
        else:
            if self.contents[item]['amount'] + 1 <= self.slot_capacity[item]:
               self.contents[item]['amount'] += 1
            
    def set_slot_capacity(self) -> None:
        for tile in TILES.keys():
            self.slot_capacity[tile] = 9999 

        for tool in TOOLS.keys():
            self.slot_capacity[tool] = 99

    def update(self) -> None:
        self.rows = 1 if not self.expand else self.slots // self.cols
        # update the old ui
        self.ui_width = self.box_width * self.cols
        self.ui_height = self.box_height * self.rows