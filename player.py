import math
from math import atan2, sin, cos, pi, degrees
import pygame
from animation import Animation
from spritesheet import SpriteSheet
import settings


class PlayerState:
    WALK = 0
    ROLL = 1
    JUMP = 2


class Player:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.render_pos = self.pos.copy()
        self.render_snap_dist = 90.0         
        self.render_follow_speed = 18.0      
        self.rad = 20
        self.walk_accel = 0.25
        self.walk_friction = 0.12
        self.walk_max_speed = 5.0
        self.roll_friction = 0.02
        self.roll_gravity = 0.4
        self.gravity = 0.5
        self.on_ground = False
        self.slope_angle = 0.0 # radians
        self.ray_offsets = [-40, -20, 0, 20, 40]
        self.ray_length = 80
        self.roll_rotation_deg = 0.0
        self.roll_rad_px = 250.0 # rot speed
        self.direction = True
        self.jumping = False
        self.jump_pow = 10.0
        self.jump_land_ignore_time = 0.08 # no collision frames after hjump
        self._jump_land_ignore_timer = 0.0
        self.jump_max_lock_time = 0.0
        self._jump_lock_timer = 0.0
        self.ground_snap_strength = 0.28  # ++ more snapp
        self.max_snap_per_frame = 10.0 
        self.ground_grace_px = 6.0 # jitter tol

        # DEBUG ---------------------------------------------------------------           
        self.debug_rays = []
        self.debug_WALK = None

        # sprites
        walk_sheet = SpriteSheet("bug_walk.png")
        roll_sheet = SpriteSheet("bug_sonic.png")
        walk_frames = walk_sheet.load_strip((0, 0, 250, 250), 2)
        roll_frames = roll_sheet.load_strip((0, 0, 250, 250), 1)

        self.animations = {
            PlayerState.WALK: Animation(walk_frames, speed=8),
            PlayerState.ROLL: Animation(roll_frames, speed=12),
        }

        self.state = PlayerState.WALK
        self.current_anim = self.animations[self.state]

        self.draw_size = (100, 100)

        self.roll_collision_frame = roll_frames[0]

        self.image = pygame.transform.scale(self.current_anim.image, self.draw_size)
        self.rect = self.image.get_rect(center=(int(self.render_pos.x), int(self.render_pos.y)))

    def update_render_pos(self, dt):

        delta = self.pos - self.render_pos
        if delta.length() > self.render_snap_dist:
            self.render_pos = self.pos.copy()
            return

        alpha = 1.0 - pow(0.001, self.render_follow_speed * dt)
        self.render_pos += delta * alpha


    def ray_casting(self, level_mask):
        # DEBUG ---------------------------------------------------------------           
        self.debug_rays = []
        #-

        hits = []

        if self.jumping:
            return hits

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

                if 0 <= lx < level_mask.get_size()[0] and 0 <= ly < level_mask.get_size()[1]:
                    if level_mask.get_at((lx, ly)):
                        hit_point = pygame.Vector2(lx, ly)
                        break

            # DEBUG ---------------------------------------------------------------           
            self.debug_rays.append(((start_x, start_y), (start_x, start_y + self.ray_length), hit_point))
            # -
            if hit_point:
                hits.append(hit_point)

        return hits

    # pulled from stack exchange - forgot to add link
    def calculate_slope_angle(self, hits):
        if len(hits) < 2:
            return 0.0

        hits_sorted = sorted(hits, key=lambda p: p.x)
        left = hits_sorted[0]
        right = hits_sorted[-1]

        dx = right.x - left.x
        dy = right.y - left.y
        if dx == 0:
            return 0.0

        angle = atan2(dy, dx)

        nx = -sin(angle)
        ny = cos(angle)
        mid = (left + right) / 2
        # DEBUG ---------------------------------------------------------------           
        self.debug_WALK = (mid, pygame.Vector2(nx, ny))
        # -
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

    
        if self.on_ground and keys[pygame.K_SPACE]:
            nx = math.sin(self.slope_angle)
            ny = -math.cos(self.slope_angle)

            jump_dir = pygame.Vector2(nx, ny)
            if jump_dir.length_squared() > 0:
                jump_dir = jump_dir.normalize()
            else:
                jump_dir = pygame.Vector2(0, -1)

            self.vel += jump_dir * self.jump_pow

        
            self.on_ground = False
            self.jumping = True
            self._jump_land_ignore_timer = self.jump_land_ignore_time

        
            self._jump_lock_timer = self.jump_max_lock_time

        if keys[pygame.K_ESCAPE]:
            pygame.quit()

    def apply_ground_physics(self, dt):
        slope_x = cos(self.slope_angle)
        slope_y = sin(self.slope_angle)

    
        slope_speed = self.vel.x * slope_x + self.vel.y * slope_y

    
        if self.state == PlayerState.ROLL:
            slope_speed += sin(self.slope_angle) * self.roll_gravity

        self.vel.x = slope_x * slope_speed
        self.vel.y = slope_y * slope_speed

        self.pos.x += self.vel.x
        self.pos.y += self.vel.y


    def apply_air_physics(self, dt):
        self.vel.y += self.gravity
        self.pos += self.vel

    def check_jump_mask_landing(self, level_mask):
        if self._jump_land_ignore_timer > 0:
            return False

        col_img = pygame.transform.scale(self.roll_collision_frame, self.draw_size)

        if not self.direction:
            col_img = pygame.transform.flip(col_img, True, False)

        player_mask = pygame.mask.from_surface(col_img)
        player_rect = col_img.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    
        offset = (
            int(player_rect.left + settings.surface_offest[0]),
            int(player_rect.top + settings.surface_offest[1]),
        )

        if not level_mask.get_rect().colliderect(pygame.Rect(offset, player_rect.size)):
            return False

        if level_mask.overlap(player_mask, offset):
            self.jumping = False
            self.on_ground = True

            if self.vel.y > 0:
                self.vel.y = 0

            for _ in range(10):
                offset = (
                    int(player_rect.left + settings.surface_offest[0]),
                    int(player_rect.top + settings.surface_offest[1]),
                )
                if not level_mask.overlap(player_mask, offset):
                    break
                self.pos.y -= 1
                player_rect.centery = int(self.pos.y)

            return True

        return False

    def smooth_ground_snap(self, target_y):
        dy = target_y - self.pos.y
        dy = max(-self.max_snap_per_frame, min(self.max_snap_per_frame, dy))
        self.pos.y += dy * self.ground_snap_strength

        if abs(target_y - self.pos.y) < 0.25:
            self.pos.y = target_y




    def update(self, dt, keys, level_mask):
        self.handle_input(keys)

        if self._jump_land_ignore_timer > 0:
            self._jump_land_ignore_timer -= dt

        if self._jump_lock_timer > 0:
            self._jump_lock_timer -= dt
            if self._jump_lock_timer <= 0:
                self.jumping = False

        hits = self.ray_casting(level_mask)

        if (not self.jumping) and hits:
            closest_hit = min(hits, key=lambda p: p.y)
            target_y = closest_hit.y - self.rad

            if (target_y - self.pos.y) <= self.ground_grace_px:
                self.on_ground = True
                self.slope_angle = self.calculate_slope_angle(hits)

                self.apply_ground_physics(dt)
                self.smooth_ground_snap(target_y)
            else:
                self.on_ground = False
                self.slope_angle = 0.0
                self.apply_air_physics(dt)

        else:
            self.on_ground = False
            self.slope_angle = 0.0
            self.apply_air_physics(dt)

            if self.jumping:
                self.check_jump_mask_landing(level_mask)

    
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
        self.current_anim.speed = 0.3 * (speed_mag * 0.2) if abs(self.vel.x) > 0 else 0 
        self.current_anim.update(dt)

    
        img = pygame.transform.scale(self.current_anim.image, self.draw_size)

        slope_deg = degrees(self.slope_angle) if self.on_ground else 0.0
        spin_deg = self.roll_rotation_deg if self.state == PlayerState.ROLL else 0.0
        total_deg = -(slope_deg + spin_deg) if self.direction else (slope_deg + spin_deg)

        self.image = pygame.transform.rotate(img, total_deg)

    
        self.update_render_pos(dt)

    
        self.rect = self.image.get_rect(center=(int(self.render_pos.x), int(self.render_pos.y)))




    def draw(self, surf):
        #blit_pos = ((self.pos.x - self.image.get_width() // 2, self.pos.y - self.image.get_height() // 2 ))
        if self.on_ground:
            # DEBUG ---------------------------------------------------------------           
            hits = [h for (_, _, h) in self.debug_rays if h]
            # -

            if hits:
                hits_sorted = sorted(hits, key=lambda p: p.x)

                ax = ((hits_sorted[0].x + hits_sorted[-1].x) // 2) - self.image.get_width() // 2
                ay = ((hits_sorted[0].y + hits_sorted[-1].y) // 2) - self.image.get_height() // 2

                nx = -math.sin(self.slope_angle)
                ny = math.cos(self.slope_angle)
                GROUND_OFFSET = -15

                blit_pos = (ax + nx * GROUND_OFFSET, ay + ny * GROUND_OFFSET)
            else:
                blit_pos = (
                    self.render_pos.x - self.image.get_width() // 2,
                    self.render_pos.y - self.image.get_height() // 2
                )
        else:
        
            blit_pos = (
                self.render_pos.x - self.image.get_width() // 2,
                self.render_pos.y - self.image.get_height() // 2
            )

        if self.direction:
            surf.blit(self.image, blit_pos)
        else:
            surf.blit(pygame.transform.flip(self.image, True, False), blit_pos)
          
        # DEBUG -----------------------------------------------------------------------------------------
        '''

        print(self.timer)
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