from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sprite_base import SpriteBase

import pygame as pg

class MachineUI:
    def __init__(
        self,
        machine: SpriteBase,
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
        self.machine = machine
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
        self.graphics = self.assets['graphics']
        self.icons = self.graphics['icons']
        self.fonts = self.assets['fonts']
        self.empty_fuel_surf = pg.transform.scale(self.icons['empty fuel'].convert_alpha(), pg.Vector2(machine.image.get_size()) * 0.8)
        self.empty_fuel_surf.set_colorkey((255, 255, 255))
        self.empty_fuel_surf.set_alpha(150)
        self.highlight_color = self.assets['colors']['ui bg highlight']
        self.machine_mask = pg.mask.from_surface(machine.image)
        self.machine_mask_surf = self.machine_mask.to_surface(setcolor=(20, 20, 20, 255), unsetcolor=(0, 0, 0, 0))
        self.padding = 10

        self.key_close_ui = self.keyboard.key_bindings['close ui window']

    def get_bg_rect(self) -> pg.Rect:
        return pg.Rect(self.machine.rect.midtop - pg.Vector2(self.bg_w // 2, self.bg_h + self.padding), (self.bg_w, self.bg_h))

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

    def extract_item(self, box_contents: dict[str, str|int], click_type: str) -> None:
        extract_total = box_contents['amount'] if click_type == 'left' else (box_contents['amount'] // 2)
        box_contents['amount'] -= extract_total
        self.player.inventory.add_item(box_contents['item'], extract_total)
        self.player.item_holding = box_contents['item']
        if box_contents['amount'] == 0:
            box_contents['item'] = None
            
    def highlight_surf_when_hovered(self, rect_mouse_collide: bool) -> None:
        if rect_mouse_collide:
            self.screen.blit(self.machine_mask_surf, self.machine.rect.topleft - self.cam_offset, special_flags=pg.BLEND_RGBA_ADD)

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

    def render_progress_bar(self, box: pg.Rect, progress_percent: float) -> None:
        bar = pg.Rect(box.bottomleft, (self.box_w, self.progress_bar_h))
        bar_outline_w = 1
        pg.draw.rect(self.screen, 'black', bar, bar_outline_w)
        progress_rect = pg.Rect(
            bar.topleft + pg.Vector2(bar_outline_w, bar_outline_w), 
            ((bar.width - (bar_outline_w * 2)) * (progress_percent / 100), bar.height - (bar_outline_w * 2))
        )
        pg.draw.rect(self.screen, 'green' if box == self.smelt_box else 'red', progress_rect)

    def update_fuel_status(self, machine_name: str) -> None:
        if not self.machine.fuel_input['item']:
            if 'furnace' in machine_name and self.machine.variant == 'burner' and not self.machine.smelt_input['item']: # always alert empty fuel for electrics, only alert for burners if containing an item to smelt
                return
            self.screen.blit(self.empty_fuel_surf, self.empty_fuel_surf.get_rect(center=self.machine.rect.center - self.cam_offset))

    def run(self, machine_name: str, rect_mouse_collide: bool) -> None:
        self.highlight_surf_when_hovered(rect_mouse_collide)
        self.update_fuel_status(machine_name)
        if not self.render:
            self.render = rect_mouse_collide and self.mouse.buttons_pressed['left']
            return
        elif self.keyboard.held_keys[self.key_close_ui]:
            self.render = False
            return
        self.render_interface()
            
    def update(self, machine_name: str) -> None:
        self.run(machine_name, self.machine.rect.collidepoint(self.mouse.world_xy))