"""Intergalactic supply-shop screen for The Cosmic Clinic."""

import pygame

from gui_theme import COLORS
from Player import DIAGNOSIS_REWARD, PERFECT_DAY_BONUS, WRONG_DIAGNOSIS_PENALTY


class ShopMixin:
    def draw_shop_screen(self):
        """Draw the placeholder shop with the current balance and locked shelves."""

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

        coming_soon = self.body_font.render(
            "UPGRADES COMING SOON",
            True,
            COLORS["accent"],
        )
        self.screen.blit(coming_soon, coming_soon.get_rect(center=(panel.centerx, 205)))

        shelf_labels = ("TEST MACHINES", "CARD STORAGE", "CLINIC DECOR")
        shelf_x_positions = (170, 445, 720)
        for label, shelf_x in zip(shelf_labels, shelf_x_positions):
            self.draw_shop_shelf(label, pygame.Rect(shelf_x, 240, 210, 150))

        hovered = self.shop_button.collidepoint(pygame.mouse.get_pos())
        button_color = COLORS["accent"] if hovered else COLORS["panel_border"]
        pygame.draw.rect(
            self.screen,
            button_color,
            self.shop_button,
            border_radius=8,
        )
        button_text = self.body_font.render(
            "START NEXT DAY",
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


    def draw_shop_shelf(self, label, shelf):
        """Draw one locked and currently empty upgrade shelf."""

        pygame.draw.rect(
            self.screen,
            COLORS["background"],
            shelf,
            border_radius=10,
        )
        pygame.draw.rect(
            self.screen,
            COLORS["muted"],
            shelf,
            width=2,
            border_radius=10,
        )

        shelf_label = self.small_font.render(label, True, COLORS["text"])
        self.screen.blit(
            shelf_label,
            shelf_label.get_rect(center=(shelf.centerx, shelf.y + 22)),
        )

        lock_body = pygame.Rect(shelf.centerx - 18, shelf.y + 65, 36, 32)
        pygame.draw.rect(self.screen, COLORS["muted"], lock_body, border_radius=5)
        pygame.draw.arc(
            self.screen,
            COLORS["muted"],
            pygame.Rect(shelf.centerx - 14, shelf.y + 48, 28, 30),
            0,
            3.14159,
            width=5,
        )
        keyhole = pygame.Rect(shelf.centerx - 3, shelf.y + 75, 6, 13)
        pygame.draw.rect(self.screen, COLORS["background"], keyhole, border_radius=3)

        empty = self.card_font.render("SHELF LOCKED", True, COLORS["muted"])
        self.screen.blit(
            empty,
            empty.get_rect(center=(shelf.centerx, shelf.bottom - 22)),
        )

        shelf_board = pygame.Rect(shelf.x - 8, shelf.bottom - 5, shelf.width + 16, 8)
        pygame.draw.rect(self.screen, (72, 101, 91), shelf_board, border_radius=3)

