import pygame
surface_offest = (0,0)
level = 1

pygame.mixer.init()

sfx_dict = {'bg_music': pygame.mixer.music.load('sfx/Buge music.mp3'), 'bird': pygame.mixer.Sound('sfx/bird.mp3'),
                 'h_land': pygame.mixer.Sound('sfx/hard land.mp3'), 'sheet': pygame.mixer.Sound('sfx/sheet.mp3'),
                 's_land': pygame.mixer.Sound('sfx/soft land.mp3'), 's_land': pygame.mixer.Sound('sfx/transformation.mp3')
                 }


pygame.mixer.music.play(-1)