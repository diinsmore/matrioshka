from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import numpy as np
    import pygame as pg

from settings import TILE_SIZE

class WoodGathering:
    def __init__(
        self, 
        tile_map: np.ndarray, 
        names_to_ids: dict[str, int], 
        tree_sprites: pg.sprite.Group, 
        tree_map: list[tuple[int, int]], 
        cam_offset: pg.Vector2,
        get_tool_strength: callable, 
        pick_up_item: callable, 
        rect_in_sprite_radius: callable
    ):
        self.tile_map = tile_map
        self.names_to_ids = names_to_ids
        self.tree_sprites = tree_sprites
        self.tree_map = tree_map
        self.cam_offset = cam_offset
        self.get_tool_strength = get_tool_strength
        self.pick_up_item = pick_up_item
        self.rect_in_sprite_radius = rect_in_sprite_radius

        self.reach_radius = TILE_SIZE * 3

    def make_cut(self, sprite: pg.sprite.Sprite, mouse_button_held: dict[str, bool], mouse_world_xy: tuple[int, int]) -> None:
        if mouse_button_held['left']:
            if sprite.item_holding and sprite.item_holding.split()[-1] == 'axe':
                if tree := next((t for t in self.tree_sprites if self.rect_in_sprite_radius(sprite, t.rect) and t.rect.collidepoint(mouse_world_xy)), None):
                    tree.cut_down(sprite, self.get_tool_strength, self.pick_up_item)

    def update(self, player: pg.sprite.Sprite, mouse_button_held: dict[str, bool], mouse_world_xy: tuple[int, int]) -> None:
        self.make_cut(player, mouse_button_held, mouse_world_xy)