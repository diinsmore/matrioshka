from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player

import pygame as pg

class FurnaceUI:
    def __init__(
        self, 
        screen: pg.Surface, 
        cam_offset: pg.Vector2,
        furnace_surf: pg.Surface,
        furnace_rect: pg.Rect,
        items_smelted: dict[str, dict],
        mouse: Mouse, 
        keyboard: Keyboard,
        player: Player,
        assets: dict[str, dict[str, any]],
        gen_outline: callable, 
        gen_bg: callable,
        rect_in_sprite_radius: callable,
        render_item_amount: callable,
        save_data: dict[str, any]
    ):
        self.screen = screen
        self.cam_offset = cam_offset
        self.furnace_surf = furnace_surf
        self.furnace_rect = furnace_rect
        self.items_smelted = items_smelted
        self.mouse = mouse
        self.keyboard = keyboard
        self.player = player
        self.assets = assets
        self.gen_outline = gen_outline
        self.gen_bg = gen_bg
        self.rect_in_sprite_radius = rect_in_sprite_radius
        self.render_item_amount = render_item_amount

        self.render = False
        self.outline_w = self.outline_h = 150
        self.padding = 10
        self.item_box_w = self.item_box_h = 40
        self.graphics = self.assets['graphics']
        
        self.highlight_color = self.assets['colors']['ui bg highlight']
        self.right_arrow = self.graphics['ui']['right arrow']
        self.fuel_icon = self.graphics['ui']['fuel icon']
        self.furnace_mask = pg.mask.from_surface(self.furnace_surf)
        self.furnace_mask_surf = self.furnace_mask.to_surface(setcolor=(20, 20, 20, 255), unsetcolor=(0, 0, 0, 0))
        
        self.smelt_input = save_data['smelt input'] if save_data else {'item': None, 'amount': 0}
        self.fuel_input = save_data['fuel input'] if save_data else {'item': None, 'amount': 0}
        self.output = save_data['fuel input'] if save_data else {'item': None, 'amount': 0}

        self.key_close_ui = self.keyboard.key_bindings['close ui window']
        
        self.variant = self.fuel_sources = None # initialized with the subclass

    def check_input(self, item: str) -> str|None:
        input_type = None
        if self.smelt_input_box.collidepoint(self.mouse.screen_xy):
            if item in self.items_smelted:
                input_type = 'smelt'

        elif self.variant == 'burner' and self.fuel_input_box.collidepoint(self.mouse.screen_xy):
            if item in self.fuel_sources:
                input_type = 'fuel'

        return input_type

    def input_item(self, item: str, input_type: str, amount: int) -> None: 
        if input_type == 'smelt':
            if not self.smelt_input['item']: 
                self.smelt_input['item'] = item

            if item == self.smelt_input['item']: 
                self.player.inventory.remove_item(item, amount)
                self.smelt_input['amount'] += amount
        else:
            if not self.fuel_input['item']:
                self.fuel_input['item'] = item
            
            if item == self.fuel_input['item']:
                self.player.inventory.remove_item(item, amount)
                self.fuel_input['amount'] += amount
    
    def extract_item(self, box: pg.Rect, click_type: str) -> None:
        box_contents = self.smelt_input if box == self.smelt_input_box else self.fuel_input
        if bool(box_contents): # not empty
            item_name, item_amount = box_contents.values()
            extract_total = item_amount if click_type == 'left' else max(1, item_amount // 2)
            box_contents['amount'] -= extract_total
            if box_contents['amount'] == 0:
                box_contents['item'] = None
            self.player.inventory.add_item(item_name, extract_total)
            self.player.item_holding = item_name
            
    def highlight_surf_when_hovered(self, rect_mouse_collide: bool) -> None:
        if rect_mouse_collide:
            self.screen.blit(self.furnace_mask_surf, self.furnace_rect.topleft - self.cam_offset, special_flags=pg.BLEND_RGBA_ADD)

    def render_interface(self) -> None:
        bg_rect = pg.Rect(self.furnace_rect.midtop - pg.Vector2(self.outline_w//2, self.outline_h + self.padding), (self.outline_w, self.outline_h))
        if not self.rect_in_sprite_radius(self.player, bg_rect):
            self.render = False 
            return
        bg_rect.topleft -= self.cam_offset # converting to world-space now to not mess with the radius check above
        self.render_slots(bg_rect)

    def render_slots(self, bg_rect: pg.Rect) -> None: 
        y_offset = (self.outline_h // 2) - ((self.item_box_h + self.padding) if self.variant == 'burner' else self.item_box_h // 2) 
        self.smelt_input_box = pg.Rect(bg_rect.topleft + pg.Vector2(self.padding, y_offset), (self.item_box_w, self.item_box_h)) 
        
        self.fuel_input_box = None 
        if self.variant == 'burner': 
            self.fuel_input_box = self.smelt_input_box.copy() 
            self.fuel_input_box.midtop = self.smelt_input_box.midbottom + pg.Vector2(0, (bg_rect.centery - self.smelt_input_box.bottom) * 2) 
            self.screen.blit(self.fuel_icon, self.fuel_icon.get_rect(midtop=self.fuel_input_box.midbottom)) 
        
        self.output_box = self.smelt_input_box.copy() 
        self.output_box.midright = bg_rect.midright - pg.Vector2(self.padding, 0) 
            
        boxes = [bg_rect, self.smelt_input_box, self.output_box, self.fuel_input_box] 
        for box in boxes if self.fuel_input_box else boxes[:-1]: 
            self.gen_bg(
                box, 
                color=self.highlight_color if box != bg_rect and box.collidepoint(self.mouse.screen_xy) else 'black', 
                transparent=False if box != bg_rect else True
            ) 
            self.gen_outline(box) 
        
        self.render_slot_contents()
        self.screen.blit(self.right_arrow, self.right_arrow.get_rect(center=bg_rect.center))
          
    def render_slot_contents(self) -> None:
        if self.smelt_input['item']:
            item_name, item_amount = self.smelt_input['item'], self.smelt_input['amount']
            surf = self.graphics[item_name]
            self.screen.blit(surf, surf.get_frect(center=self.smelt_input_box.center))
            self.render_item_amount(item_amount, self.smelt_input_box.bottomright)

        elif self.fuel_input['item']:
            item_name, item_amount = self.fuel_input['item'], self.fuel_input['amount']
            surf = self.graphics[item_name]
            self.screen.blit(surf, surf.get_frect(center=self.fuel_input_box.center))
            self.render_item_amount(item_amount, self.fuel_input_box.bottomright - pg.Vector2(5, 5))

    def run(self, rect_mouse_collide: bool) -> None:
        self.highlight_surf_when_hovered(rect_mouse_collide)
        if not self.render:
            self.render = rect_mouse_collide and self.mouse.click_states['left']
        else:
            if self.keyboard.held_keys[self.key_close_ui]:
                self.render = False
            else:
                self.render_interface()
            
    def update(self) -> None:
        self.run(self.furnace_rect.collidepoint(self.mouse.world_xy))