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
        self.box_w = self.box_h = 40 
        self.padding = 10
        self.graphics = self.assets['graphics']
        self.right_arrow_surf = self.graphics['ui']['right arrow']
        if furnace.variant == 'burner':
            self.fuel_icon = self.graphics['ui']['fuel icon']
        self.highlight_color = self.assets['colors']['ui bg highlight']
        self.furnace_mask = pg.mask.from_surface(furnace.image)
        self.furnace_mask_surf = self.furnace_mask.to_surface(setcolor=(20, 20, 20, 255), unsetcolor=(0, 0, 0, 0))
        
        self.key_close_ui = self.keyboard.key_bindings['close ui window']
    
    def get_box_rects(self) -> tuple[pg.Rect, pg.Rect|None, pg.Rect]:
        y_offset = (self.bg_h // 2) - ((self.box_h + self.padding) if self.furnace.variant == 'burner' else self.box_h // 2) 
        smelt_box = pg.Rect(self.bg_rect.topleft + pg.Vector2(self.padding, y_offset), (self.box_w, self.box_h))
        fuel_box = None
        if self.furnace.variant == 'burner': 
            fuel_box = smelt_box.copy() 
            fuel_box.midtop = smelt_box.midbottom + pg.Vector2(0, (self.bg_rect.centery - smelt_box.bottom) * 2) 
        output_box = smelt_box.copy() 
        output_box.midright = self.bg_rect.midright - pg.Vector2(self.padding, 0)
        return smelt_box, fuel_box, output_box 
    
    def get_box_data(self) -> dict[str, dict]:
        self.smelt_box, self.fuel_box, self.output_box = self.get_box_rects()
        data = {
            'smelt': {'contents': self.furnace.smelt_input, 'valid inputs': self.furnace.can_smelt, 'rect': self.smelt_box}, 
            'output': {'contents': self.furnace.output, 'valid inputs': self.furnace.output['item'], 'rect': self.output_box} # only allow input if adding to the existing total, to prevent items the furnace can't produce from being inserted
        }
        if self.furnace.variant == 'burner':
            data['fuel'] = {'contents': self.furnace.fuel_input, 'valid inputs': self.furnace.fuel_sources, 'rect': self.fuel_box}
        return data

    def check_input(self, box_data: dict[str, dict]) -> str|None:
        box_name = None
        for name in box_data:
            if box_data[name]['rect'].collidepoint(self.mouse.screen_xy):
                box_name = name
        return box_name

    def input_item(self, box_name: str, amount: int, box_data: dict[str, dict]) -> None: 
        if self.player.item_holding in box_data['valid inputs']:
            if box_name != 'output' and box_data['contents']['item'] is None: # the previous check would have failed for the output box (requires an existing item to accept input)
                box_data['contents']['item'] = self.player.item_holding
            if self.player.item_holding == box_data['contents']['item']:
                box_data['contents']['amount'] += amount
                self.player.inventory.remove_item(self.player.item_holding, amount)
    
    def extract_item(self, box_type: str, click_type: str) -> None:
        box_inv = self.get_box_data()[box_type]['contents']
        if box_inv['item'] is not None:
            extract_total = box_inv['amount'] if click_type == 'left' else max(1, box_inv['amount'] // 2)
            box_inv['amount'] -= extract_total
            self.player.inventory.add_item(box_inv['item'], extract_total)
            self.player.item_holding = box_inv['item']
            if box_inv['amount'] == 0:
                box_inv['item'] = None
            
    def highlight_surf_when_hovered(self, rect_mouse_collide: bool) -> None:
        if rect_mouse_collide:
            self.screen.blit(self.furnace_mask_surf, self.furnace.rect.topleft - self.cam_offset, special_flags=pg.BLEND_RGBA_ADD)

    def render_boxes(self) -> None: 
        data = self.get_box_data()
        for key in data:
            contents, rect = data[key]['contents'], data[key]['rect']
            self.gen_bg(rect, color=self.highlight_color if rect.collidepoint(self.mouse.screen_xy) else 'black', transparent=False) 
            self.gen_outline(rect)
            if contents['item']: 
                self.render_box_contents(contents, rect)          
        
    def render_box_contents(self, content_data: dict[str, str|int], box_rect: pg.Rect) -> None:
        surf = self.graphics[content_data['item']]
        self.screen.blit(surf, surf.get_frect(center=box_rect.center))
        self.render_item_amount(content_data['amount'], box_rect.bottomright - pg.Vector2(5, 5))

    def render_interface(self) -> None:
        self.bg_rect = pg.Rect(self.furnace.rect.midtop - pg.Vector2(self.bg_w // 2, self.bg_h + self.padding), (self.bg_w, self.bg_h))
        if self.rect_in_sprite_radius(self.player, self.bg_rect):
            self.bg_rect.topleft -= self.cam_offset # converting to screen-space now to not mess with the radius check above
            self.gen_bg(self.bg_rect, color='black', transparent=True) 
            self.gen_outline(self.bg_rect)
            self.render_boxes()
            self.screen.blit(self.right_arrow_surf, self.right_arrow_surf.get_rect(center=self.bg_rect.center))
            if self.furnace.variant == 'burner':
                self.screen.blit(self.fuel_icon, self.fuel_icon.get_rect(midtop=self.fuel_box.midbottom))
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