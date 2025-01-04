import pygame
import random
import math
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class GameConfig:
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    FPS = 60
    PLAYER_SPEED = 5
    BULLET_SPEED = 7
    ENEMY_SPEED = 2
    ENEMY_DROP = 30
    ENEMY_ROWS = 3
    ENEMIES_PER_ROW = 8
    BONUS_SPAWN_CHANCE = 0.002
    POWER_UP_DURATION = 300


class GameObject:
    def __init__(self, x: float, y: float, width: int, height: int, speed: float, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = speed
        self.color = color

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.width, self.height)


class Bullet(GameObject):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, 4, 12, GameConfig.BULLET_SPEED, (255, 200, 0))

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        pygame.draw.circle(screen, (255, 220, 100), (int(self.x + self.width / 2), int(self.y + self.height / 2)), 4)

    def update(self):
        self.y -= self.speed


class PowerUp(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, 20, 20, 2, (255, 255, 255))
        self.type = random.choice(['double_shot', 'speed_up', 'shield'])
        self.colors = {
            'double_shot': (255, 215, 0),
            'speed_up': (0, 255, 255),
            'shield': (147, 112, 219)
        }
        self.color = self.colors[self.type]

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))

    def update(self):
        self.y += self.speed


class Player(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, 60, 80, GameConfig.PLAYER_SPEED, (50, 150, 50))
        self.bullets = []
        self.shoot_cooldown = 0
        self.double_shot = False
        self.shield = False
        self.power_up_timer = 0
        self.current_power_up = None

    def draw(self, screen):
        # Body
        pygame.draw.rect(screen, (70, 70, 70), (self.x + 20, self.y + 30, 20, 30))
        # Head
        pygame.draw.circle(screen, (200, 150, 150), (self.x + 30, self.y + 20), 10)
        # Arms
        pygame.draw.rect(screen, (70, 70, 70), (self.x + 10, self.y + 35, 10, 20))
        pygame.draw.rect(screen, (70, 70, 70), (self.x + 40, self.y + 35, 10, 20))
        # Gun
        pygame.draw.rect(screen, (100, 100, 100), (self.x + 35, self.y + 25, 25, 8))
        # Shield effect
        if self.shield:
            pygame.draw.circle(screen, (147, 112, 219, 128),
                               (int(self.x + self.width / 2), int(self.y + self.height / 2)),
                               45, 2)

    def move(self, direction: int):
        new_x = self.x + (direction * self.speed)
        if 0 <= new_x <= GameConfig.SCREEN_WIDTH - self.width:
            self.x = new_x

    def shoot(self):
        if self.shoot_cooldown == 0:
            if self.double_shot:
                self.bullets.append(Bullet(self.x + 45, self.y + 29))
                self.bullets.append(Bullet(self.x + 65, self.y + 29))
            else:
                self.bullets.append(Bullet(self.x + 55, self.y + 29))
            self.shoot_cooldown = 15

    def update(self):
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        if self.power_up_timer > 0:
            self.power_up_timer -= 1
            if self.power_up_timer == 0:
                self.disable_power_ups()

        for bullet in self.bullets[:]:
            bullet.update()
            if bullet.y < 0:
                self.bullets.remove(bullet)

    def activate_power_up(self, power_up_type):
        self.current_power_up = power_up_type
        self.power_up_timer = GameConfig.POWER_UP_DURATION

        if power_up_type == 'double_shot':
            self.double_shot = True
        elif power_up_type == 'speed_up':
            self.speed = GameConfig.PLAYER_SPEED * 1.5
        elif power_up_type == 'shield':
            self.shield = True

    def disable_power_ups(self):
        self.double_shot = False
        self.shield = False
        self.speed = GameConfig.PLAYER_SPEED
        self.current_power_up = None


