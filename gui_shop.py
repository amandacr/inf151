"""Intergalactic supply-shop screen for The Cosmic Clinic."""

import pygame

from gui_theme import COLORS


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
            "END DAY" if self.patients_waiting() == 0 else "CONTINUE / NEXT PATIENT",
            True,
            COLORS["background"],
        )
        self.screen.blit(
            button_text,
            button_text.get_rect(center=self.shop_button.center),
        )

    def draw_day_complete_screen(self):
        """Draw a compact summary after the final patient of the day."""

        panel = pygame.Rect(170, 135, 760, 390)
        self.draw_panel(panel)

        heading = self.heading_font.render("SHIFT COMPLETE", True, COLORS["accent"])
        self.screen.blit(heading, heading.get_rect(center=(panel.centerx, panel.y + 65)))

        subheading = self.body_font.render(
            "Every patient in today's waiting room has been treated.",
            True,
            COLORS["text"],
        )
        self.screen.blit(
            subheading,
            subheading.get_rect(center=(panel.centerx, panel.y + 112)),
        )

        summary = pygame.Rect(panel.centerx - 245, panel.y + 150, 490, 120)
        pygame.draw.rect(self.screen, COLORS["background"], summary, border_radius=10)
        pygame.draw.rect(
            self.screen,
            COLORS["panel_border"],
            summary,
            width=2,
            border_radius=10,
        )

        patients = self.body_font.render(
            f"PATIENTS TREATED: {len(self.waiting_room_queue)}",
            True,
            COLORS["text"],
        )
        balance = self.body_font.render(
            f"CURRENT MONEY: ${self.player.balance}",
            True,
            COLORS["accent"],
        )
        self.screen.blit(patients, patients.get_rect(center=(summary.centerx, summary.y + 40)))
        self.screen.blit(balance, balance.get_rect(center=(summary.centerx, summary.y + 80)))

        hovered = self.day_complete_button.collidepoint(pygame.mouse.get_pos())
        button_color = COLORS["accent"] if hovered else COLORS["panel_border"]
        pygame.draw.rect(
            self.screen,
            button_color,
            self.day_complete_button,
            border_radius=8,
        )
        button_text = self.body_font.render(
            "START NEW DAY",
            True,
            COLORS["background"],
        )
        self.screen.blit(
            button_text,
            button_text.get_rect(center=self.day_complete_button.center),
        )


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

