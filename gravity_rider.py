"""
Gravity Rider - An Antigravity Hill Climb Racing Game
Built with Pygame

Controls:
- RIGHT ARROW / D: Accelerate
- LEFT ARROW / A: Brake/Reverse
- SPACE: Flip Gravity
- R: Restart after game over
- ESC: Quit
"""

import pygame
import math
import random
import sys

# Initialize Pygame
pygame.init()

# Screen settings
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Gravity Rider - Antigravity Racing")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_BLUE = (135, 206, 235)
GROUND_GREEN = (34, 139, 34)
GROUND_BROWN = (139, 90, 43)
CAR_RED = (220, 50, 50)
CAR_DARK = (40, 40, 40)
WHEEL_COLOR = (30, 30, 30)
COIN_YELLOW = (255, 215, 0)
FUEL_GREEN = (50, 205, 50)
CEILING_COLOR = (100, 100, 120)

# Game settings
FPS = 60
GRAVITY = 0.5
MAX_SPEED = 12
ACCELERATION = 0.3
BRAKE_POWER = 0.4
FRICTION = 0.02
CAR_WIDTH = 60
CAR_HEIGHT = 25
WHEEL_RADIUS = 10

PARTICLE_COLORS = {
    'exhaust': [(200, 200, 200), (150, 150, 150), (100, 100, 100)],
    'spark': [(255, 255, 0), (255, 165, 0), (255, 50, 0)],
    'coin': [(255, 255, 150), (255, 215, 0), (200, 150, 0)]
}

# Fonts
font_large = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 36)

class Particle:
    def __init__(self, x: float, y: float, dx: float, dy: float, life: int, max_life: int, color: tuple, size: int, p_type: str):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.life = life
        self.max_life = max_life
        self.color = color
        self.size = size
        self.p_type = p_type

class ParticleSystem:
    """Manages all particle effects"""
    def __init__(self):
        self.particles: list[Particle] = []
        
    def add_particle(self, x, y, dx, dy, life, p_type='exhaust', size=3):
        color = random.choice(PARTICLE_COLORS[p_type])
        self.particles.append(Particle(x, y, dx, dy, life, life, color, size, p_type))
        
    def update(self):
        for p in reversed(self.particles):
            p.x += p.dx
            p.y += p.dy
            p.life -= 1
            if p.life <= 0:
                self.particles.remove(p)
                
    def draw(self, screen, camera_x):
        for p in self.particles:
            x, y = int(p.x - camera_x), int(p.y)
            life_ratio = max(0.0, p.life / p.max_life)
            size = max(1, int(p.size * life_ratio))
            
            # Fade out alpha with life, using a surface
            surf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            alpha = int(255 * (0.3 + 0.7 * life_ratio))
            
            c = p.color
            color = (c[0], c[1], c[2])
            pygame.draw.circle(surf, (*color, alpha), (size, size), size)
            screen.blit(surf, (x - size, y - size))


