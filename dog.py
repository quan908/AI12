import pygame
import random
import pygame_gui
from enum import Enum

WIDTH, HEIGHT = 800, 600
NUM_AGENTS = 1
DOG_SIZE = 20
FOOD_SIZE = 10
BALL_SIZE = 15
MAX_SPEED = 2

SLEEP_AREA = pygame.Rect(WIDTH - 150, HEIGHT - 150, 100, 100)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
manager = pygame_gui.UIManager((WIDTH, HEIGHT))

dog_sprite_sheet = pygame.image.load('./assets/DogSprites.png').convert_alpha()
dog_walk_animation = [dog_sprite_sheet.subsurface(pygame.Rect(x * 100, 0, 100, 100)) for x in range(6)]
dog_play_animation = [dog_sprite_sheet.subsurface(pygame.Rect(x * 100, 100, 100, 100)) for x in range(6)]
dog_sleep_animation = [dog_sprite_sheet.subsurface(pygame.Rect(x * 100, 200, 100, 100)) for x in range(6)]

FRAME_RATE = 0.4
font = pygame.font.Font(None, 30)

class DogState(Enum):
    WALKING = 0
    SLEEPING = 1
    PLAYING = 2
    GET_FOOD = 3

class Food:
    def __init__(self, position):
        self.position = position

    def draw(self, screen):
        pygame.draw.circle(screen, (255, 0, 0), (int(self.position.x), int(self.position.y)), FOOD_SIZE)

class Dog:
    def __init__(self):
        self.position = pygame.Vector2(random.uniform(0, WIDTH), random.uniform(0, HEIGHT))
        self.velocity = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() * MAX_SPEED
        self.frame_index = 0

        self.current_state = DogState.WALKING
        self.current_animation = dog_walk_animation

        self.sleepiness = random.randint(0, 100)
        self.happiness = random.randint(0, 100)
        self.hunger = random.randint(0, 100)

        self.stat_timer = 0
        self.play_timer = 0
        self.playing_ball = None  # Track the ball when playing

    def update(self, food_list, delta_time):
        self.stat_timer += delta_time
        if self.stat_timer >= 5.0:
            self.increase_stats()
            self.stat_timer = 0

        if self.current_state == DogState.WALKING:
            self.random_walk()
            if self.sleepiness > 51:
                self.current_state = DogState.SLEEPING
                self.current_animation = dog_sleep_animation
            elif self.happiness > 76:
                self.current_state = DogState.PLAYING
                self.current_animation = dog_play_animation
                self.playing_ball = Ball(self.position + pygame.Vector2(0, -DOG_SIZE))  # Spawn the ball above the dog
                self.play_timer = 3.0  # Start 3-second timer for playing
            elif self.hunger > 51 and food_list:
                self.current_state = DogState.GET_FOOD

        elif self.current_state == DogState.SLEEPING:
            self.move_to_sleep_area()
            if self.position.distance_to(pygame.Vector2(SLEEP_AREA.center)) < 5:
                self.sleepiness = 0
                self.current_state = DogState.WALKING
                self.current_animation = dog_walk_animation

        elif self.current_state == DogState.PLAYING:
            self.play_timer -= delta_time
            if self.play_timer <= 0:
                self.happiness = 0  # Reset happiness
                self.current_state = DogState.WALKING
                self.current_animation = dog_walk_animation
                self.playing_ball = None  # Remove the ball after playing

        elif self.current_state == DogState.GET_FOOD:
            nearest_food = min(food_list, key=lambda food: self.position.distance_to(food.position))
            self.move_towards(nearest_food.position)
            if self.position.distance_to(nearest_food.position) < FOOD_SIZE:
                self.hunger = 0
                food_list.remove(nearest_food)
                self.current_state = DogState.WALKING
                self.current_animation = dog_walk_animation

        self.wrap_around()

    def random_walk(self):
        self.velocity.x = random.uniform(-1, 1) * MAX_SPEED
        self.velocity.y = random.uniform(-1, 1) * MAX_SPEED
        self.position += self.velocity

    def move_to_sleep_area(self):
        target = pygame.Vector2(SLEEP_AREA.center)
        direction = (target - self.position).normalize() * MAX_SPEED
        self.position += direction

    def move_towards(self, target_position):
        direction = (target_position - self.position).normalize() * MAX_SPEED
        self.position += direction

    def increase_stats(self):
        self.sleepiness = min(self.sleepiness + 5, 100)
        self.happiness = min(self.happiness + 5, 100)
        self.hunger = min(self.hunger + 5, 100)

    def wrap_around(self):
        if self.position.x > WIDTH:
            self.position.x = 0
        elif self.position.x < 0:
            self.position.x = WIDTH
        if self.position.y > HEIGHT:
            self.position.y = 0
        elif self.position.y < 0:
            self.position.y = HEIGHT

    def draw(self, screen):
        self.frame_index = (self.frame_index + FRAME_RATE) % len(self.current_animation)
        current_frame = self.current_animation[int(self.frame_index)]
        screen.blit(current_frame, (int(self.position.x) - DOG_SIZE // 2, int(self.position.y) - DOG_SIZE // 2))

        if self.playing_ball:
            self.playing_ball.draw(screen)  # Draw the ball if playing

    def draw_stats(self, screen):
        stats_text = f"Sleepiness: {self.sleepiness}\nHappiness: {self.happiness}\nHunger: {self.hunger}"
        y_offset = 10
        for line in stats_text.split('\n'):
            text_surface = font.render(line, True, (255, 255, 255))
            screen.blit(text_surface, (WIDTH - text_surface.get_width() - 10, y_offset))
            y_offset += text_surface.get_height() + 5

class Ball:
    def __init__(self, position):
        self.position = position

    def draw(self, screen):
        pygame.draw.circle(screen, (0, 0, 255), (int(self.position.x), int(self.position.y)), BALL_SIZE)

def main():
    dogs = [Dog() for _ in range(NUM_AGENTS)]
    food_list = []

    clock = pygame.time.Clock()
    running = True
    while running:
        delta_time = clock.tick(60) / 1000.0
        screen.fill((100, 100, 100))
        manager.update(delta_time)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                food_list.append(Food(pygame.Vector2(event.pos)))
            manager.process_events(event)

        pygame.draw.rect(screen, (50, 205, 50), SLEEP_AREA)

        for dog in dogs:
            dog.update(food_list, delta_time)
            dog.draw(screen)
            dog.draw_stats(screen)

        for food in food_list:
            food.draw(screen)

        manager.draw_ui(screen)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
