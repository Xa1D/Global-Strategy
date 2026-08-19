from GUI import Sidebar, Button
import pygame 

class UI:
    def __init__(self):
        self.clock = pygame.time.Clock()
        self.text_font = pygame.font.SysFont("Roboto", 32)
        self.menu_font = pygame.font.SysFont("cambria", 60)
        self.result_font = pygame.font.SysFont("Roboto",32)
        self.background_font = pygame.font.SysFont("Roboto", 20)

        self.sidebar = Sidebar(pos=(1000, 0), width=280, height=720, font=self.text_font)
        self.sidebar_visible = False

        self.panel = Sidebar(pos=(350,50), width=650, height=590, font=self.text_font)
        self.panel_visible = False

        self.background_panel = Sidebar(pos=(350,50), width=650, height=620, font=self.background_font)
        self.background_panel_visible = False

        self.player_sidebar = Sidebar(pos=(0,50), width=250, height=570, font=self.text_font)
        self.player_sidebar_visible = False
        self.setup_mode = "player"
        
        self.play_img = pygame.image.load("assets/Play Rect.png").convert_alpha()
        self.quit_img = pygame.image.load("assets/Quit Rect.png").convert_alpha()

        self.play_button = Button("Play", (640, 300), self.menu_font, "white", "blue", image=self.play_img)
        self.quit_button = Button("Quit", (640, 450), self.menu_font, "white", "red", image=self.quit_img)
        self.continue_button = Button("Continue", (640, 300), self.menu_font, "white", "blue", image=self.play_img)
        self.newgame_button = Button("New Game", (640, 420), self.menu_font, "white", "blue", image=self.play_img)
        self.return_button = Button("Return", (640, 540), self.menu_font, "white", "red", image=self.quit_img)

        self.europe_button = Button("Europe", (640, 250), self.menu_font, "white", "blue", image=self.play_img)
        self.asia_button = Button("Asia", (640, 385), self.menu_font, "white", "blue", image=self.play_img)
        self.africa_button = Button("Africa", (640, 510), self.menu_font, "white", "blue", image=self.play_img)

        self.enemy_count = 1
        self.enemies_placed = 0
        
        self.one_ai_button = Button("1 AI", (640, 250), self.menu_font, "white", "blue", image=self.play_img)
        self.two_ai_button = Button("2 AI", (640, 385), self.menu_font, "white", "blue", image=self.play_img)
        self.three_ai_button = Button("3 AI", (640, 510), self.menu_font, "white", "blue", image=self.play_img)
        
        self.menu_buttons = [self.play_button, self.quit_button]
        self.option_buttons = [self.continue_button, self.newgame_button, self.return_button]
        self.map_buttons = [self.europe_button,self.asia_button,self.africa_button]
        self.ai_count_buttons = [self.one_ai_button, self.two_ai_button, self.three_ai_button]

    def remove_highlight(self,map):
        for country in map.countries.values():
            country.highlighted = False

    def highlight_attack(self,selected_country,map,player):
        for name in selected_country.adjacent:
            if map.countries[name] not in player.territories and not map.countries[name].combat:
                map.countries[name].highlighted = True
        
    def highlight_move(self,selected_country,map,player):
        for name in selected_country.adjacent:
            if map.countries[name] in player.territories and not map.countries[name].combat:
                map.countries[name].highlighted = True

    def draw_setup(self,screen,map_display):
        screen.fill((0, 0, 0))
        map_display.draw(None, [])
        if self.setup_mode == "player":
             text = self.text_font.render("Choose your starting country", True, (255, 255, 255))
        else:
            text = self.text_font.render(f"Choose enemy {self.enemies_placed + 1} of {self.enemy_count}", True, (255, 255, 255))
        rect = text.get_rect(center=(640, 100))
        screen.blit(text, rect)

    def update_sidebar(self,selected_country,player,buy_units,enter_attack,enter_move):
        self.sidebar.buttons.clear()
        self.sidebar.labels.clear()
        if selected_country:
            self.sidebar.add_text(f"{selected_country.name}",(1020,10))
            self.sidebar.add_text(f"Infantry: {selected_country.units['infantry']}", (1020, 45))
            self.sidebar.add_text(f"Tanks: {selected_country.units['tank']}", (1020, 85))
            self.sidebar.add_text(f"Artillery: {selected_country.units['artillery']}", (1020, 125))
        if selected_country and selected_country in player.territories:
            self.sidebar.add_button("Buy Units",(1120,210), buy_units)
            self.sidebar.add_button("Attack", (1120, 270), enter_attack)
            self.sidebar.add_button("Move Units", (1120, 330), enter_move)

    def update_player_sidebar(self,player,ai_players):
        if player is None:
            return
        self.player_sidebar.buttons.clear()
        self.player_sidebar.labels.clear()
        self.player_sidebar.add_text("Player Stats", (20, 50))
        self.player_sidebar.add_text(f"Territories: {len(player.territories)}", (20, 90))
        self.player_sidebar.add_text(f"Total infantry: {sum(c.units['infantry'] for c in player.territories)}", (20, 120))
        self.player_sidebar.add_text(f"Total tanks: {sum(c.units['tank'] for c in player.territories)}", (20, 150))
        self.player_sidebar.add_text(f"Total artillery: {sum(c.units['artillery'] for c in player.territories)}", (20, 180))
        y = 210
        count = 1
        for ai in ai_players:
            self.player_sidebar.add_text(f"AI {count} territories: {len(ai.territories)}", (20, y))
            self.player_sidebar.add_text(f"AI {count} currency: {ai.currency}", (20, y + 30))
            count += 1
            y += 60

    def close_panel(self):
        self.panel_visible = False

    def open_panel(self):
        self.panel_visible = True

    def open_move_info(self, move_from, count, adjust, confirm, cancel):
        self.panel.buttons.clear()
        self.panel.labels.clear()
        self.panel.add_text("Select amount and type of units to move", (370, 60))

        self.panel.add_text(f"Infantry: {count['infantry']} / {move_from.units['infantry']}", (390, 150))
        self.panel.add_button("+", (590, 150), lambda: adjust("infantry", 1))
        self.panel.add_button("-", (630, 150), lambda: adjust("infantry", -1))

        self.panel.add_text(f"Tank: {count['tank']} / {move_from.units['tank']}", (390, 230))
        self.panel.add_button("+", (590, 230), lambda: adjust("tank", 1))
        self.panel.add_button("-", (630, 230), lambda: adjust("tank", -1))

        self.panel.add_text(f"Artillery: {count['artillery']} / {move_from.units['artillery']}", (390, 310))
        self.panel.add_button("+", (590, 310), lambda: adjust("artillery", 1))
        self.panel.add_button("-", (630, 310), lambda: adjust("artillery", -1))

        self.panel.add_button("Confirm Move", (450, 460), confirm)
        self.panel.add_button("Cancel", (600, 460), cancel)

    def open_units_info(self,buy_infantry,buy_tank,buy_artillery):
        self.panel.buttons.clear()
        self.panel.labels.clear()
        self.panel.add_text("Select type of unit to buy:", (400, 60))
        self.panel.add_button("Buy Infantry  (5) ", (480, 150), buy_infantry)
        self.panel.add_button("Buy Tank      (15)", (480, 230), buy_tank)
        self.panel.add_button("Buy Artillery (20)", (480, 310), buy_artillery)
        self.panel.add_button("Back              ", (480, 410), self.close_panel)

    def add_stats(self,label, p, x, y):
        lines = [f"{label}: {len(p.territories)} territories (peak {p.peak_territories})",
            f"  2-min territories: {p.territories_at_2min if p.territories_at_2min is not None else 'N/A'}",
            f"  Attacks made: {p.attacks_made} ({p.attacks_won}W / {p.attacks_lost}L)",
            f"  Defended: {p.times_defended} held / {p.times_conquered} lost",
            f"  Units lost - attacking: {p.units_lost}, defending: {p.units_lost_defending}",
            f"  Currency earned/spent: {p.currency_earned} / {p.currency_spent}",]
        for line in lines:
            self.background_panel.add_text(line, (x, y))
            y += 20
        return y + 12

    def open_background_panel(self, result, player, ai_players):
        self.background_panel.buttons.clear()
        self.background_panel.labels.clear()
        result_text = "You Win" if result == "win" else "You Lose"
        self.background_panel.add_text(result_text, (self.background_panel.pos[0] + 250, self.panel.pos[1] + 20))
        y = self.background_panel.pos[1] + 70
        x = self.background_panel.pos[0] + 30
        y = self.add_stats("Player", player, x, y)
        count = 1
        for ai in ai_players:
            y = self.add_stats(f"AI {count} ({ai.playstyle})", ai, x, y)
            count += 1
        self.background_panel_visible = True

    def draw_result(self,screen,game_result,player,ai_players):
        #background = pygame.Surface((1280, 720))
        #background.set_alpha(180)
        #background.fill((0, 0, 0))
        #screen.blit(background, (0, 0))
        self.open_background_panel(game_result,player,ai_players)

    def draw_player_stats(self,player,screen):
        currency_text = self.text_font.render(f"Currency: {player.currency}", True, (255, 255, 255))
        income_text = self.text_font.render(f"Income: {player.income}", True, (255, 255, 255))
        screen.blit(currency_text, (250, 10))
        screen.blit(income_text, (500, 10))
        
    def draw_fps(self,screen,clock):
        fps_text = self.text_font.render(f"FPS: {int(clock.get_fps())}", True, (255, 255, 255))
        screen.blit(fps_text, (50, 10))

    def draw_menu(self,screen):
        screen.fill("black")
        text = self.menu_font.render("MAIN MENU", True, "white")
        screen.blit(text, text.get_rect(center=(640, 150)))
        for button in self.menu_buttons:
            button.update(screen)

    def draw_map_selection(self,screen):
        screen.fill("black")
        text = self.menu_font.render("SELECT A MAP TO PLAY ON", True, "white")
        screen.blit(text,text.get_rect(center=(640,100)))
        for button in self.map_buttons:
            button.update(screen)

    def select_map(self,event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return None
        mouse_pos = event.pos
        if self.europe_button.rect.collidepoint(mouse_pos):
            return "Europe"
        if self.asia_button.rect.collidepoint(mouse_pos):
            return "Asia"
        if self.africa_button.rect.collidepoint(mouse_pos):
            return "Africa"
        return None 
 
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

    def draw_ai_selection(self, screen):
        screen.fill("black")
        text = self.menu_font.render("HOW MANY AI OPPONENTS?", True, "white")
        screen.blit(text, text.get_rect(center=(640, 100)))
        for button in self.ai_count_buttons:
            button.update(screen)

    def select_ai_count(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return None
        mouse_pos = event.pos
        if self.one_ai_button.rect.collidepoint(mouse_pos):
            return 1
        if self.two_ai_button.rect.collidepoint(mouse_pos):
            return 2
        if self.three_ai_button.rect.collidepoint(mouse_pos):
            return 3
        return None

    def show_combat(self, combat_log, round_num, max_round, continue_round, skip, can_skip, is_last_round, result_text):
        self.panel.buttons.clear()
        self.panel.labels.clear()
        round_data = combat_log[round_num - 1]
        phases = round_data["phases"]
        start_attacker = phases[0]["attacker_before"]
        start_defender = phases[0]["defender_before"]
        end_attacker = phases[-1]["attacker_after"]
        end_defender = phases[-1]["defender_after"]

        self.panel.add_text("Combat", (370, 60))
        self.panel.add_text(f"Round {round_num} / {max_round}", (370, 90))
        self.panel.add_text(f"Player units: Infantry - {start_attacker['infantry']} / Tank - {start_attacker['tank']} / Artillery - {start_attacker['artillery']}", (370, 120))
        self.panel.add_text(f"Enemy units: Infantry - {start_defender['infantry']} / Tank - {start_defender['tank']} / Artillery - {start_defender['artillery']}", (370, 140))
        y = 170
        for phase in phases:
            self.panel.add_text("-" * 70, (390, y))
            self.panel.add_text(f"{phase['unit_type'].capitalize()} phase", (390, y + 20))
            self.panel.add_text(f"Attacker damage dealt: {phase['attacker_damage_dealt']}", (410, y + 45))
            self.panel.add_text(f"Defender damage dealt: {phase['defender_damage_dealt']}", (410, y + 70))
            y += 100
        self.panel.add_text(f"Player units: Infantry - {end_attacker['infantry']} / Tank - {end_attacker['tank']} / Artillery - {end_attacker['artillery']}", (370, y + 10))
        self.panel.add_text(f"Enemy units: Infantry - {end_defender['infantry']} / Tank - {end_defender['tank']} / Artillery - {end_defender['artillery']}", (370, y + 30))
        if is_last_round and result_text:
            self.panel.add_text(f"Result: {result_text}", (590, 60))
        continue_label = "FINISH" if is_last_round else "CONTINUE"
        self.panel.add_button(continue_label, (430, y + 90), continue_round)
        if not is_last_round:
            skip_label = "SKIP" if can_skip else "SKIP (locked)"
            self.panel.add_button(skip_label, (630, y + 90), skip if can_skip else None)

        self.open_panel()
        
    def draw(self,screen,map_display,state,selected_country,player,ai_players,game_result):
        screen.fill((0, 0, 0))
        if state == "map_selection":
            self.draw_map_selection(screen)
        if state == "setup":
            self.draw_setup(screen, map_display)
            return
        else:
            map_display.draw(player,ai_players)
        if self.panel_visible:
            self.panel.draw(screen)
        if self.background_panel_visible:
            self.background_panel.draw(screen)
        if self.sidebar_visible:
            self.sidebar.draw(screen)
        if player:
            self.draw_player_stats(player, screen)
        if self.player_sidebar_visible:
            self.player_sidebar.draw(screen)
        if state == "game_over":
           self.draw_result(screen, game_result,player,ai_players)