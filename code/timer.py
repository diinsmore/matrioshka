import pygame as pg

class Timer:
    def __init__(self, length: int, function: callable=None, auto_start: bool=False, loop: bool=False, store_progress: bool=False, *args, **kwargs):
        self.length = length
        self.function = function
        self.loop = loop
        self.store_progress = store_progress
        if self.store_progress:
            self.percent = 0
        self.args = args
        self.kwargs = kwargs
        
        self.running = False
        if auto_start: 
            self.start()

    def start(self) -> None:
        self.running = True
        self.start_time = pg.time.get_ticks()

    def end(self) -> None:
        self.running = False
        self.start_time = 0
        if self.function:
            self.function(*self.args, **self.kwargs)
        if self.loop:
            self.start()

    def update(self) -> None:
        if self.running:
            progress = pg.time.get_ticks() - self.start_time
            if self.store_progress:
                self.percent = (progress / self.length) * 100
            if progress >= self.length:
                self.end()