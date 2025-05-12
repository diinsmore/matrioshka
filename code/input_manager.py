from __future__ import annotations
from typing import TYPE_CHECKING, Literal
if TYPE_CHECKING:
    from physics_engine import PhysicsEngine
    from sprite_manager import SpriteManager
    from ui import UI
    from player import Player

import pygame as pg
from settings import TILE_SIZE

class InputManager:
    def __init__(
        self, 
        physics_engine: PhysicsEngine, 
        sprite_manager: SpriteManager, 
        ui: UI,
    ):
        self.physics_engine = physics_engine
        self.sprite_manager = sprite_manager
        self.ui = ui
        
        self.mouse = Mouse(self.physics_engine, self.sprite_manager, self.ui)
        self.keyboard = Keyboard(self.physics_engine, self.sprite_manager, self.ui, self.mouse.tile_coords)

    def update(self, player: Player, camera_offset: pg.Vector2, update_collision_map: callable, dt: float) -> None:
        self.mouse.update(camera_offset)
        self.keyboard.update(player, update_collision_map, self.mouse.tile_coords, dt)
        

class Keyboard:
    def __init__(
        self,
        physics_engine: PhysicsEngine, 
        sprite_manager: SpriteManager, 
        ui: UI,
        tile_coords: tuple[int, int]
    ):
        self.physics_engine = physics_engine
        self.sprite_manager = sprite_manager
        self.ui = ui
        self.tile_coords = tile_coords # mining depends on the mouse location but is triggered by the 's' key

        self.num_keys = {pg.K_0 + num for num in range(10)}
        # map the key's ascii value to the key number pressed 
        # subtracting 1 so the 1 key corresponds to index 0 and the 0 key to index 9
        self.key_map = {key: (key - pg.K_0 - 1) % 10 for key in self.num_keys}

    def get_input(self, player: Player, update_collision_map: callable, dt: float) -> None:
        self.get_key_pressed(player)
        self.get_key_held(player, update_collision_map, dt)

    def get_key_pressed(self, player: Player) -> None:
        '''
        tracks keys being pressed
        the key must be lifted before the associated function is called again
        '''
        keys = pg.key.get_just_pressed()

        if keys[pg.K_SPACE]:
            self.physics_engine.jump(player)

        for key in self.num_keys:
            if keys[key]:
                self.update_inv_index(player, key)

        self.update_render_state(keys)
          
    def get_key_held(self, player: Player, update_collision_map: callable, dt: float) -> None:
        '''
        tracks keys being held down
        associated functions will be called continuously until the key is lifted
        '''
        keys = pg.key.get_pressed()

        direction_x = self.get_direction_x(keys)
        self.physics_engine.move_sprite(player, direction_x, dt)

        if keys[pg.K_s]:
            self.sprite_manager.mining.start(player, self.tile_coords, update_collision_map)
        else:
            if player.state == 'mining':
                self.sprite_manager.end_action(player)
    
    def update_inv_index(self, player: Player, key: pg.key) -> None:
        '''select an inventory item by index number (only applies to keys <= 10)'''
        player.inv.index = self.key_map[key]

    def update_render_state(self, keys: list[bool]) -> None:
        '''switch between rendering/not rendering a given ui component'''
        if keys[pg.K_c]:
            self.ui.craft_window.open = not self.ui.craft_window.open
            self.ui.inv_ui.expand = self.ui.craft_window.open
            self.ui.HUD.shift_right = not self.ui.HUD.shift_right

        if keys[pg.K_LSHIFT]:
            self.ui.inv_ui.expand = not self.ui.inv_ui.expand

        if keys[pg.K_m]:
            self.ui.mini_map.render = not self.ui.mini_map.render

        if keys[pg.K_i]:
            self.ui.inv_ui.render = not self.ui.inv_ui.render

        if keys[pg.K_h]:
            self.ui.HUD.render = not self.ui.HUD.render

    @staticmethod
    def get_direction_x(keys: list[bool]) -> int:
        direction = {'left': False, 'right': False}
        if keys[pg.K_a]: 
            direction['left'] = True

        if keys[pg.K_d]: 
            direction['right'] = True

        return direction['right'] - direction['left']

    def update(
        self, 
        player: Player, 
        update_collision_map: callable, 
        updated_tile_coords: tuple[int, int], 
        dt: float
    ) -> None:

        self.get_input(player, update_collision_map, dt)
        self.tile_coords = updated_tile_coords # updated in the mouse class


class Mouse:
    def __init__(
        self,
        physics_engine: PhysicsEngine, 
        sprite_manager: SpriteManager, 
        ui: UI
    ):
        self.physics_engine = physics_engine
        self.sprite_manager = sprite_manager
        self.ui = ui
        
        self.clicks = {'left': False, 'right': False} 
        self.moving = False
        self.coords = pg.Vector2()
        self.tile_coords = pg.Vector2()
        
    def get_input(self, camera_offset: pg.Vector2) -> None:
        self.get_mouse_movement(camera_offset)
        self.get_mouse_click()
    
    def get_mouse_movement(self, camera_offset: pg.Vector2) -> None:
        self.moving = False
        if pg.mouse.get_rel():
            self.moving = True
            self.coords = self.get_mouse_coords(camera_offset)
            self.tile_coords = (self.coords[0] // TILE_SIZE, self.coords[1] // TILE_SIZE)

    def get_mouse_click(self) -> None:
        click = pg.mouse.get_pressed()
        if click[0]:
            self.clicks['left'] = True
        
        if click[2]:
            self.clicks['right'] = True

    @staticmethod
    def get_mouse_coords(camera_offset: pg.Vector2, rel_screen: bool = False) -> tuple[int, int]:
        screen_space = pg.mouse.get_pos()
        if rel_screen:
            return screen_space
        
        # convert from screen-space to world-space
        return (int(screen_space[0] + camera_offset.x), int(screen_space[1] + camera_offset.y))

    def update(self, camera_offset: pg.Vector2) -> None:
        self.get_input(camera_offset)