class Terrain:
    """Generates and manages the terrain (ground and ceiling)"""
    
    def __init__(self):
        self.ground_points = []
        self.ceiling_points = []
        self.segment_width = 50
        self.generate_initial_terrain()
        
    def generate_initial_terrain(self):
        """Generate initial terrain"""
        x = -100
        ground_y = SCREEN_HEIGHT - 100
        ceiling_y = 80
        
        while x < SCREEN_WIDTH + 500:
            # Ground - hilly terrain
            ground_variation = math.sin(x * 0.01) * 40 + math.sin(x * 0.02) * 20
            self.ground_points.append((x, ground_y + ground_variation))
            
            # Ceiling - also hilly but inverted
            ceiling_variation = math.sin(x * 0.015 + 1) * 30 + math.sin(x * 0.008) * 15
            self.ceiling_points.append((x, ceiling_y + ceiling_variation))
            
            x += self.segment_width
    
    def update(self, camera_x):
        """Extend terrain as camera moves"""
        # Remove old points
        while self.ground_points and self.ground_points[0][0] < camera_x - 200:
            self.ground_points.pop(0)
            self.ceiling_points.pop(0)
        
        # Add new points
        while self.ground_points[-1][0] < camera_x + SCREEN_WIDTH + 500:
            last_x = self.ground_points[-1][0]
            new_x = last_x + self.segment_width
            
            # Ground
            ground_y = SCREEN_HEIGHT - 100
            ground_variation = math.sin(new_x * 0.01) * 40 + math.sin(new_x * 0.02) * 20
            # Add some random hills
            if random.random() < 0.1:
                ground_variation += random.randint(-30, 30)
            self.ground_points.append((new_x, ground_y + ground_variation))
            
            # Ceiling
            ceiling_y = 80
            ceiling_variation = math.sin(new_x * 0.015 + 1) * 30 + math.sin(new_x * 0.008) * 15
            self.ceiling_points.append((new_x, ceiling_y + ceiling_variation))
    
    def get_height_at(self, x, is_ceiling=False):
        """Get terrain height at given x position"""
        points = self.ceiling_points if is_ceiling else self.ground_points
        
        for i in range(len(points) - 1):
            if points[i][0] <= x < points[i + 1][0]:
                # Linear interpolation
                t = (x - points[i][0]) / (points[i + 1][0] - points[i][0])
                return points[i][1] + t * (points[i + 1][1] - points[i][1])
        
        return SCREEN_HEIGHT - 100 if not is_ceiling else 80
    
    def get_slope_at(self, x, is_ceiling=False):
        """Get terrain slope (angle) at given x position"""
        points = self.ceiling_points if is_ceiling else self.ground_points
        
        for i in range(len(points) - 1):
            if points[i][0] <= x < points[i + 1][0]:
                dx = points[i + 1][0] - points[i][0]
                dy = points[i + 1][1] - points[i][1]
                return math.atan2(dy, dx)
        return 0
    
    def draw(self, screen, camera_x):
        """Draw the terrain"""
        # Draw ground
        ground_draw_points = [(p[0] - camera_x, p[1]) for p in self.ground_points]
        ground_draw_points.append((ground_draw_points[-1][0], SCREEN_HEIGHT))
        ground_draw_points.append((ground_draw_points[0][0], SCREEN_HEIGHT))
        
        if len(ground_draw_points) > 2:
            # Deep ground shadow
            pygame.draw.polygon(screen, (80, 50, 20), ground_draw_points)
            
            # Mid ground (slightly shifted up)
            mid_points = [(p[0], min(float(SCREEN_HEIGHT), p[1] + 25.0)) for p in ground_draw_points[0:len(ground_draw_points)-2]]
            mid_points.extend([(ground_draw_points[-1][0], SCREEN_HEIGHT), (ground_draw_points[0][0], SCREEN_HEIGHT)])
            pygame.draw.polygon(screen, GROUND_BROWN, mid_points)
            
            # Thick grass line with a highlight
            top_line = [(p[0] - camera_x, p[1]) for p in self.ground_points]
            pygame.draw.lines(screen, (20, 100, 20), False, top_line, 8)
            highlight_line = [(p[0] - camera_x, p[1] + 2) for p in self.ground_points]
            pygame.draw.lines(screen, GROUND_GREEN, False, highlight_line, 4)
        
        # Draw ceiling
        ceiling_draw_points = [(p[0] - camera_x, p[1]) for p in self.ceiling_points]
        ceiling_draw_points.insert(0, (ceiling_draw_points[0][0], 0))
        ceiling_draw_points.append((ceiling_draw_points[-1][0], 0))
        
        if len(ceiling_draw_points) > 2:
            # Deep ceiling shadow
            pygame.draw.polygon(screen, (50, 50, 60), ceiling_draw_points)
            
            # Mid ceiling (shifted down)
            mid_c_points = [(p[0], max(0, p[1] - 20)) for p in ceiling_draw_points[1:len(ceiling_draw_points)-1]]
            mid_c_points.insert(0, (ceiling_draw_points[0][0], 0))
            mid_c_points.append((ceiling_draw_points[-1][0], 0))
            pygame.draw.polygon(screen, CEILING_COLOR, mid_c_points)
            
            # Ceiling edge outline
            bot_line = [(p[0] - camera_x, p[1]) for p in self.ceiling_points]
            pygame.draw.lines(screen, (80, 80, 100), False, bot_line, 5)


