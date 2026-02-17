import pygame

class Animation:
    def __init__(self, frames, speed=0.01):
        self.frames = frames
        self.speed = speed
        self.index = 0
        self.image = frames[0]

    def update(self, dt):
        self.index += self.speed * (dt / 16)  # dt from main is ~16 at 60fps
        print(self.index)
        if self.index >= len(self.frames):
            self.index = 0
        self.image = self.frames[int(self.index)]
        
