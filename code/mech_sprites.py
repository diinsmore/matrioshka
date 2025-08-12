from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from player import Player

import pygame as pg

from settings import TILE_SIZE, MACHINES
from sprite_base import SpriteBase

class Furnace(SpriteBase):
    def __init__(
        self, 
        coords: pg.Vector2, 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group],
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        mouse: Mouse,
        keyboard: Keyboard,
        player: Player,
        assets: dict[str, dict[str, any]],
        gen_outline: callable,
        gen_bg: callable
    ):
        super().__init__(coords, image, z, sprite_groups)
        self.rect = image.get_rect(topleft = self.coords)
        self.screen = screen
        self.cam_offset = cam_offset
        self.mouse = mouse
        self.keyboard = keyboard
        self.player = player
        self.assets = assets
        self.gen_outline = gen_outline
        self.gen_bg = gen_bg
        
        self.active = False
        self.max_capacity = {'smelting': 100, 'fuel': 50}
        self.items_smelted = {
            'copper': {'speed': 4000, 'output': 'copper plate'}, 
            'iron': {'speed': 5000, 'output': 'iron plate'},
            'iron plate': {'speed': 7000, 'output': 'steel plate'},
        }
        self.current_smelt_input = {}
        self.current_fuel_input = {}
        
        self.ui = FurnaceUI(
            self.screen, 
            self.cam_offset,
            self.image, 
            self.rect,
            self.items_smelted,
            self.mouse, 
            self.keyboard,
            self.player,
            self.assets,
            self.gen_outline, 
            self.gen_bg
        )
    
    def smelt(self) -> None:
        pass

    def update(self, dt) -> None:
        self.ui.update()


