import pygame as pg
import sys
import os
import json

from settings import RES, FPS
from engine import Engine

class Main:
    def __init__(self):
        pg.init()
        pg.display.set_caption('matrioshka')
        self.running = True
        self.screen = pg.display.set_mode(RES)
        self.clock = pg.time.Clock()
        self.saved_data = self.get_saved_data()
        self.engine = Engine(self.screen, self.saved_data)
        
    def get_saved_data(self) -> dict[str, any] | None:
        saved_data = None
        if os.path.exists('save.json'):
            with open('save.json', 'r') as f:
                saved_data = json.load(f)
        return saved_data

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            for event in pg.event.get():
                if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                    self.engine.make_save('save.json')
                    pg.quit()
                    sys.exit()

            self.engine.update(dt)
            pg.display.update()
             
if __name__ == '__main__':
    main = Main()
    main.run()