class Car:
    """Player's car with physics"""
    
    def __init__(self, x: float, y: float):
        self.x: float = x
        self.y: float = y
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.angle: float = 0.0
        self.angular_velocity: float = 0.0
        self.gravity_direction: int = 1  # 1 = down, -1 = up
        self.on_ground: bool = True
        self.fuel: float = 100.0
        self.crashed: bool = False
        
    def flip_gravity(self):
        """Flip gravity direction"""
        self.gravity_direction *= -1
        self.vy = -self.vy * 0.5  # Bounce effect
        
    def update(self, terrain, keys_pressed, particles):
        """Update car physics"""
        if self.crashed:
            return
            
        # Get terrain info
        is_on_ceiling = self.gravity_direction == -1
        terrain_y = terrain.get_height_at(self.x, is_on_ceiling)
        terrain_slope = terrain.get_slope_at(self.x, is_on_ceiling)
        
        # Input handling
        accelerating = keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]
        braking = keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]
        
        # Acceleration
        if accelerating and self.fuel > 0:
            self.vx += ACCELERATION * math.cos(self.angle)
            self.vy += ACCELERATION * math.sin(self.angle)
            self.fuel -= 0.05
            
            # Exhaust particles
            if random.random() < 0.5:
                px = self.x - 20 * math.cos(self.angle)
                py = self.y - 20 * math.sin(self.angle)
                particles.add_particle(px, py, -self.vx*0.2 + random.uniform(-1, 1), -self.vy*0.2 + random.uniform(-1, 1), random.randint(15, 30), 'exhaust', random.randint(2, 5))
        
        # Braking
        if braking:
            self.vx *= (1 - BRAKE_POWER * 0.1)
        
        # Apply gravity
        self.vy += GRAVITY * self.gravity_direction
        
        # Apply friction when on ground
        if self.on_ground:
            self.vx *= (1 - FRICTION)
        
        # Limit speed
        speed = math.sqrt(self.vx ** 2 + self.vy ** 2)
        if speed > MAX_SPEED:
            self.vx = (self.vx / speed) * MAX_SPEED
            self.vy = (self.vy / speed) * MAX_SPEED
        
        # Update position
        self.x += self.vx
        self.y += self.vy
        
        # Ground/Ceiling collision
        car_bottom = self.y + CAR_HEIGHT // 2 + WHEEL_RADIUS
        car_top = self.y - CAR_HEIGHT // 2 - WHEEL_RADIUS
        
        if self.gravity_direction == 1:  # Normal gravity
            if car_bottom >= terrain_y:
                self.y = terrain_y - CAR_HEIGHT // 2 - WHEEL_RADIUS
                self.vy = 0
                self.on_ground = True
                # Align to slope
                target_angle = terrain_slope
                self.angle += (target_angle - self.angle) * 0.2
            else:
                self.on_ground = False
        else:  # Reversed gravity
            ceiling_y = terrain.get_height_at(self.x, True)
            if car_top <= ceiling_y:
                self.y = ceiling_y + CAR_HEIGHT // 2 + WHEEL_RADIUS
                self.vy = 0
                self.on_ground = True
                # Align to slope (inverted)
                target_angle = terrain.get_slope_at(self.x, True) + math.pi
                self.angle += (target_angle - self.angle) * 0.2
            else:
                self.on_ground = False
        
        # Angular physics when in air
        if not self.on_ground:
            self.angular_velocity += 0.001 * self.vx
            self.angle += self.angular_velocity
            self.angular_velocity *= 0.98
        else:
            self.angular_velocity = 0
        
        # Check for crash (too much rotation)
        angle_deg = abs(math.degrees(self.angle) % 360)
        if self.on_ground:
            if 60 < angle_deg < 120 or 240 < angle_deg < 300:
                self.crashed = True
                for _ in range(30):
                    particles.add_particle(self.x + random.uniform(-10, 10), self.y + random.uniform(-10, 10), random.uniform(-5, 5), random.uniform(-5, 5), random.randint(30, 60), 'spark', random.randint(3, 7))
        
        # Clamp fuel
        self.fuel = max(0.0, min(100.0, self.fuel))
        
    def draw(self, screen, camera_x):
        """Draw the car"""
        draw_x = self.x - camera_x
        draw_y = self.y
        
        # Car body
        car_surface = pygame.Surface((CAR_WIDTH, CAR_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(car_surface, CAR_RED, (0, 5, CAR_WIDTH, CAR_HEIGHT - 10), border_radius=5)
        pygame.draw.rect(car_surface, CAR_DARK, (10, 0, 25, CAR_HEIGHT), border_radius=3)  # Cabin
        
        # Rotate and draw
        rotated = pygame.transform.rotate(car_surface, -math.degrees(self.angle))
        rect = rotated.get_rect(center=(draw_x, draw_y))
        screen.blit(rotated, rect)
        
        # Wheels
        wheel_offset_x = 18
        wheel_offset_y = CAR_HEIGHT // 2
        
        for wx in [-wheel_offset_x, wheel_offset_x]:
            wheel_x = draw_x + wx * math.cos(self.angle) - wheel_offset_y * math.sin(self.angle)
            wheel_y = draw_y + wx * math.sin(self.angle) + wheel_offset_y * math.cos(self.angle)
            pygame.draw.circle(screen, WHEEL_COLOR, (int(wheel_x), int(wheel_y)), WHEEL_RADIUS)
            pygame.draw.circle(screen, (80, 80, 80), (int(wheel_x), int(wheel_y)), WHEEL_RADIUS - 3)


class Coin:
    """Collectible coins"""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.collected = False
        self.radius = 15
        self.animation: float = 0.0
        
    def update(self):
        self.animation += 0.1
        
    def draw(self, screen, camera_x):
        if self.collected:
            return
        draw_x = self.x - camera_x
        # Bobbing animation
        draw_y = self.y + math.sin(self.animation) * 5
        
        pygame.draw.circle(screen, COIN_YELLOW, (int(draw_x), int(draw_y)), self.radius)
        pygame.draw.circle(screen, (255, 180, 0), (int(draw_x), int(draw_y)), self.radius - 4)
        
    def check_collision(self, car):
        if self.collected:
            return False
        dist = math.sqrt((self.x - car.x) ** 2 + (self.y - car.y) ** 2)
        if dist < self.radius + 30:
            self.collected = True
            return True
        return False


class FuelCan:
    """Fuel pickup"""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.collected = False
        self.width = 20
        self.height = 25
        
    def draw(self, screen, camera_x):
        if self.collected:
            return
        draw_x = self.x - camera_x
        pygame.draw.rect(screen, FUEL_GREEN, (draw_x - self.width//2, self.y - self.height//2, 
                                               self.width, self.height), border_radius=3)
        pygame.draw.rect(screen, (30, 150, 30), (draw_x - 5, self.y - self.height//2 - 5, 10, 8))
        
    def check_collision(self, car):
        if self.collected:
            return False
        dist = math.sqrt((self.x - car.x) ** 2 + (self.y - car.y) ** 2)
        if dist < 35:
            self.collected = True
            return True
        return False


class Game:
    """Main game class"""
    
    def __init__(self):
        self.clock = pygame.time.Clock()
        self.terrain: Terrain
        self.car: Car
        self.particles: ParticleSystem
        self.shake: int = 0
        self.camera_x: float = 0.0
        self.score: int = 0
        self.coins: list = []
        self.fuel_cans: list = []
        self.distance: float = 0.0
        self.game_over: bool = False
        self.reset_game()
        
    def reset_game(self):
        """Reset/Initialize game state"""
        self.terrain: Terrain = Terrain()
        self.car: Car = Car(100.0, SCREEN_HEIGHT - 200.0)
        self.particles: ParticleSystem = ParticleSystem()
        self.shake: int = 0
        self.camera_x: float = 0.0
        self.score: int = 0
        self.coins: list = []
        self.fuel_cans: list = []
        self.distance: float = 0.0
        self.game_over: bool = False
        self.spawn_collectibles()
        
    def spawn_collectibles(self):
        """Spawn coins and fuel cans"""
        for i in range(20):
            x = random.randint(200, 2000) + i * 100
            # Randomly place on ground or ceiling area
            if random.random() < 0.5:
                y = self.terrain.get_height_at(x) - random.randint(50, 150)
            else:
                y = self.terrain.get_height_at(x, True) + random.randint(50, 150)
            self.coins.append(Coin(x, y))
            
            if random.random() < 0.3:
                fuel_x = x + random.randint(-50, 50)
                fuel_y = self.terrain.get_height_at(fuel_x) - random.randint(30, 80)
                self.fuel_cans.append(FuelCan(fuel_x, fuel_y))
    
    def update(self, keys_pressed):
        """Update game state"""
        if self.shake > 0:
            self.shake -= 1
            
        if self.game_over:
            return
            
        was_gravity = self.car.gravity_direction
        
        # Update car
        self.car.update(self.terrain, keys_pressed, self.particles)
        
        if self.car.gravity_direction != was_gravity:
            self.shake = 15
        
        # Update camera
        target_camera = self.car.x - SCREEN_WIDTH // 3
        self.camera_x += (target_camera - self.camera_x) * 0.1
            
        self.particles.update()
        
        # Update terrain
        self.terrain.update(self.camera_x)
        
        # Update distance/score
        if self.car.x > self.distance:
            self.score += int(self.car.x - self.distance)
            self.distance = self.car.x
        
        # Update collectibles
        for coin in self.coins:
            coin.update()
            if coin.check_collision(self.car):
                self.score += 100
                for _ in range(15):
                    self.particles.add_particle(coin.x, coin.y, random.uniform(-3, 3), random.uniform(-3, 3), random.randint(20, 40), 'coin', random.randint(2, 5))
                
        for fuel in self.fuel_cans:
            if fuel.check_collision(self.car):
                self.car.fuel = min(100.0, self.car.fuel + 30.0)
        
        # Spawn more collectibles as we progress
        while self.coins[-1].x < self.camera_x + SCREEN_WIDTH + 500:
            new_x = self.coins[-1].x + random.randint(100, 300)
            if random.random() < 0.5:
                new_y = self.terrain.get_height_at(new_x) - random.randint(50, 150)
            else:
                new_y = self.terrain.get_height_at(new_x, True) + random.randint(50, 150)
            self.coins.append(Coin(new_x, new_y))
            
            if random.random() < 0.25:
                fuel_y = self.terrain.get_height_at(new_x) - random.randint(30, 80)
                self.fuel_cans.append(FuelCan(new_x + random.randint(-30, 30), fuel_y))
        
        # Remove old collectibles
        self.coins = [c for c in self.coins if c.x > self.camera_x - 200]
        self.fuel_cans = [f for f in self.fuel_cans if f.x > self.camera_x - 200]
        
        # Check game over conditions
        if self.car.crashed or self.car.fuel <= 0:
            if not self.game_over and self.car.crashed:
                self.shake = 30
            self.game_over = True
    
    def draw(self):
        """Draw everything"""
        draw_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        draw_surface.fill(SKY_BLUE)
        
        # Parallax Mountains
        for i in range(6):
            mx = (i * 350 - self.camera_x * 0.15) % (SCREEN_WIDTH + 400) - 200
            pygame.draw.polygon(draw_surface, (110, 160, 210), [(mx, SCREEN_HEIGHT), (mx + 175, SCREEN_HEIGHT - 300 + (i%3)*40), (mx + 350, SCREEN_HEIGHT)])
        
        # Draw stars/background elements when gravity is flipped
        if self.car.gravity_direction == -1:
            draw_surface.fill((30, 30, 60))  # Dark space-like background
            for i in range(50):
                star_x = (i * 73 + int(self.camera_x * 0.1)) % SCREEN_WIDTH
                star_y = (i * 47) % SCREEN_HEIGHT
                pygame.draw.circle(draw_surface, WHITE, (star_x, star_y), 1)
        
        # Terrain
        self.terrain.draw(draw_surface, self.camera_x)
        
        # Particles
        self.particles.draw(draw_surface, self.camera_x)
        
        # Collectibles
        for coin in self.coins:
            coin.draw(draw_surface, self.camera_x)
        for fuel in self.fuel_cans:
            fuel.draw(draw_surface, self.camera_x)
        
        # Car
        self.car.draw(draw_surface, self.camera_x)
        
        # UI - Score
        score_bg = font_medium.render(f"Score: {self.score}", True, BLACK)
        draw_surface.blit(score_bg, (22, 22))
        score_text = font_medium.render(f"Score: {self.score}", True, WHITE)
        draw_surface.blit(score_text, (20, 20))
        
        # UI - Distance
        dist_bg = font_small.render(f"Distance: {int(self.distance)}m", True, BLACK)
        draw_surface.blit(dist_bg, (22, 72))
        dist_text = font_small.render(f"Distance: {int(self.distance)}m", True, WHITE)
        draw_surface.blit(dist_text, (20, 70))
        
        # UI - Fuel bar
        pygame.draw.rect(draw_surface, BLACK, (SCREEN_WIDTH - 218, 22, 200, 25), border_radius=5)
        pygame.draw.rect(draw_surface, (50, 50, 50), (SCREEN_WIDTH - 220, 20, 200, 25), border_radius=5)
        fuel_width = int(self.car.fuel * 1.9)
        fuel_color = FUEL_GREEN if self.car.fuel > 30 else (max(0, 255 - int(self.shake)*8), 50, 50)
        pygame.draw.rect(draw_surface, fuel_color, (SCREEN_WIDTH - 215, 25, fuel_width, 15), border_radius=3)
        fuel_label = font_small.render("FUEL", True, WHITE)
        draw_surface.blit(fuel_label, (SCREEN_WIDTH - 220, 50))
        
        # Game over screen
        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            draw_surface.blit(overlay, (0, 0))
            
            if self.car.crashed:
                go_text_bg = font_large.render("CRASHED!", True, BLACK)
                draw_surface.blit(go_text_bg, (SCREEN_WIDTH // 2 - go_text_bg.get_width() // 2 + 4, SCREEN_HEIGHT // 2 - 76))
                go_text = font_large.render("CRASHED!", True, (255, 100, 100))
            else:
                go_text_bg = font_large.render("OUT OF FUEL!", True, BLACK)
                draw_surface.blit(go_text_bg, (SCREEN_WIDTH // 2 - go_text_bg.get_width() // 2 + 4, SCREEN_HEIGHT // 2 - 76))
                go_text = font_large.render("OUT OF FUEL!", True, (255, 150, 50))
            
            draw_surface.blit(go_text, (SCREEN_WIDTH // 2 - go_text.get_width() // 2, SCREEN_HEIGHT // 2 - 80))
            
            score_final_bg = font_medium.render(f"Final Score: {self.score}", True, BLACK)
            draw_surface.blit(score_final_bg, (SCREEN_WIDTH // 2 - score_final_bg.get_width() // 2 + 2, SCREEN_HEIGHT // 2 + 2))
            score_final = font_medium.render(f"Final Score: {self.score}", True, WHITE)
            draw_surface.blit(score_final, (SCREEN_WIDTH // 2 - score_final.get_width() // 2, SCREEN_HEIGHT // 2))
            
            restart_text = font_small.render("Press R to Restart", True, WHITE)
            draw_surface.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 60))
        
        # Apply screen shake and blit to real screen
        shake_x = random.randint(-self.shake, self.shake) if self.shake > 0 else 0
        shake_y = random.randint(-self.shake, self.shake) if self.shake > 0 else 0
        screen.blit(draw_surface, (shake_x, shake_y))
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r and self.game_over:
                        self.reset_game()
            
            # Get pressed keys
            keys = pygame.key.get_pressed()
            
            # Update
            self.update(keys)
            
            # Draw
            self.draw()
            
            # Cap framerate
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()


# Start screen
def show_start_screen():
    """Display start screen"""
    screen.fill(SKY_BLUE)
    
    title = font_large.render("GRAVITY RIDER", True, WHITE)
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 150))
    
    subtitle = font_medium.render("Antigravity Racing", True, (200, 200, 200))
    screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 220))
    
    controls = [
        "Controls:",
        "→ / D  -  Accelerate",
        "← / A  -  Brake",
        "R  -  Restart",
        "ESC  -  Quit"
    ]
    
    y_offset = 320
    for line in controls:
        text = font_small.render(line, True, WHITE)
        screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, y_offset))
        y_offset += 35
    
    start_text = font_medium.render("Press SPACE to Start", True, COIN_YELLOW)
    screen.blit(start_text, (SCREEN_WIDTH // 2 - start_text.get_width() // 2, 530))
    
    pygame.display.flip()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    waiting = False
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()


# Main entry point
if __name__ == "__main__":
    show_start_screen()
    game = Game()
    game.run()
