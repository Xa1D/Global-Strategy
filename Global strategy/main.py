import pygame
import sys
from game import Game
from MenuUI import MenuUI
from ui_config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

def main():
    state = "menu"
    game = None 
    menu_ui = MenuUI()
    pending_map = None
    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if state == "menu":
                result = menu_ui.handle_menu_event(event)
                if result == "play":
                    state = "map_selection"
                elif result == "quit":
                    pygame.quit()
                    sys.exit()
            elif state == "map_selection":
                result = menu_ui.select_map(event)
                if result in ("Europe", "Asia", "Africa"):
                    pending_map = result
                    state = "ai_selection"
            elif state == "ai_selection":
                count = menu_ui.select_ai_count(event)
                if count:
                    filename = {"Europe": "europe_coordinates.json", "Asia": "asia_coordinates.json", "Africa": "africa_coordinates.json"}[pending_map]
                    try:
                        game = Game(screen, filename, clock, ai_count=count)
                        state = "game"
                    except (RuntimeError, ValueError) as error:
                        print(f"Could not start game: {error}")
                        game = None
                        state = "menu"
            elif state == "game":   
                result = game.handle_event(event)
                if result == "pause":
                    game.start_pause = pygame.time.get_ticks()
                    state = "paused"
                if result == "menu":
                    game = None
                    state = "menu"
            elif state == "paused":
                result = menu_ui.handle_pause_event(event)
                if result == "continue":
                    if game.start_pause is not None:
                        paused_duration = pygame.time.get_ticks() - game.start_pause
                        game.shift_timers(paused_duration)
                        game.start_pause = None
                    state = "game"
                elif result == "new_game":
                    state = "map_selection"
                elif result == "rules":
                    state = "rules"
                elif result == "menu":
                    state = "menu"
            elif state == "rules":
                result = menu_ui.handle_rules_event(event)
                if result == "back":
                    state = "paused"
        if state == "menu":
            menu_ui.draw_menu(screen)
        elif state == "map_selection":
            menu_ui.draw_map_selection(screen)
        elif state == "ai_selection":
            menu_ui.draw_ai_selection(screen)
        elif state == "game":
            game.update(events)
            game.draw()
        elif state == "paused":
            menu_ui.draw_pause_screen(screen)
        elif state == "rules":
            menu_ui.draw_rules_screen(screen)
        clock.tick(FPS)
        pygame.display.update()

if __name__ == "__main__":
    main()