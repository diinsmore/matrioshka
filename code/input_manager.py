import pygame as pg

from settings import TILE_SIZE

class InputManager:
    def __init__(self):
        self.mouse = Mouse()
        self.keyboard = Keyboard()

    def update(self, cam_offset: pg.Vector2) -> None:
        self.mouse.update(cam_offset)
        self.keyboard.update()
        

class Keyboard:
    def __init__(self):
        self.held_keys = self.pressed_keys = None
        self.num_keys = {pg.K_0 + num for num in range(10)}
        self.key_map = {key: (key - pg.K_0 - 1) % 10 for key in self.num_keys} # maps the ascii value to the number pressed
        self.key_bindings = {
            'move left': pg.K_a,
            'move right': pg.K_d,
            'jump': pg.K_SPACE,
            'mine': pg.K_s,
            'expand inventory ui': pg.K_i,
            'toggle inventory ui': pg.K_j,
            'toggle craft window ui': pg.K_c,
            'toggle mini map ui': pg.K_m,
            'toggle HUD ui': pg.K_h,
            'close ui window': pg.K_q,       
        }

    def update(self) -> None:
        self.held_keys = pg.key.get_pressed()
        self.pressed_keys = pg.key.get_just_pressed()


class Mouse:
    def __init__(self):
        self.buttons_pressed, self.buttons_held = {'left': False, 'right': False}, {'left': False, 'right': False}
        self.moving = False
        self.screen_xy = self.world_xy = self.tile_xy = None
        
    def get_movement(self, cam_offset: pg.Vector2) -> None:
        self.moving = False
        if pg.mouse.get_rel():
            self.moving = True
            self.screen_xy = pg.mouse.get_pos()
            self.world_xy = (int(self.screen_xy[0] + cam_offset.x), int(self.screen_xy[1] + cam_offset.y))
            self.tile_xy = (self.world_xy[0] // TILE_SIZE, self.world_xy[1] // TILE_SIZE)
    
    def update_click_states(self) -> None:
        self.reset_click_states()

        clicked = pg.mouse.get_just_pressed()
        if clicked[0]:
            self.buttons_pressed['left'] = True
        elif clicked[2]:
            self.buttons_pressed['right'] = True

        held = pg.mouse.get_pressed()
        if held[0]:
            self.buttons_held['left'] = True
        elif held[1]:
            self.buttons_held['right'] = True

    def reset_click_states(self) -> None:
        self.buttons_held['left'] = self.buttons_held['right'] = self.buttons_pressed['left'] = self.buttons_pressed['right'] = False

    def update(self, cam_offset: pg.Vector2) -> None:
        self.get_movement(cam_offset)
        self.update_click_states()