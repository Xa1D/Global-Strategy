import pygame
import sys
from game import Game
from GUI import Button
pygame.init()
pygame.mixer.init()
pygame.font.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
font = pygame.font.SysFont("cambria", 60)
play_img = pygame.image.load("assets/Play Rect.png").convert_alpha()
quit_img = pygame.image.load("assets/Quit Rect.png").convert_alpha()
PLAY_BUTTON = Button("PLAY", (640, 300), font, "white", "white", play_img)
QUIT_BUTTON = Button("QUIT", (640, 450), font, "white", "white", quit_img)
CONTINUE_BUTTON = Button("CONTINUE", (640, 300), font, "white", "white", play_img)
NEW_GAME_BUTTON = Button("NEW GAME", (640, 420), font, "white", "white", play_img)
MENU_QUIT_BUTTON = Button("QUIT", (640, 540), font, "white", "white", quit_img)

def draw_menu():
    screen.fill("black")
    mouse_pos = pygame.mouse.get_pos()
    text = font.render("MAIN MENU", True, "white")
    screen.blit(text, text.get_rect(center=(640, 100)))
    for button in [PLAY_BUTTON, QUIT_BUTTON]:
        button.hover_colour(mouse_pos)
        button.update(screen)

def draw_pause():
    screen.fill("black")
    mouse_pos = pygame.mouse.get_pos()
    text = font.render("PAUSED", True, "white")
    screen.blit(text, text.get_rect(center=(640, 150)))
    for button in [CONTINUE_BUTTON, NEW_GAME_BUTTON, MENU_QUIT_BUTTON]:
        button.hover_colour(mouse_pos)
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
                        game = Game(screen, clock, 1280, 720)
                        state = "game"
                    elif QUIT_BUTTON.rect.collidepoint(mouse_pos):
                        pygame.quit()
                        sys.exit()
            elif state == "game":   
                result = game.handle_event(event)
                if result == "pause":
                    state = "paused"
                if result == "menu":
                    state = "menu"
            elif state == "paused":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if CONTINUE_BUTTON.rect.collidepoint(mouse_pos):
                        state = "game"
                    elif NEW_GAME_BUTTON.rect.collidepoint(mouse_pos):
                        game = Game(screen, clock, 1280, 720)
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
            draw_pause()
        pygame.display.update()
        clock.tick(60)

if __name__ == "__main__":
    main()