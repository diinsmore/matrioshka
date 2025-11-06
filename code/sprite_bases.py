from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player

import pygame as pg

class SpriteBase(pg.sprite.Sprite):
    def __init__(
        self, 
        xy: pg.Vector2,
        image: pg.Surface,
        z: dict[str, int],  
        sprite_groups: list[pg.sprite.Group]
    ):
        super().__init__(*sprite_groups)
        self.xy = xy
        self.image = image
        self.rect = self.image.get_rect(topleft=self.xy)
        self.z = z # layer to render on


class MachineSpriteBase(SpriteBase):
    def __init__(
        self, 
        xy: pg.Vector2, 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group],
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        mouse: Mouse,
        keyboard: Keyboard,
        player: Player,
        assets: dict[str, dict[str, any]], 
        tile_map: np.ndarray,
        obj_map: np.ndarray,
        item_transport_map: np.ndarray,
        gen_outline: callable,
        gen_bg: callable,
        rect_in_sprite_radius: callable,
        render_item_amount: callable,
        save_data: dict[str, any]
    ):
        super().__init__(xy, image, z, sprite_groups)
        self.tile_map = tile_map
        self.obj_map = obj_map
        self.item_transport_map = item_transport_map
        local_vars = locals()
        self.ui_params = {
            k: local_vars[k] for k in ('screen', 'cam_offset', 'mouse', 'keyboard', 'player', 'assets', 'gen_outline', 'gen_bg', 'rect_in_sprite_radius', 'render_item_amount')
        }
        
        self.active = False
        self.fuel_input = save_data['fuel input'] if save_data else {'item': None, 'amount': 0}
        self.output = save_data['output'] if save_data else {'item': None, 'amount': 0}
        self.pipe_connections = {}

    def init_ui(self, ui_cls: any) -> None:
        self.ui = ui_cls(machine=self, **self.ui_params) # not initializing self.ui until the machine variant (burner/electric) is determined