class FurnaceUI:
    def __init__(
        self, 
        screen: pg.Surface, 
        cam_offset: pg.Vector2,
        furnace_surf: pg.Surface,
        furnace_rect: pg.Rect,
        items_smelted: dict[str, dict[str, int | str]],
        mouse: Mouse, 
        keyboard: Keyboard,
        player: Player,
        assets: dict[str, dict[str, any]],
        gen_outline: callable, 
        gen_bg: callable
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

        self.render = False
        self.outline_w, self.outline_h = 150, 150
        self.padding = 10
        self.item_box_w, self.item_box_h = 50, 50
        
        self.arrow_surf = self.assets['graphics']['ui']['arrow']
        self.furnace_mask = pg.mask.from_surface(self.furnace_surf)
        self.furnace_highlight_surf = self.furnace_mask.to_surface(setcolor=(20, 20, 20, 255), unsetcolor=(0, 0, 0, 0))
        self.smelt_surf, self.fuel_surf, self.output_surf = None, None, None

        self.key_close_ui = self.keyboard.key_bindings['close ui window']
        self.variant = None # initialized with the subclass
    
    def input_item(self, smelt_input_box: pg.Rect, fuel_input_box: pg.Rect = None, amount: int = 1) -> None:
        if smelt_input_box.collidepoint(self.mouse.world_xy) and self.player.item_holding in self.items_smelted:
            self.player.inventory.contents[self.player.item_holding]['amount'] -= min(
                amount, self.player.inventory.contents[self.player.item_holding]['amount']
            )
            self.smelt_surf = self.assets['graphics'][item]
            self.screen.blit(self.smelt_surf, self.smelt_surf.get_rect(center=smelt_input_box.center))

        if self.variant == 'burner' and fuel_input_box.collidepoint(self.mouse.world_xy) and self.player.item_holding in self.fuel_sources:
            self.player.inventory.contents[self.player.item_holding]['amount'] -= min(
                amount, self.player.inventory.contents[self.player.item_holding]['amount']
            )
            self.fuel_surf = self.assets['graphics'][self.player.item_holding]
            self.screen.blit(self.fuel_surf, self.fuel_surf.get_rect(center=fuel_input_box.center))

    def highlight_surf_when_hovered(self, rect_mouse_collide: bool) -> None:
        if rect_mouse_collide:
            self.screen.blit(self.furnace_highlight_surf, self.furnace_rect.topleft - self.cam_offset, special_flags=pg.BLEND_RGBA_ADD)

    def render_interface(self) -> None:
        bg_rect = pg.Rect(self.furnace_rect.topright - pg.Vector2(0, self.outline_w) - self.cam_offset, (self.outline_w, self.outline_h))
        
        offset = 0 if self.variant == 'burner' else (self.outline_h // 2) - (self.item_box_h // 2) - self.padding
        smelt_input_box = pg.Rect(bg_rect.topleft + pg.Vector2(self.padding, self.padding + offset), (self.item_box_w, self.item_box_h))

        fuel_input_box = None
        if self.variant == 'burner':
            fuel_input_box = smelt_input_box.copy()
            fuel_input_box.topleft += pg.Vector2(0, bg_rect.bottom - smelt_input_box.bottom - self.padding)

        output_box = smelt_input_box.copy()
        output_box.topleft += pg.Vector2(
            bg_rect.right - (smelt_input_box.right + self.padding), 
            0 if self.variant == 'electric' else (self.outline_h // 2) - (self.item_box_h // 2)  - self.padding
        )

        boxes = [bg_rect, smelt_input_box, output_box, fuel_input_box]
        for box in boxes if fuel_input_box else boxes[:-1]:
            color = 'black'
            transparent = False
            if box == bg_rect:
                transparent = True
            else:
                if box.collidepoint(self.mouse.screen_xy):
                    color = self.assets['colors']['ui bg highlight']
                    
            self.gen_bg(box, color, transparent)
            self.gen_outline(box)

        self.screen.blit(
            self.arrow_surf, 
            self.arrow_surf.get_rect(center=bg_rect.center)
        )

        self.input_item(smelt_input_box, fuel_input_box)

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


class BurnerFurnace(Furnace):
    def __init__(
        self,
        coords: pg.Vector2, 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group],
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        mouse: Mouse,
        keyboard: Keyboard,
        player: Player,
        assets: dict[str, dict[str, any]],
        gen_outline: callable,
        gen_bg: callable
    ):
        super().__init__(coords, image, z, sprite_groups, screen, cam_offset, mouse, keyboard, player, assets, gen_outline, gen_bg)
        self.variant = 'burner'
        self.ui.variant = self.variant
        self.recipe = MACHINES['burner furnace']['recipe']
        self.fuel_sources = {'wood': {'capacity': 99}, 'coal': {'capacity': 99}}


class ElectricFurnace(Furnace):
    def __init__(
        self,
        coords: pg.Vector2, 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group],
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        mouse: Mouse,
        keyboard: Keyboard,
        assets: dict[str, dict[str, any]],
        gen_outline: callable,
        gen_bg: callable
    ):
        super().__init__(coords, image, z, sprite_groups, screen, cam_offset, mouse, keyboard, player, assets, gen_outline, gen_bg)
        self.variant = 'electric'
        self.ui.variant = self.variant
        self.recipe = MACHINES['electric furnace']['recipe']
        self.fuel_sources = {'electric poles'}


class Drill(SpriteBase):
    def __init__(
        self, 
        coords: pg.Vector2, 
        image: dict[str, dict[str, pg.Surface]],
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group],
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        mouse: Mouse,
        keyboard: Keyboard,
        player: Player,
        assets: dict[str, dict[str, any]],
        gen_outline: callable,
        gen_bg: callable
    ):
        super().__init__(coords, image, z, sprite_groups, cam_offset)
        self.screen = screen
        self.cam_offset = cam_offset
        self.mouse = mouse
        self.keyboard = keyboard
        self.player = player
        self.assets = assets
        self.gen_outline = gen_outline
        self.gen_bg = gen_bg

        self.target_ore = None
        self.reach_radius = ((image.width // TILE_SIZE) + 2, RES[1] // 5)


mech_sprite_dict = { # matches the sprite.item_holding variable to the class to be instantiated when the item is placed
    'burner furnace': BurnerFurnace, 
    'electric furnace': ElectricFurnace, 
    'drill': Drill
}