from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from inventory import Inventory
    from player import Player
    from item_placement import ItemPlacement
    from input_manager import Mouse
    from ui import InvUIHelpers

import pygame as pg
from dataclasses import dataclass

from settings import TILE_SIZE, TILES, PLACEABLE_ITEMS, MATERIALS

class InventoryUI:
    def __init__(
        self,
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        assets: dict[str, dict[str, any]], 
        mouse: Mouse,
        keyboard: Keyboard,
        top: int,
        player: Player,
        mech_sprites: pg.sprite.Group,
        helpers: InvUIHelpers
    ):  
        self.screen = screen
        self.cam_offset = cam_offset
        self.assets = assets
        self.mouse = mouse
        self.keyboard = keyboard
        self.padding = 5
        self.top = top + self.padding
        self.player = player
        self.mech_sprites = mech_sprites
        self.helpers = helpers
        
        self.graphics = self.assets['graphics']
        self.fonts = self.assets['fonts']
        self.colors = self.assets['colors']

        self.inventory = self.player.inventory
        self.num_slots = self.inventory.num_slots
        self.num_cols, self.num_rows = 5, 2
        self.slot_w = self.slot_h = TILE_SIZE * 2
        self.total_w, self.total_h = self.slot_w * self.num_cols, self.slot_h * self.num_rows
        self.icon_size = pg.Vector2(TILE_SIZE, TILE_SIZE)
        self.icon_padding = ((self.slot_w, self.slot_h) - self.icon_size) // 2
        self.outline = pg.Rect(self.padding, self.top, self.total_w, self.total_h)

        self.render = True
        self.expand = False

        self.item_drag = ItemDrag(
            screen, 
            cam_offset,
            self.graphics,
            player, 
            mouse, 
            keyboard, 
            self.inventory,
            InvUIDimensions(self.outline, self.slot_w, self.slot_h, self.num_rows, self.num_cols, self.icon_size, self.icon_padding),
            helpers.get_grid_xy
        )

        self.item_placement = None # not initialized yet

    def update_dimensions(self) -> None:
        self.num_rows = 2 if not self.expand else self.num_slots // self.num_cols
        self.total_height = self.slot_h * self.num_rows

    def render_bg(self) -> None:
        rect = pg.Rect(self.padding, self.top, self.total_w, self.total_h)
        self.helpers.gen_outline(rect)
        self.helpers.gen_bg(rect, transparent=True)
        
    def render_slots(self) -> None:
        selected_idx = self.inventory.index
        for x in range(self.num_cols):
            for y in range(self.num_rows):
                box = pg.Rect((self.padding, self.top) + pg.Vector2(x * self.slot_w, y * self.slot_h), (self.slot_w - 1, self.slot_h - 1))
                pg.draw.rect(self.screen, 'black', box, 1)
                if (y * (self.num_rows - 1) * self.num_cols) + x == selected_idx:
                    self.highlight_slot(box)

    def highlight_slot(self, slot: pg.Rect) -> None:
        hl_surf = pg.Surface(slot.size - pg.Vector2(2, 2)) # -2 to not overlap with the 1px borders
        hl_surf.fill('gray')
        hl_surf.set_alpha(50)
        hl_rect = hl_surf.get_rect(topleft = slot.topleft)
        self.screen.blit(hl_surf, hl_rect)
        
    def render_icons(self) -> None:
        for item_name, item_data in list(self.player.inventory.contents.items()): # storing in a list to avoid the 'dictionary size changed during iteration' error when removing placed items
            try:
                surf = self.get_item_surf(item_name)
                row, col = divmod(item_data['index'], self.num_cols) # determine the slot an item corresponds to
                topleft = self.outline.topleft + pg.Vector2(col * self.slot_w, row * self.slot_h)
                padding = (pg.Vector2(self.slot_w, self.slot_h) - surf.get_size()) // 2
                blit_xy = topleft + padding
                rect = surf.get_rect(topleft=blit_xy)
                self.screen.blit(surf, rect)
                self.helpers.render_item_amount(item_data['amount'], blit_xy)
                self.helpers.render_inv_item_name(rect, item_name)
            except KeyError:
                pass

    def get_item_surf(self, name: str) -> pg.Surface:
        surf = self.graphics[name] 
        return surf if surf.get_size() == self.icon_size else self.helpers.get_scaled_img(surf, name, *self.icon_size)

    def update(self) -> None:
        if self.render:
            self.update_dimensions()
            self.render_bg()
            self.render_slots()
            self.render_icons()
            self.item_drag.update()


