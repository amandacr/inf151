"""Intergalactic supply-shop screen for The Cosmic Clinic."""

import pygame

from gui_theme import COLORS
from Player import DIAGNOSIS_REWARD, PERFECT_DAY_BONUS, WRONG_DIAGNOSIS_PENALTY


SHOP_UPGRADES = (
    {"id": "temperature", "name": "THERMAL CALIBRATION", "category": "TEMPERATURE", "cost": 100,
     "description": "Upgrade to level 2. Halves the operating cost of every temperature card.", "machine": "TEMPERATURE"},
    {"id": "xray", "name": "FOCUSED X-RAY", "category": "X-RAY", "cost": 100,
     "description": "Upgrade to level 2. Halves the operating cost of every X-ray card.", "machine": "X-RAY"},
    {"id": "ultrasound", "name": "SONIC AMPLIFIER", "category": "ULTRASOUND", "cost": 150,
     "description": "Upgrade to level 2. Halves the operating cost of every ultrasound card.", "machine": "ULTRASOUND"},
    {"id": "allergy", "name": "ALLERGEN ANALYZER", "category": "ALLERGY", "cost": 175,
     "description": "Upgrade to level 2. Halves the operating cost of every allergy card.", "machine": "ALLERGY"},
    {"id": "power", "name": "EFFICIENT POWER CORE", "category": "ALL MACHINES", "cost": 125,
     "description": "Save another $2 on every test. Works with all machine calibrations.", "discount": 2},
    {"id": "recycling", "name": "SUPPLY RECYCLER", "category": "ALL MACHINES", "cost": 75,
     "description": "Save another $1 on every test. Stacks with the efficient power core.", "discount": 1},
)


