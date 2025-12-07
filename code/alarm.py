import pygame as pg

class Alarm:
    def __init__(self, length: int, fn: callable=None, auto: bool=False, loop: bool=False, track_pct: bool=False, *args, **kwargs):
        self.length = length
        self.fn = fn
        self.loop = loop
        self.track_pct = track_pct
        if self.track_pct:
            self.pct = 0
        self.args = args
        self.kwargs = kwargs
        
        self.running = False
        if auto: 
            self.start()

    def start(self) -> None:
        self.running = True
        self.start_time = pg.time.get_ticks()

    def end(self) -> None:
        self.running = False
        self.start_time = 0
        if self.fn:
            self.fn(*self.args, **self.kwargs)
        if self.loop:
            self.start()

    def update(self) -> None:
        if self.running:
            progress = pg.time.get_ticks() - self.start_time
            if self.track_pct:
                self.pct = (progress / self.length) * 100
            if progress >= self.length:
                self.end()