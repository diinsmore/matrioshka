from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import InputManager
    from player import Player

import pygame as pg

class MachineUI:
    def __init__(
        self, 
        machine: pg.sprite.Sprite, 
        screen: pg.Surface, 
        cam_offset: pg.Vector2, 
        input_manager: InputManager,
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
        self.keyboard, self.mouse = input_manager.keyboard, input_manager.mouse
        self.player = player
        self.graphics, self.fonts, self.colors = assets['graphics'], assets['fonts'], assets['colors']
        self.gen_outline = gen_outline
        self.gen_bg = gen_bg
        self.rect_in_sprite_radius = rect_in_sprite_radius
        self.render_item_amount = render_item_amount
       
        self.render = False
        self.mouse_hover = False
        self.bg_rect = None
        self.bg_w, self.bg_h = 150, 150
        self.progress_bar_height = 4
        self.icons = self.graphics['icons']
        self.box_len = 40
        self.padding = 15
        self.empty_fuel_surf = pg.transform.scale(self.icons['empty fuel'].convert_alpha(), pg.Vector2(machine.image.get_size()) * 0.8)
        self.empty_fuel_surf.set_colorkey((255, 255, 255))
        self.empty_fuel_surf.set_alpha(150)
        self.machine_mask = pg.mask.from_surface(machine.image)
        self.machine_mask_surf = self.machine_mask.to_surface(setcolor=(20, 20, 20, 255), unsetcolor=(0, 0, 0, 0))
        self.key_close_ui = self.keyboard.key_bindings['close ui window']

    def update_bg_rect(self) -> None:
        self.bg_rect = pg.Rect(self.machine.rect.midtop - self.cam_offset - pg.Vector2(self.bg_w // 2, self.bg_h + self.padding), (self.bg_w, self.bg_h))

    def check_input(self) -> Slot | None:
        return next((slot for slot in self.machine.inv if slot.rect.collidepoint(self.mouse.screen_xy)), None)

    def input_item(self, slot: InvSlot, amount: int) -> None: 
        if slot.valid_inputs and self.player.item_holding in slot.valid_inputs:
            if slot.item is None:
                slot.item = self.player.item_holding
        if self.player.item_holding == slot.item:
            slot.amount += amount
            self.player.inventory.remove_item(amount=amount)

    def extract_item(self, slot: InvSlot, click_type: str) -> None:
        extract_total = slot.amount if click_type == 'left' else max(1, slot.amount // 2)
        slot.amount -= extract_total
        self.player.inventory.add_item(slot.item, extract_total)
        if slot.amount == 0:
            slot.item = None
            
    def highlight_surf_when_hovered(self) -> None:
        if self.mouse_hover:
            self.screen.blit(self.machine_mask_surf, self.machine.rect.topleft - self.cam_offset, special_flags=pg.BLEND_RGBA_SUB)

    def render_inv(self, color='black', icon_scale: int=None, slot_preview: bool=False) -> None: 
        self.update_inv_rects()
        for slot in [s for s in [*self.machine.inv.input_slots.values(), self.machine.inv.output_slot] if s.rect]: 
            self.gen_bg(slot.rect, self.colors['ui bg highlight'] if slot.rect.collidepoint(self.mouse.screen_xy) else color) 
            self.gen_outline(slot.rect)
            if slot.item or (slot_preview and slot.valid_inputs): # checking valid inputs to avoid rendering a preview of nothing if the assembler's output slot is empty
                self.render_inv_contents(slot, icon_scale, slot_preview)
        
    def render_inv_contents(self, slot: InvSlot, icon_scale: int | None, slot_preview: bool=False) -> None:
        try:
            surf = self.graphics[slot.item if not slot_preview else next(iter(slot.valid_inputs))].copy() # valid_inputs only contains 1 string
        except KeyError:
            return
        if icon_scale is not None:
            surf = pg.transform.scale(surf, pg.Vector2(surf.get_size()) * icon_scale)
        if not slot.amount > 0 and slot_preview:
            surf.set_alpha(150)
        self.screen.blit(surf, surf.get_frect(center=slot.rect.center))
        if slot.amount:
            self.render_item_amount(slot.amount, slot.rect.bottomright - pg.Vector2(5, 5))

    def render_progress_bar(self, inv_box: pg.Rect, percent: float, width=None, padding: pg.Vector2=pg.Vector2(0, 1), color: str='black') -> None:
        bar = pg.Rect(inv_box.bottomleft + padding, (width if width else self.box_len, self.progress_bar_height))
        pg.draw.rect(self.screen, color, bar, 1)
        progress_rect = pg.Rect(bar.topleft + pg.Vector2(1, 1), ((bar.width - 2) * (percent / 100), bar.height - 2))
        pg.draw.rect(self.screen, 'forestgreen', progress_rect)

    def update_fuel_status(self) -> None:
        slots = self.machine.inv.input_slots
        if 'smelt' in slots and not slots['fuel'].item:
            self.screen.blit(self.empty_fuel_surf, self.empty_fuel_surf.get_rect(center=self.machine.rect.center - self.cam_offset))

    def update(self) -> None:
        self.mouse_hover = self.machine.rect.collidepoint(self.mouse.world_xy)
        self.highlight_surf_when_hovered()
        if not self.render:
            self.render = self.mouse_hover and self.mouse.buttons_pressed['left']
        elif self.keyboard.held_keys[self.key_close_ui]:
            self.render = False
        else:
            self.render_interface()
        self.update_fuel_status()