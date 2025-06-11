import pygame as pg

class Timer:
    def __init__(self, length: int, function: callable = False, auto_start: bool = False, loop: bool = False):
        self.length = length
        self.function = function
        self.auto_start = auto_start
        self.loop = loop
        
        self.running = False

        if self.auto_start: 
            self.start()

    def start(self):
        self.running = True
        self.start_time = pg.time.get_ticks()

    def end(self):
        self.running = False
        self.start_time = 0
        
        if self.function:
            self.function()

        if self.loop:
            self.start()

    def update(self):
        if self.running:
            time = pg.time.get_ticks()
            if time - self.start_time >= self.length: # expired
                self.end()