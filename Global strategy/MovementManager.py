import pygame

class MovementManager:
    def __init__(self, player, ui):
        self.player = player
        self.ui = ui
        self.map = None
        self.move_finished = False
        self.count = {"infantry": 0, "tank": 0, "artillery": 0}
        self.move_from, self.move_to = None, None

    def enter_move(self, selected_territory, state, map):
        if len(self.player.territories) <= 1:
            self.ui.show_message("Cannot move units with only 1 territory")
            return state
        if selected_territory not in self.player.territories:
            return state
        if selected_territory.combat:
            self.ui.show_message("Territory is in combat")
            return state
        state = "moving"
        self.move_from = selected_territory
        self.move_to = None
        self.count = {"infantry": 0, "tank": 0, "artillery": 0}
        self.map = map
        self.ui.highlight_move(self.move_from, map, self.player)
        return state
    
    def handle_move(self, clicked_territory):
        if self.move_from and self.move_to is None:
            if clicked_territory in self.player.territories:
                if clicked_territory.name in self.move_from.adjacent:
                    if clicked_territory.combat:
                        self.ui.show_message("Territory is in combat")
                        return
                    self.move_to = clicked_territory
                    self.ui.remove_highlight(self.map)
                    self.refresh_panel()

    def refresh_panel(self):
        self.ui.open_move_panel(self.move_from, self.count, self.adjust, self.confirm_move, self.finish_move)

    def adjust(self, unit_type, unit_change):
        max_amount = self.move_from.units.get(unit_type, 0)
        new_value = self.count[unit_type] + unit_change
        self.count[unit_type] = max(0, min(new_value, max_amount))
        self.refresh_panel()

    def confirm_move(self):
        if sum(self.count.values()) <= 0:
            return
        success = self.player.move_units(self.move_from, self.move_to, self.count["infantry"], self.count["tank"], self.count["artillery"])
        if success:
            self.player.last_action = "reinforcing"
            self.ui.show_message(f"Moved {self.count['infantry']} infantry, {self.count['tank']} tanks, {self.count['artillery']} artillery to {self.move_to.name}")
        self.finish_move()

    def finish_move(self):
        self.move_from = None
        self.move_to = None
        self.ui.close_panel()
        if self.map:
            self.ui.remove_highlight(self.map)
        self.move_finished = True

    def update(self, state):
        if self.move_finished:
            self.move_finished = False
            return "play"
        return state

