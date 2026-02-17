import pygame

class SpriteSheet:
    def __init__(self, image_path):
        self.sheet = pygame.image.load(image_path).convert_alpha()

    def image_at(self, rect):
        #u
        rect = pygame.Rect(rect)
        image = pygame.Surface(rect.size, pygame.SRCALPHA)
        image.blit(self.sheet, (0, 0), rect)
        return image

    def load_strip(self, rect, frame_count):
        #v
        frames = []
        x, y, w, h = rect
        for i in range(frame_count):
            frame_rect = (x + i * w, y, w, h)
            frames.append(self.image_at(frame_rect))
        return frames
