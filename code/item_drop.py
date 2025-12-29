import pygame as pg

from sprite_base_classes import Sprite

class ItemDrop(Sprite):
    def __init__(
        self, 
        xy: pg.Vector2,
        cam_offset: pg.Vector2,
        image: pg.Surface, 
        screen: pg.Surface,
        z: int,
        sprite_groups: list[pg.sprite.Group], 
        name: str,
        direction: pg.Vector2, 
        speed: int, 
        sprite_movement: callable,
        pick_up_item: callable
    ):
        super().__init__(xy, cam_offset, image, screen, z, sprite_groups)
        self.name = name
        self.direction = direction
        self.speed = speed
        self.sprite_movement = sprite_movement
        self.pick_up_item = pick_up_item

        self.gravity = GRAVITY

    def update(self, dt: float) -> None:
        self.sprite_movement.move_sprite(self, self.direction.x, dt)
        if self.direction.x and int(self.direction.y) == 0:
            self.direction.x = 0
        
        self.pick_up_item(self, self.name, self.rect)

    def get_save_data(self) -> dict[str, list]:
        return {'xy': list(self.rect.topleft)}