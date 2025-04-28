from collections import defaultdict

class Inventory:
    def __init__(self):
        self.data = defaultdict(int)

        self.slots = 50
        self.cols = 10
        self.rows = 1
        self.box_width, self.box_height = 32, 32
        self.ui_width = self.box_width * self.cols
        self.ui_height = self.box_height * self.rows
        
        self.index = 0
        self.expand = False
        
    def add_item(self, item: str) -> None:
        self.data[item] += 1

    def update(self) -> None:
        self.rows = 1 if not self.expand else self.slots // self.cols
        # update the old ui
        self.ui_width = self.box_width * self.cols
        self.ui_height = self.box_height * self.rows