class Enemy(GameObject):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, 40, 40, GameConfig.ENEMY_SPEED, (200, 50, 50))
        self.direction = 1
        self.animation_phase = 0
        self.animation_speed = 0.1

    def draw(self, screen):
        self.animation_phase += self.animation_speed
        wave_offset = math.sin(self.animation_phase) * 3

        points = [
            (self.x + 20, self.y + wave_offset),
            (self.x, self.y + 20),
            (self.x + 40, self.y + 20),
            (self.x + 35, self.y + 40),
            (self.x + 5, self.y + 40)
        ]
        pygame.draw.polygon(screen, self.color, points)

        # Eyes
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x + 15), int(self.y + 15)), 5)
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x + 25), int(self.y + 15)), 5)
        pygame.draw.circle(screen, (0, 0, 0), (int(self.x + 15), int(self.y + 15)), 2)
        pygame.draw.circle(screen, (0, 0, 0), (int(self.x + 25), int(self.y + 15)), 2)

    def move(self, drop: bool = False):
        if drop:
            self.y += GameConfig.ENEMY_DROP
        else:
            self.x += self.speed * self.direction


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT))
        pygame.display.set_caption("Space Invaders")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.reset_game()

    def reset_game(self):
        self.player = Player(GameConfig.SCREEN_WIDTH // 2, GameConfig.SCREEN_HEIGHT - 100)
        self.enemies = []
        self.power_ups = []
        self.score = 0
        self.level = 1
        self.game_over = False
        self.win_condition = False
        self.setup_enemies()

    def setup_enemies(self):
        for row in range(GameConfig.ENEMY_ROWS):
            for col in range(GameConfig.ENEMIES_PER_ROW):
                x = 100 + col * 80
                y = 50 + row * 60
                self.enemies.append(Enemy(x, y))

    def handle_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.player.move(-1)
        if keys[pygame.K_RIGHT]:
            self.player.move(1)
        if keys[pygame.K_SPACE]:
            self.player.shoot()

    def update_enemies(self):
        move_down = False
        for enemy in self.enemies:
            if (enemy.x <= 0 and enemy.direction < 0) or \
                    (enemy.x >= GameConfig.SCREEN_WIDTH - enemy.width and enemy.direction > 0):
                move_down = True
                break

        if move_down:
            for enemy in self.enemies:
                enemy.direction *= -1
                enemy.move(drop=True)
        else:
            for enemy in self.enemies:
                enemy.move()

    def update_power_ups(self):
        if random.random() < GameConfig.BONUS_SPAWN_CHANCE:
            x = random.randint(0, GameConfig.SCREEN_WIDTH - 20)
            self.power_ups.append(PowerUp(x, 0))

        for power_up in self.power_ups[:]:
            power_up.update()
            if power_up.y > GameConfig.SCREEN_HEIGHT:
                self.power_ups.remove(power_up)
            elif power_up.get_rect().colliderect(self.player.get_rect()):
                self.player.activate_power_up(power_up.type)
                self.power_ups.remove(power_up)

    def check_collisions(self):
        for bullet in self.player.bullets[:]:
            bullet_rect = bullet.get_rect()
            for enemy in self.enemies[:]:
                if bullet_rect.colliderect(enemy.get_rect()):
                    if enemy in self.enemies:  # Extra check to prevent error
                        self.enemies.remove(enemy)
                        self.player.bullets.remove(bullet)
                        self.score += 100
                        break

        if not self.player.shield:  # Check enemy collisions only if not shielded
            for enemy in self.enemies:
                if enemy.get_rect().colliderect(self.player.get_rect()):
                    self.game_over = True

    def check_win_condition(self):
        if not self.enemies:
            if self.level < 3:
                self.level += 1
                GameConfig.ENEMY_SPEED += 0.5
                self.setup_enemies()
            else:
                self.win_condition = True

    def draw(self):
        self.screen.fill((0, 0, 20))

        if self.win_condition:
            win_text = self.font.render("Congratulations! You Won!", True, (0, 255, 0))
            score_text = self.font.render(f"Final Score: {self.score}", True, (255, 255, 255))
            exit_text = self.font.render("Press ESC to exit", True, (255, 255, 255))

            center_x = GameConfig.SCREEN_WIDTH // 2
            self.screen.blit(win_text, (center_x - win_text.get_width() // 2, 200))
            self.screen.blit(score_text, (center_x - score_text.get_width() // 2, 300))
            self.screen.blit(exit_text, (center_x - exit_text.get_width() // 2, 400))
        elif self.game_over:
            game_over_text = self.font.render("GAME OVER", True, (255, 0, 0))
            score_text = self.font.render(f"Final Score: {self.score}", True, (255, 255, 255))
            exit_text = self.font.render("Press ESC to exit", True, (255, 255, 255))

            center_x = GameConfig.SCREEN_WIDTH // 2
            self.screen.blit(game_over_text, (center_x - game_over_text.get_width() // 2, 200))
            self.screen.blit(score_text, (center_x - score_text.get_width() // 2, 300))
            self.screen.blit(exit_text, (center_x - exit_text.get_width() // 2, 400))
        else:
            self.player.draw(self.screen)
            for bullet in self.player.bullets:
                bullet.draw(self.screen)
            for enemy in self.enemies:
                enemy.draw(self.screen)
            for power_up in self.power_ups:
                power_up.draw(self.screen)

            # HUD
            score_text = f"Score: {self.score}"
            level_text = f"Level: {self.level}"
            score_surface = self.font.render(score_text, True, (255, 255, 255))
            level_surface = self.font.render(level_text, True, (255, 255, 255))
            self.screen.blit(score_surface, (10, 10))
            self.screen.blit(level_surface, (GameConfig.SCREEN_WIDTH - 120, 10))

            if self.player.current_power_up:
                power_up_text = f"Power-up: {self.player.current_power_up.replace('_', ' ').title()} ({self.player.power_up_timer // 60}s)"
                power_up_surface = self.font.render(power_up_text, True, (255, 255, 255))
                self.screen.blit(power_up_surface, (10, 50))

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            self.clock.tick(GameConfig.FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

            if not self.game_over and not self.win_condition:
                self.handle_input()
                self.player.update()
                self.update_enemies()
                self.update_power_ups()
                self.check_collisions()
                self.check_win_condition()

            self.draw()

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()