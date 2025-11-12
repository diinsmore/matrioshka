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
        rect_base: pg.Rect,
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
        self.rect_base = rect_base
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
            if (icon_rect := self.rect_base.move(self.outline.topleft + padding)).collidepoint(self.mouse.screen_xy):
                return item_name

    def check_drag(self) -> None:
        left_click, right_click = self.mouse.buttons_pressed.values()
        if left_click or right_click:
            if self.active:
                if right_click:
                    self.item_drag_amount //= 2
                else:
                    self.end_drag()
            else:
                if self.outline.collidepoint(self.mouse.screen_xy) and (item_name := self.get_clicked_item()):
                    self.start_drag(item_name, 'left' if left_click else 'right')   
                else:
                    if machines_with_inv := [m for m in self.get_sprites_in_radius(self.player.rect, self.mech_sprites) if hasattr(m, 'has_inv') and m.ui.render]:
                        self.check_machine_extract(machines_with_inv, left_click, right_click)
        else:
            if self.active:
                self.render_item_drag()
                if self.keyboard.pressed_keys[pg.K_q]:
                    self.end_drag()
                
    def start_drag(self, item_name: str, click_type: str) -> None:
        self.active = True
        self.player.inventory.index = self.player.inventory.contents[item_name]['index']
        self.update_item_data(item_name, click_type)
    
    def update_item_data(self, item_name: str, click_type: str, start_drag: bool=True, end_drag: bool=False) -> None:
        self.player.item_holding = item_name if start_drag else None
        self.image = self.graphics[item_name].copy() if start_drag else None # a copy to not alter the alpha value of the original
        self.rect = self.image.get_rect(center=self.mouse.world_xy) if start_drag else None
        if start_drag:
            self.image.set_alpha(150) # slightly transparent until it's placed
            item_amount = self.player.inventory.contents[item_name]['amount'] 
            self.amount = item_amount if click_type == 'left' else (item_amount // 2)
        else:
            self.amount = 0
            self.active = False

    def end_drag(self) -> None: 
        if self.player.item_holding in (self.material_names | self.tile_names) and not self.item_placement.valid_placement(self.mouse.tile_xy, self.player): # calling valid_placement to distinguish between placing e.g a copper block in the smelt compartment vs on the ground
            self.place_item_in_machine()
        else:
            self.item_placement.place_item(self.player, (self.mouse.world_xy[0] // TILE_SIZE, self.mouse.world_xy[1] // TILE_SIZE), self.old_pipe_idx)
        if not self.player.item_holding:
            self.active, self.image, self.rect, self.amount, self.old_pipe_idx = None, None, None, None, None

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
        if self.player.item_holding:
            self.check_drag()
        else:
            self.update_item_data(None, None, False, True)