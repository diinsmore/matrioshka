from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player

import pygame as pg
from dataclasses import dataclass, fields

@dataclass(slots=True)
class InvSlot:
    item: str
    rect: pg.Rect
    valid_inputs: dict
    amount: int=0
    max_capacity: int=99


class MachineUI:
    def __init__(
        self,
        machine: pg.sprite.Sprite,
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
        self.mouse_hover = False
        self.graphics = self.assets['graphics']
        self.icons = self.graphics['icons']
        self.fonts = self.assets['fonts']
        self.highlight_color = self.assets['colors']['ui bg highlight']

        self.empty_fuel_surf = pg.transform.scale(self.icons['empty fuel'].convert_alpha(), pg.Vector2(machine.image.get_size()) * 0.8)
        self.empty_fuel_surf.set_colorkey((255, 255, 255))
        self.empty_fuel_surf.set_alpha(150)

        self.machine_mask = pg.mask.from_surface(machine.image)
        self.machine_mask_surf = self.machine_mask.to_surface(setcolor=(20, 20, 20, 255), unsetcolor=(0, 0, 0, 0))

        self.padding = 15
        self.key_close_ui = self.keyboard.key_bindings['close ui window']

    def update_bg_rect(self) -> None:
        self.bg_rect = pg.Rect(
            self.machine.rect.midtop - pg.Vector2(self.bg_width // 2, self.bg_height + self.padding), 
            (self.bg_width, self.bg_height)
        )

    def check_input(self) -> str | None:
        for slot in self.machine.inv:
            if slot.rect.collidepoint(self.mouse.screen_xy):
                return slot
        return None

    def input_item(self, slot: InvSlot, amount: int) -> None: 
        if self.player.item_holding in slot.valid_inputs and slot.rect != self.inv.output.rect: # the output box only allows input if you're adding to the item it's holding
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
            self.screen.blit(self.machine_mask_surf, self.machine.rect.topleft - self.cam_offset, special_flags=pg.BLEND_RGBA_ADD)

    def render_inv(self) -> None: 
        self.update_inv_rects()
        for slot in self.machine.inv: 
            self.gen_bg(slot.rect, color=self.highlight_color if slot.rect.collidepoint(self.mouse.screen_xy) else 'black', transparent=False) 
            self.gen_outline(slot.rect)
            if slot.item: 
                self.render_inv_contents(slot)          
        
    def render_inv_contents(self, slot: InvSlot) -> None:
        surf = self.graphics[slot.item]
        self.screen.blit(surf, surf.get_frect(center=slot.rect.center))
        self.render_item_amount(slot.amount, slot.rect.bottomright - pg.Vector2(5, 5))

    def render_progress_bar(self, inv_box: pg.Rect, percent: float) -> None:
        bar = pg.Rect(inv_box.bottomleft, (self.box_len, self.progress_bar_height))
        pg.draw.rect(self.screen, 'black', bar, 1)
        progress_rect = pg.Rect(bar.topleft + pg.Vector2(1, 1), ((bar.width - 2) * (percent / 100), bar.height - 2))
        pg.draw.rect(self.screen, 'green' if inv_box == self.inv.smelt.rect else 'red', progress_rect)

    def update_fuel_status(self) -> None:
        if not self.machine.inv.fuel.item:
            if hasattr(self.machine, 'can_smelt') and self.machine.variant == 'burner' and not self.machine.inv.smelt.item: 
                return
            self.screen.blit(self.empty_fuel_surf, self.empty_fuel_surf.get_rect(center=self.machine.rect.center - self.cam_offset))
            
    def update(self) -> None:
        self.mouse_hover = self.machine.rect.collidepoint(self.mouse.world_xy)
        self.highlight_surf_when_hovered()
        self.update_fuel_status()
        if not self.render:
            self.render = self.mouse_hover and self.mouse.buttons_pressed['left']
        elif self.keyboard.held_keys[self.key_close_ui]:
            self.render = False
        else:
            self.render_interface()