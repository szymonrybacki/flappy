import pygame
import random
import sys
import os

# Inicjalizacja Pygame
pygame.init()

# Stałe gry
SCREEN_WIDTH = 288
SCREEN_HEIGHT = 512
GRAVITY = 0.25
BIRD_JUMP = -7
PIPE_SPEED = 3
PIPE_GAP = 150
PIPE_FREQUENCY = 1500  # ms

# Kolory
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

class AssetLoader:
    def __init__(self):
        self.images = {}
        
    def load_images(self):
        try:
            self.images["background"] = pygame.image.load("background.png").convert()
            self.images["bird"] = pygame.image.load("bird.png").convert_alpha()
            self.images["pipe"] = pygame.image.load("pipe.png").convert_alpha()
        except:
            # Tworzenie placeholderów jeśli ładowanie się nie powiedzie
            self._create_placeholders()

class Bird:
    def __init__(self, image):
        self.x = 100
        self.y = SCREEN_HEIGHT // 2
        self.velocity = 0
        self.image = image
        self.rect = self.image.get_rect(center=(self.x, self.y))
        
    def update(self):
        self.velocity += GRAVITY
        self.y += self.velocity
        self.rect.center = (self.x, self.y)
        
        if self.y > SCREEN_HEIGHT:
            self.y = SCREEN_HEIGHT
            self.velocity = 0
        if self.y < 0:
            self.y = 0
            self.velocity = 0
            
    def jump(self):
        self.velocity = BIRD_JUMP
        
    def draw(self, screen):
        screen.blit(self.image, self.rect)

class Pipe:
    def __init__(self, image):
        self.x = SCREEN_WIDTH
        self.height = random.randint(100, SCREEN_HEIGHT - 100 - PIPE_GAP)
        self.passed = False
        self.image_top = pygame.transform.flip(image, False, True)
        self.image_bottom = image
        self.rect_top = self.image_top.get_rect(topleft=(self.x, self.height - self.image_top.get_height()))
        self.rect_bottom = self.image_bottom.get_rect(topleft=(self.x, self.height + PIPE_GAP))
        
    def update(self):
        self.x -= PIPE_SPEED
        self.rect_top.x = self.x
        self.rect_bottom.x = self.x
        
    def draw(self, screen):
        screen.blit(self.image_top, self.rect_top)
        screen.blit(self.image_bottom, self.rect_bottom)
        
    def collide(self, bird):
        return self.rect_top.colliderect(bird.rect) or self.rect_bottom.colliderect(bird.rect)

def main():
    # Inicjalizacja ekranu - TERAZ NA SAMYM POCZĄTKU
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('Flappy Bird')
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('Arial', 30)
    
    # Ładowanie zasobów PO inicjalizacji ekranu
    assets = AssetLoader()
    assets.load_images()
    
    bird = Bird(assets.images["bird"])
    pipes = []
    score = 0
    try:
        with open("best.txt", "r") as f:
            best = int(f.read())
    except:
        best = 0 
    last_pipe = pygame.time.get_ticks()
    game_over = False
    
    while True:
        clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game_over:
                    bird.jump()
                if event.key == pygame.K_SPACE and game_over:
                    # Restart gry
                    bird = Bird(assets.images["bird"])
                    pipes = []
                    score = 0
                    last_pipe = pygame.time.get_ticks()
                    game_over = False
        
        if not game_over:
            bird.update()
            
            time_now = pygame.time.get_ticks()
            if time_now - last_pipe > PIPE_FREQUENCY:
                pipes.append(Pipe(assets.images["pipe"]))
                last_pipe = time_now
                
            for pipe in pipes:
                pipe.update()
                
                if pipe.collide(bird):
                    game_over = True
                
                if pipe.x + pipe.rect_top.width < bird.x and not pipe.passed:
                    pipe.passed = True
                    score += 1
                    
            pipes = [pipe for pipe in pipes if pipe.x > -pipe.rect_top.width]
        
        # Rysowanie
        screen.blit(assets.images["background"], (0, 0))
        
        for pipe in pipes:
            pipe.draw(screen)
            
        bird.draw(screen)
        
        score_text = font.render(f'Score: {score}', True, BLACK)
        screen.blit(score_text, (10, 10))
        best_text = font.render(f'Record: {best}', True, BLACK)
        screen.blit(best_text, (10, 40))
        
        if game_over:
            game_over_text = font.render('Game Over! Press SPACE to restart', True, BLACK)
            screen.blit(game_over_text, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2))
            if score > best:
                best = score
                with open("best.txt", "w") as f:
                    f.write(str(best))
        
        pygame.display.update()

if __name__ == "__main__":
    main()