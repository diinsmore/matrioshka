from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player

import pygame as pg
from settings import TILE_SIZE

class SpriteBase(pg.sprite.Sprite):
    def __init__(
        self, 
        xy: tuple[int, int],
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
        xy: tuple[int, int], 
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
        self.screen = screen
        self.cam_offset = cam_offset
        self.mouse = mouse
        self.keyboard = keyboard
        self.player = player
        self.assets = assets
        self.tile_map = tile_map
        self.obj_map = obj_map
        self.item_transport_map = item_transport_map
        self.gen_outline = gen_outline
        self.gen_bg = gen_bg
        self.rect_in_sprite_radius = rect_in_sprite_radius
        self.render_item_amount = render_item_amount
        _vars = vars()
        self.ui_params = {k: _vars[k] for k in ('screen', 'cam_offset', 'mouse', 'keyboard', 'player', 'assets', 'gen_outline', 'gen_bg', 
            'rect_in_sprite_radius', 'render_item_amount')}
        
        self.active = False
        self.tile_xy = (self.xy[0] // TILE_SIZE, self.xy[1] // TILE_SIZE)
        self.fuel_input = save_data['fuel input'] if save_data else {'item': None, 'amount': 0}
        self.output = save_data['output'] if save_data else {'item': None, 'amount': 0}
        self.pipe_connections = {}

    def init_ui(self, ui_cls: any) -> None:
        self.ui = ui_cls(machine=self, **self.ui_params) # not initializing self.ui until the machine variant (burner/electric) is determined


class TransportSpriteBase(MachineSpriteBase):
    def __init__(
        self,
        xy: tuple[int, int], 
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
        super().__init__(
            xy, 
            image, 
            z, 
            sprite_groups, 
            screen, 
            cam_offset, 
            mouse, 
            keyboard, 
            player, 
            assets, 
            tile_map,
            obj_map,
            item_transport_map,
            gen_outline, 
            gen_bg, 
            rect_in_sprite_radius, 
            render_item_amount, 
            save_data
        )
        self.graphics = self.assets['graphics']
        self.dir_surfs = self.graphics['transport dirs']
        self.item_holding = None
        self.xy_to_cardinal = {
            0: {(1, 0): 'E', (-1, 0): 'W'},
            1: {(0, -1): 'N', (0, 1): 'S'},
            2: {(1, 0): 'SE', (0, -1): 'WN'},
            3: {(0, -1): 'EN', (-1, 0): 'SW'},
            4: {(1, 0): 'NE', (0, 1): 'WS'},
            5: {(-1, 0): 'NW', (0, 1): 'ES'},
            6: {(1, 0): 'E', (-1, 0): 'W', (0, -1): 'N', (0, 1): 'S'},
            7: {(1, 0): 'E', (0, -1): 'N', (0, 1): 'S'},
            8: {(0, -1): 'N', (0, 1): 'S', (-1, 0): 'W'},
            9: {(1, 0): 'E', (-1, 0): 'W', (0, -1): 'N'},
            10: {(1, 0): 'E', (-1, 0): 'W', (0, 1): 'S'}
        }

    def update_timers(self) -> None:
        for t in self.timers.values():
            if not t.running:
                t.start()
            t.update()