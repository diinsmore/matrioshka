import pygame as pg

class SpriteBase(pg.sprite.Sprite):
    def __init__(
        self, 
        coords: pg.Vector2,
        image: pg.Surface,
        z: dict[str, int],  
        sprite_groups: list[pg.sprite.Group]
    ):
        super().__init__(sprite_groups)
        self.image = image
        self.rect = self.image.get_rect(topleft = coords)
        self.z = z # layer to render on
        self.sprite_groups = sprite_groups