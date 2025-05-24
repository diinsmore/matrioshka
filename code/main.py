import pygame as pg
import sys

from settings import RES, FPS
from engine import Engine

class Main:
    def __init__(self):
        pg.init()
        pg.display.set_caption('matrioshka')
        self.running = True
        self.screen = pg.display.set_mode(RES)
        self.clock = pg.time.Clock()

        self.engine = Engine(self.screen)
     
    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            for event in pg.event.get():
                if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                    pg.quit()
                    sys.exit()

            self.engine.update(dt)
            pg.display.update()
             
if __name__ == '__main__':
    main = Main()
    main.run()