import pygame as pg

from settings import TILE_SIZE

class MiniMap:
    def __init__(
        self, 
        screen: pg.Surface, 
        assets: dict[str, dict[str, any]], 
        get_outline: callable
    ):
        self.screen = screen
        self.assets = assets
        self.get_outline = get_outline

        self.colors = self.assets['colors']
        self.fonts = self.assets['fonts']

        self.width, self.height = TILE_SIZE * 10, TILE_SIZE * 10
        self.padding = 5
        self.render = True

    def render_outline(self) -> None:
        if self.render:
            base_rect = pg.Rect(self.padding, self.padding, self.width, self.height)
            outline1 = self.get_outline(base_rect, draw = False, return_outline = True)
            outline2 = self.get_outline(outline1, draw = True)
            pg.draw.rect(self.screen, 'black', outline1, 1)

    def update(self) -> None:
        self.render_outline()