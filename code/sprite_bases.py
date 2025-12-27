from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player
    from machine_ui import MachineUI

import pygame as pg
from dataclasses import dataclass, field

from settings import TILE_SIZE, Z_LAYERS, GRAVITY, BIOME_WIDTH
from inventory import SpriteInventory
from alarm import Alarm

class SpriteBase(pg.sprite.Sprite):
    def __init__(self, xy: tuple[int, int], image: pg.Surface, z: dict[str, int], sprite_groups: list[pg.sprite.Group]):
        super().__init__(*sprite_groups)
        self.xy = xy
        self.image = image
        self.rect = self.image.get_rect(topleft=self.xy)
        self.z = z # layer to render on

        self.tile_xy = (self.xy[0] // TILE_SIZE, self.xy[1] // TILE_SIZE)


class Colonist(pg.sprite.Sprite):
    def __init__(
        self,
        screen: pg.Surface,
        xy: tuple[int, int], 
        cam_offset: pg.Vector2,
        frames: dict[str, pg.Surface], 
        sprite_groups: list[pg.sprite.Group], 
        input_manager: InputManager, 
        tile_map: np.ndarray, 
        current_biome: str,
        biome_order: dict[str, int], 
        assets: dict[str, any],
        save_data: dict[str, any] | None
    ):
        super().__init__(*sprite_groups)
        self.screen = screen
        self.spawn_point, self.xy = xy, xy
        self.cam_offset = cam_offset
        self.frames = frames
        self.sprite_groups = sprite_groups
        self.keyboard, self.mouse = input_manager.keyboard, input_manager.mouse
        self.tile_map = tile_map
        self.current_biome = current_biome
        self.biome_order = biome_order
        self.graphics = assets['graphics']
        self.save_data = save_data
        
        self.state = 'idle'
        self.frame_idx = 0
        self.image = self.frames[self.state][self.frame_idx]
        self.rect = self.image.get_rect(midbottom=self.xy)
        self.z = Z_LAYERS['main']
        self.direction = pg.Vector2()
        self.facing_left = save_data['facing left'] if save_data else True
        self.speed = 225
        self.animation_speed = {'walking': 8, 'mining': 4, 'jumping': 0}
        self.grounded = False
        self.default_gravity, self.gravity = GRAVITY, GRAVITY
        self.default_jump_height, self.jump_height = 350, 350 
        self.hearts = save_data['lives'] if save_data else 8
        self.inventory = SpriteInventory(parent_sprite=self)
        self.item_holding = save_data['item holding'] if save_data else None
        self.arm_strength = 4
        self.underwater = False
        self.oxygen_lvl, self.max_oxygen_lvl = 8, 8
        self.oxygen_icon = self.graphics['icons']['oxygen']
        self.oxygen_icon_w, self.oxygen_icon_h = self.oxygen_icon.get_size()
        self.alarms = {'lose oxygen': Alarm(1500, self.lose_oxygen, False, True)}
    
    def get_current_biome(self) -> None:
        if self.direction:
            biome_idx = (self.rect.x // TILE_SIZE) // BIOME_WIDTH
            if self.biome_order[self.current_biome] != biome_idx:
                for biome in self.biome_order.keys():
                    if self.biome_order[biome] == biome_idx:
                        self.current_biome = biome
                        return

    def update_oxygen_level(self) -> None:
        if self.underwater:
            if not self.alarms['lose oxygen'].running:
                self.alarms['lose oxygen'].start()
            else:
                self.alarms['lose oxygen'].update()
            self.render_oxygen_icons()

    def lose_oxygen(self) -> None:
        if self.oxygen_lvl >= 1:
            self.oxygen_lvl -= 1
        else:
            self.hearts -= 1
            if not self.hearts:
                self.die()
    
    def die(self) -> None:
        if self.z == Z_LAYERS['player']: 
            self.respawn()
        else:
            self.kill()

    def drop_items(self) -> None:
        pass

    def render_oxygen_icons(self) -> None:
        x_padding = self.oxygen_icon_w * (self.oxygen_lvl // 2)
        for i in range(self.oxygen_lvl):
            self.screen.blit(
                self.oxygen_icon, 
                self.rect.midtop - self.cam_offset + pg.Vector2((self.oxygen_icon_w * i) - x_padding, -self.oxygen_icon_h)
            ) 

    def update(self, dt: float) -> None:
        self.get_current_biome()
        self.inventory.get_idx_selection(self.keyboard)
        self.update_oxygen_level()

    def get_save_data(self) -> dict[str, any]:
        return {
            'xy': self.spawn_point, 
            'current biome': self.current_biome, 
            'inventory data': {'contents': self.inventory.contents, 'index': self.inventory.index},
            'facing left': self.facing_left, 
            'lives': self.health, 
            'item holding': self.item_holding
        }


@dataclass(slots=True)
class MachineInvSlot:
    item: str=None
    rect: pg.Rect=None
    valid_inputs: set=None
    amount: int=0
    max_capacity: int=99


@dataclass
class MachineInventory:
    input_slots: dict[str, InvSlot]=None
    output_slot: InvSlot=field(default_factory=MachineInvSlot)

    def __iter__(self):
        if self.input_slots:
            for slot in self.input_slots.values():
                yield slot
        yield self.output_slot


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
        self.gen_outline = gen_outline
        self.gen_bg = gen_bg
        self.rect_in_sprite_radius = rect_in_sprite_radius
        self.render_item_amount = render_item_amount

        _vars = vars()
        self.ui_params = {
            k: _vars[k] for k in (
                'screen', 
                'cam_offset', 
                'mouse', 
                'keyboard', 
                'player', 
                'assets', 
                'gen_outline', 
                'gen_bg', 
                'rect_in_sprite_radius', 
                'render_item_amount'
            )
        }
        self.active = False
        self.fuel_input = save_data['fuel input'] if save_data else {'item': None, 'amount': 0}
        self.output = save_data['output'] if save_data else {'item': None, 'amount': 0}
        self.pipe_connections = {}

    def init_ui(self, ui_cls: MachineUI) -> None:
        self.ui = ui_cls(machine=self, **self.ui_params) # not initializing self.ui until the machine variant (burner/electric) is determined


class TransportSpriteBase(SpriteBase):
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
        save_data: dict[str, any]=None
    ):
        super().__init__(xy, image, z, sprite_groups)
        self.image = self.image.copy() # for rotating the inserters
        self.screen = screen
        self.cam_offset = cam_offset
        self.mouse = mouse
        self.keyboard = keyboard
        self.player = player
        self.graphics = assets['graphics']
        self.tile_map = tile_map
        self.obj_map = obj_map

        self.dir_ui = self.graphics['transport dirs']
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

    def update_alarms(self) -> None:
        for alarm in self.alarms.values():
            alarm.update()