class ShopMixin:
    def draw_shop_screen(self):
        """Draw the six-card machine supply shop."""
        panel = pygame.Rect(70, 108, 960, 508)
        pygame.draw.rect(self.screen, COLORS["panel"], panel)
        pygame.draw.rect(self.screen, COLORS["panel_border"], panel, width=2)
        title = self.heading_font.render("INTERGALACTIC SUPPLY SHOP", True, COLORS["accent"])
        self.screen.blit(title, (95, 125))
        balance = self.body_font.render(f"BALANCE: ${self.player.balance}", True, COLORS["accent"])
        self.screen.blit(balance, balance.get_rect(topright=(1005, 132)))
        hint = self.small_font.render("Permanent upgrades for this run. Select a machine, then buy to install.", True, COLORS["muted"])
        self.screen.blit(hint, (95, 165))
        for upgrade, rect in zip(SHOP_UPGRADES, self.get_shop_upgrade_rects()):
            self.draw_shop_shelf(upgrade, rect)
        selected = self.get_selected_shop_upgrade()
        owned = selected and selected["id"] in self.purchased_shop_upgrades
        can_buy = selected and not owned and self.player.balance >= selected["cost"]
        label = "SELECT AN UPGRADE"
        if selected:
            label = "INSTALLED" if owned else (f"BUY & INSTALL  ${selected['cost']}" if can_buy else f"NEED ${selected['cost'] - self.player.balance} MORE")
        for rect, text, enabled in ((self.shop_purchase_button, label, can_buy), (self.shop_next_day_button, "NEXT SHIFT", True), (self.shop_button, "FINISH SHIFT", True)):
            color = COLORS["accent"] if enabled else (71, 83, 91)
            pygame.draw.rect(self.screen, color, rect)
            rendered = self.small_font.render(text, True, COLORS["background"] if enabled else COLORS["muted"])
            self.screen.blit(rendered, rendered.get_rect(center=rect.center))
        message = self.card_font.render(self.shop_message, True, COLORS["text"])
        self.screen.blit(message, message.get_rect(center=(550, 588)))

    def draw_day_complete_screen(self):
        """Draw the end-of-day earnings recap before opening the Shop."""

        panel = pygame.Rect(170, 135, 760, 390)
        self.draw_panel(panel)

        heading = self.heading_font.render("SHIFT COMPLETE", True, COLORS["accent"])
        self.screen.blit(heading, heading.get_rect(center=(panel.centerx, panel.y + 65)))

        subheading = self.body_font.render(
            "All patients treated — calculating today's clinic pay.",
            True,
            COLORS["text"],
        )
        self.screen.blit(
            subheading,
            subheading.get_rect(center=(panel.centerx, panel.y + 112)),
        )

        summary = pygame.Rect(panel.centerx - 245, panel.y + 125, 490, 180)
        pygame.draw.rect(self.screen, COLORS["background"], summary, border_radius=10)
        pygame.draw.rect(
            self.screen,
            COLORS["panel_border"],
            summary,
            width=2,
            border_radius=10,
        )

        base_pay, penalties, bonus, total = self.get_daily_pay_breakdown()
        mistake_label = (
            "WRONG DIAGNOSIS"
            if self.daily_wrong_diagnoses == 1
            else "WRONG DIAGNOSES"
        )
        recap_lines = (
            (f"{self.daily_correct_diagnoses} PATIENTS × ${DIAGNOSIS_REWARD}", f"+${base_pay}"),
            (
                f"{self.daily_test_count} TESTS PERFORMED",
                f"-${self.daily_test_expenses}",
            ),
            (
                f"{self.daily_wrong_diagnoses} {mistake_label} × ${WRONG_DIAGNOSIS_PENALTY}",
                f"-${penalties}",
            ),
            ("PERFECT SHIFT BONUS", f"+${bonus}"),
            (
                "TOTAL SHIFT PAY",
                f"-${abs(total)}" if total < 0 else f"${total}",
            ),
            (
                "BALANCE AFTER PAY",
                f"${self.player.balance + total}",
            ),
        )
        for index, (label_text, amount_text) in enumerate(recap_lines):
            y = summary.y + 14 + index * 27
            color = COLORS["accent"] if index >= len(recap_lines) - 2 else COLORS["text"]
            label = self.small_font.render(label_text, True, color)
            amount = self.small_font.render(amount_text, True, color)
            self.screen.blit(label, (summary.x + 24, y))
            self.screen.blit(amount, amount.get_rect(topright=(summary.right - 24, y)))

        hovered = self.day_complete_button.collidepoint(pygame.mouse.get_pos())
        button_color = COLORS["accent"] if hovered else COLORS["panel_border"]
        pygame.draw.rect(
            self.screen,
            button_color,
            self.day_complete_button,
            border_radius=8,
        )
        button_text = self.body_font.render(
            "COLLECT PAY & OPEN SHOP",
            True,
            COLORS["background"],
        )
        self.screen.blit(
            button_text,
            button_text.get_rect(center=self.day_complete_button.center),
        )

    def get_daily_pay_breakdown(self):
        """Return earnings, diagnosis penalties, bonus, and net shift payout."""

        base_pay = self.daily_correct_diagnoses * DIAGNOSIS_REWARD
        penalties = self.daily_wrong_diagnoses * WRONG_DIAGNOSIS_PENALTY
        perfect_day = (
            self.daily_correct_diagnoses == len(self.waiting_room_queue)
            and self.daily_wrong_diagnoses == 0
        )
        bonus = PERFECT_DAY_BONUS if perfect_day else 0
        total = base_pay - penalties - self.daily_test_expenses + bonus
        return base_pay, penalties, bonus, total

    def settle_daily_pay(self):
        """Deposit the calculated shift pay exactly once."""

        if self.daily_payout_applied:
            return
        self.player.earn(self.get_daily_pay_breakdown()[3])
        self.daily_payout_applied = True

    def get_shop_upgrade_rects(self):
        """Stable three-column, two-row layout matching the concept art."""
        return [pygame.Rect(x, y, 290, 154) for y in (198, 367) for x in (95, 405, 715)]

    def get_selected_shop_upgrade(self):
        return next((item for item in SHOP_UPGRADES if item["id"] == self.selected_shop_upgrade), None)

    def handle_shop_upgrade_click(self, position):
        for upgrade, rect in zip(SHOP_UPGRADES, self.get_shop_upgrade_rects()):
            if rect.collidepoint(position):
                self.play_sfx("button")
                self.selected_shop_upgrade = upgrade["id"]
                self.shop_message = f"{upgrade['name']} " + ("is installed." if upgrade["id"] in self.purchased_shop_upgrades else "selected. Buy to install immediately.")
                return
        if not self.shop_purchase_button.collidepoint(position):
            return
        self.play_sfx("button")
        upgrade = self.get_selected_shop_upgrade()
        if upgrade is None:
            self.shop_message = "Select an upgrade first."
        elif upgrade["id"] in self.purchased_shop_upgrades:
            self.shop_message = f"{upgrade['name']} is already installed."
        elif self.player.balance < upgrade["cost"]:
            self.shop_message = f"Not enough money for {upgrade['name']} — need ${upgrade['cost']}."
        else:
            self.player.pay(upgrade["cost"])
            if "machine" in upgrade:
                self.player.machine_levels[upgrade["machine"]] = 2
            else:
                self.player.test_discount += upgrade["discount"]
            self.player.sync_machine_levels(self.player.test_hand + self.deck.contents + self.discard_pile)
            self.purchased_shop_upgrades.add(upgrade["id"])
            self.shop_message = f"Installed {upgrade['name']}. Test costs updated!"

    def draw_shop_shelf(self, upgrade, shelf):
        selected = upgrade["id"] == self.selected_shop_upgrade
        owned = upgrade["id"] in self.purchased_shop_upgrades
        color = COLORS["accent"] if selected or owned else COLORS["muted"]
        pygame.draw.rect(self.screen, COLORS["background"], shelf)
        pygame.draw.rect(self.screen, color, shelf, width=3 if selected else 1)
        category = self.card_font.render(upgrade["category"] + (" / LV.2" if owned and "machine" in upgrade else ""), True, color)
        self.screen.blit(category, (shelf.x + 15, shelf.y + 12))
        name = self.small_font.render(upgrade["name"], True, COLORS["text"])
        self.screen.blit(name, (shelf.x + 15, shelf.y + 34))
        words = upgrade["description"].split()
        line, y = "", shelf.y + 61
        for word in words + [None]:
            candidate = f"{line} {word}".strip() if word else ""
            if word is None or self.card_font.size(candidate)[0] > shelf.width - 30:
                self.screen.blit(self.card_font.render(line, True, COLORS["muted"]), (shelf.x + 15, y))
                y += 17
                line = word or ""
            else:
                line = candidate
        pygame.draw.line(self.screen, color, (shelf.x + 1, shelf.bottom - 32), (shelf.right - 2, shelf.bottom - 32))
        status = "INSTALLED" if owned else f"${upgrade['cost']}  /  " + ("SELECT" if self.player.balance >= upgrade["cost"] else "INSUFFICIENT FUNDS")
        text = self.card_font.render(status, True, color)
        self.screen.blit(text, text.get_rect(center=(shelf.centerx, shelf.bottom - 16)))
