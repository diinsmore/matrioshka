from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from inventory import Inventory
    from player import Player
    from item_placement import ItemPlacement
    from input_manager import Mouse

import pygame as pg

from settings import TILE_SIZE, PLACEABLE_ITEMS, MATERIALS

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
        render_inventory_item_name: callable,
        get_scaled_image: callable,
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
        self.render_inventory_item_name = render_inventory_item_name
        self.get_scaled_image = get_scaled_image
        self.get_grid_xy = get_grid_xy
        self.get_sprites_in_radius = get_sprites_in_radius
        self.render_item_amount = render_item_amount
        
        self.graphics = self.assets['graphics']
        self.fonts = self.assets['fonts']
        self.colors = self.assets['colors']

        self.inventory = self.player.inventory
        self.num_slots = self.inventory.num_slots
        self.num_cols = 5
        self.num_rows = 2
        self.box_width = self.box_height = TILE_SIZE * 2
        self.total_width = self.box_width * self.num_cols
        self.total_height = self.box_height * self.num_rows
        self.icon_size = pg.Vector2(TILE_SIZE, TILE_SIZE)
        self.render = True
        self.expand = False
        self.outline = pg.Rect(self.padding, self.top, self.total_width, self.total_height)

        self.drag = False
        self.image_to_drag = self.rect_to_drag = self.item_drag_amount = None
        self.material_names = set(MATERIALS.keys())
        self.item_placement = None # not initialized yet
    
    def update_dimensions(self) -> None:
        self.num_rows = 2 if not self.expand else self.num_slots // self.num_cols
        self.total_height = self.box_height * self.num_rows

    def render_bg(self) -> None:
        rect = pg.Rect(self.padding, self.top, self.total_width, self.total_height)
        self.gen_outline(rect)
        self.gen_bg(rect, transparent=True)
        
    def render_slots(self) -> None:
        selected_idx = self.inventory.index
        for x in range(self.num_cols):
            for y in range(self.num_rows):
                box = pg.Rect(
                    (self.padding, self.top) + pg.Vector2(x * self.box_width, y * self.box_height), 
                    (self.box_width - 1, self.box_height - 1)  # -1 for a slight gap between boxes
                )
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
                topleft = self.outline.topleft + pg.Vector2(col * self.box_width, row * self.box_height)
                padding = (pg.Vector2(self.box_width, self.box_height) - surf.get_size()) // 2
                blit_xy = topleft + padding
                rect = surf.get_rect(topleft=blit_xy)
                self.screen.blit(surf, rect)
                self.render_item_amount(item_data['amount'], blit_xy)
                self.render_inventory_item_name(rect, item_name)
            except KeyError:
                pass

    def get_item_surf(self, name: str) -> pg.Surface:
        surf = self.graphics[name] 
        return surf if surf.get_size() == self.icon_size else self.get_scaled_image(surf, name, *self.icon_size)
    
    def check_drag(self) -> None:
        l_click, r_click = self.mouse.click_states.values()
        if l_click or r_click:
            if self.drag and self.player.item_holding:
                if r_click and self.item_drag_amount:
                    self.item_drag_amount //= 2
                else:
                    self.end_drag()
            else:
                if self.outline.collidepoint(self.mouse.screen_xy):
                    item = self.get_clicked_item()
                    if item:
                        self.start_drag(item, 'left' if l_click else 'right')    
                else:
                    machines_with_ui_open = [m for m in self.get_sprites_in_radius(self.player.rect, self.mech_sprites) if m.ui.render]
                    if machines_with_ui_open: 
                        self.check_machine_box_input(machines_with_ui_open, l_click, r_click)
        else:
            if self.drag:
                self.render_item_drag()
                if self.keyboard.pressed_keys[pg.K_q]:
                    self.end_drag()
                
    def start_drag(self, item: str, click_type: str) -> None:
        self.drag = True
        self.player.item_holding = item
        self.player.inventory.index = self.player.inventory.contents[item]['index']  
        self.image_to_drag = self.graphics[item].copy() # a copy to not alter the alpha value of the original
        self.image_to_drag.set_alpha(150) # slightly transparent until it's placed
        self.rect_to_drag = self.image_to_drag.get_rect(center=self.mouse.world_xy)
        item_amount = self.player.inventory.contents[item]['amount']
        self.item_drag_amount = item_amount if click_type == 'left' else item_amount // 2
 
    def end_drag(self) -> None: 
        if self.player.item_holding in self.material_names:
            self.place_item_in_machine()
        else:
            self.item_placement.place_item(self.player, (self.mouse.world_xy[0] // TILE_SIZE, self.mouse.world_xy[1] // TILE_SIZE))
        self.drag = False
        self.image_to_drag = self.rect_to_drag = self.item_drag_amount = self.player.item_holding = None 
    
    def get_clicked_item(self) -> str|None:
        for item_name, item_data in self.inventory.contents.items():
            row, col = divmod(item_data['index'], self.num_cols)
            topleft = self.outline.topleft + pg.Vector2(col * self.box_width, row * self.box_height)
            padding = ((self.box_width, self.box_height) - self.icon_size) // 2
            icon_rect = pg.Rect(topleft + padding, self.icon_size)
            if icon_rect.collidepoint(self.mouse.screen_xy):
                return item_name
    
    def render_item_drag(self) -> None:
        self.rect_to_drag.topleft = self.get_grid_xy()
        self.screen.blit(self.image_to_drag, self.rect_to_drag)
        if self.player.item_holding in PLACEABLE_ITEMS:
            item_xy_world = (pg.Vector2(self.rect_to_drag.topleft) + self.cam_offset) // TILE_SIZE
            self.item_placement.render_ui(
                self.image_to_drag, 
                self.rect_to_drag, 
                (int(item_xy_world.x), int(item_xy_world.y)),
                self.player
            )

    def place_item_in_machine(self) -> None:
        for machine in [m for m in self.get_sprites_in_radius(self.player.rect, self.mech_sprites) if m.ui.render]:
            box_data = machine.ui.get_box_data()
            input_box_name = machine.ui.check_input(box_data)
            if input_box_name:
                machine.ui.input_item(input_box_name, self.item_drag_amount, box_data[input_box_name])
                return
    
    def check_machine_box_input(self, machines: list[pg.sprite.Sprite], l_click: bool, r_click: bool) -> None:
        for machine in machines:
            ui = machine.ui
            boxes = [('smelt', ui.smelt_box), ('output', ui.output_box)]
            if machine.variant == 'burner':
                boxes.append(('fuel', ui.fuel_box))
            for name, rect in boxes:
                if rect.collidepoint(self.mouse.screen_xy) and (l_click or r_click):
                    ui.extract_item(name, 'left' if l_click else 'right')

    def update(self) -> None:
        if self.render:
            self.update_dimensions()
            self.render_bg()
            self.render_slots()
            self.render_icons()
            self.check_drag()