import pygame
import sys
from game import Game
from GUI import Button
pygame.init()
pygame.mixer.init()
pygame.font.init()
WIDTH = 1280
HEIGHT = 720
window_size = pygame.Vector2(WIDTH, HEIGHT)
screen = pygame.display.set_mode(window_size)
clock = pygame.time.Clock()
font = pygame.font.SysFont("cambria", 60)
play_img = pygame.image.load("assets/Play Rect.png").convert_alpha()
options_img = pygame.image.load("assets/Options Rect.png").convert_alpha()
quit_img = pygame.image.load("assets/Quit Rect.png").convert_alpha()
PLAY_BUTTON = Button("PLAY", (640, 250), font, "#d7fcd4", "white", play_img)
OPTIONS_BUTTON = Button("OPTIONS", (640, 400), font, "#d7fcd4", "white", options_img)
QUIT_BUTTON = Button("QUIT", (640, 550), font, "#d7fcd4", "white", quit_img)
CONTINUE_BUTTON = Button("CONTINUE", (640, 300), font, "#d7fcd4", "white", play_img)
NEW_GAME_BUTTON = Button("NEW GAME", (640, 420), font, "#d7fcd4", "white", options_img)
MENU_QUIT_BUTTON = Button("QUIT", (640, 540), font, "#d7fcd4", "white", quit_img)

def draw_menu():
    screen.fill("black")
    mouse_pos = pygame.mouse.get_pos()
    text = font.render("MAIN MENU", True, "#b68f40")
    screen.blit(text, text.get_rect(center=(640, 100)))
    for button in [PLAY_BUTTON, OPTIONS_BUTTON, QUIT_BUTTON]:
        button.changeColor(mouse_pos)
        button.update(screen)

def draw_pause_menu():
    screen.fill("black")
    mouse_pos = pygame.mouse.get_pos()
    text = font.render("PAUSED", True, "#b68f40")
    screen.blit(text, text.get_rect(center=(640, 150)))
    for button in [CONTINUE_BUTTON, NEW_GAME_BUTTON, MENU_QUIT_BUTTON]:
        button.changeColor(mouse_pos)
        button.update(screen)

def main():
    state = "menu"
    game = None 
    while True:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if state == "menu":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if PLAY_BUTTON.rect.collidepoint(mouse_pos):
                        game = Game(screen, clock, window_size)
                        state = "game"
                    elif QUIT_BUTTON.rect.collidepoint(mouse_pos):
                        pygame.quit()
                        sys.exit()
            elif state == "game":   
                result = game.handle_event(event)
                if result == "pause":
                    state = "paused"
            elif state == "paused":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if CONTINUE_BUTTON.rect.collidepoint(mouse_pos):
                        state = "game"
                    elif NEW_GAME_BUTTON.rect.collidepoint(mouse_pos):
                        game = Game(screen, clock, window_size)
                        state = "game"
                    elif MENU_QUIT_BUTTON.rect.collidepoint(mouse_pos):
                        state = "menu"
        if state == "menu":
            draw_menu()
        elif state == "game":
            game.update()
            game.draw()
        elif state == "paused":
            game.draw()
            draw_pause_menu()
        pygame.display.update()
        clock.tick(60)

if __name__ == "__main__":
    main()