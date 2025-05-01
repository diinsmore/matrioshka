from __future__ import annotations
from typing import TYPE_CHECKING
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
        camera_offset: pg.Vector2
    ):
        self.physics_engine = physics_engine
        self.sprite_manager = sprite_manager
        self.ui = ui
        self.camera_offset = camera_offset

        self.mouse_coords = pg.Vector2()
        self.tile_coords = pg.Vector2()

        self.clicks = {'left': False, 'right': False} 

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
        the key must be lifted before the associated function is called again
        '''
        keys = pg.key.get_just_pressed()

        if keys[pg.K_SPACE]:
            self.physics_engine.jump(player)
        
        if keys[pg.K_RSHIFT]:
            player.inventory.expand = not player.inventory.expand

        if keys[pg.K_c]:
            self.ui.craft_window.open = not self.ui.craft_window.open

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
        move_keys = {'a': False, 'd': False}

        if keys[pg.K_a]:
            move_keys['a'] = True
            if not player.facing_left:
                player.facing_left = True

        if keys[pg.K_d]:
            move_keys['d'] = True
            if player.facing_left:
                player.facing_left = True

        direction_x = move_keys['d'] - move_keys['a']
        self.physics_engine.move_sprite(player, direction_x, dt)

        # holding the left click for mining hurts my fingers after awhile
        if keys[pg.K_x]:
            # locate the tile at the mouse's current coordinates
            self.mouse_coords = self.get_mouse_coords()
            self.tile_coords = (
                self.mouse_coords[0] // TILE_SIZE, 
                self.mouse_coords[1] // TILE_SIZE
            )
            self.sprite_manager.mining.start(player, self.tile_coords, update_collision_map)

    def mouse_input(self, player: Player, update_collision_map: callable) -> None:
        if pg.mouse.get_rel(): # only update after the mouse has moved
            self.mouse_coords = self.get_mouse_coords()

        click = pg.mouse.get_pressed()
        if click[0]: 
            self.clicks['left'] = True
            self.tile_coords = (
                self.mouse_coords[0] // TILE_SIZE, 
                self.mouse_coords[1] // TILE_SIZE
            )
            self.activate_mouse_action(player, update_collision_map)
        else:
            if player.state != 'walking':
                player.state = 'idle' 
                player.frame_index = 0
    
    def get_mouse_coords(self, screen_space: bool = False) -> tuple[int, int]:
        screen_coords = pg.mouse.get_pos()
        if screen_space:
            return screen_coords
        # convert to world-space
        return (
            int(screen_coords[0] + self.camera_offset.x),
            int(screen_coords[1] + self.camera_offset.y)
        )

    def activate_mouse_action(self, player: Player, update_collision_map: callable) -> None:
        # ignore the item's material if specified
        item_holding = player.item_holding.split()[1] if ' ' in player.item_holding else player.item_holding
        # once more items are added, this should probably be divided into categories to avoid a colossal switch statement
        match item_holding:
            case 'pickaxe':
                self.sprite_manager.mining.start(player, self.tile_coords, update_collision_map)

    def update(self, player: Player, update_collision_map: callable, dt: float) -> None:
        self.keyboard_input(player, update_collision_map, dt)
        self.mouse_input(player, update_collision_map)