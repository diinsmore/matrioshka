from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player
    from furnaces import BurnerFurnace, ElectricFurnace
    from machine_ui import MachineUIHelpers, MachineUIDimensions

import pygame as pg
from machine_ui import MachineUI

class FurnaceUI(MachineUI):
    def __init__(
        self, 
        furnace: BurnerFurnace|ElectricFurnace,
        screen: pg.Surface, 
        cam_offset: pg.Vector2,
        mouse: Mouse, 
        keyboard: Keyboard,
        player: Player,
        assets: dict[str, dict[str, any]],
        helpers: MachineUIHelpers
    ):
        super().__init__(furnace, screen, cam_offset, mouse, keyboard, player, assets, helpers)
        self.bg_w = self.bg_h = 150
        self.box_w = self.box_h = 40
        self.progress_bar_w, self.progress_bar_h = self.box_w, 4
        self.padding = 10
        self.right_arrow_surf = self.graphics['ui']['right arrow']
        if furnace.variant == 'burner':
            self.fuel_icon = self.graphics['ui']['fuel icon']

    def get_box_rects(self) -> tuple[pg.Rect, pg.Rect|None, pg.Rect]:
        y_offset = (self.bg_h // 2) - ((self.box_h + self.padding) if self.machine.variant == 'burner' else self.box_h // 2) 
        smelt_box = pg.Rect(self.bg_rect.topleft + pg.Vector2(self.padding, y_offset), (self.box_w, self.box_h))
        fuel_box = None
        if self.machine.variant == 'burner': 
            fuel_box = smelt_box.copy() 
            fuel_box.midtop = smelt_box.midbottom + pg.Vector2(0, (self.bg_rect.centery - smelt_box.bottom) * 2) 
        output_box = smelt_box.copy() 
        output_box.midright = self.bg_rect.midright - pg.Vector2(self.padding, 0)
        return smelt_box, fuel_box, output_box 
    
    def get_box_data(self) -> dict[str, dict]:
        self.smelt_box, self.fuel_box, self.output_box = self.get_box_rects()
        data = {
            'smelt': {'contents': self.machine.smelt_input, 'valid inputs': self.machine.can_smelt.keys(), 'rect': self.smelt_box}, 
            'output': {'contents': self.machine.output, 'valid inputs': self.machine.output['item'], 'rect': self.output_box}
        }
        if self.machine.variant == 'burner':
            data['fuel'] = {'contents': self.machine.fuel_input, 'valid inputs': self.machine.fuel_sources, 'rect': self.fuel_box}
        return data

    def check_input(self, box_data: dict[str, dict]) -> str|None:
        box_name = None
        for name in box_data:
            if box_data[name]['rect'].collidepoint(self.mouse.screen_xy):
                box_name = name
        return box_name

    def input_item(self, box_name: str, amount: int, box_data: dict[str, dict]) -> None: 
        if self.player.item_holding in box_data['valid inputs'] and box_name != 'output': # the output box only allows input if you're adding to the item it's holding
            if box_data['contents']['item'] is None:
                box_data['contents']['item'] = self.player.item_holding

        if self.player.item_holding == box_data['contents']['item']:
            box_data['contents']['amount'] += amount
            self.player.inventory.remove_item(self.player.item_holding, amount)
    
    def extract_item(self, box_type: str, click_type: str) -> None:
        box_inv = self.get_box_data()[box_type]['contents']
        if box_inv['item'] is not None:
            extract_total = box_inv['amount'] if click_type == 'left' else (box_inv['amount'] // 2)
            box_inv['amount'] -= extract_total
            self.player.inventory.add_item(box_inv['item'], extract_total)
            self.player.item_holding = box_inv['item']
            if box_inv['amount'] == 0:
                box_inv['item'] = None
            
    def highlight_surf_when_hovered(self, rect_mouse_collide: bool) -> None:
        if rect_mouse_collide:
            self.screen.blit(self.machine_mask_surf, self.machine.rect.topleft - self.cam_offset, special_flags=pg.BLEND_RGBA_ADD)

    def render_boxes(self) -> None: 
        data = self.get_box_data()
        for key in data:
            contents, rect = data[key]['contents'], data[key]['rect']
            self.helpers.gen_bg(rect, color=self.highlight_color if rect.collidepoint(self.mouse.screen_xy) else 'black', transparent=False) 
            self.helpers.gen_outline(rect)
            if contents['item']: 
                self.render_box_contents(contents, rect)          
        
    def render_box_contents(self, content_data: dict[str, str|int], box_rect: pg.Rect) -> None:
        surf = self.graphics[content_data['item']]
        self.screen.blit(surf, surf.get_frect(center=box_rect.center))
        self.helpers.render_item_amount(content_data['amount'], box_rect.bottomright - pg.Vector2(5, 5))

    def render_progress_bar(self, box: pg.Rect, progress_percent: float) -> None:
        bar = pg.Rect(box.bottomleft, (self.box_w, self.progress_bar_h))
        bar_outline_w = 1
        pg.draw.rect(self.screen, 'black', bar, bar_outline_w)
        progress_rect = pg.Rect(
            bar.topleft + pg.Vector2(bar_outline_w, bar_outline_w), 
            ((bar.width - (bar_outline_w * 2)) * (progress_percent / 100), bar.height - (bar_outline_w * 2))
        )
        pg.draw.rect(self.screen, 'green' if box == self.smelt_box else 'red', progress_rect)

    def render_interface(self) -> None:
        self.bg_rect = pg.Rect(self.machine.rect.midtop - pg.Vector2(self.bg_w // 2, self.bg_h + self.padding), (self.bg_w, self.bg_h))
        if self.helpers.rect_in_sprite_radius(self.player, self.bg_rect):
            self.bg_rect.topleft -= self.cam_offset # converting to screen-space now to not mess with the radius check above
            self.helpers.gen_bg(self.bg_rect, color='black', transparent=True) 
            self.helpers.gen_outline(self.bg_rect)
            self.render_boxes()
            self.screen.blit(self.right_arrow_surf, self.right_arrow_surf.get_rect(center=self.bg_rect.center))

            if self.machine.variant == 'burner':
                self.screen.blit(self.fuel_icon, self.fuel_icon.get_rect(midtop=self.fuel_box.midbottom + pg.Vector2(0, self.progress_bar_h)))
            
            if self.machine.active:
                self.render_progress_bar(self.smelt_box, self.machine.timers['smelt'].progress_percent)
                if self.machine.variant == 'burner':
                    self.render_progress_bar(self.fuel_box, self.machine.timers['fuel'].progress_percent)
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
        self.run(self.machine.rect.collidepoint(self.mouse.world_xy))