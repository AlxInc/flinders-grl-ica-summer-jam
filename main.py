import pygame
from player import Player
import settings

pygame.init()
screen = pygame.display.set_mode((1000, 600))
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 18)

class GameState:
    INTRO = 0
    GAME = 1
    level = 1
    scene = 1
    

state = GameState.INTRO
timer = 10

# placveholder terrain
level_surface = pygame.transform.scale(pygame.image.load("bowl.png"), (1000,600))
scene_1 = pygame.transform.scale(pygame.image.load("gfx/Background_00.png"), (1000,600))


level_mask = pygame.mask.from_surface(level_surface)

player = Player(100, 200)
camera = pygame.Vector2(0, 0)


running = True
while running:
    dt = clock.tick(60) 
    #dt = clock.get_time() / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    if state == GameState.INTRO:
        if GameState.scene == 1:
            screen.blit(scene_1)
            if timer <= 0:
                GameState.scene += 1
        if GameState.scene == 2:
            state = GameState.GAME

    elif state == GameState.GAME:
        player.update(dt, keys, level_mask)
        screen.fill((40, 40, 60))
        screen.blit(level_surface, (0, settings.surface_offest[1]))
        player.draw(screen)
    
    print(timer)
    if timer > 0:
        timer -= .01 * dt

    

    pygame.display.flip()

pygame.quit()
