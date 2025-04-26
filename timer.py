import pygame as pg

class Timer:
    def __init__(self, length: int, function: callable, auto_start: bool, loop: bool) -> None:
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
        time = pg.time.get_ticks()
        if self.running and time - self.start_time >= self.length: # timer has expired
            self.end()
