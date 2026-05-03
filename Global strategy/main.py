import pygame
import sys
from game import Game
from ui import UI
pygame.init()

screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()

def main():
    state = "menu"
    game = None 
    ui = UI()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if state == "menu":
                result = ui.handle_menu_event(event)
                if result == "play":
                        game = Game(screen, clock)
                        state = "game"
                elif result == "quit":
                    pygame.quit()
                    sys.exit()
            elif state == "game":   
                result = game.handle_event(event)
                if result == "pause":
                    state = "paused"
                if result == "menu":
                    state = "menu"
            elif state == "paused":
                result = ui.handle_pause_event(event)
                if result == "continue":
                    state = "game"
                elif result == "new_game":
                    game = Game(screen, clock)
                    state = "game"
                elif result == "menu":
                    state = "menu"
        if state == "menu":
            ui.draw_menu(screen)
        elif state == "game":
            game.update()
            game.draw()
        elif state == "paused":
            ui.draw_pause(screen)
        pygame.display.update()
        clock.tick(60)

if __name__ == "__main__":
    main()