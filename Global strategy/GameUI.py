from GUI import Panel
import pygame

class GameUI:
    def __init__(self):
        self.clock = pygame.time.Clock()
        self.text_font = pygame.font.SysFont("Roboto", 29)
        self.result_font = pygame.font.SysFont("Roboto",33)
        self.background_font = pygame.font.SysFont("Roboto", 20)

        self.sidebar = Panel(pos=(1000, 0), width=280, height=720, font=self.text_font)
        self.sidebar_visible = False

        self.panel = Panel(pos=(320,50), width=650, height=590, font=self.text_font)
        self.panel_visible = False

        self.background_panel = Panel(pos=(350,50), width=650, height=620, font=self.background_font)
        self.background_panel_visible = False

        self.player_sidebar = Panel(pos=(0,40), width=280, height=570, font=self.text_font)
        self.player_sidebar_visible = False

        self.setup_mode = "player"
        self.enemy_count = 1
        self.enemies_placed = 0

        self.message_text = None
        self.message_time = 0
        self.message_duration = 2000
        self.message_position = (640, 680)
        self.message_colour = (255, 255, 255)

    def reset_game_ui(self, enemy_count):
        self.setup_mode = "player"
        self.enemy_count = enemy_count
        self.enemies_placed = 0
        self.panel_visible = False
        self.sidebar_visible = False
        self.player_sidebar_visible = False
        self.background_panel_visible = False
        self.message_text = None
        self.clear_panel(self.panel)
        self.clear_panel(self.sidebar)
        self.clear_panel(self.player_sidebar)
        self.clear_panel(self.background_panel)

    def remove_highlight(self,map):
        for territory in map.territories.values():
            territory.highlighted = False

    def highlight_attack(self,selected_territory,map,player):
        for name in selected_territory.adjacent:
            if map.territories[name] not in player.territories and not map.territories[name].combat:
                map.territories[name].highlighted = True

    def highlight_move(self,selected_territory,map,player):
        for name in selected_territory.adjacent:
            if map.territories[name] in player.territories and not map.territories[name].combat:
                map.territories[name].highlighted = True

    def show_message(self,text):
        self.message_text = text
        self.message_time = pygame.time.get_ticks()

    def update_message(self):
        if self.message_text:
            if pygame.time.get_ticks() - self.message_time >= self.message_duration:
                self.message_text = None

    def draw_message(self,screen):
        if self.message_text:
            surface = self.text_font.render(self.message_text, True, self.message_colour)
            screen.blit(surface, surface.get_rect(center=self.message_position))

    def clear_panel(self,panel):
        panel.buttons.clear()
        panel.labels.clear()
        panel.dividers.clear()

    def draw_setup(self,screen,map_display):
        screen.fill((0, 0, 0))
        map_display.draw(None, [])
        if self.setup_mode == "player":
            text = self.text_font.render("Choose your starting territory", True, (255, 255, 255))
        elif self.setup_mode == "enemy":
            text = self.text_font.render(f"Choose enemy {self.enemies_placed + 1} of {self.enemy_count}", True, (255, 255, 255))
        rect = text.get_rect(center=(640, 100))
        screen.blit(text, rect)

    def update_sidebar(self,selected_territory,player,buy_units,enter_attack,enter_move):
        self.clear_panel(self.sidebar)
        if selected_territory:
            self.sidebar.add_text(f"{selected_territory.name}",(1020,10))
            self.sidebar.add_text(f"Infantry: {selected_territory.units['infantry']}", (1020, 45))
            self.sidebar.add_text(f"Tanks: {selected_territory.units['tank']}", (1020, 85))
            self.sidebar.add_text(f"Artillery: {selected_territory.units['artillery']}", (1020, 125))
        if selected_territory and selected_territory in player.territories:
            self.sidebar.add_button("Buy Units",(1120,210), buy_units)
            self.sidebar.add_button("Attack", (1120, 270), enter_attack)
            self.sidebar.add_button("Move Units", (1120, 330), enter_move)

    def update_player_sidebar(self,player,ai_players):
        if player is None:
            return
        self.clear_panel(self.player_sidebar)
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

    def get_setup_mode(self):
        return self.setup_mode

    def set_setup_mode(self,mode):
        self.setup_mode = mode

    def place_enemy(self):
        self.enemies_placed += 1

    def all_enemies_placed(self):
        if self.enemies_placed == self.enemy_count:
            return True
        else:
            return False

    def close_panel(self):
        self.panel_visible = False

    def open_panel(self):
        self.panel_visible = True

    def open_sidebar(self):
        self.sidebar_visible = True

    def close_sidebar(self):
        self.sidebar_visible = False

    def open_player_sidebar(self):
        self.player_sidebar_visible = True

    def close_player_sidebar(self):
        self.player_sidebar_visible = False

    def is_panel_visible(self):
        return self.panel_visible

    def is_sidebar_visible(self):
        return self.sidebar_visible

    def is_player_sidebar_visible(self):
        return self.player_sidebar_visible

    def toggle_player_sidebar(self):
        self.player_sidebar_visible = not self.player_sidebar_visible

    def handle_panel_event(self,event):
        self.panel.handle_event(event)

    def handle_sidebar_event(self,event):
        self.sidebar.handle_event(event)

    def handle_player_sidebar_event(self,event):
        self.player_sidebar.handle_event(event)

    def open_move_panel(self, move_from, count, adjust, confirm, cancel):
        self.clear_panel(self.panel)
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

        self.open_panel()

    def open_buy_panel(self, amounts, adjust, buy_infantry, buy_tank, buy_artillery):
        self.clear_panel(self.panel)
        self.panel.add_text("Select amount and type of unit to buy:", (370, 60))

        self.panel.add_text(f"Infantry (5 each): {amounts['infantry']}", (390, 140))
        self.panel.add_button("+", (620, 140), lambda: adjust("infantry", 1))
        self.panel.add_button("-", (660, 140), lambda: adjust("infantry", -1))
        self.panel.add_button("Buy Infantry", (470, 200), buy_infantry)

        self.panel.add_text(f"Tank (10 each): {amounts['tank']}", (390, 230))
        self.panel.add_button("+", (620, 230), lambda: adjust("tank", 1))
        self.panel.add_button("-", (660, 230), lambda: adjust("tank", -1))
        self.panel.add_button("Buy Tank", (470, 290), buy_tank)

        self.panel.add_text(f"Artillery (15 each): {amounts['artillery']}", (390, 320))
        self.panel.add_button("+", (620, 320), lambda: adjust("artillery", 1))
        self.panel.add_button("-", (660, 320), lambda: adjust("artillery", -1))
        self.panel.add_button("Buy Artillery", (470, 380), buy_artillery)

        self.panel.add_button("Back", (480, 480), self.close_panel)

        self.open_panel()

    def add_endgame_stats(self,label,player,x,y):
        lines = [f"{label}: {len(player.territories)} territories (peak {player.peak_territories})",
            f"  2-min territories: {player.territories_at_2min if player.territories_at_2min is not None else 'N/A'}",
            f"  Attacks made: {player.attacks_made} ({player.attacks_won}W / {player.attacks_lost}L)",
            f"  Defended: {player.times_defended} held / {player.times_conquered} lost",
            f"  Units lost - attacking: {player.units_lost}, defending: {player.units_lost_defending}",
            f"  Currency earned/spent: {player.currency_earned} / {player.currency_spent}",]
        for line in lines:
            self.background_panel.add_text(line, (x, y))
            y += 20
        return y + 12

    def open_background_panel(self,result,player,ai_players):
        self.clear_panel(self.background_panel)
        result_text = "You Win" if result == "win" else "You Lose"
        self.background_panel.add_text(result_text, (self.background_panel.pos[0] + 250, self.panel.pos[1] + 20))
        y = self.background_panel.pos[1] + 70
        x = self.background_panel.pos[0] + 30
        y = self.add_endgame_stats("Player", player,x,y)
        count = 1
        for ai in ai_players:
            y = self.add_endgame_stats(f"AI {count} ({ai.playstyle})", ai,x,y)
            count += 1
        self.background_panel_visible = True

    def draw_player_stats(self,player,screen):
        currency_text = self.text_font.render(f"Currency: {player.currency}", True, (255, 255, 255))
        income_text = self.text_font.render(f"Income: {player.income}", True, (255, 255, 255))
        screen.blit(currency_text, (250, 10))
        screen.blit(income_text, (500, 10))

    def draw_fps(self,screen,clock):
        fps_text = self.text_font.render(f"FPS: {int(clock.get_fps())}", True, (255, 255, 255))
        screen.blit(fps_text, (50, 10))

    def open_combat_panel(self, combat_log, round_num, max_rounds, continue_round, skip, can_skip, can_finish,is_last_round, result_text):
        self.clear_panel(self.panel)
        self.sidebar_visible = False
        left_x = 350
        right_x = 700
        self.panel.add_divider(right_x-40,self.panel.pos[1]+60,right_x-40,self.panel.pos[1] + 480)

        if not combat_log:
            self.panel.add_text("Territory was undefended - captured instantly", (left_x-20, 160))
            y = 220
        else:
            round_data = combat_log[round_num - 1]
            phase = round_data["phases"][0]
            start_attacker = phase["attacker_before"]
            start_defender = phase["defender_before"]
            end_attacker = phase["attacker_after"]
            end_defender = phase["defender_after"]

            left_x = 350
            right_x = 700

            self.panel.add_divider(right_x-40,self.panel.pos[1]+60,right_x-40,self.panel.pos[1] + 480)
            self.panel.add_text("Combat", (580, 60))
            self.panel.add_text(f"Round {round_num} / {max_rounds}", (560, 80))

            self.panel.add_text("Player", (left_x, 120))
            self.panel.add_text("Enemy", (right_x, 120))

            self.panel.add_text(f"Infantry: {start_attacker['infantry']}", (left_x, 150))
            self.panel.add_text(f"Tank: {start_attacker['tank']}", (left_x, 172))
            self.panel.add_text(f"Artillery: {start_attacker['artillery']}", (left_x, 194))

            self.panel.add_text(f"Infantry: {start_defender['infantry']}", (right_x, 150))
            self.panel.add_text(f"Tank: {start_defender['tank']}", (right_x, 172))
            self.panel.add_text(f"Artillery: {start_defender['artillery']}", (right_x, 194))

            left_y = 230
            right_y = 230

            self.panel.add_text("Attacks", (left_x, left_y))
            self.panel.add_text("Attacks", (right_x, right_y))

            left_y += 30
            right_y += 30

            attacker_types = phase["attacker_unit_type"]

            if not attacker_types:
                self.panel.add_text("no attacks this round", (left_x, left_y))
                left_y += 25

            for unit_type in attacker_types:
                breakdown = phase["attacker_breakdowns"].get(unit_type, {})
                damage = sum(breakdown.values()) if breakdown else 0
                self.panel.add_text(f"{unit_type.capitalize()}: {damage:.1f} dmg", (left_x, left_y))
                left_y += 25

                for target_type, target_damage in breakdown.items():
                    self.panel.add_text(f"  -> {target_type.capitalize()}: {target_damage:.1f}", (left_x + 15, left_y))
                    left_y += 25

            defender_types = phase["defender_unit_type"]

            if not defender_types:
                self.panel.add_text("(none this round)", (right_x, right_y))
                right_y += 25

            for unit_type in defender_types:
                breakdown = phase["defender_breakdowns"].get(unit_type, {})
                damage = sum(breakdown.values()) if breakdown else 0
                self.panel.add_text(f"{unit_type.capitalize()}: {damage:.1f} dmg", (right_x, right_y))
                right_y += 25

                for target_type, target_damage in breakdown.items():
                    self.panel.add_text(f"  -> {target_type.capitalize()}: {target_damage:.1f}", (right_x + 15, right_y))
                    right_y += 25

            y = max(left_y,right_y) + 25

            self.panel.add_text(f"Infantry {end_attacker['infantry']} / Tank {end_attacker['tank']} / Artillery {end_attacker['artillery']}", (left_x-10, y))
            self.panel.add_text(f"Infantry {end_defender['infantry']} / Tank {end_defender['tank']} / Artillery {end_defender['artillery']}", (right_x-10, y))

            y += 40

        self.panel.add_divider(right_x-40,self.panel.pos[1]+60,right_x-40,y)

        if is_last_round and result_text:
            self.panel.add_text(f"Result: {result_text}", (700, y+40))

        if is_last_round:
            continue_label = "FINISH" if can_finish else "FINISH (disabled)"
            continue_action = continue_round if can_finish else None
        else:
            continue_label = "CONTINUE"
            continue_action = continue_round

        self.panel.add_button(continue_label,(420, y + 50),continue_action)

        if not is_last_round:
            skip_label = "SKIP" if can_skip else "SKIP (disabled)"
            self.panel.add_button(skip_label, (570, y+50), skip if can_skip else None)

        self.open_panel()

    def draw(self,screen,map_display,state,player,ai_players,game_result):
        screen.fill((0, 0, 0))

        if state == "setup":
            self.draw_setup(screen, map_display)
            self.draw_message(screen)
            self.update_message()
            return

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
            self.open_background_panel(game_result,player,ai_players)

        self.draw_message(screen)