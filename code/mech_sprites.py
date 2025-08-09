from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse

import pygame as pg

from settings import TILE_SIZE, MACHINES
from sprite_base import SpriteBase

class Furnace(SpriteBase):
    def __init__(
        self, 
        coords: pg.Vector2, 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group],
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        mouse: Mouse,
        make_outline: callable,
        make_transparent_bg: callable
    ):
        super().__init__(coords, image, z, sprite_groups)
        self.coords = coords
        self.rect = image.get_rect(topleft = self.coords)
        self.screen = screen
        self.cam_offset = cam_offset
        self.mouse = mouse
        self.make_outline = make_outline
        self.make_transparent_bg = make_transparent_bg
        
        self.active = False
        self.load_ui = False
        self.ui_box_w, self.ui_box_h = 200, 200

        self.max_capacity = {'smelting': 100, 'fuel': 50}
        self.valid_inputs = {
            'smelting': {
                'copper': {'speed': 4000, 'output': 'copper plate'}, 
                'iron': {'speed': 5000, 'output': 'iron plate'},
                'iron plate': {'speed': 7000, 'output': 'steel plate'},
            },
        }
    
    def smelt(self) -> None:
        pass
    
    def render(self) -> None:
        if not self.load_ui:
            self.load_ui = self.rect.collidepoint(self.mouse.world_xy) and self.mouse.click_states['left']
        else:
            self.render_ui()
            if self.mouse.click_states['left']:
                self.load_ui = False
                
    def render_ui(self):
        rect = pg.Rect(self.rect.topright - pg.Vector2(0, self.ui_box_h) - self.cam_offset, (self.ui_box_w, self.ui_box_h))
        self.make_transparent_bg(rect)
        self.make_outline(rect)

    def update(self, dt) -> None:
        self.render()


class BurnerFurnace(Furnace):
    def __init__(
        self,
        coords: pg.Vector2, 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group],
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        mouse: Mouse,
        make_outline: callable,
        make_transparent_bg: callable
    ):
        super().__init__(coords, image, z, sprite_groups, screen, cam_offset, mouse, make_outline, make_transparent_bg)
        self.recipe = MACHINES['burner furnace']['recipe']
        self.valid_inputs['fuel'] = {'wood', 'coal'}


class ElectricFurnace(Furnace):
    def __init__(
        self,
        coords: pg.Vector2, 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group],
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        mouse: Mouse,
        make_outline: callable,
        make_transparent_bg: callable
    ):
        super().__init__(coords, image, z, sprite_groups, screen, cam_offset, mouse, make_outline, make_transparent_bg)
        self.recipe = MACHINES['electric furnace']['recipe']


class Drill(SpriteBase):
    def __init__(
        self, 
        coords: pg.Vector2, 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group],
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        mouse: Mouse,
        make_outline: callable,
        make_transparent_bg: callable
    ):
        super().__init__(coords, image, z, sprite_groups, cam_offset)
        self.screen = screen
        self.cam_offset = cam_offset
        self.mouse = mouse
        self.make_outline = make_outline
        self.make_transparent_bg = make_transparent_bg

        self.target_ore = None
        self.reach_radius = ((image.width // TILE_SIZE) + 2, RES[1] // 5)


mech_sprite_dict = { # matches the sprite.item_holding variable to the class to be instantiated when the item is placed
    'burner furnace': BurnerFurnace, 
    'electric furnace': ElectricFurnace, 
    'drill': Drill
}