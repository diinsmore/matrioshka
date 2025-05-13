import pygame as pg

from sprite_manager import BaseSprite

# machinery
class Furnace(BaseSprite):
    def __init__(
        self, 
        coords: pg.Vector2, 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group]
    ):
        super().__init__(coords, image, z, *sprite_groups)
        self.recipe = {'stone': 3}
        self.valid_inputs = {
            'smelting': ['copper', 'iron', 'silver', 'gold'],
            'fuel': ['wood', 'coal']
        }
        self.max_capacity = {'smelting': 100, 'fuel': 50} 
        self.placed = False 

    def make(self) -> None:
        pass

    def smelt(self) -> None:
        pass