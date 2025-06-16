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
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)

# --- Klasy i funkcje pomocnicze ---

class AssetLoader:
    """Klasa do ładowania wszystkich zasobów gry."""
    def __init__(self):
        self.images = {}
        self.fonts = {}
        
    def load(self):
        try:
            self.images["background"] = pygame.image.load("background.png").convert()
            # ZMIANA: Ładowanie i skalowanie tła menu
            menu_bg_raw = pygame.image.load("tlo2.png").convert()
            self.images["menu_background"] = pygame.transform.scale(menu_bg_raw, (SCREEN_WIDTH, SCREEN_HEIGHT))
            
            self.images["bird_frames"] = [
                pygame.image.load("yellowbird-downflap.png").convert_alpha(),
                pygame.image.load("bird.png").convert_alpha(),
                pygame.image.load("yellowbird-upflap.png").convert_alpha()
            ]
            self.images["pipe"] = pygame.image.load("pipe.png").convert_alpha()
            
            # ZMIANA: Zmniejszenie rozmiarów czcionek, aby pasowały do interfejsu
            self.fonts["menu"] = pygame.font.Font("Pacifico-Regular.ttf", 30)
            self.fonts["button"] = pygame.font.Font("Pacifico-Regular.ttf", 25)
            self.fonts["label"] = pygame.font.Font("Pacifico-Regular.ttf", 20)
            self.fonts["score"] = pygame.font.Font("Pacifico-Regular.ttf", 35)

        except pygame.error as e:
            print(f"Błąd ładowania zasobów: {e}. Używam zasobów domyślnych.")
            self._create_placeholders()

    def _create_placeholders(self):
        self.images["background"] = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); self.images["background"].fill((135, 206, 235))
        self.images["menu_background"] = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); self.images["menu_background"].fill((70, 70, 70))
        bird_placeholder = pygame.Surface((34, 24)); bird_placeholder.fill((255, 255, 0))
        self.images["bird_frames"] = [bird_placeholder] * 3
        pipe_placeholder = pygame.Surface((52, 320)); pipe_placeholder.fill((0, 128, 0))
        self.images["pipe"] = pipe_placeholder
        # ZMIANA: Zmniejszone rozmiary czcionek awaryjnych
        self.fonts["menu"] = pygame.font.SysFont('Arial', 30)
        self.fonts["button"] = pygame.font.SysFont('Arial', 25)
        self.fonts["label"] = pygame.font.SysFont('Arial', 20)
        self.fonts["score"] = pygame.font.SysFont('Arial', 35)


class Bird:
    def __init__(self, frames):
        self.x = 100
        self.y = SCREEN_HEIGHT // 2
        self.velocity = 0
        self.frames = frames
        self.current_frame_index = 0
        self.image = self.frames[self.current_frame_index]
        self.animation_timer = pygame.time.get_ticks()
        self.flap_rate = 100
        self.rect = self.image.get_rect(center=(self.x, self.y))
        
    def update(self):
        self.velocity += GRAVITY
        self.y += self.velocity
        self.rect.center = (self.x, self.y)
        if self.y > SCREEN_HEIGHT: self.y = SCREEN_HEIGHT
        if self.y < 0: self.y = 0; self.velocity = 0
        self.animate()
            
    def jump(self):
        self.velocity = BIRD_JUMP
        
    def animate(self):
        if pygame.time.get_ticks() - self.animation_timer > self.flap_rate:
            self.animation_timer = pygame.time.get_ticks()
            self.current_frame_index = (self.current_frame_index + 1) % len(self.frames)
            center = self.rect.center
            self.image = self.frames[self.current_frame_index]
            self.rect = self.image.get_rect(center=center)

    def draw(self, screen):
        rotated_bird = pygame.transform.rotozoom(self.image, -self.velocity * 3, 1)
        screen.blit(rotated_bird, rotated_bird.get_rect(center=self.rect.center))

class Pipe:
    def __init__(self, image):
        self.x = SCREEN_WIDTH
        self.height = random.randint(150, SCREEN_HEIGHT - 150 - PIPE_GAP)
        self.passed = False
        self.image_top = pygame.transform.flip(image, False, True)
        self.image_bottom = image
        self.rect_top = self.image_top.get_rect(midbottom=(self.x, self.height))
        self.rect_bottom = self.image_bottom.get_rect(midtop=(self.x, self.height + PIPE_GAP))
        
    def update(self):
        self.x -= PIPE_SPEED
        self.rect_top.x = self.x
        self.rect_bottom.x = self.x
        
    def draw(self, screen):
        screen.blit(self.image_top, self.rect_top)
        screen.blit(self.image_bottom, self.rect_bottom)
        
    def collide(self, bird):
        return self.rect_top.colliderect(bird.rect) or self.rect_bottom.colliderect(bird.rect)

def load_scores():
    scores = []
    try:
        with open("scores.txt", "r") as f:
            for line in f:
                try:
                    score, name = line.strip().split(";")
                    scores.append((int(score), name))
                except ValueError:
                    continue
    except FileNotFoundError:
        return []
    scores.sort(key=lambda x: x[0], reverse=True)
    return scores

def save_score(new_score, new_name):
    scores = load_scores()
    scores.append((new_score, new_name))
    scores.sort(key=lambda x: x[0], reverse=True)
    scores = scores[:10]
    with open("scores.txt", "w") as f:
        for score, name in scores:
            f.write(f"{score};{name}\n")

