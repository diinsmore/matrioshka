from __future__ import annotations
from typing import Sequence
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from input_manager import Mouse, Keyboard
    from inventory import Inventory
    from sprite_manager import SpriteManager
    from player import Player
    import numpy as np

import pygame as pg
from collections import defaultdict

from settings import TILE_SIZE, RES
from mini_map import MiniMap
from craft_window import CraftWindow
from inventory_ui import InventoryUI
from timer import Timer

class UI:
    def __init__(
        self,
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        assets: dict[str, dict[str, any]],
        mouse: Mouse,
        keyboard: Keyboard,
        inventory: Inventory,
        sprite_manager: SpriteManager,
        player: Player,
        tile_map: np.ndarray,
        tile_IDs: dict[str, int],
        tile_IDs_to_names: dict[int, str],
        saved_data: dict[str, any] | None
    ):
        self.screen = screen
        self.cam_offset = cam_offset
        self.assets = assets
        self.mouse = mouse
        self.keyboard = keyboard
        self.inventory = inventory
        self.sprite_manager = sprite_manager
        self.player = player
        self.tile_map = tile_map
        self.tile_IDs = tile_IDs
        self.tile_IDs_to_names = tile_IDs_to_names
        self.saved_data = saved_data

        self.mini_map = MiniMap(
            self.screen, 
            self.cam_offset, 
            self.tile_map,
            self.tile_IDs,
            self.tile_IDs_to_names, 
            self.gen_outline,
            self.sprite_manager.mining.get_tile_material,
            self.saved_data
        )
        
        self.mouse_grid = MouseGrid(self.mouse, self.screen, self.cam_offset, self.get_grid_xy)

        self.inventory_ui = InventoryUI(
            self.screen,
            self.cam_offset,
            self.assets,
            self.mouse,
            self.mini_map.outline_h + self.mini_map.padding,
            self.player,
            self.sprite_manager.item_placement,
            self.sprite_manager.mech_sprites,
            self.gen_outline,
            self.gen_bg,
            self.render_inventory_item_name,
            self.get_scaled_image,
            self.get_grid_xy,
            self.sprite_manager.get_sprites_in_radius,
            self.render_item_amount
        )

        self.craft_window = CraftWindow(
            self.mouse,
            self.screen,
            self.cam_offset,
            self.assets, 
            self.inventory_ui, 
            self.sprite_manager,
            self.player,
            self.get_craft_window_height(),
            self.gen_outline,
            self.gen_bg,
            self.render_inventory_item_name,
            self.get_scaled_image
        )

        self.HUD = HUD(
            self.screen, 
            self.assets, 
            self.craft_window.outline.right, 
            self.gen_outline, 
            self.gen_bg
        )

        for key in (
            'expand inventory ui', 
            'toggle inventory ui', 
            'toggle craft window ui', 
            'toggle mini map ui', 
            'toggle HUD ui'
        ):
            setattr(self, '_'.join(key.split(' ')), self.keyboard.key_bindings[key])

        self.active_item_names = []

    def get_craft_window_height(self) -> int:
        inv_grid_max_height = self.inventory_ui.box_height * (self.inventory.num_slots // self.inventory_ui.num_cols)
        return inv_grid_max_height + self.mini_map.outline_h + self.mini_map.padding

    def gen_outline(
        self,
        rect: pg.Rect,
        color: str | tuple[int, int, int] = None,
        width: int = 1,
        padding: int = 1,
        radius: int = 0,
        draw: bool = True, # if multiple rects are used, this gives more flexibility for their layering
        return_outline: bool = False
    ) -> None | pg.Rect:

        # avoids evaluating 'self' prematurely when set as a default parameter
        if color is None:
            color = self.assets['colors']['outline bg']

        outline = pg.Rect(rect.topleft - pg.Vector2(padding, padding), (rect.width + (padding * 2), rect.height + (padding * 2)))
        if draw:
            pg.draw.rect(self.screen, color, outline, width, radius)

        if return_outline: # use the outline as the base rect for creating another outline
            return outline

    def gen_bg(
        self, 
        rect: pg.Rect, 
        color: str | tuple[int, int, int] = 'black', 
        transparent: bool = False, 
        alpha: int = None
    ) -> None:
        if alpha is None:
            alpha = 200 if transparent else 255
        
        img = pg.Surface(rect.size)
        img.fill(color)
        img.set_alpha(alpha)
        self.screen.blit(img, rect)

    def render_inventory_item_name(self, rect: pg.Rect, name: str) -> None:
        if rect.collidepoint(pg.mouse.get_pos()):
            font = self.assets['fonts']['item label'].render(name, True, self.assets['colors']['text'])
            self.screen.blit(font, font.get_rect(topleft = rect.bottomleft))

    def render_new_item_name(self, item_name: str, item_rect: pg.Rect) -> None:
        '''render the name of the item that was just picked up'''
        color = self.assets['colors']['text']
        item_total = self.inventory.contents[item_name]['amount']
        world_coords = pg.Vector2(item_rect.midtop)
        self.active_item_names.append(
            ItemName(
                name = item_name,
                color = color,
                alpha = 255,
                font = self.assets['fonts']['item label'].render(f'+1 {item_name} ({item_total})', True, color),
                screen = self.screen,
                cam_offset = self.cam_offset,
                world_coords = world_coords,
                timer = Timer(length = 2000)
            )
        )

    def update_item_name_data(self) -> None:
        for index, cls in enumerate(self.active_item_names):
            cls.update(index)
        
        self.active_item_names = [cls for cls in self.active_item_names if cls.timer.running]

    def get_scaled_image(self, image: pg.Surface, item_name: str, width: int, height: int, padding: int = 0) -> pg.Surface:
        '''returns an image scaled to a given size while accounting for its aspect ratio'''
        bounding_box = (width - (padding * 2), height - (padding * 2))
        aspect_ratio = min(image.width / bounding_box[0], image.height / bounding_box[1]) # avoid stretching an image too wide/tall
        scale = (min(bounding_box[0], image.width * aspect_ratio), min(bounding_box[1], image.height * aspect_ratio))
        return pg.transform.scale(self.assets['graphics'][item_name], scale)

    def get_grid_xy(self) -> pg.Vector2:
        return ((pg.Vector2(self.mouse.world_xy) // TILE_SIZE) * TILE_SIZE) - self.cam_offset
    
    def update_render_states(self) -> None:
        pressed_keys = self.keyboard.pressed_keys

        if pressed_keys[self.expand_inventory_ui]:
            self.inventory_ui.expand = not self.inventory_ui.expand
        
        if pressed_keys[self.toggle_inventory_ui]:
            self.inventory_ui.render = not self.inventory_ui.render

        if pressed_keys[self.toggle_craft_window_ui]:
            self.craft_window.opened = not self.craft_window.opened
            self.inventory_ui.expand = self.craft_window.opened
            self.HUD.shift_right = not self.HUD.shift_right

        if pressed_keys[self.toggle_mini_map_ui]:
            self.mini_map.render = not self.mini_map.render

        if pressed_keys[self.toggle_HUD_ui]:
            self.HUD.render = not self.HUD.render

    def render_item_amount(self, amount: int, coords: tuple[int, int], add_x_offset: bool=True) -> None:
        image = self.assets['fonts']['number'].render(str(amount), False, self.assets['colors']['text'])
        x_offset = 0
        if add_x_offset: # making it optional in case the amount will never reach a lengthy value
            num_digits = len(str(amount))
            x_offset = 5 * (num_digits - 2) if num_digits > 2 else 0 # move 3+ digit values to the left by 5px for every remaining digit 
        rect = image.get_rect(center = (coords[0] + x_offset, coords[1] - 2))
        self.gen_bg(rect, transparent=True)
        self.screen.blit(image, rect)

    def update(self) -> None:
        self.mouse_grid.update()
        self.HUD.update()
        self.mini_map.update()
        self.craft_window.update() # keep above the inventory ui otherwise item names may be rendered behind the window
        self.inventory_ui.update()
        self.update_item_name_data()
        self.update_render_states()
        

class MouseGrid:
    '''a grid around the mouse position to guide block placement'''
    def __init__(self, mouse: Mouse, screen: pg.Surface, cam_offset: pg.Vector2, get_grid_xy: callable):
        self.mouse = mouse
        self.screen = screen
        self.cam_offset = cam_offset
        self.get_grid_xy = get_grid_xy

        self.tile_w = self.tile_h = 3

    def render_grid(self) -> None:
        if self.mouse.moving or self.mouse.click_states['left']:
            topleft = self.get_grid_xy()
            for x in range(self.tile_w):
                for y in range(self.tile_h):
                    cell_surf = pg.Surface((TILE_SIZE, TILE_SIZE), pg.SRCALPHA)
                    cell_surf.fill((0, 0, 0, 0))
                    pg.draw.rect(cell_surf, (255, 255, 255, 10), (0, 0, TILE_SIZE, TILE_SIZE), 1) # (0, 0) is relative to the topleft of cell_surf 
                    self.screen.blit(cell_surf, cell_surf.get_rect(topleft=topleft + pg.Vector2(x * TILE_SIZE, y * TILE_SIZE)))

    def update(self) -> None:
        self.render_grid()


class HUD:
    def __init__(
        self, 
        screen: pg.Surface, 
        assets: dict[str, dict[str, any]], 
        craft_window_right: int,
        gen_outline: callable,
        gen_bg: callable,
    ):
        self.screen = screen
        self.assets = assets
        self.craft_window_right = craft_window_right
        self.gen_outline = gen_outline
        self.gen_bg = gen_bg

        self.colors = self.assets['colors']
        self.fonts = self.assets['fonts']

        self.height = TILE_SIZE * 3
        self.width = RES[0] // 2
        self.shift_right = False
        self.render = True

    def render_bg(self) -> None:
        self.image = pg.Surface((self.width, self.height))
        self.rect = self.image.get_rect(topleft = (self.get_left_point(), 0))
        self.gen_bg(self.rect, transparent=True)
        
        outline1 = self.gen_outline(self.rect, draw = False, return_outline = True)
        outline2 = self.gen_outline(outline1, draw = True)
        pg.draw.rect(self.screen, 'black', outline1, 1)

    def get_left_point(self) -> int:
        default = (RES[0] // 2) - (self.width // 2)
        if not self.shift_right:
            return default
        else:
            # center between the craft window's right border and the screen's right border
            padding = (RES[0] - self.craft_window_right) - self.width
            return self.craft_window_right + (padding // 2)
        
    def update(self) -> None:
        if self.render:
            self.render_bg()


class ItemName:
    def __init__(
        self, 
        name: str, 
        color: str, 
        alpha: int,
        font: pg.Font, 
        screen: pg.Surface,
        cam_offset: pg.Vector2,
        world_coords: tuple[int, int],
        timer: Timer
    ):
        self.name = name
        self.color = color
        self.alpha = alpha
        self.font = font
        self.screen = screen
        self.cam_offset = cam_offset
        self.world_coords = world_coords
        self.timer = timer

    def update(self, index: int) -> None:
        if not self.timer.running:
            self.timer.start()
            return
            
        self.timer.update()    
        
        self.alpha = max(0, self.alpha - 2)
        self.font.set_alpha(self.alpha)
        screen_coords = self.world_coords - self.cam_offset
        self.screen.blit(self.font, self.font.get_rect(midbottom = screen_coords))
        self.world_coords[1] -= index + 1 # move north across the screen


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
        
        self.smelt_input = save_data['smelt input'] if save_data else defaultdict(lambda: {'amount': 0})
        self.fuel_input = save_data['fuel input'] if save_data else defaultdict(lambda: {'amount': 0})
        self.output = save_data['output'] if save_data else defaultdict(lambda: {'amount': 0})

        self.key_close_ui = self.keyboard.key_bindings['close ui window']
        
        self.variant = self.fuel_sources = None # initialized with the subclass
    
    def check_input(self) -> str|None:
        input_type = None
        item = self.player.item_holding
        if self.smelt_input_box.collidepoint(self.mouse.screen_xy) and item in self.items_smelted:
            input_type = 'smelt'

        elif self.variant == 'burner' and self.fuel_input_box.collidepoint(self.mouse.screen_xy) and item in self.fuel_sources:
            input_type = 'fuel'
        return input_type

    def input_item(self, item:str, input_type:str, amount:int=1) -> None: 
        self.player.inventory.contents[item]['amount'] -= amount
        if input_type == 'smelt':
            self.smelt_input[item]['amount'] += amount
        else:
            self.fuel_input[item]['amount'] += amount

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
        if self.smelt_input:
            item_name = next(iter(self.smelt_input))
            surf = self.graphics[item_name]
            self.screen.blit(surf, surf.get_frect(center=self.smelt_input_box.center))
            self.render_item_amount(self.smelt_input[item_name]['amount'], self.smelt_input_box.bottomright)

        elif self.fuel_input:
            item_name = next(iter(self.fuel_input))
            surf = self.graphics[item_name]
            self.screen.blit(surf, surf.get_frect(center=self.fuel_input_box.center))
            self.render_item_amount(self.fuel_input[item_name]['amount'], self.fuel_input_box.bottomright - pg.Vector2(5, 5))

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