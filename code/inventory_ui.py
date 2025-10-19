from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from inventory import Inventory
    from player import Player
    from item_placement import ItemPlacement
    from input_manager import Mouse

import pygame as pg

from settings import TILE_SIZE, TILES, PLACEABLE_ITEMS, MATERIALS, PIPE_TRANSPORT_DIRECTIONS

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
        gen_outline: callable,
        gen_bg: callable,
        render_inv_item_name: callable,
        get_scaled_img: callable,
        get_grid_xy: callable,
        get_sprites_in_radius: callable,
        render_item_amount: callable
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
        self.gen_outline = gen_outline
        self.gen_bg = gen_bg
        self.render_inv_item_name = render_inv_item_name
        self.get_scaled_img = get_scaled_img
        self.get_grid_xy = get_grid_xy
        self.get_sprites_in_radius = get_sprites_in_radius
        self.render_item_amount = render_item_amount
        
        self.graphics = self.assets['graphics']
        self.fonts = self.assets['fonts']
        self.colors = self.assets['colors']

        self.inventory = self.player.inventory
        self.num_slots = self.inventory.num_slots
        self.num_cols, self.num_rows = 5, 2
        self.slot_width = self.slot_height = TILE_SIZE * 2
        self.outline_width, self.outline_height = self.slot_width * self.num_cols, self.slot_height * self.num_rows
        self.icon_size = pg.Vector2(TILE_SIZE, TILE_SIZE)
        self.icon_padding = ((self.slot_width, self.slot_height) - self.icon_size) // 2
        self.outline = pg.Rect(self.padding, self.top, self.outline_width, self.outline_height)

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
            self.outline, 
            self.slot_width, 
            self.slot_height, 
            self.num_rows, 
            self.num_cols, 
            self.icon_size, 
            self.icon_padding,
            self.mech_sprites,
            self.get_grid_xy,
            self.get_sprites_in_radius
        )

        self.item_placement = None # not initialized yet

    def update_dimensions(self) -> None:
        self.num_rows = 2 if not self.expand else (self.num_slots // self.num_cols)
        self.outline_height = self.slot_height * self.num_rows
        self.outline = pg.Rect(self.padding, self.top, self.outline_width, self.outline_height)

    def render_bg(self) -> None:
        self.gen_bg(self.outline, transparent=True)
        self.gen_outline(self.outline)

    def render_slots(self) -> None:
        selected_idx = self.inventory.index
        for x in range(self.num_cols):
            for y in range(self.num_rows):
                box = pg.Rect((self.padding, self.top) + pg.Vector2(x * self.slot_width, y * self.slot_height), (self.slot_width - 1, self.slot_height - 1))
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
                topleft = self.outline.topleft + pg.Vector2(col * self.slot_width, row * self.slot_height)
                padding = (pg.Vector2(self.slot_width, self.slot_height) - surf.get_size()) // 2
                blit_xy = topleft + padding
                rect = surf.get_rect(topleft=blit_xy)
                self.screen.blit(surf, rect)
                self.render_item_amount(item_data['amount'], blit_xy)
                self.render_inv_item_name(rect, item_name)
            except KeyError:
                pass

    def get_item_surf(self, name: str) -> pg.Surface:
        surf = self.graphics[name] 
        return surf if surf.get_size() == self.icon_size else self.get_scaled_img(surf, name, *self.icon_size)

    def update(self) -> None:
        if self.render:
            self.render_bg()
            self.render_slots()
            self.render_icons()
            self.item_drag.update()


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
        slot_width: int,
        slot_height: int,
        num_rows: int,
        num_cols: int,
        icon_size: pg.Vector2,
        icon_padding: pg.Vector2,
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
        self.slot_width = slot_width
        self.slot_height = slot_height
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.icon_size = icon_size
        self.icon_padding = icon_padding
        self.mech_sprites = mech_sprites
        self.get_grid_xy = get_grid_xy
        self.get_sprites_in_radius = get_sprites_in_radius

        self.active = False
        self.image = None
        self.rect = None
        self.amount = None
        self.rect_base = pg.Rect(self.icon_padding, self.icon_size)
        self.material_names = set(MATERIALS.keys())
        self.tile_names = set(TILES.keys())

        self.item_placement = None # not initialized yet

    def get_clicked_item(self) -> str|None:
        for item_name, item_data in self.inventory.contents.items():
            row, col = divmod(item_data['index'], self.num_cols)
            if (icon_rect := self.rect_base.move(self.outline.topleft + pg.Vector2(col * self.slot_width, row * self.slot_height))).collidepoint(self.mouse.screen_xy):
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
                if self.outline.collidepoint(self.mouse.screen_xy) and (item := self.get_clicked_item()):
                    self.start_drag(item, 'left' if left_click else 'right')   
                else:
                    if machines_with_inv := [m for m in self.get_sprites_in_radius(self.player.rect, self.mech_sprites) if m.ui.render and hasattr(m, 'has_inv')]:
                        self.check_machine_extract(machines_with_inv, left_click, right_click)
        else:
            if self.active:
                self.render_item_drag()
                if self.keyboard.pressed_keys[pg.K_q]:
                    self.end_drag()
                
    def start_drag(self, item_name: str, click_type: str) -> None:
        self.active = True
        self.player.item_holding = item_name
        self.player.inventory.index = self.player.inventory.contents[item_name]['index']
        self.image = self.graphics[item_name].copy() # a copy to not alter the alpha value of the original
        self.image.set_alpha(150) # slightly transparent until it's placed
        self.rect = self.image.get_rect(center=self.mouse.world_xy)
        item_amount = self.player.inventory.contents[self.player.item_holding]['amount']
        self.amount = item_amount if click_type == 'left' else (item_amount // 2)
 
    def end_drag(self) -> None: 
        if self.player.item_holding in (self.material_names|self.tile_names) and not self.item_placement.valid_placement(self.mouse.tile_xy, self.player): # calling valid_placement to distinguish between placing e.g a copper block in the smelt compartment vs on the ground
            self.place_item_in_machine()
        else:
            self.item_placement.place_item(self.player, (self.mouse.world_xy[0] // TILE_SIZE, self.mouse.world_xy[1] // TILE_SIZE))
        self.active = False
        self.image = None
        self.rect = None
        self.amount = None
        self.player.item_holding = None 

    def render_item_drag(self) -> None:
        self.rect.topleft = self.get_grid_xy()
        self.screen.blit(self.image, self.rect)
        if 'pipe' in self.player.item_holding:
            item_name, idx = self.player.item_holding.split(' ')
        else:
            item_name = self.player.item_holding
        if item_name in PLACEABLE_ITEMS:
            item_xy_world = (pg.Vector2(self.rect.topleft) + self.cam_offset) // TILE_SIZE
            if item_name == 'pipe' and self.keyboard.pressed_keys[pg.K_r]:
                self.rotate_pipe(idx)
            self.item_placement.render_ui(self.image, self.rect, (int(item_xy_world.x), int(item_xy_world.y)), self.player)
    
    def rotate_pipe(self, idx: int) -> None:
        idx = (idx + 1) % len(PIPE_TRANSPORT_DIRECTIONS)
        self.image = self.graphics[f'pipe {idx}']

    def place_item_in_machine(self) -> None:
        for machine in [m for m in self.get_sprites_in_radius(self.player.rect, self.mech_sprites) if m.ui.render]:
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