@dataclass
class InvUIDimensions:
    outline: pg.Rect
    slot_w: int
    slot_h: int
    num_rows: int
    num_cols: int
    icon_size: int
    icon_padding: int


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
        dims: InvUIDimensions,
        get_grid_xy: callable
    ):
        self.screen = screen
        self.cam_offset = cam_offset
        self.graphics = graphics
        self.player = player
        self.mouse = mouse
        self.keyboard = keyboard
        self.inventory = inventory
        self.dims = dims
        self.get_grid_xy = get_grid_xy

        self.active = False
        self.image = self.rect = self.amount = None
        self.rect_base = pg.Rect(self.dims.icon_padding, self.dims.icon_size)
        self.material_names = set(MATERIALS.keys())
        self.tile_names = set(TILES.keys())

        self.item_placement = None # not initialized yet

    def get_clicked_item(self) -> str|None:
        for item_name, item_data in self.inventory.contents.items():
            row, col = divmod(item_data['index'], self.dims.num_cols)
            offset = self.dims.outline.topleft + pg.Vector2(col * self.dims.slot_w, row * self.dims.slot_h)
            if (icon_rect := pg.Rect((self.rect_base.topleft + offset), self.rect_base.size)).collidepoint(self.mouse.screen_xy):
                return item_name

    def check_drag(self) -> None:
        l_click, r_click = self.mouse.click_states.values()
        if l_click or r_click:
            if self.active:
                if r_click:
                    self.item_drag_amount //= 2
                else:
                    self.end_drag()
            else:
                if self.dims.outline.collidepoint(self.mouse.screen_xy):
                    if item := self.get_clicked_item():
                        self.start_drag(item, 'left' if l_click else 'right')    
                else:
                    if machines_can_extract_from := [
                        m for m in self.helpers.get_sprites_in_radius(self.player.rect, self.mech_sprites) 
                        if m.ui.render and hasattr(m, 'can_extract_from')
                    ]:
                        self.check_machine_extract(machines_can_extract_from, l_click, r_click)
        else:
            if self.active:
                self.render_item_drag()
                if self.keyboard.pressed_keys[pg.K_q]:
                    self.end_drag()
                
    def start_drag(self, item: str, click_type: str) -> None:
        self.active = True
        self.player.item_holding = item
        self.player.inventory.index = self.player.inventory.contents[item]['index']  
        self.image = self.graphics[item].copy() # a copy to not alter the alpha value of the original
        self.image.set_alpha(150) # slightly transparent until it's placed
        self.rect = self.image.get_rect(center=self.mouse.world_xy)
        item_amount = self.player.inventory.contents[item]['amount']
        self.amount = item_amount if click_type == 'left' else item_amount // 2
 
    def end_drag(self) -> None: 
        if self.player.item_holding in (self.material_names|self.tile_names) and not self.item_placement.valid_placement(self.mouse.tile_xy, self.player): # calling valid_placement to distinguish between placing e.g a copper block in the smelt compartment vs on the ground
            self.place_item_in_machine()
        else:
            self.item_placement.place_item(self.player, (self.mouse.world_xy[0] // TILE_SIZE, self.mouse.world_xy[1] // TILE_SIZE))
        self.active = False
        self.image = self.rect = self.amount = self.player.item_holding = None 

    def render_item_drag(self) -> None:
        self.rect.topleft = self.get_grid_xy()
        self.screen.blit(self.image, self.rect)
        if self.player.item_holding in PLACEABLE_ITEMS:
            item_xy_world = (pg.Vector2(self.rect.topleft) + self.cam_offset) // TILE_SIZE
            self.item_placement.render_ui(self.image, self.rect, (int(item_xy_world.x), int(item_xy_world.y)), self.player)

    def place_item_in_machine(self) -> None:
        for machine in [m for m in self.get_sprites_in_radius(self.player.rect, self.mech_sprites) if m.ui.render]:
            box_data = machine.ui.get_box_data()
            if input_box_name := machine.ui.check_input(box_data):
                machine.ui.input_item(input_box_name, self.amount, box_data[input_box_name])
                return
    
    def check_machine_extract(self, machines: list[pg.sprite.Sprite], l_click: bool, r_click: bool) -> None:
        for machine in machines:
            input_box_data = machine.ui.get_box_data()
            for box_type in input_box_data.keys():
                if input_box_data[box_type]['rect'].collidepoint(self.mouse.screen_xy) and (l_click or r_click):
                    machine.ui.extract_item(box_type, 'left' if l_click else 'right')

    def update(self) -> None:
        self.check_drag()
        if self.active:
            self.render_item_drag()