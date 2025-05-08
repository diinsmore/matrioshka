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

        self.mouse_coords = pg.Vector2()
        self.tile_coords = pg.Vector2()

        self.clicks = {'left': False, 'right': False} 
        self.mouse_moving = False

        self.num_keys = [pg.K_0 + num for num in range(10)]
        # map the key's ascii value to the key number pressed 
        # subtracting 1 so the 1 key corresponds to index 0 and the 0 key to index 9
        self.key_map = {key: (key - pg.K_0 - 1) % 10 for key in self.num_keys}
   
    def keyboard_input(self, player: Player, update_collision_map: callable, dt: float) -> None:
        self.get_key_pressed(player)
        self.get_key_held(player, update_collision_map, dt)

    def get_key_pressed(self, player: Player) -> None:
        '''
        tracks keys being pressed
        the key must be lifted before the associated function called again
        '''
        keys = pg.key.get_just_pressed()

        if keys[pg.K_SPACE]:
            self.physics_engine.jump(player)
        
        if keys[pg.K_RSHIFT] and not self.ui.craft_window.open:
            self.ui.inv_ui.expand = not self.ui.inv_ui.expand

        if keys[pg.K_c]:
            self.ui.craft_window.open = not self.ui.craft_window.open
            self.ui.inv_ui.expand = self.ui.craft_window.open # open/close the inventory along with the craft window

        if keys[pg.K_m]:
            self.ui.mini_map.render = not self.ui.mini_map.render

        # select an inventory item by index number 
        # only applies to the top row (first 10)
        # TODO: add arrow key navigation
        for key in self.num_keys:
            if keys[key]:
                player.inventory.index = self.key_map[key]
                break
                
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
                
    def get_direction_x(self, keys: list[bool]) -> int:
        direction = {'left': False, 'right': False}
        if keys[pg.K_a]: 
            direction['left'] = True

        if keys[pg.K_d]: 
            direction['right'] = True

        return direction['right'] - direction['left']

    def mouse_input(self, player: Player, camera_offset: pg.Vector2, update_collision_map: callable) -> None:
        self.mouse_moving = False
        if pg.mouse.get_rel():
            self.mouse_moving = True
            self.mouse_coords = self.get_mouse_coords(camera_offset)
            
            self.tile_coords = (
                self.mouse_coords[0] // TILE_SIZE, 
                self.mouse_coords[1] // TILE_SIZE
            )
        
        click = pg.mouse.get_pressed()
        if click[0]: 
            self.clicks['left'] = True
        
    @staticmethod
    def get_mouse_coords(camera_offset: pg.Vector2, rel_screen: bool = False) -> tuple[int, int]:
        screen_space = pg.mouse.get_pos()
        if rel_screen:
            return screen_space
    
        world_space = (
            int(screen_space[0] + camera_offset.x),
            int(screen_space[1] + camera_offset.y)
        )
        return world_space

    def update(self, player: Player, camera_offset: pg.Vector2, update_collision_map: callable, dt: float) -> None:
        self.keyboard_input(player, update_collision_map, dt)
        self.mouse_input(player, camera_offset, update_collision_map)