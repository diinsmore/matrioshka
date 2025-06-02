import pygame as pg

from settings import TILE_SIZE, MACHINES
from sprite_base import SpriteBase

class Furnace(SpriteBase):
    def __init__(
        self, 
        coords: tuple[int, int], 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group],
        camera_offset: pg.Vector2
    ):
        super().__init__(coords, image, z, sprite_groups)
        self.coords = pg.Vector2(coords)
        self.rect = image.get_rect(topleft = coords)
        self.camera_offset = camera_offset

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
    
    def smelt(self) -> None:
        pass
    
    def load_ui(self) -> None:
        if self.rect.collidepoint(pg.mouse.get_pos()):
            pass

    def update(self, dt) -> None:
        self.rect.topleft = self.coords - self.camera_offset
        self.load_ui()


class BurnerFurnace(Furnace):
    def __init__(
        self,
        coords: tuple[int, int], 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group],
        camera_offset: pg.Vector2
    ):
        super().__init__(coords, image, z, sprite_groups, camera_offset)
        self.recipe = MACHINES['burner furnace']['recipe']
        self.valid_inputs['fuel'] = {'wood', 'coal'}


class ElectricFurnace(Furnace):
    def __init__(
        self,
        coords: tuple[int, int], 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group],
        camera_offset: pg.Vector2
    ):
        super().__init__(coords, image, z, sprite_groups, camera_offset)
        self.recipe = {'iron plate': 4, 'circuit': 2}


class Drill(SpriteBase):
    def __init__(
        self, 
        coords: tuple[int, int], 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group],
        camera_offset: pg.Vector2
    ):
        super().__init__(coords, image, z, sprite_groups, camera_offset)
        self.target_ore = None
        self.reach_radius = ((image.width // TILE_SIZE) + 2, RES[1] // 5)


# match the sprite.item_holding variable to the class to instantiate when the item is placed
mech_sprite_dict = {
    'burner furnace': BurnerFurnace, 
    'electric furnace': ElectricFurnace, 
    'drill': Drill
}