from GUI import Sidebar, Button
import pygame 

class UI:
    def __init__(self):
        self.text_font = pygame.font.SysFont(None, 35)
        self.menu_font = pygame.font.SysFont("cambria", 60)

        self.sidebar = Sidebar(pos=(1000, 0), width=280, height=720, font=self.text_font)

        self.panel = Sidebar(pos=(350,50), width=630, height=570, font=self.text_font)
        self.panel_visible = False

        self.player_sidebar = Sidebar(pos=(0,40), width=250, height=640, font=self.text_font)
        self.player_sidebar_visible = False
        self.setup_mode = "player"
        
        self.play_img = pygame.image.load("assets/Play Rect.png").convert_alpha()
        self.quit_img = pygame.image.load("assets/Quit Rect.png").convert_alpha()

        self.play_button = Button("Play", (640, 300), self.menu_font, "white", "blue", image=self.play_img)
        self.quit_button = Button("Quit", (640, 450), self.menu_font, "white", "red", image=self.quit_img)
        self.continue_button = Button("Continue", (640, 300), self.menu_font, "white", "blue", image=self.play_img)
        self.newgame_button = Button("New Game", (640, 420), self.menu_font, "white", "blue", image=self.play_img)
        self.return_button = Button("Return", (640, 540), self.menu_font, "white", "red", image=self.quit_img)
 
        self.menu_buttons = [self.play_button, self.quit_button]
        self.option_buttons = [self.continue_button, self.newgame_button, self.return_button]

    def remove_highlight(self,world):
        for country in world.countries.values():
            country.highlighted = False

    def highlight_attack(self,selected_country,world,player):
        for name in selected_country.adjacent:
            if world.countries[name] not in player.territories and not world.countries[name].combat:
                world.countries[name].highlighted = True
        
    def highlight_move(self,selected_country,world,player):
        for name in selected_country.adjacent:
            if world.countries[name] in player.territories and not world.countries[name].combat:
                world.countries[name].highlighted = True

    def draw_setup(self,screen,world):
        screen.fill((0, 0, 0))
        world.draw(screen, None, None)
        if self.setup_mode == "player":
             text = self.text_font.render("Choose your starting country", True, (255, 255, 255))
        elif self.setup_mode == "enemy":
            text = self.text_font.render("Choose an enemy country", True, (255, 255, 255))
        rect = text.get_rect(center=(640, 100))
        screen.blit(text, rect)

    def update_sidebar(self,selected_country,player,buy_units,enter_attack,enter_move):
        self.sidebar.buttons.clear()
        self.sidebar.labels.clear()
        if selected_country:
            self.sidebar.add_text("Units", (1020, 10))
            self.sidebar.add_text(f"Infantry: {selected_country.units['infantry']}", (1020, 40))
            self.sidebar.add_text(f"Tanks: {selected_country.units['tank']}", (1020, 70))
            self.sidebar.add_text(f"Artillery: {selected_country.units['artillery']}", (1020, 100))
        if selected_country and selected_country in player.territories:
            self.sidebar.add_button("Buy Units",(1120,210), buy_units)
            self.sidebar.add_button("Attack", (1120, 270), enter_attack)
            self.sidebar.add_button("Move Units", (1120, 330), enter_move)

    def update_player_sidebar(self,player,enemy):
        if player is None:
            return 
        self.player_sidebar.buttons.clear()
        self.player_sidebar.labels.clear()
        self.player_sidebar.add_text("Player Stats", (20, 50))
        self.player_sidebar.add_text(f"Territories: {len(player.territories)}", (20, 90))
        self.player_sidebar.add_text(f"Total infantry: {sum(country.units['infantry'] for country in player.territories)}", (20, 120))
        self.player_sidebar.add_text(f"Total tanks: {sum(country.units['tank'] for country in player.territories)}", (20, 150))
        self.player_sidebar.add_text(f"Total artillery: {sum(country.units['artillery'] for country in player.territories)}", (20, 180))
        self.player_sidebar.add_text(f"Enemy territories: {len(enemy.territories)}", (20, 210))
        self.player_sidebar.add_text(f"Enemy infantry: {sum(country.units['infantry'] for country in enemy.territories)}", (20, 240))
        self.player_sidebar.add_text(f"Enemy tanks: {sum(country.units['tank'] for country in enemy.territories)}", (20, 270))
        self.player_sidebar.add_text(f"Enemy artillery: {sum(country.units['artillery'] for country in enemy.territories)}", (20, 300))
        self.player_sidebar.add_text(f"Enemy income: {enemy.income}", (20, 330))
        self.player_sidebar.add_text(f"Enemy currency: {enemy.currency}", (20, 360))

    def close_panel(self):
        self.panel_visible = False

    def open_move_info(self):
        self.panel.buttons.clear()
        self.panel.labels.clear()
        self.panel.add_text("Select amount and type of units to move", (370, 60))
        self.panel.add_button("Move Infantry", (480, 150), None)
        self.panel.add_button("Move Tank", (480, 230), None)
        self.panel.add_button("Move Artillery", (480, 310), None)
        self.panel.add_button("Back         ", (480, 410), self.close_panel)

    def open_attack_info(self):
        self.panel.buttons.clear()
        self.panel.labels.clear()
        self.panel.add_text("Select amount and type of units to attack with", (400, 60))
        self.panel.add_button("Infantry  ", (480, 150), None)
        self.panel.add_button("Tank      ", (480, 230), None)
        self.panel.add_button("Artillery ", (480, 310), None)
        self.panel.add_text(f"Infantry:         Tank:       Artillery:", (400, 385))
        self.panel.add_button("Confirm Attack", (480, 460), None)
        self.panel.add_button("Back          ", (480, 550), self.close_panel)

    def open_units_info(self,buy_infantry,buy_tank,buy_artillery):
        self.panel.buttons.clear()
        self.panel.labels.clear()
        self.panel.add_text("Select type of unit to buy:", (400, 60))
        self.panel.add_button("Buy Infantry  (5) ", (480, 150), buy_infantry)
        self.panel.add_button("Buy Tank      (15)", (480, 230), buy_tank)
        self.panel.add_button("Buy Artillery (20)", (480, 310), buy_artillery)
        self.panel.add_button("Back              ", (480, 410), self.close_panel)

    
    def draw_result(self,screen,game_result):
        background = pygame.Surface((1280, 720))
        background.set_alpha(180)
        background.fill((0, 0, 0))
        screen.blit(background, (0, 0))
        if game_result == "win":
            text = self.text_font.render("You Win", True, ("green"))
        else:
            text = self.text_font.render("You Lose", True, ("red"))
        rect = text.get_rect(center=(640, 300))
        screen.blit(text, rect)
        subtext = self.text_font.render("Click to return to menu", True, (255, 255, 255))
        screen.blit(subtext, subtext.get_rect(center=(640, 400)))

    def draw_player_stats(self,player,screen):
        currency_text = self.text_font.render(f"Currency: {player.currency}", True, (255, 255, 255))
        income_text = self.text_font.render(f"Income: {player.income}", True, (255, 255, 255))
        screen.blit(currency_text, (250, 10))
        screen.blit(income_text, (500, 10))
        
    def draw_fps(self,clock,screen):
        fps_text = self.text_font.render(f"FPS: {int(clock.get_fps())}", True, (255, 255, 255))
        screen.blit(fps_text, (50, 10))

    def draw_menu(self,screen):
        screen.fill("black")
        text = self.menu_font.render("MAIN MENU", True, "white")
        screen.blit(text, text.get_rect(center=(640, 150)))
        for button in self.menu_buttons:
            button.update(screen)

    def draw_pause(self,screen):
        screen.fill("black")
        text = self.menu_font.render("PAUSED", True, "white")
        screen.blit(text, text.get_rect(center=(640, 150)))
        for button in self.option_buttons:
            button.update(screen)

    def handle_menu_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return None
        mouse_pos = pygame.mouse.get_pos()
        if self.play_button.rect.collidepoint(mouse_pos):
            return "play"
        if self.quit_button.rect.collidepoint(mouse_pos):
            return "quit"
        return None

    def handle_pause_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return None
        mouse_pos = pygame.mouse.get_pos()
        if self.continue_button.rect.collidepoint(mouse_pos):
            return "continue"
        if self.newgame_button.rect.collidepoint(mouse_pos):
            return "new_game"
        if self.return_button.rect.collidepoint(mouse_pos):
            return "menu"
        return None

    def draw(self,screen,world,state,selected_country,player,enemy,game_result):
        screen.fill((0, 0, 0))
        if state == "setup":
            self.draw_setup(screen, world)
            return
        else:
            world.draw(screen,player,enemy)
        if self.panel_visible:
            self.panel.draw(screen)
        if selected_country:
            self.sidebar.draw(screen)
        if player:
            self.draw_player_stats(player, screen)
        if self.player_sidebar_visible:
            self.player_sidebar.draw(screen)
        if state == "game_over":
           self.draw_result(screen, game_result)