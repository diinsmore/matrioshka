from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from player import Player
    from input_manager import Mouse, Keyboard
    from inventory import Inventory

import pygame as pg
from settings import MATERIALS, TILES, TILE_SIZE, PLACEABLE_ITEMS, TRANSPORT_DIRS

class ItemDrag:
    def __init__(
        self, 
        screen: pg.Surface, 
        cam_offset: pg.Vector2,
        graphics: dict[str, pg.Surface],
        player: Player, 
        mouse: Mouse, 
        keyboard: Keyboard, 
        inventory: Inventory,
        outline: pg.Rect,
        slot_len: int,
        num_cols: int,
        num_rows: int,
        item_rect_base: pg.Rect,
        mech_sprites: pg.sprite.Group,
        get_grid_xy: callable,
        get_sprites_in_radius: callable
    ):
        self.screen = screen
        self.cam_offset = cam_offset
        self.graphics = graphics
        self.player = player
        self.mouse = mouse
        self.keyboard = keyboard
        self.inventory = inventory
        self.outline = outline
        self.slot_len = slot_len
        self.num_cols = num_cols
        self.num_rows = num_rows
        self.item_rect_base = item_rect_base
        self.mech_sprites = mech_sprites
        self.get_grid_xy = get_grid_xy
        self.get_sprites_in_radius = get_sprites_in_radius

        self.active = False
        self.image, self.rect = None, None 
        self.amount = None
        self.material_names, self.tile_names = set(MATERIALS.keys()), set(TILES.keys())
        self.old_pipe_idx = None # storing the original pipe index if it gets rotated while being dragged
        self.item_placement = None # not initialized yet

    def get_clicked_item(self) -> str|None:
        for item_name, item_data in self.inventory.contents.items():
            row, col = divmod(item_data['index'], self.num_cols)
            padding = pg.Vector2(col * self.slot_len, row * self.slot_len)
            if (item_rect := self.item_rect_base.move(self.outline.topleft + padding)).collidepoint(self.mouse.screen_xy):
                return item_name

    def check_drag(self) -> None:
        l_click, r_click = self.mouse.buttons_pressed.values()
        if l_click or r_click:
            if self.active:
                if r_click:
                    self.amount //= 2
                else:
                    self.end_drag()
            else:
                if self.outline.collidepoint(self.mouse.screen_xy):
                    if item_name := self.get_clicked_item():
                        self.start_drag(item_name, 'left' if l_click else 'right')   
                else:
                    if machines_with_inv := [m for m in self.get_sprites_in_radius(self.player.rect, self.mech_sprites) if hasattr(m, 'has_inv') and m.ui.render]:
                        self.check_machine_extract(machines_with_inv, l_click, r_click)
        else:
            if self.active:
                self.render_item_drag()
                if self.keyboard.pressed_keys[pg.K_q]:
                    self.update_item_data(remove=True)
                
    def start_drag(self, item_name: str, click_type: str) -> None:
        self.player.inventory.index = self.player.inventory.contents[item_name]['index']
        self.update_item_data(item_name, click_type, add=True)

    def end_drag(self) -> None: 
        if self.player.item_holding in (self.material_names | self.tile_names) and not self.item_placement.valid_placement(self.mouse.tile_xy, self.player): # calling valid_placement to distinguish between placing e.g a copper block in the smelt compartment vs on the ground
            self.place_item_in_machine()
        else:
            self.item_placement.place_item(self.player, (self.mouse.world_xy[0] // TILE_SIZE, self.mouse.world_xy[1] // TILE_SIZE), self.old_pipe_idx)
        if self.player.item_holding not in self.player.inventory.contents: # placed the last of its kind
            self.update_item_data(remove=True)

    def update_item_data(self, item_name: str=None, click_type: str=None, add: bool=False, remove: bool=False) -> None:
        if add:
            self.player.item_holding = item_name
            self.image = self.graphics[item_name].copy() # a copy to not alter the alpha value of the original
            self.image.set_alpha(150)
            self.rect = self.image.get_rect(center=self.mouse.world_xy)
            item_amount = self.player.inventory.contents[item_name]['amount'] 
            self.amount = item_amount if click_type == 'left' else (item_amount // 2)
        else:
            self.player.item_holding = None
            self.image = None
            self.rect = None
            self.amount = 0
            self.active = False
            self.old_pipe_idx = None
        self.active = add

    def render_item_drag(self) -> None:
        self.rect.topleft = self.get_grid_xy()
        self.screen.blit(self.image, self.rect)
        if self.player.item_holding in PLACEABLE_ITEMS:
            item_xy_world = (pg.Vector2(self.rect.topleft) + self.cam_offset) // TILE_SIZE
            if 'pipe' in self.player.item_holding and self.keyboard.pressed_keys[pg.K_r]:
                self.rotate_pipe()
            self.item_placement.render_ui(self.image, self.rect, (int(item_xy_world.x), int(item_xy_world.y)), self.player)
    
    def rotate_pipe(self) -> None:
        if self.old_pipe_idx is None:
            self.old_pipe_idx = int(self.player.item_holding[-1])
        idx = (int(self.player.item_holding[-1]) + 1) % len(TRANSPORT_DIRS)
        self.image = self.graphics[f'pipe {idx}']
        self.player.item_holding = f'pipe {idx}'

    def place_item_in_machine(self) -> None:
        for machine in [m for m in self.get_sprites_in_radius(self.player.rect, self.mech_sprites) if hasattr(m, 'has_inv') and m.ui.render]:
            inv_box_data = machine.ui.get_inv_box_data()
            if inv_type := machine.ui.check_input(inv_box_data):
                machine.ui.input_item(inv_type, self.amount, inv_box_data[inv_type])
                return
    
    def check_machine_extract(self, machines: list[pg.sprite.Sprite], l_click: bool, r_click: bool) -> None:
        for machine in machines:
            inv_data = machine.ui.get_inv_box_data()
            for inv_type in inv_data.keys():
                inv_contents = inv_data[inv_type]['contents']
                if inv_data[inv_type]['rect'].collidepoint(self.mouse.screen_xy) and inv_contents['item']:
                    machine.ui.extract_item(inv_contents, 'left' if l_click else 'right')
                    return

    def update(self) -> None:
        self.check_drag()