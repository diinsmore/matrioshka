import pygame as pg

from settings import TILE_SIZE, MACHINES
from sprite_base import SpriteBase

class Furnace(SpriteBase):
    def __init__(
        self, 
        coords: tuple[int, int], 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group]
    ):
        super().__init__(coords, image, z, sprite_groups)
        self.max_capacity = {'smelting': 100, 'fuel': 50}
        self.valid_inputs = {
            'smelting': {
                # speeds are in milliseconds
                'copper': {'speed': 4000, 'output': 'copper plate'}, 
                'iron': {'speed': 5000, 'output': 'iron plate'},
                'iron plate': {'speed': 7000, 'output': 'steel plate'},
            },
        } 
        self.placed = False
        
    def make(self, sprite_inv: dict[str, int]) -> None:
        if all(sprite_inv[item]['amount'] >= self.recipe[item] for item in self.recipe.keys()):
            for item in self.recipe.keys():
                sprite_inv[item]['amount'] -= self.recipe[item]
        
    def smelt(self) -> None:
        pass


class BurnerFurnace(Furnace):
    def __init__(
        self,
        coords: tuple[int, int], 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group]
    ):
        super().__init__(coords, image, z, sprite_groups)
        self.recipe = MACHINES['burner furnace']['recipe']
        self.valid_inputs['fuel'] = {'wood', 'coal'}


class ElectricFurnace(Furnace):
    def __init__(
        self,
        coords: tuple[int, int], 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group]
    ):
        super().__init__(coords, image, z, sprite_groups)
        self.recipe = {'iron plate': 4, 'circuit': 2}


class Drill(SpriteBase):
    def __init__(
        self, 
        coords: tuple[int, int], 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group]
    ):
        super().__init__(coords, image, z, sprite_groups)
        self.target_ore = None
        self.reach_radius = ((image.width // TILE_SIZE) + 2, RES[1] // 5)


# match the sprite.item_holding variable to the class to instantiate when the item is placed
mech_sprite_dict = {
    'burner furnace': BurnerFurnace, 
    'electric furnace': ElectricFurnace, 
    'drill': Drill
}