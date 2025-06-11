import pygame as pg
from random import randint, choice
from math import sin

from settings import RES, TOOLS
from sprite_base import SpriteBase
from timer import Timer

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
        sprite_groups: list[pg.sprite.Group],
        tree_map: list[tuple[int, int]],
        tree_map_coords: tuple[int, int], # the coords value before it was adjusted by the camera offset & tile size
        camera_offset: pg.Vector2,
    ):
        super().__init__(coords, image, z, sprite_groups)
        self.coords = coords
        self.tree_map = tree_map
        self.tree_map_coords = tree_map_coords
        self.camera_offset = camera_offset
        
        self.image = self.image.copy()
        self.rect = self.image.get_rect(midbottom = coords) # SpriteBase uses the topleft
        self.max_strength, self.current_strength = 50, 50
        self.alpha = 255

        self.delay_timer = Timer(length = 1000) # prevents cut_down() from being called every frame

    def cut_down(self, sprite: pg.sprite.Sprite) -> None:
        self.delay_timer.update()
    
        if not self.delay_timer.running:
            axe_material = sprite.item_holding.split()[0]
            tool_strength = TOOLS['axe'][axe_material]['strength']
            self.current_strength = max(0, self.current_strength - tool_strength)
            
            rel_strength = self.max_strength // tool_strength
            rel_alpha = self.alpha * (1 / rel_strength)
            self.alpha = max(0, self.alpha - rel_alpha)
            self.image.set_alpha(self.alpha)

            if self.current_strength == 0 and self.tree_map_coords in self.tree_map:
                self.tree_map.remove(self.tree_map_coords)  
                self.kill()

            self.delay_timer.start()

    def produce_wood(self, sprite: pg.sprite.Sprite) -> None:
        pass