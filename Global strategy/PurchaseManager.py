from combat import STATS

class PurchaseManager:
    def __init__(self, player, ui):
        self.player = player
        self.ui = ui
        self.purchase_amounts = {"infantry": 1, "tank": 1, "artillery": 1}
        self.selected_territory = None

    def open_panel(self, selected_territory):
        if selected_territory and selected_territory.combat:
            self.ui.show_message("Territory in combat")
            return
        self.refresh_panel(selected_territory)

    def refresh_panel(self, selected_territory):
        self.selected_territory = selected_territory
        self.ui.open_buy_panel(self.purchase_amounts, self.adjust,self.buy_infantry, self.buy_tank, self.buy_artillery)

    def adjust(self, unit_type, unit_change):
        cost = STATS[unit_type]["cost"]
        max_affordable = max(self.player.currency // cost, 1)
        new_value = self.purchase_amounts[unit_type] + unit_change
        new_value = max(1, min(new_value, max_affordable))
        self.purchase_amounts[unit_type] = new_value
        self.refresh_panel(self.selected_territory)

    def attempt_buy(self, unit_type):
        if not self.selected_territory:
            return
        amount = self.purchase_amounts[unit_type]
        cost = STATS[unit_type]["cost"] * amount
        if self.player.currency < cost:
            self.ui.show_message("Cannot afford units")
            return
        self.player.buy_units(self.selected_territory, unit_type, amount)
        self.refresh_panel(self.selected_territory)

    def buy_infantry(self):
        self.attempt_buy("infantry")

    def buy_tank(self):
        self.attempt_buy("tank")

    def buy_artillery(self):
        self.attempt_buy("artillery")