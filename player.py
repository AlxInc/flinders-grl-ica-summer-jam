import math
from math import atan2, sin, cos, pi, degrees
import pygame
from pygame.math import clamp
from animation import Animation
from spritesheet import SpriteSheet
import settings

class PlayerState:
    WALK = 0
    ROLL = 1


class Player:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.rad = 20  # col sphere
        self.sprite_offset = pygame.Vector2(50, 50)
        self.walk_accel = 0.25
        self.walk_friction = 0.12
        self.walk_max_speed = 5.0
        self.roll_friction = 0.02
        self.roll_gravity = 0.4
        self.gravity = 0.5
        self.state = PlayerState.WALK
        self.on_ground = False
        self.slope_angle = 0.0  # radians
        self.ray_offsets = [-40, -20, 0, 20, 40]
        self.ray_length = 80
        self.roll_rotation_deg = 0.0
        self.roll_rad_px = 250.0 # rot speed
        self.direction = True


        # Debug
        self.debug_rays = []
        self.debug_WALK = None

        # sprites
        walk_sheet = SpriteSheet("bug_walk.png")
        roll_sheet = SpriteSheet("bug_sonic.png")
        walk_frames = walk_sheet.load_strip((0, 0, 250, 250), 2)
        roll_frames = roll_sheet.load_strip((0, 0, 250, 250), 1)

        self.animations = {
            PlayerState.WALK: Animation(walk_frames, speed=8),
            PlayerState.ROLL: Animation(roll_frames, speed=12)
        }

        self.current_anim = self.animations[self.state]
        self.image = self.current_anim.image
        self.rect = self.image.get_rect(center=self.pos)

    def ray_casting(self, level_mask):
        self.debug_rays = []
        hits = []
        start_y_base = self.pos.y

        for offset in self.ray_offsets:
            start_x = self.pos.x + offset
            start_y = start_y_base
            hit_point = None

            for dy in range(self.ray_length):
                x = int(start_x)
                y = int(start_y + dy)
                lx = x + settings.surface_offest[0]
                ly = y + settings.surface_offest[1]
                if level_mask.overlap(level_mask, (lx - self.pos.x, ly - self.pos.y)):
                    if lx > 0 and lx < level_mask.get_size()[0] and ly > 0 and ly < level_mask.get_size()[1]:
                        if level_mask.get_at((lx, ly)):
                            hit_point = pygame.Vector2(lx, ly)
                            break

            self.debug_rays.append(((start_x, start_y), (start_x, start_y + self.ray_length), hit_point))

            if hit_point:
                hits.append(hit_point)

        return hits

    # pulled from stack exchange - forgot to add link
    def calculate_slope_angle(self, hits):
        if len(hits) < 2:
            return 0.0
        
        hits_sorted = sorted(hits, key=lambda p: p.x)
        left = hits_sorted[0] #first
        right = hits_sorted[-1] #last

        dx = right.x - left.x
        dy = right.y - left.y

        if dx == 0:
            return 0.0

        angle = atan2(dy, dx)
        nx = -sin(angle)
        ny = cos(angle)
        mid = (left + right) / 2
        self.debug_WALK = (mid, pygame.Vector2(nx, ny))

        return angle

    def handle_input(self, keys):
        if self.on_ground and keys[pygame.K_DOWN]:
            self.state = PlayerState.ROLL
        elif not keys[pygame.K_DOWN]: # ROLLY BOY
            if self.state == PlayerState.ROLL and abs(self.vel.x) < 1.0:
                self.state = PlayerState.WALK
            elif self.state != PlayerState.ROLL:
                self.state = PlayerState.WALK

        if self.state == PlayerState.WALK:
            if keys[pygame.K_LEFT]:
                self.vel.x -= self.walk_accel
                self.direction = False
            elif keys[pygame.K_RIGHT]:
                self.vel.x += self.walk_accel
                self.direction = True
            else:
                self.vel.x *= (1 - self.walk_friction)

            self.vel.x = max(-self.walk_max_speed, min(self.walk_max_speed, self.vel.x))

        elif self.state == PlayerState.ROLL:
            self.vel.x *= (1 - self.roll_friction)

        # need to add jump
        # way to control roll might be good too

    def apply_ground_physics(self):
        slope_x = cos(self.slope_angle)
        slope_y = sin(self.slope_angle)
        slope_speed = self.vel.x * slope_x + self.vel.y * slope_y

        if self.state == PlayerState.ROLL:
            slope_speed += sin(self.slope_angle) * self.roll_gravity

        self.vel.x = slope_x * slope_speed
        self.vel.y = slope_y * slope_speed
        self.pos.x += self.vel.x
        self.pos.y += self.vel.y

    def apply_air_physics(self):
        self.vel.y += self.gravity
        self.pos += self.vel

    def update(self, dt, keys, level_mask):
        self.handle_input(keys)

        hits = self.ray_casting(level_mask)

        if hits:
            self.on_ground = True
            self.slope_angle = self.calculate_slope_angle(hits)
            self.apply_ground_physics()
            closest_hit = min(hits, key=lambda p: p.y)
            self.pos.y = closest_hit.y - self.rad
        else:
            self.on_ground = False
            self.slope_angle = 0.0
            self.apply_air_physics()

        if self.state == PlayerState.ROLL:
            if self.on_ground:
                tx = cos(self.slope_angle)
                ty = sin(self.slope_angle)
                v_tangent = self.vel.x * tx + self.vel.y * ty
                dist = v_tangent * dt

            else:
                dist = self.vel.x * dt


            circumference = 2.0 * pi * self.roll_rad_px
            if circumference > 0:
                self.roll_rotation_deg += (dist / circumference) * 360.0

            self.roll_rotation_deg %= 360.0
        else:

            self.roll_rotation_deg = 0.0

        speed_mag = abs(self.vel.x)
        self.current_anim = self.animations[self.state]
        if abs(self.vel.x) > 0:
            self.current_anim.speed = .3 * (speed_mag * .2) # 6 + speed_mag * 1.5
        else:
            self.current_anim.speed = 0 # 6 + speed_mag * 1.5
        self.current_anim.update(dt)

        img = pygame.transform.scale(self.current_anim.image, (100, 100))

        slope_deg = degrees(self.slope_angle) if self.on_ground else 0.0
        spin_deg = self.roll_rotation_deg if self.state == PlayerState.ROLL else 0.0

        if self.direction:
            total_deg = -(slope_deg + spin_deg)
        else:
            total_deg = (slope_deg + spin_deg)
        self.image = pygame.transform.rotate(img, total_deg)
        
        self.rect = self.image.get_rect(center=self.pos)


    def draw(self, surf):
        blit_pos = ((self.pos.x - self.image.get_width() // 2, self.pos.y - self.image.get_height() // 2 ))

        
        if self.direction:
            surf.blit(self.image, blit_pos)
        else:
            surf.blit(pygame.transform.flip(self.image, True, False), blit_pos)
        
        
        # DEBUG -----------------------------------------------------------------------------------------
        #'''
        pygame.draw.rect(surf, (255,0,0), self.rect, 2)

        pygame.draw.circle(surf, (0,0,0), self.pos, 3)
        # collsion spheer
        pygame.draw.circle(
            surf,
            (0, 200, 255),
            (int(self.pos.x), int(self.pos.y)),
            self.rad,
            2
        )

        # Debug slope line
        hits = [h for (_, _, h) in self.debug_rays if h]
        if self.on_ground and len(hits) >= 2:
            hits_sorted = sorted(hits, key=lambda p: p.x)
            pygame.draw.line(surf, (255, 255, 0), hits_sorted[0], hits_sorted[-1], 2)

        # Debug ray casts
        for start, end, hit in self.debug_rays:
            pygame.draw.line(surf, (0, 255, 0), start, end, 1)
            if hit:
                pygame.draw.circle(surf, (255, 0, 0), (int(hit.x), int(hit.y)), 3)
        #'''        
