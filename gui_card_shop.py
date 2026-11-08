"""In-shift Card Shop interface for The Cosmic Clinic."""

import pygame

from gui_theme import COLORS, RARITY_COLORS
from Player import MAX_TEST_HAND_SIZE


CARD_SHOP_BASE_PRICE = 10
CARD_SHOP_PRICE_STEP = 5
CARD_SHOP_NOTICE_DURATION = 1200
CARD_SHOP_PURPOSES = {
    "TEMPERATURE": "Measures species-adjusted body temperature.",
    "X-RAY": "Checks bones and tissue for structural damage.",
    "BLOOD CHEMISTRY": "Analyzes circulating fluids and metabolic markers.",
    "OXYGEN SCAN": "Measures breathing efficiency and oxygen exchange.",
    "ULTRASOUND": "Images organs, internal motion, and blood flow.",
    "TOXIN SCREEN": "Screens fluids and residue for harmful compounds.",
    "ALLERGY": "Detects immune reactions and their severity.",
    "NEURAL SCAN": "Maps nerve signals, senses, and motor control.",
}


class CardShopMixin:
    """Draw and control targeted card purchases during an examination."""

    def draw_card_shop_button(self):
        """Draw the compact control beneath the random draw deck."""

        rect = self.card_shop_button
        hovered = rect.collidepoint(self.get_mouse_position())
        active = self.card_shop_open
        border = (216, 159, 238) if hovered or active else (155, 116, 190)
        fill = (61, 42, 78) if hovered or active else (37, 31, 52)
        pygame.draw.rect(self.screen, (4, 9, 15), rect.move(2, 3), border_radius=7)
        pygame.draw.rect(self.screen, fill, rect, border_radius=7)
        pygame.draw.rect(self.screen, border, rect, width=2, border_radius=7)
        label = self.card_font.render("CARD SHOP", True, (238, 218, 246))
        self.screen.blit(label, label.get_rect(center=rect.center))

    def get_card_shop_slot_rects(self):
        """Return one stable slot rectangle for each basic test-card type."""

        grid = pygame.Rect(
            self.card_shop_panel.x + 22,
            self.card_shop_panel.y + 58,
            self.card_shop_panel.width - 44,
            98,
        )
        gap = 8
        slot_width = (grid.width - gap * 3) // 4
        slot_height = (grid.height - gap) // 2
        return [
            pygame.Rect(
                grid.x + column * (slot_width + gap),
                grid.y + row * (slot_height + gap),
                slot_width,
                slot_height,
            )
            for row in range(2)
            for column in range(4)
        ]

    def get_card_shop_price(self):
        """Return the next targeted-card price for the current patient."""

        return CARD_SHOP_BASE_PRICE + self.card_shop_patient_purchases * CARD_SHOP_PRICE_STEP

    def get_card_shop_inventory_count(self, test_name):
        """Count matching cards still available in the live draw deck."""

        return sum(
            getattr(card.value, "name", None) == test_name
            for card in self.deck.contents
        )

    def get_selected_card_shop_test(self):
        """Return the selected catalog entry, if one is selected."""

        return next(
            (
                test
                for test in self.card_shop_catalog
                if test.name == self.selected_card_shop_test
            ),
            None,
        )

    def get_card_shop_purchase_state(self):
        """Return whether the purchase can proceed and a concise button label."""

        selected = self.get_selected_card_shop_test()
        if selected is None:
            return False, "SELECT A CARD"
        if len(self.player.test_hand) >= MAX_TEST_HAND_SIZE:
            return False, "HAND FULL"
        if self.get_card_shop_inventory_count(selected.name) <= 0:
            return False, "SOLD OUT"
        price = self.get_card_shop_price()
        if self.get_live_balance() < price:
            return False, f"NEED ${price - self.get_live_balance()} MORE"
        return True, f"BUY FOR ${price}  •  NEXT CARD ${price + CARD_SHOP_PRICE_STEP}"

    def get_card_shop_information(self):
        """Return concise purpose and billing details for the selected card."""

        selected = self.get_selected_card_shop_test()
        if selected is None:
            return (
                "Choose a test card to add directly to your hand.",
                "CARD: $10, THEN $15, $20...  •  RUNNING IT COSTS EXTRA",
            )
        inventory = self.get_card_shop_inventory_count(selected.name)
        purpose = CARD_SHOP_PURPOSES[selected.name]
        details = (
            f"{selected.rarity.upper()}  •  {inventory} IN STOCK  •  "
            f"RUN TEST: ${self.player.get_test_cost(selected)}"
        )
        return purpose, details

    def draw_card_shop_overlay(self):
        """Draw the targeted card dispenser over the available-tests area."""

        if not self.card_shop_open:
            return

        panel = self.card_shop_panel
        mouse = self.get_mouse_position()
        pygame.draw.rect(self.screen, (3, 7, 12), panel.move(7, 8), border_radius=15)
        pygame.draw.rect(self.screen, (22, 28, 43), panel, border_radius=15)
        pygame.draw.rect(self.screen, (187, 137, 211), panel, width=3, border_radius=15)
        pygame.draw.rect(
            self.screen,
            COLORS["accent"],
            panel.inflate(-10, -10),
            width=1,
            border_radius=11,
        )

        header = pygame.Rect(panel.x + 16, panel.y + 12, panel.width - 32, 36)
        pygame.draw.rect(self.screen, (9, 18, 29), header, border_radius=9)
        pygame.draw.rect(self.screen, (94, 77, 116), header, width=1, border_radius=9)
        notice_active = (
            self.card_shop_notice_started_at is not None
            and pygame.time.get_ticks() - self.card_shop_notice_started_at
            < CARD_SHOP_NOTICE_DURATION
        )
        title = self.heading_font.render(
            "CARD ADDED TO YOUR HAND!" if notice_active else "CLINIC CARD SHOP",
            True,
            COLORS["accent"] if notice_active else (232, 211, 242),
        )
        self.screen.blit(title, title.get_rect(center=header.center))

        close = self.card_shop_close_button
        close_hovered = close.collidepoint(mouse)
        close_border = (232, 211, 242) if close_hovered else (187, 137, 211)
        pygame.draw.rect(
            self.screen,
            (61, 42, 78) if close_hovered else (37, 31, 52),
            close,
            border_radius=6,
        )
        pygame.draw.rect(self.screen, close_border, close, width=2, border_radius=6)
        pygame.draw.line(
            self.screen,
            close_border,
            (close.x + 7, close.y + 7),
            (close.right - 7, close.bottom - 7),
            width=2,
        )
        pygame.draw.line(
            self.screen,
            close_border,
            (close.right - 7, close.y + 7),
            (close.x + 7, close.bottom - 7),
            width=2,
        )

        for test, slot in zip(self.card_shop_catalog, self.get_card_shop_slot_rects()):
            selected = test.name == self.selected_card_shop_test
            inventory = self.get_card_shop_inventory_count(test.name)
            sold_out = inventory <= 0
            hovered = slot.collidepoint(mouse)
            rarity_color = RARITY_COLORS.get(test.rarity, COLORS["accent"])
            border = COLORS["accent"] if selected else rarity_color if hovered else (92, 72, 111)
            fill = (41, 47, 65) if selected or hovered else (29, 36, 52)
            if sold_out:
                fill = (25, 29, 39)
                border = (74, 72, 84)
            if selected:
                pygame.draw.rect(self.screen, (44, 83, 72), slot.inflate(8, 8), border_radius=11)
            pygame.draw.rect(self.screen, fill, slot, border_radius=8)
            pygame.draw.rect(
                self.screen,
                border,
                slot,
                width=3 if selected else 2 if hovered else 1,
                border_radius=8,
            )

            icon = pygame.Rect(slot.x + 8, slot.y + 8, 31, 31)
            pygame.draw.rect(self.screen, (218, 228, 216), icon, border_radius=6)
            pygame.draw.rect(self.screen, rarity_color, icon, width=2, border_radius=6)
            self.draw_test_icon(test.name, icon.inflate(-2, -2), rarity_color)

            display_name = {
                "BLOOD CHEMISTRY": "BLOOD CHEM.",
                "OXYGEN SCAN": "OXYGEN SCAN",
                "TOXIN SCREEN": "TOXIN SCREEN",
            }.get(test.name, test.name)
            name_color = (117, 116, 127) if sold_out else (231, 237, 235)
            name = self.compact_ui_font.render(display_name, True, name_color)
            self.screen.blit(name, (slot.x + 46, slot.y + 8))
            stock = self.legible_micro_font.render(
                "SOLD OUT" if sold_out else f"STOCK: {inventory}",
                True,
                (106, 102, 113) if sold_out else rarity_color,
            )
            self.screen.blit(stock, (slot.x + 46, slot.y + 27))

        information = pygame.Rect(panel.x + 22, panel.bottom - 43, 365, 31)
        pygame.draw.rect(self.screen, (12, 22, 31), information, border_radius=7)
        pygame.draw.rect(
            self.screen,
            (67, 97, 100),
            information,
            width=1,
            border_radius=7,
        )
        purpose, details = self.get_card_shop_information()
        purpose_text = self.compact_ui_font.render(purpose, True, COLORS["text"])
        details_text = self.compact_ui_font.render(
            details,
            True,
            COLORS["muted"],
        )
        self.screen.blit(
            purpose_text,
            purpose_text.get_rect(midleft=(information.x + 9, information.y + 8)),
        )
        self.screen.blit(
            details_text,
            details_text.get_rect(midleft=(information.x + 9, information.y + 23)),
        )

        enabled, button_label = self.get_card_shop_purchase_state()
        button = self.card_shop_buy_button
        button_hovered = button.collidepoint(mouse) and enabled
        button_fill = (
            (132, 83, 160)
            if button_hovered
            else (87, 57, 111)
            if enabled
            else (45, 48, 58)
        )
        button_border = (224, 176, 241) if enabled else (84, 83, 92)
        pygame.draw.rect(self.screen, button_fill, button, border_radius=7)
        pygame.draw.rect(self.screen, button_border, button, width=2, border_radius=7)
        buy_text = self.card_font.render(
            button_label,
            True,
            (246, 231, 250) if enabled else (135, 135, 143),
        )
        self.screen.blit(buy_text, buy_text.get_rect(center=button.center))

    def toggle_card_shop(self):
        """Open or close the shop without changing the selected inventory item."""

        self.card_shop_open = not self.card_shop_open
        self.selected_card_index = None
        if self.card_shop_open and self.selected_card_shop_test is None:
            self.card_shop_message = "Choose one card type from the live deck."
        self.play_sfx("button")

    def purchase_selected_card_shop_test(self):
        """Buy the selected card from the live deck and add it to the hand."""

        selected = self.get_selected_card_shop_test()
        enabled, button_label = self.get_card_shop_purchase_state()
        if selected is None:
            self.card_shop_message = "Select a card before purchasing."
            return False
        if not enabled:
            self.card_shop_message = button_label.replace("  •  ", " ").title()
            return False

        price = self.get_card_shop_price()
        card = self.deck.draw_matching(selected.name)
        if card is None:
            self.card_shop_message = f"{selected.name.title()} is sold out."
            return False

        if self.showing_diagnosis_hand:
            self.switch_active_hand(False)
        self.start_live_money_deduction(price, "CARD SHOP")
        self.daily_card_shop_expenses += price
        self.daily_card_shop_purchases += 1
        self.card_shop_patient_purchases += 1
        self.player.draw(card)
        self.refresh_hand_layout()
        self.card_shop_notice = f"{selected.name.title()} added to your hand."
        self.card_shop_notice_started_at = pygame.time.get_ticks()
        self.card_shop_message = (
            f"{selected.name.title()} added. Next card costs ${self.get_card_shop_price()}."
        )
        self.play_sfx("card_select")
        return True

    def handle_card_shop_click(self, position):
        """Handle shop selection, purchase, and close controls as a modal."""

        if self.card_shop_button.collidepoint(position) or self.card_shop_close_button.collidepoint(position):
            self.toggle_card_shop()
            return
        for test, rect in zip(self.card_shop_catalog, self.get_card_shop_slot_rects()):
            if rect.collidepoint(position):
                self.selected_card_shop_test = test.name
                inventory = self.get_card_shop_inventory_count(test.name)
                self.card_shop_message = f"{test.name.title()} selected  •  {inventory} left in deck."
                self.play_sfx("button")
                return
        if self.card_shop_buy_button.collidepoint(position):
            self.purchase_selected_card_shop_test()
