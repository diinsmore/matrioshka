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

    def input_item(self, item: str, compartment: str, amount: int) -> None: 
        if compartment == 'smelt':
            self.furnace.add_item(item, compartment, amount)
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
    
    def get_compartments(self, bg_rect: pg.Rect) -> tuple[pg.Rect, pg.Rect|None, pg.Rect]:
        y_offset = (self.bg_h // 2) - ((self.compartment_h + self.padding) if self.furnace.variant == 'burner' else self.compartment_h // 2) 
        smelt_compartment = pg.Rect(bg_rect.topleft + pg.Vector2(self.padding, y_offset), (self.compartment_w, self.compartment_h))
        fuel_compartment = None
        if self.furnace.variant == 'burner': 
            fuel_compartment = smelt_compartment.copy() 
            fuel_compartment.midtop = smelt_compartment.midbottom + pg.Vector2(0, (bg_rect.centery - smelt_compartment.bottom) * 2) 
        output_compartment = smelt_compartment.copy() 
        output_compartment.midright = bg_rect.midright - pg.Vector2(self.padding, 0)
        return smelt_compartment, fuel_compartment, output_compartment 
        
    def render_compartments(self, bg_rect: pg.Rect) -> None: 
        self.smelt_compartment, self.fuel_compartment, self.output_compartment = self.get_compartments(bg_rect)
        data = {
            'smelt': {'contents': self.furnace.smelt_input, 'rect': self.smelt_compartment}, 
            'output': {'contents': self.furnace.output, 'rect': self.output_compartment}
        }
        if self.furnace.variant == 'burner':
            data['fuel'] = {'contents': self.furnace.fuel_input, 'rect': self.fuel_compartment}
            self.screen.blit(self.fuel_icon, self.fuel_icon.get_rect(midtop=self.fuel_compartment.midbottom)) 
        
        for key in data:
            contents, rect = data[key]['contents'], data[key]['rect']
            self.gen_bg(rect, color=self.highlight_color if rect.collidepoint(self.mouse.screen_xy) else 'black', transparent=False) 
            self.gen_outline(rect)
            if contents['item']: 
                self.render_compartment_contents(contents, rect)          
        
    def render_compartment_contents(self, data: dict[str, str|int], compartment_rect: pg.Rect) -> None:
        surf = self.graphics[data['item']]
        self.screen.blit(surf, surf.get_frect(center=compartment_rect.center))
        self.render_item_amount(data['amount'], compartment_rect.bottomright - pg.Vector2(5, 5))

    def render_interface(self) -> None:
        bg_rect = pg.Rect(self.furnace.rect.midtop - pg.Vector2(self.bg_w // 2, self.bg_h + self.padding), (self.bg_w, self.bg_h))
        if self.rect_in_sprite_radius(self.player, bg_rect):
            bg_rect.topleft -= self.cam_offset # converting to world-space now to not mess with the radius check above
            self.gen_bg(bg_rect, color='black', transparent=True) 
            self.gen_outline(bg_rect)
            self.render_compartments(bg_rect)
            self.screen.blit(self.right_arrow_surf, self.right_arrow_surf.get_rect(center=bg_rect.center))
        else:
            self.render = False

    def run(self, rect_mouse_collide: bool) -> None:
        self.highlight_surf_when_hovered(rect_mouse_collide)
        if not self.render:
            self.render = rect_mouse_collide and self.mouse.click_states['left']
            return
        
        elif self.keyboard.held_keys[self.key_close_ui]:
            self.render = False
            return

        self.render_interface()
            
    def update(self) -> None:
        self.run(self.furnace.rect.collidepoint(self.mouse.world_xy))