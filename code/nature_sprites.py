from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from physics_engine import PhysicsEngine
    from player import Player

import pygame as pg
from random import randint, choice
from math import sin, ceil

from settings import RES, TOOLS, Z_LAYERS, GRAVITY
from sprite_base import SpriteBase
from timer import Timer
from ui import UI

class Cloud(SpriteBase):
    def __init__(
        self, 
        coords: pg.Vector2, 
        image: dict[str, pg.Surface], 
        z: dict[str, int],
        sprite_groups: list[pg.sprite.Group],
        speed: int,
        player: Player,
        rect_in_sprite_radius: callable
    ):
        super().__init__(coords, image, z, sprite_groups)
        self.speed = speed
        self.player = player
        self.rect_in_sprite_radius = rect_in_sprite_radius

    def move(self, dt: float) -> None:  
        self.rect.x -= self.speed * dt
        if self.rect.right <= 0:
            self.kill()
        
    def update(self, dt: float) -> None:
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
        # passing to the Wood class:
        wood_image: pg.Surface,
        wood_sprites: list[pg.sprite.Group],
        sprite_movement: callable
    ):
        super().__init__(coords, image, z, sprite_groups)
        self.image = self.image.copy()
        self.rect = self.image.get_rect(midbottom = self.coords) # SpriteBase uses the topleft
        self.tree_map = tree_map
        self.tree_map_coords = tree_map_coords
        
        self.wood_image = wood_image
        self.wood_sprites = wood_sprites
        self.sprite_movement = sprite_movement

        self.max_strength, self.current_strength = 50, 50
        self.alpha = 255

        self.total_wood = ceil(self.image.height / 25)

        self.delay_timer = Timer(length = 500) # prevents cut_down() from being called every frame

    def cut_down(self, sprite: pg.sprite.Sprite, get_tool_strength: callable, pick_up_item: callable) -> None:
        self.delay_timer.update()
    
        if not self.delay_timer.running:
            sprite.state = 'chopping'
            axe_material = sprite.item_holding.split()[0]
            tool_strength = get_tool_strength(sprite)
            self.current_strength = max(0, self.current_strength - tool_strength)
            
            rel_strength = self.max_strength // tool_strength
            rel_alpha = self.alpha * (1 / rel_strength)
            self.alpha = max(0, self.alpha - rel_alpha)
            self.image.set_alpha(self.alpha)

            if self.current_strength == 0 and self.tree_map_coords in self.tree_map:
                self.tree_map.remove(self.tree_map_coords)  
                self.kill()
                sprite.state = 'idle'
                self.produce_wood(sprite, pick_up_item)
                return

            self.delay_timer.start()
    
    def produce_wood(self, sprite: pg.sprite.Sprite, pick_up_item: callable) -> None:
        for i in range(self.total_wood):
            left = choice((self.rect.left - randint(5, 50), self.rect.right + randint(5, 50)))
            wood = Wood(
                coords = pg.Vector2(left, self.rect.top + (self.wood_image.height * i)),
                image = self.wood_image,
                z = Z_LAYERS['main'],
                sprite_groups = self.wood_sprites,
                direction = pg.Vector2(-1 if left < self.rect.left else 1, 1),
                speed = randint(15, 30),
                sprite_movement = self.sprite_movement,
                pick_up_item = pick_up_item
            )


class Wood(SpriteBase):
    def __init__(
        self, 
        coords: pg.Vector2,
        image: pg.Surface,
        z: dict[str, int], 
        sprite_groups: list[pg.sprite.Group],
        direction: pg.Vector2,
        speed: int,
        sprite_movement: callable,
        pick_up_item: callable
    ):
        super().__init__(coords, image, z, sprite_groups)
        self.direction = direction
        self.speed = speed
        self.sprite_movement = sprite_movement
        self.pick_up_item = pick_up_item

        self.gravity = GRAVITY

    def update(self, dt: float) -> None:
        self.sprite_movement.move_sprite(self, self.direction.x, dt)
        if self.direction.x and int(self.direction.y) == 0:
            self.direction.x = 0
        
        self.pick_up_item(self, 'wood', self.rect)