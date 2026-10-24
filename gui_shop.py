"""Intergalactic supply-shop screen for The Cosmic Clinic."""

import pygame

from gui_theme import COLORS
from Player import DIAGNOSIS_REWARD, PERFECT_DAY_BONUS, WRONG_DIAGNOSIS_PENALTY


SHOP_UPGRADES = (
    {
        "id": "scanner",
        "name": "SCANNER CALIBRATION",
        "category": "TEST MACHINES",
        "cost": 150,
    },
    {
        "id": "card_case",
        "name": "EXPANDED CARD CASE",
        "category": "CARD STORAGE",
        "cost": 125,
    },
    {
        "id": "nebula_plant",
        "name": "NEBULA DESK PLANT",
        "category": "CLINIC DECOR",
        "cost": 75,
    },
)


class ShopMixin:
    def draw_shop_screen(self):
        """Draw selectable upgrade placeholders and the next-day control."""

        panel = pygame.Rect(100, 115, 900, 435)
        self.draw_panel(panel)

        heading = self.heading_font.render(
            "INTERGALACTIC SUPPLY SHOP",
            True,
            COLORS["text"],
        )
        self.screen.blit(heading, heading.get_rect(center=(panel.centerx, 150)))

        balance_box = pygame.Rect(panel.right - 210, 130, 175, 42)
        pygame.draw.rect(
            self.screen,
            COLORS["background"],
            balance_box,
            border_radius=8,
        )
        pygame.draw.rect(
            self.screen,
            COLORS["panel_border"],
            balance_box,
            width=2,
            border_radius=8,
        )
        balance = self.small_font.render(
            "CURRENT MONEY: $" + str(self.player.balance),
            True,
            COLORS["accent"],
        )
        self.screen.blit(balance, balance.get_rect(center=balance_box.center))

        shift_pay = self.get_daily_pay_breakdown()[3]
        shift_summary = self.small_font.render(
            f"SHIFT RECAP: {self.daily_correct_diagnoses} PATIENTS TREATED  •  ${shift_pay} EARNED",
            True,
            COLORS["muted"],
        )
        self.screen.blit(shift_summary, shift_summary.get_rect(center=(panel.centerx, 188)))

        coming_soon = self.body_font.render(
            "PLACEHOLDER UPGRADES — EFFECTS COMING SOON",
            True,
            COLORS["accent"],
        )
        self.screen.blit(coming_soon, coming_soon.get_rect(center=(panel.centerx, 216)))

        for upgrade, shelf in zip(SHOP_UPGRADES, self.get_shop_upgrade_rects()):
            self.draw_shop_shelf(upgrade, shelf)

        selected = self.get_selected_shop_upgrade()
        can_buy = (
            selected is not None
            and selected["id"] not in self.purchased_shop_upgrades
            and self.player.balance >= selected["cost"]
        )
        purchase_hovered = self.shop_purchase_button.collidepoint(pygame.mouse.get_pos())
        purchase_color = (
            COLORS["accent"]
            if can_buy and purchase_hovered
            else COLORS["panel_border"] if can_buy else (71, 83, 91)
        )
        pygame.draw.rect(
            self.screen,
            purchase_color,
            self.shop_purchase_button,
            border_radius=8,
        )
        if selected is None:
            purchase_label = "SELECT AN UPGRADE"
        elif selected["id"] in self.purchased_shop_upgrades:
            purchase_label = "PLACEHOLDER OWNED"
        elif self.player.balance < selected["cost"]:
            purchase_label = f"NEED ${selected['cost']}"
        else:
            purchase_label = f"BUY PLACEHOLDER  ${selected['cost']}"
        purchase_text = self.small_font.render(
            purchase_label,
            True,
            COLORS["background"] if can_buy else COLORS["muted"],
        )
        self.screen.blit(
            purchase_text,
            purchase_text.get_rect(center=self.shop_purchase_button.center),
        )

        message = self.card_font.render(self.shop_message, True, COLORS["muted"])
        self.screen.blit(message, message.get_rect(center=(panel.centerx, 462)))

        hovered = self.shop_button.collidepoint(pygame.mouse.get_pos())
        button_color = COLORS["accent"] if hovered else COLORS["panel_border"]
        pygame.draw.rect(
            self.screen,
            button_color,
            self.shop_button,
            border_radius=8,
        )
        button_text = self.body_font.render(
            "FINISH SHIFT",
            True,
            COLORS["background"],
        )
        self.screen.blit(
            button_text,
            button_text.get_rect(center=self.shop_button.center),
        )

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
                f"{self.daily_wrong_diagnoses} {mistake_label} × ${WRONG_DIAGNOSIS_PENALTY}",
                f"-${penalties}",
            ),
            ("PERFECT SHIFT BONUS", f"+${bonus}"),
            ("TOTAL SHIFT PAY", f"${total}"),
            ("BALANCE AFTER PAY", f"${self.player.balance + total}"),
        )
        for index, (label_text, amount_text) in enumerate(recap_lines):
            y = summary.y + 20 + index * 32
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
        """Return base pay, mistake deductions, perfect bonus, and final payout."""

        base_pay = self.daily_correct_diagnoses * DIAGNOSIS_REWARD
        penalties = self.daily_wrong_diagnoses * WRONG_DIAGNOSIS_PENALTY
        perfect_day = (
            self.daily_correct_diagnoses == len(self.waiting_room_queue)
            and self.daily_wrong_diagnoses == 0
        )
        bonus = PERFECT_DAY_BONUS if perfect_day else 0
        total = max(0, base_pay - penalties + bonus)
        return base_pay, penalties, bonus, total

    def settle_daily_pay(self):
        """Deposit the calculated shift pay exactly once."""

        if self.daily_payout_applied:
            return
        self.player.earn(self.get_daily_pay_breakdown()[3])
        self.daily_payout_applied = True

    def get_shop_upgrade_rects(self):
        """Return the three stable clickable rectangles used by placeholder upgrades."""

        return [pygame.Rect(x, 235, 210, 145) for x in (170, 445, 720)]

    def get_selected_shop_upgrade(self):
        """Return the selected placeholder's data, or None when nothing is selected."""

        return next(
            (
                upgrade
                for upgrade in SHOP_UPGRADES
                if upgrade["id"] == self.selected_shop_upgrade
            ),
            None,
        )

    def handle_shop_upgrade_click(self, position):
        """Select or purchase an upgrade placeholder without applying an effect yet."""

        for upgrade, rect in zip(SHOP_UPGRADES, self.get_shop_upgrade_rects()):
            if rect.collidepoint(position):
                self.selected_shop_upgrade = upgrade["id"]
                if upgrade["id"] in self.purchased_shop_upgrades:
                    self.shop_message = f"{upgrade['name']} is already owned."
                else:
                    self.shop_message = f"{upgrade['name']} selected — effect coming soon."
                return

        if not self.shop_purchase_button.collidepoint(position):
            return
        selected = self.get_selected_shop_upgrade()
        if selected is None:
            self.shop_message = "Select an upgrade placeholder first."
        elif selected["id"] in self.purchased_shop_upgrades:
            self.shop_message = f"{selected['name']} is already owned."
        elif self.player.balance < selected["cost"]:
            self.shop_message = (
                f"Not enough money for {selected['name']} — need ${selected['cost']}."
            )
        else:
            self.player.pay(selected["cost"])
            self.purchased_shop_upgrades.add(selected["id"])
            self.shop_message = f"Purchased {selected['name']} — effect coming soon."

    def draw_shop_shelf(self, upgrade, shelf):
        """Draw one selectable placeholder upgrade shelf."""

        selected = upgrade["id"] == self.selected_shop_upgrade
        owned = upgrade["id"] in self.purchased_shop_upgrades
        pygame.draw.rect(
            self.screen,
            COLORS["background"],
            shelf,
            border_radius=10,
        )
        pygame.draw.rect(
            self.screen,
            COLORS["accent"] if selected else COLORS["muted"],
            shelf,
            width=3 if selected else 2,
            border_radius=10,
        )

        shelf_label = self.card_font.render(upgrade["category"], True, COLORS["muted"])
        self.screen.blit(
            shelf_label,
            shelf_label.get_rect(center=(shelf.centerx, shelf.y + 18)),
        )

        icon_center = (shelf.centerx, shelf.y + 62)
        pygame.draw.circle(
            self.screen,
            (34, 61, 66),
            icon_center,
            25,
        )
        pygame.draw.circle(
            self.screen,
            COLORS["accent"] if selected or owned else COLORS["muted"],
            icon_center,
            25,
            width=2,
        )
        symbol = self.small_font.render("OK" if owned else "+", True, COLORS["accent"])
        self.screen.blit(symbol, symbol.get_rect(center=icon_center))

        name = self.card_font.render(upgrade["name"], True, COLORS["text"])
        self.screen.blit(name, name.get_rect(center=(shelf.centerx, shelf.y + 101)))
        status_text = "OWNED" if owned else f"${upgrade['cost']}  •  SELECT"
        status = self.card_font.render(
            status_text,
            True,
            COLORS["accent"] if owned or selected else COLORS["muted"],
        )
        self.screen.blit(
            status,
            status.get_rect(center=(shelf.centerx, shelf.bottom - 19)),
        )

        shelf_board = pygame.Rect(shelf.x - 8, shelf.bottom - 5, shelf.width + 16, 8)
        pygame.draw.rect(self.screen, (72, 101, 91), shelf_board, border_radius=3)

