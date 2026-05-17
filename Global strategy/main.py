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
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if state == "menu":
                result = ui.handle_menu_event(event)
                if result == "play":
                    state = "map_selection"
                elif result == "quit":
                    pygame.quit()
                    sys.exit()
            elif state == "map_selection":
              result = ui.select_map(event)
              if result == "Europe":
                  game = Game(screen,"europe_coords.json",clock)
                  state = "game"
              elif result == "Asia":
                  game = Game(screen,"asia_coords.json",clock)
                  state = "game"
              elif result == "Africa":
                  game = Game(screen,"africa_coords.json",clock)
                  state = "game"
            elif state == "game":   
                result = game.handle_event(event)
                if result == "pause":
                    state = "paused"
                if result == "menu":
                    game = None
                    state = "menu"
            elif state == "paused":
                result = ui.handle_pause_event(event)
                if result == "continue":
                    state = "game"
                elif result == "new_game":
                    state = "map_selection"
                elif result == "menu":
                    state = "menu"
        if state == "menu":
            ui.draw_menu(screen)
        elif state == "map_selection":
            ui.draw_map_selection(screen)
        elif state == "game":
            game.update(event)
            game.draw()
        elif state == "paused":
            ui.draw_pause(screen)
        clock.tick(60)
        pygame.display.update()

if __name__ == "__main__":
    main()