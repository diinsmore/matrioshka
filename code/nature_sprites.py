import pygame as pg
from random import randint, choice
from math import sin

from settings import RES
from sprite_base import SpriteBase

class Cloud(SpriteBase):
    def __init__(
        self, 
        coords: pg.Vector2, 
        image: dict[str, pg.Surface], 
        z: dict[str, int],
        speed: int,
        player_x: int,
        sprite_groups: list[pg.sprite.Group], 
    ):
        super().__init__(coords, image, z, *sprite_groups)
        self.speed = speed
        self.player_x = player_x

    def spawn(self, image: dict[str, dict[str, pg.Surface]], dt: float) -> None:
        if not self.cloud_sprites: 
            for cloud in range(random.randint(5, 10)):
                x = player_x + RES[0] / 2 + image.get_width() + random.randint(0, 1500) # start outside the screen boundary
                y = random.randint(100, 300) 
                Cloud(
                    coords = (x, -y), 
                    image = random.choice(image), 
                    z = Z_LAYERS['clouds'], 
                    speed = random.randint(15, 25),
                    player_x = self.player_x,
                    sprite_groups = self.sprite_groups,
                )

    def move(self, dt: float) -> None:  
        self.rect.x -= self.speed * dt
        # remove clouds that surpassed the left edge of the screen
        if self.rect.right < self.player_x - RES[0] - self.img.get_width() or self.rect.left <= 0:
            self.kill()
        
    def update(self, image: dict[str, dict[str, pg.Surface]], player_x: int, dt: float) -> None:
        self.spawn(image, player_x, dt)
        self.move(dt)
            

class Tree(SpriteBase):
    def __init__(
        self, 
        coords: pg.Vector2, 
        image: pg.Surface,
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group]
    ):
        super().__init__(coords, image, z, *sprite_groups)
        self.rect = self.image.get_rect(midbottom = coords) # SpriteBase uses the topleft
        self.strength = 50 # chopped down when <= 0