# --- Główne pętle stanów gry ---

def run_menu(screen, clock, assets, player_name):
    input_box = pygame.Rect(SCREEN_WIDTH // 2 - 125, 120, 250, 40)
    play_button = pygame.Rect(SCREEN_WIDTH // 2 - 100, 190, 200, 50)
    scores_button = pygame.Rect(SCREEN_WIDTH // 2 - 100, 260, 200, 50)
    exit_button = pygame.Rect(SCREEN_WIDTH // 2 - 100, 330, 200, 50)
    input_active = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "EXIT", player_name
            if event.type == pygame.MOUSEBUTTONDOWN:
                input_active = bool(input_box.collidepoint(event.pos))
                if play_button.collidepoint(event.pos): return "GAME", player_name if player_name else "Player"
                if scores_button.collidepoint(event.pos): return "HIGH_SCORES", player_name
                if exit_button.collidepoint(event.pos): return "EXIT", player_name
            if event.type == pygame.KEYDOWN and input_active:
                if event.key == pygame.K_RETURN: input_active = False
                elif event.key == pygame.K_BACKSPACE: player_name = player_name[:-1]
                else: player_name += event.unicode

        screen.blit(assets.images["menu_background"], (0, 0))
        pygame.draw.rect(screen, GRAY if input_active else DARK_GRAY, input_box, border_radius=10)
        text_surface = assets.fonts["button"].render(player_name, True, WHITE)
        screen.blit(text_surface, (input_box.x + 10, input_box.y + 5))
        pygame.draw.rect(screen, WHITE, input_box, 2, border_radius=10)
        
        label_text = assets.fonts["label"].render("Wpisz imię:", True, WHITE)
        screen.blit(label_text, (input_box.x, input_box.y - 25))

        for btn, text in [(play_button, "Graj"), (scores_button, "Top 10"), (exit_button, "Wyjdź")]:
            pygame.draw.rect(screen, DARK_GRAY, btn, border_radius=10)
            btn_text = assets.fonts["button"].render(text, True, WHITE)
            screen.blit(btn_text, btn_text.get_rect(center=btn.center))

        pygame.display.update()
        clock.tick(30)

def run_high_scores(screen, clock, assets):
    scores = load_scores()
    back_button = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 80, 200, 50)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "EXIT"
            if event.type == pygame.MOUSEBUTTONDOWN and back_button.collidepoint(event.pos): return "MENU"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return "MENU"

        screen.blit(assets.images["menu_background"], (0, 0))
        title_text = assets.fonts["menu"].render("Top 10", True, WHITE)
        screen.blit(title_text, title_text.get_rect(centerx=SCREEN_WIDTH//2, y=20))
        
        # ZMIANA: Mniejszy odstęp między wierszami
        for i, (score, name) in enumerate(scores):
            score_text = assets.fonts["label"].render(f"{i+1}. {name}: {score}", True, WHITE)
            screen.blit(score_text, (40, 90 + i * 30))

        pygame.draw.rect(screen, DARK_GRAY, back_button, border_radius=10)
        back_text = assets.fonts["button"].render("Wróć", True, WHITE)
        screen.blit(back_text, back_text.get_rect(center=back_button.center))

        pygame.display.update()
        clock.tick(30)

def run_game(screen, clock, assets, player_name):
    bird = Bird(assets.images["bird_frames"])
    pipes = []
    score = 0
    last_pipe = pygame.time.get_ticks() - PIPE_FREQUENCY
    game_over = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "EXIT"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game_over: bird.jump()
                if event.key == pygame.K_SPACE and game_over:
                    save_score(score, player_name)
                    return "MENU"

        if not game_over:
            bird.update()
            if pygame.time.get_ticks() - last_pipe > PIPE_FREQUENCY:
                pipes.append(Pipe(assets.images["pipe"]))
                last_pipe = pygame.time.get_ticks()
            for p in pipes:
                p.update()
                if p.collide(bird): game_over = True
                if p.x + p.image_top.get_width() < bird.x and not p.passed:
                    p.passed = True
                    score += 1
            pipes = [p for p in pipes if p.x > -p.image_top.get_width()]
            if bird.rect.bottom >= SCREEN_HEIGHT: game_over = True

        screen.blit(assets.images["background"], (0, 0))
        for pipe in pipes: pipe.draw(screen)
        bird.draw(screen)
        score_text = assets.fonts["score"].render(str(score), True, WHITE)
        screen.blit(score_text, score_text.get_rect(center=(SCREEN_WIDTH // 2, 50)))

        if game_over:
            over_text = assets.fonts["label"].render('Koniec Gry!', True, WHITE)
            restart_text = assets.fonts["label"].render('Naciśnij SPACJĘ by wrócić', True, WHITE)
            screen.blit(over_text, over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 20)))
            screen.blit(restart_text, restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 10)))

        pygame.display.update()
        clock.tick(60)

# --- Główny kontroler gry ---

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('Flappy Bird')
    clock = pygame.time.Clock()
    assets = AssetLoader()
    assets.load()
    player_name = "Gracz"
    game_state = "MENU"

    while game_state != "EXIT":
        if game_state == "MENU":
            game_state, player_name = run_menu(screen, clock, assets, player_name)
        elif game_state == "GAME":
            game_state = run_game(screen, clock, assets, player_name)
        elif game_state == "HIGH_SCORES":
            game_state = run_high_scores(screen, clock, assets)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()