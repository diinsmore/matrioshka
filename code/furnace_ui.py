from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player
    from furnaces import Furnace

import pygame as pg

class FurnaceUI:
    def __init__(
        self, 
        furnace: Furnace,
        screen: pg.Surface, 
        cam_offset: pg.Vector2,
        mouse: Mouse, 
        keyboard: Keyboard,
        player: Player,
        assets: dict[str, dict[str, any]],
        gen_outline: callable, 
        gen_bg: callable,
        rect_in_sprite_radius: callable,
        render_item_amount: callable
    ):
        self.furnace = furnace
        self.screen = screen
        self.cam_offset = cam_offset
        self.mouse = mouse
        self.keyboard = keyboard
        self.player = player
        self.assets = assets
        self.gen_outline = gen_outline
        self.gen_bg = gen_bg
        self.rect_in_sprite_radius = rect_in_sprite_radius
        self.render_item_amount = render_item_amount

        self.render = False
        self.bg_w = self.bg_h = 150
        self.compartment_w = self.compartment_h = 40 
        self.padding = 10
        self.graphics = self.assets['graphics']
        self.right_arrow_surf = self.graphics['ui']['right arrow']
        if furnace.variant == 'burner':
            self.fuel_icon = self.graphics['ui']['fuel icon']
        self.highlight_color = self.assets['colors']['ui bg highlight']
        self.furnace_mask = pg.mask.from_surface(furnace.image)
        self.furnace_mask_surf = self.furnace_mask.to_surface(setcolor=(20, 20, 20, 255), unsetcolor=(0, 0, 0, 0))
        
        self.key_close_ui = self.keyboard.key_bindings['close ui window']

    def check_input(self, item: str) -> str|None:
        input_type = None
        if self.smelt_compartment.collidepoint(self.mouse.screen_xy):
            if item in self.furnace.can_smelt:
                input_type = 'smelt'

        elif self.furnace.variant == 'burner' and self.fuel_compartment.collidepoint(self.mouse.screen_xy):
            if item in self.furnace.fuel_sources:
                input_type = 'fuel'

        return input_type

    def input_item(self, item: str, input_type: str, amount: int) -> None: 
        if input_type == 'smelt':
            if not self.furnace.smelt_input['item']: 
                self.furnace.smelt_input['item'] = item

            if item == self.furnace.smelt_input['item']: 
                self.player.inventory.remove_item(item, amount)
                self.furnace.smelt_input['amount'] += amount
        else:
            if not self.furnace.fuel_input['item']:
                self.furnace.fuel_input['item'] = item
            
            if item == self.furnace.fuel_input['item']:
                self.player.inventory.remove_item(item, amount)
                self.furnace.fuel_input['amount'] += amount
    
    def extract_item(self, compartment: pg.Rect, click_type: str) -> None:
        compartment_inv = self.furnace.smelt_input if compartment == self.smelt_compartment else self.furnace.fuel_input
        if bool(compartment_inv): # not empty
            item_name, item_amount = compartment_inv.values()
            extract_total = item_amount if click_type == 'left' else max(1, item_amount // 2)
            compartment_inv['amount'] -= extract_total
            if compartment_inv['amount'] == 0:
                compartment_inv['item'] = None
            self.player.inventory.add_item(item_name, extract_total)
            self.player.item_holding = item_name
            
    def highlight_surf_when_hovered(self, rect_mouse_collide: bool) -> None:
        if rect_mouse_collide:
            self.screen.blit(self.furnace_mask_surf, self.furnace.rect.topleft - self.cam_offset, special_flags=pg.BLEND_RGBA_ADD)
    
    def add_compartments(self, bg_rect: pg.Rect) -> tuple[pg.Rect, pg.Rect|None, pg.Rect]:
        y_offset = (self.bg_h // 2) - ((self.compartment_h + self.padding) if self.furnace.variant == 'burner' else self.compartment_h // 2) 
        self.smelt_compartment = pg.Rect(bg_rect.topleft + pg.Vector2(self.padding, y_offset), (self.compartment_w, self.compartment_h))
        self.fuel_compartment = None
        if self.furnace.variant == 'burner': 
            self.fuel_compartment = self.smelt_compartment.copy() 
            self.fuel_compartment.midtop = self.smelt_compartment.midbottom + pg.Vector2(0, (bg_rect.centery - self.smelt_compartment.bottom) * 2) 
        self.output_compartment = self.smelt_compartment.copy() 
        self.output_compartment.midright = bg_rect.midright - pg.Vector2(self.padding, 0)
        return self.smelt_compartment, self.fuel_compartment, self.output_compartment 
        
    def render_boxes(self, bg_rect: pg.Rect) -> None: 
        boxes = [bg_rect, *self.add_compartments(bg_rect)]
        if self.furnace.variant == 'electric':
            boxes.remove(self.fuel_compartment)
        for box in boxes:
            self.gen_bg(
                box, 
                color=self.highlight_color if box != bg_rect and box.collidepoint(self.mouse.screen_xy) else 'black', 
                transparent=False if box != bg_rect else True
            ) 
            self.gen_outline(box)
            if self.furnace.variant == 'burner' and box == self.fuel_compartment:
                self.screen.blit(self.fuel_icon, self.fuel_icon.get_rect(midtop=self.fuel_compartment.midbottom)) 

        self.render_compartment_input()
        
    def render_compartment_input(self) -> None:
        if self.furnace.smelt_input['item']:
            item_name, item_amount = self.furnace.smelt_input['item'], self.furnace.smelt_input['amount']
            surf = self.graphics[item_name]
            self.screen.blit(surf, surf.get_frect(center=self.smelt_compartment.center))
            self.render_item_amount(item_amount, self.smelt_compartment.bottomright - pg.Vector2(5, 5))

        elif self.furnace.fuel_input['item']:
            item_name, item_amount = self.furnace.fuel_input['item'], self.furnace.fuel_input['amount']
            surf = self.graphics[item_name]
            self.screen.blit(surf, surf.get_frect(center=self.fuel_compartment.center))
            self.render_item_amount(item_amount, self.fuel_compartment.bottomright - pg.Vector2(5, 5))

    def render_interface(self) -> None:
        bg_rect = pg.Rect(self.furnace.rect.midtop - pg.Vector2(self.bg_w // 2, self.bg_h + self.padding), (self.bg_w, self.bg_h))
        if not self.rect_in_sprite_radius(self.player, bg_rect):
            self.render = False 
            return
        bg_rect.topleft -= self.cam_offset # converting to world-space now to not mess with the radius check above
        self.render_boxes(bg_rect)
        self.screen.blit(self.right_arrow_surf, self.right_arrow_surf.get_rect(center=bg_rect.center))

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
        self.run(self.furnace.rect.collidepoint(self.mouse.world_xy))