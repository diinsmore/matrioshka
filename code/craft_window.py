from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from inv_ui import InvUI

import pygame as pg
import math

class CraftWindow:
    def __init__(
        self, 
        screen: pg.Surface, 
        assets: dict[str, dict[str, any]], 
        inv_ui: InvUI, 
        height: int, 
        get_outline: callable
    ):
        self.screen = screen
        self.assets = assets
        self.inv_ui = inv_ui
        self.height = height
        self.get_outline = get_outline

        self.graphics = self.assets['graphics']
        self.fonts = self.assets['fonts']
        self.colors = self.assets['colors']

        self.width = (self.inv_ui.total_width * 2) + 1 # +1 to be divisible by 3 (the number of columns)
        self.padding = 5
        # defining the outline as a class attribute to allow the HUD and potentially other ui elements to access its location
        self.outline = pg.Rect(self.inv_ui.outline.right + self.padding, self.padding, self.width, self.height)
        self.open = False
        self.categories = {
            'tools': {
                'material gathering': ['pickaxe', 'axe', 'chainsaw'], 
                'defense': ['sword', 'bow', 'arrow', 'pistol', 'shotgun'], 
                'explosives': ['bomb', 'dynamite']
            },

            'machinery': {
                'smelting': ['coal furnace', 'electric furnace'],
                'automation': ['drill', 'assembler', 'printing press'],
                'power': ['electric pole', 'electric grid', 'steam engine', 'solar panel'],
            },

            'logistics': ['belt', 'pipes'], # TODO: add trains or maybe minecarts with similar functionality?

            'storage': {
                'chest': {'materials': ['wood', 'glass', 'stone', 'iron']},
                'energy': ['battery', 'accumulator']
            },

            'research': ['lab', 'research cores'],

            'decor': {
                'walls': {'materials': ['wood', 'stone', 'iron', 'copper', 'silver', 'gold']},
                'doors': {'materials': ['wood', 'glass', 'stone', 'iron']},
                'tables': {'materials': ['wood', 'glass', 'sandstone', 'ice']},
                'chairs': {'materials': ['wood', 'glass', 'ice']},
            },
        }

    def render_outline(self) -> None:
        pg.draw.rect(self.screen, 'black', self.outline, 1, 2)
        bg = self.get_outline(self.outline)

    def split_into_sections(self) -> None:
        category_names = list(self.categories.keys())
        num_categories = len(category_names)

        num_cols = 3
        num_rows = math.ceil(num_categories / num_cols)
        col_width = self.outline.width // num_cols
        row_height = (self.outline.height // 3) // num_rows

        # TODO: there's some line overlap in the center
        for col in range(num_cols):
            left = self.outline.left + (col_width * col)
            col_rect = pg.Rect(left, self.outline.top, col_width, self.outline.height)
            pg.draw.rect(self.screen, 'black', col_rect, 1)

            for row in range(num_rows):
                top = self.outline.top + (row_height * row)
                row_rect = pg.Rect(self.outline.left, top, self.outline.width, row_height)
                pg.draw.rect(self.screen, 'black', row_rect, 1)
                
                category_index = col + (row * num_cols)
                self.add_labels((left, top), label = category_names[category_index])

    def add_labels(self, topleft: tuple[int, int], label: str) -> None:
        padding = 2
        text = self.fonts['label'].render(label, True, self.colors['text'])
        text_rect = text.get_rect(topleft = topleft + pg.Vector2(padding, padding))
        self.screen.blit(text, text_rect)
        outline = pg.Rect(topleft, (text.size + pg.Vector2(padding * 2, padding * 2)))
        pg.draw.rect(self.screen, 'black', outline, 1)

    def render(self) -> None:
        if self.open:
            self.render_outline()
            self.split_into_sections()

    def update(self) -> None:
        self.render()