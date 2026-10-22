"""Reusable card interaction and rendering for The Cosmic Clinic GUI."""

import math

import pygame

from gui_state import GameState
from gui_theme import (
    COLORS,
    RARITY_CARD_COLORS,
    RARITY_COLORS,
    TEST_SUBTITLES,
    WINDOW_SIZE,
)
from Player import DIAGNOSIS_REWARD


class CardMixin:
    def get_active_hand(self):
        """Return whichever card hand is currently displayed in the center panel."""

        if self.showing_diagnosis_hand:
            return self.player.diagnosis_hand
        return self.player.test_hand


    def switch_active_hand(self, show_diagnoses):
        """Switch between test and diagnosis cards and clear the previous selection."""

        self.showing_diagnosis_hand = show_diagnoses
        self.selected_card_index = None
        self.run_test_button = None
        self.discard_button = None
        self.play_diagnosis_button = None
        self.diagnosis_confirmation_open = False
        self.diagnosis_folder_animation_started_at = (
            pygame.time.get_ticks() if show_diagnoses else None
        )
        self.refresh_hand_layout()


    def calculate_hand_layout(self, card_count):
        """Calculate a centered fan for any number of cards without changing game data."""

        panel = self.layout["active_hand"]
        card_width = 96
        card_height = 118

        if card_count == 0:
            return []

        usable_width = panel.width - 28
        if card_count == 1:
            card_step = 0
            total_width = card_width
        else:
            available_step = (usable_width - card_width) / (card_count - 1)
            card_step = min(card_width - 4, available_step)
            total_width = card_width + card_step * (card_count - 1)
        start_x = panel.centerx - total_width // 2
        hand_center = (card_count - 1) / 2

        return [
            pygame.Rect(
                round(start_x + index * card_step),
                panel.y + 43 + min(9, round(abs(index - hand_center) * 3)),
                card_width,
                card_height,
            )
            for index in range(card_count)
        ]


    def refresh_hand_layout(self):
        """Recalculate positions after player.draw, play, discard, or a hand switch."""

        self.card_rects = self.calculate_hand_layout(len(self.get_active_hand()))
        if (
            self.selected_card_index is not None
            and self.selected_card_index >= len(self.card_rects)
        ):
            self.selected_card_index = None


    def build_card_rects(self):
        """Return the current hand layout for compatibility with earlier GUI code."""

        return self.calculate_hand_layout(len(self.get_active_hand()))


    def handle_card_click(self, position):
        """Select or dismiss a card and run it when it belongs to the test hand."""

        if self.selected_card_index is not None:
            selected_rect = self.get_selected_card_rect(self.selected_card_index)
            if self.showing_diagnosis_hand:
                action_button = self.get_card_action_button(selected_rect)
                if action_button.collidepoint(position):
                    self.open_diagnosis_confirmation()
                    return
            else:
                if self.get_run_test_button(selected_rect).collidepoint(position):
                    self.run_selected_test()
                    return
                if self.get_discard_button(selected_rect).collidepoint(position):
                    self.discard_selected_test()
                    return

            if selected_rect.collidepoint(position):
                self.selected_card_index = None
                return

        for index in reversed(range(len(self.card_rects))):
            if self.card_rects[index].collidepoint(position):
                self.selected_card_index = index
                return

        if self.selected_card_index is not None:
            self.selected_card_index = None


    def run_selected_test(self):
        """Play the selected test card and open its patient-specific result screen."""

        if self.selected_card_index is None:
            return
        if self.showing_diagnosis_hand:
            return

        card = self.player.test_hand[self.selected_card_index]
        self.last_test_name = card.value.name
        result = self.patient.perform_test(self.last_test_name)
        self.last_test_result = result.replace("RESULTS: ", "", 1)

        self.player.play(card)
        self.pending_test_discard = card
        self.selected_card_index = None
        self.run_test_button = None
        self.refresh_hand_layout()
        self.test_result_started_at = pygame.time.get_ticks()
        self.state = GameState.TEST_RESULT
        self.notebook.add_test(self.patient, self.last_test_name, self.last_test_result)


    def discard_selected_test(self):
        """Move the selected test card to the throwaway pile without running it."""

        if self.showing_diagnosis_hand or self.selected_card_index is None:
            return

        selected_rect = self.get_selected_card_rect(self.selected_card_index)
        card = self.player.test_hand.pop(self.selected_card_index)
        self.discard_pile.append(card)
        self.discard_animation = {
            "card": card,
            "start": selected_rect.center,
            "started_at": pygame.time.get_ticks(),
        }
        self.selected_card_index = None
        self.run_test_button = None
        self.discard_button = None
        self.refresh_hand_layout()


    def start_pending_test_discard_animation(self):
        """Begin the card-to-bin animation after its result has entered the notebook."""

        if self.pending_test_discard is None:
            return
        self.discard_animation = {
            "card": self.pending_test_discard,
            "start": self.layout["active_hand"].center,
            "started_at": pygame.time.get_ticks(),
            "duration": self.test_discard_animation_duration,
            "add_to_pile_on_complete": True,
            "locks_input": True,
            "arc_height": 105,
        }
        self.pending_test_discard = None


    def get_selected_card_rect(self, index):
        """Return the larger rectangle used to display a selected test card."""

        preview = pygame.Rect(0, 0, 220, 218)
        preview.midbottom = (
            self.card_rects[index].centerx,
            self.layout["active_hand"].bottom - 5,
        )
        return preview


    def get_run_test_button(self, selected_rect):
        """Return the Run Test button rectangle for an enlarged card."""

        return pygame.Rect(
            selected_rect.x + 16,
            selected_rect.bottom - 38,
            90,
            28,
        )


    def get_discard_button(self, selected_rect):
        """Return the Discard button rectangle for an enlarged test card."""

        return pygame.Rect(
            selected_rect.right - 106,
            selected_rect.bottom - 38,
            90,
            28,
        )


    def get_card_action_button(self, selected_rect):
        """Return the action-button rectangle used by an enlarged card."""

        return pygame.Rect(
            selected_rect.x + 24,
            selected_rect.bottom - 38,
            selected_rect.width - 48,
            28,
        )


    def play_selected_diagnosis(self):
        """Play the selected diagnosis and open its correct-or-incorrect result."""

        if not self.showing_diagnosis_hand or self.selected_card_index is None:
            return

        card = self.player.diagnosis_hand[self.selected_card_index]
        self.diagnosis_confirmation_open = False
        self.last_diagnosis = card.value
        self.player.play(card)
        self.diagnosis_correct = self.patient.receive_diagnosis(card.value)
        if self.diagnosis_correct:
            self.player.earn(DIAGNOSIS_REWARD)
        self.selected_card_index = None
        self.play_diagnosis_button = None
        self.state = GameState.OUTCOME


    def open_diagnosis_confirmation(self):
        """Open a confirmation dialog for the currently selected diagnosis card."""

        if self.showing_diagnosis_hand and self.selected_card_index is not None:
            self.diagnosis_confirmation_open = True


    def confirm_selected_diagnosis(self):
        """Confirm and play the diagnosis currently shown in the dialog."""

        if not self.diagnosis_confirmation_open:
            return
        self.diagnosis_confirmation_open = False
        self.play_selected_diagnosis()


    def handle_diagnosis_confirmation_click(self, position):
        """Handle the submit and return buttons in the diagnosis confirmation dialog."""

        if self.diagnosis_confirm_button.collidepoint(position):
            self.confirm_selected_diagnosis()
        elif self.diagnosis_cancel_button.collidepoint(position):
            self.diagnosis_confirmation_open = False


    def draw_active_hand(self):
        """Draw the currently active test or diagnosis hand and its selection state."""

        panel = self.layout["active_hand"]
        tray = panel.inflate(-8, -8)
        tray.y += 3
        pygame.draw.rect(
            self.screen,
            (8, 12, 20),
            tray.move(5, 6),
            border_radius=13,
        )
        pygame.draw.rect(self.screen, (20, 28, 39), tray, border_radius=13)
        pygame.draw.rect(
            self.screen,
            (90, 88, 113),
            tray,
            width=2,
            border_radius=13,
        )
        pygame.draw.rect(
            self.screen,
            (11, 18, 27),
            tray.inflate(-12, -12),
            width=1,
            border_radius=9,
        )
        hand_name = (
            "DIAGNOSIS OPTIONS"
            if self.showing_diagnosis_hand
            else "AVAILABLE TESTS"
        )
        name_plate = pygame.Rect(0, 0, 158, 24)
        name_plate.midtop = (tray.centerx, tray.y + 5)
        pygame.draw.rect(self.screen, (38, 48, 61), name_plate, border_radius=7)
        pygame.draw.rect(
            self.screen,
            (112, 119, 142),
            name_plate,
            width=1,
            border_radius=7,
        )
        self.draw_centered_label(hand_name, name_plate, name_plate.centery)

        for light_x, light_color in (
            (tray.x + 18, COLORS["accent"]),
            (tray.x + 29, (79, 151, 235)),
            (tray.right - 29, (79, 151, 235)),
            (tray.right - 18, COLORS["accent"]),
        ):
            pygame.draw.circle(self.screen, (8, 14, 21), (light_x, tray.y + 17), 4)
            pygame.draw.circle(self.screen, light_color, (light_x, tray.y + 17), 2)

        active_hand = self.get_active_hand()
        # Future draw-card code can update the hand data without managing coordinates.
        if len(self.card_rects) != len(active_hand):
            self.refresh_hand_layout()

        if not active_hand:
            empty_text = (
                "NO DIAGNOSIS CARDS"
                if self.showing_diagnosis_hand
                else "NO TEST CARDS"
            )
            empty = self.body_font.render(empty_text, True, COLORS["muted"])
            self.screen.blit(empty, empty.get_rect(center=panel.center))
            return

        mouse_position = pygame.mouse.get_pos()

        for index, card in enumerate(active_hand):
            if index == self.selected_card_index:
                continue

            card_rect = self.card_rects[index]
            hovered = (
                self.selected_card_index is None
                and card_rect.collidepoint(mouse_position)
            )
            display_rect = (
                self.get_hovered_card_rect(card_rect)
                if hovered
                else card_rect
            )
            if self.showing_diagnosis_hand:
                self.draw_diagnosis_card(card, display_rect, hovered=hovered)
            else:
                self.draw_test_card(card, display_rect, hovered=hovered)
            if self.selected_card_index is not None:
                self.draw_card_dimming_overlay(display_rect)

        if self.selected_card_index is not None:
            selected_card = active_hand[self.selected_card_index]
            selected_rect = self.get_selected_card_rect(self.selected_card_index)
            if self.showing_diagnosis_hand:
                self.draw_diagnosis_card(selected_card, selected_rect, selected=True)
            else:
                self.draw_test_card(selected_card, selected_rect, selected=True)


    def get_hovered_card_rect(self, card_rect):
        """Lift and gently enlarge a hovered card without changing its color."""

        width_growth = max(4, round(card_rect.width * 0.04))
        height_growth = max(6, round(card_rect.height * 0.04))
        return card_rect.inflate(width_growth, height_growth).move(0, -7)


    def get_card_shape_points(self, card_rect, corner_cut=7):
        """Return the clipped-corner outline shared by every card style."""

        return (
            (card_rect.x + corner_cut, card_rect.y),
            (card_rect.right - corner_cut, card_rect.y),
            (card_rect.right, card_rect.y + corner_cut),
            (card_rect.right, card_rect.bottom - corner_cut),
            (card_rect.right - corner_cut, card_rect.bottom),
            (card_rect.x + corner_cut, card_rect.bottom),
            (card_rect.x, card_rect.bottom - corner_cut),
            (card_rect.x, card_rect.y + corner_cut),
        )


    def draw_card_shell(
        self,
        card_rect,
        fill_color,
        border_color,
        border_width,
        selected,
        hovered=False,
    ):
        """Draw one reusable sci-fi card body with a clipped outline and shadow."""

        corner_cut = 10 if selected else 7
        if hovered:
            soft_shadow = card_rect.inflate(10, 10).move(6, 8)
            pygame.draw.polygon(
                self.screen,
                (9, 16, 24),
                self.get_card_shape_points(soft_shadow, corner_cut + 3),
            )

        shadow_offset = 7 if selected else 5 if hovered else 4
        shadow_rect = card_rect.move(shadow_offset, shadow_offset)
        pygame.draw.polygon(
            self.screen,
            (3, 8, 12),
            self.get_card_shape_points(shadow_rect, corner_cut),
        )
        card_points = self.get_card_shape_points(card_rect, corner_cut)
        pygame.draw.polygon(self.screen, fill_color, card_points)
        pygame.draw.polygon(
            self.screen,
            border_color,
            card_points,
            width=border_width,
        )


    def draw_card_dimming_overlay(self, card_rect):
        """Subtly dim unselected cards while an enlarged card has focus."""

        overlay = pygame.Surface(card_rect.size, pygame.SRCALPHA)
        local_rect = overlay.get_rect()
        pygame.draw.polygon(
            overlay,
            (5, 11, 17, 42),
            self.get_card_shape_points(local_rect, 7),
        )
        self.screen.blit(overlay, card_rect.topleft)


    def draw_fitted_card_title(self, title, area, selected=False):
        """Choose the largest existing font that keeps a card title inside its header."""

        fonts = (
            (self.body_font, self.small_font, self.card_font)
            if selected
            else (self.card_font, self.pile_font, self.tiny_font)
        )
        font = fonts[-1]
        for candidate in fonts:
            if candidate.size(title)[0] <= area.width - 8:
                font = candidate
                break
        title_surface = font.render(title, True, COLORS["card_text"])
        self.screen.blit(title_surface, title_surface.get_rect(center=area.center))


    def draw_rarity_badge(self, rarity, card_rect):
        """Show card rarity with both text and a shape so color is not the only cue."""

        rarity_color = RARITY_COLORS.get(rarity, COLORS["panel_border"])
        badge = pygame.Rect(
            card_rect.x + 7,
            card_rect.bottom - 23,
            card_rect.width - 14,
            16,
        )
        pygame.draw.rect(self.screen, (203, 214, 202), badge, border_radius=6)
        pygame.draw.rect(
            self.screen,
            rarity_color,
            badge,
            width=1,
            border_radius=6,
        )

        symbol_center = (badge.x + 11, badge.centery)
        if rarity == "Rare":
            symbol = (
                (symbol_center[0], symbol_center[1] - 5),
                (symbol_center[0] + 3, symbol_center[1] - 2),
                (symbol_center[0] + 5, symbol_center[1]),
                (symbol_center[0] + 2, symbol_center[1] + 2),
                (symbol_center[0], symbol_center[1] + 5),
                (symbol_center[0] - 2, symbol_center[1] + 2),
                (symbol_center[0] - 5, symbol_center[1]),
                (symbol_center[0] - 3, symbol_center[1] - 2),
            )
            pygame.draw.polygon(self.screen, rarity_color, symbol)
        elif rarity == "Uncommon":
            pygame.draw.polygon(
                self.screen,
                rarity_color,
                (
                    (symbol_center[0], symbol_center[1] - 5),
                    (symbol_center[0] + 5, symbol_center[1]),
                    (symbol_center[0], symbol_center[1] + 5),
                    (symbol_center[0] - 5, symbol_center[1]),
                ),
            )
        else:
            pygame.draw.circle(self.screen, rarity_color, symbol_center, 4)

        rarity_text = self.pile_font.render(rarity.upper(), True, rarity_color)
        self.screen.blit(
            rarity_text,
            rarity_text.get_rect(midleft=(badge.x + 20, badge.centery)),
        )


    def draw_diagnosis_card(self, card, card_rect, hovered=False, selected=False):
        """Draw one diagnosis card in either its compact or enlarged state."""

        diagnosis = card.value
        diagnosis_color = (183, 92, 211)
        border_color = diagnosis_color
        border_width = 4 if selected else 2
        self.draw_card_shell(
            card_rect,
            (235, 220, 239),
            border_color,
            border_width,
            selected,
            hovered=hovered,
        )

        if selected:
            self.draw_selected_diagnosis_details(
                diagnosis,
                card_rect,
                diagnosis_color,
            )
        else:
            self.draw_compact_diagnosis_card(
                diagnosis,
                card_rect,
                diagnosis_color,
            )


    def draw_compact_diagnosis_card(self, diagnosis, card_rect, diagnosis_color):
        """Draw a diagnosis option with the same hierarchy as a compact test card."""

        header = pygame.Rect(card_rect.x + 6, card_rect.y + 6, card_rect.width - 12, 30)
        pygame.draw.rect(self.screen, (218, 199, 226), header, border_radius=5)
        pygame.draw.line(
            self.screen,
            diagnosis_color,
            (header.x + 6, header.bottom),
            (header.right - 6, header.bottom),
        )
        # Base this decision on the resting 96-pixel card, not the slightly wider
        # hover rectangle, so titles never switch fonts while the mouse moves.
        resting_single_line_width = 80
        if (
            self.diagnosis_card_font.size(diagnosis.name)[0]
            <= resting_single_line_width
        ):
            title = self.diagnosis_card_font.render(
                diagnosis.name,
                True,
                COLORS["card_text"],
            )
            self.screen.blit(title, title.get_rect(center=header.center))
        else:
            name_parts = diagnosis.name.split(maxsplit=1)
            for line_index, line_text in enumerate(name_parts):
                title = self.pile_font.render(line_text, True, COLORS["card_text"])
                line_y = header.centery - 6 + line_index * 11
                self.screen.blit(
                    title,
                    title.get_rect(center=(header.centerx, line_y)),
                )

        icon = pygame.Rect(card_rect.centerx - 25, card_rect.y + 40, 50, 43)
        pygame.draw.rect(self.screen, (210, 211, 216), icon, border_radius=6)
        pygame.draw.rect(self.screen, diagnosis_color, icon, width=2, border_radius=6)
        self.draw_diagnosis_file_icon(icon, diagnosis_color)

        subtitle = self.card_font.render(
            "CASE FILE",
            True,
            COLORS["card_text"],
        )
        self.screen.blit(
            subtitle,
            subtitle.get_rect(center=(card_rect.centerx, card_rect.y + 90)),
        )
        self.draw_diagnosis_badge(card_rect, diagnosis_color)


    def draw_selected_diagnosis_details(self, diagnosis, card_rect, diagnosis_color):
        """Draw the enlarged diagnosis file with its description and play action."""

        header = pygame.Rect(card_rect.x + 9, card_rect.y + 8, card_rect.width - 18, 39)
        pygame.draw.rect(self.screen, (218, 199, 226), header, border_radius=7)
        self.draw_fitted_card_title(diagnosis.name, header, selected=True)
        type_label = self.card_font.render("FINAL DIAGNOSIS", True, diagnosis_color)
        self.screen.blit(
            type_label,
            type_label.get_rect(center=(card_rect.centerx, card_rect.y + 56)),
        )

        icon = pygame.Rect(card_rect.x + 16, card_rect.y + 68, 58, 58)
        pygame.draw.rect(self.screen, (210, 211, 216), icon, border_radius=7)
        pygame.draw.rect(self.screen, diagnosis_color, icon, width=2, border_radius=7)
        self.draw_diagnosis_file_icon(icon, diagnosis_color)

        description_box = pygame.Rect(
            card_rect.x + 84,
            card_rect.y + 69,
            card_rect.width - 100,
            100,
        )
        self.draw_wrapped_text(
            diagnosis.description,
            self.card_font,
            COLORS["card_text"],
            description_box,
        )

        self.play_diagnosis_button = self.get_card_action_button(card_rect)
        pygame.draw.rect(
            self.screen,
            diagnosis_color,
            self.play_diagnosis_button,
            border_radius=5,
        )
        pygame.draw.rect(
            self.screen,
            (218, 159, 235),
            self.play_diagnosis_button,
            width=2,
            border_radius=5,
        )
        play_text = self.small_font.render(
            "PLAY DIAGNOSIS",
            True,
            COLORS["background"],
        )
        self.screen.blit(
            play_text,
            play_text.get_rect(center=self.play_diagnosis_button.center),
        )


    def draw_diagnosis_file_icon(self, icon, diagnosis_color):
        """Draw a clipped patient-file symbol in place of the old letter placeholder."""

        icon_surface = pygame.Surface(icon.size, pygame.SRCALPHA)
        center_x, center_y = icon_surface.get_rect().center
        paper = pygame.Rect(center_x - 13, center_y - 14, 27, 30)
        pygame.draw.rect(icon_surface, (240, 234, 219), paper, border_radius=3)
        pygame.draw.rect(icon_surface, COLORS["card_text"], paper, width=2, border_radius=3)
        clip = pygame.Rect(center_x - 7, paper.y - 3, 14, 7)
        pygame.draw.rect(icon_surface, diagnosis_color, clip, border_radius=3)
        pygame.draw.line(
            icon_surface,
            (118, 122, 116),
            (paper.x + 5, paper.y + 9),
            (paper.right - 5, paper.y + 9),
            width=2,
        )
        pygame.draw.line(
            icon_surface,
            (118, 122, 116),
            (paper.x + 5, paper.y + 14),
            (paper.right - 8, paper.y + 14),
            width=2,
        )
        pygame.draw.line(
            icon_surface,
            diagnosis_color,
            (paper.x + 6, paper.bottom - 8),
            (paper.x + 11, paper.bottom - 4),
            width=2,
        )
        pygame.draw.line(
            icon_surface,
            diagnosis_color,
            (paper.x + 11, paper.bottom - 4),
            (paper.right - 5, paper.bottom - 12),
            width=2,
        )
        self.screen.blit(icon_surface, icon.topleft)


    def draw_diagnosis_badge(self, card_rect, diagnosis_color):
        """Draw the diagnosis-type badge in the same position as test rarity badges."""

        badge = pygame.Rect(
            card_rect.x + 7,
            card_rect.bottom - 23,
            card_rect.width - 14,
            16,
        )
        pygame.draw.rect(self.screen, (213, 205, 218), badge, border_radius=6)
        pygame.draw.rect(self.screen, diagnosis_color, badge, width=1, border_radius=6)
        symbol_center = (badge.x + 11, badge.centery)
        pygame.draw.polygon(
            self.screen,
            diagnosis_color,
            (
                (symbol_center[0], symbol_center[1] - 5),
                (symbol_center[0] + 5, symbol_center[1]),
                (symbol_center[0], symbol_center[1] + 5),
                (symbol_center[0] - 5, symbol_center[1]),
            ),
        )
        label = self.pile_font.render("DIAGNOSIS", True, diagnosis_color)
        self.screen.blit(
            label,
            label.get_rect(midleft=(badge.x + 20, badge.centery)),
        )


    def draw_test_card(self, card, card_rect, hovered=False, selected=False):
        """Draw one test card in either its compact or enlarged state."""

        test = card.value
        rarity_color = RARITY_COLORS.get(test.rarity, COLORS["panel_border"])
        card_color = RARITY_CARD_COLORS.get(test.rarity, COLORS["card"])
        border_color = rarity_color
        border_width = 4 if selected else 2
        self.draw_card_shell(
            card_rect,
            card_color,
            border_color,
            border_width,
            selected,
            hovered=hovered,
        )

        if selected:
            self.draw_selected_card_details(test, card_rect, rarity_color)
        else:
            self.draw_compact_card(test, card_rect, rarity_color)


    def draw_compact_card(self, test, card_rect, rarity_color):
        """Draw the compact header, artwork, subtitle, and rarity badge of a test card."""

        header = pygame.Rect(card_rect.x + 6, card_rect.y + 6, card_rect.width - 12, 25)
        header_color = tuple(max(0, channel - 18) for channel in RARITY_CARD_COLORS.get(
            test.rarity,
            COLORS["card"],
        ))
        pygame.draw.rect(self.screen, header_color, header, border_radius=5)
        pygame.draw.line(
            self.screen,
            rarity_color,
            (header.x + 6, header.bottom),
            (header.right - 6, header.bottom),
            width=1,
        )
        self.draw_fitted_card_title(test.name, header)

        icon = pygame.Rect(card_rect.centerx - 25, card_rect.y + 35, 50, 45)
        pygame.draw.rect(self.screen, (201, 214, 205), icon, border_radius=6)
        pygame.draw.rect(self.screen, rarity_color, icon, width=2, border_radius=6)
        self.draw_test_icon(test.name, icon, rarity_color)

        subtitle = self.tiny_font.render(
            TEST_SUBTITLES.get(test.name.upper(), "MEDICAL TEST"),
            True,
            COLORS["card_text"],
        )
        self.screen.blit(
            subtitle,
            subtitle.get_rect(center=(card_rect.centerx, card_rect.y + 88)),
        )
        self.draw_rarity_badge(test.rarity, card_rect)


    def draw_selected_card_details(self, test, card_rect, rarity_color):
        """Draw an enlarged test card with Run Test and Discard buttons."""

        header = pygame.Rect(card_rect.x + 9, card_rect.y + 8, card_rect.width - 18, 39)
        header_color = tuple(max(0, channel - 18) for channel in RARITY_CARD_COLORS.get(
            test.rarity,
            COLORS["card"],
        ))
        pygame.draw.rect(self.screen, header_color, header, border_radius=7)
        self.draw_fitted_card_title(test.name, header, selected=True)

        rarity = self.card_font.render(test.rarity.upper(), True, rarity_color)
        self.screen.blit(rarity, rarity.get_rect(center=(card_rect.centerx, card_rect.y + 55)))

        icon = pygame.Rect(card_rect.x + 16, card_rect.y + 65, 58, 58)
        pygame.draw.rect(self.screen, (201, 214, 205), icon, border_radius=7)
        pygame.draw.rect(self.screen, rarity_color, icon, width=2, border_radius=7)
        self.draw_test_icon(test.name, icon, rarity_color)

        subtitle = self.tiny_font.render(
            TEST_SUBTITLES.get(test.name.upper(), "MEDICAL TEST"),
            True,
            COLORS["card_text"],
        )
        self.screen.blit(
            subtitle,
            subtitle.get_rect(center=(icon.centerx, icon.bottom + 9)),
        )

        description_box = pygame.Rect(
            card_rect.x + 84,
            card_rect.y + 67,
            card_rect.width - 100,
            100,
        )
        self.draw_wrapped_text(
            test.description,
            self.card_font,
            COLORS["card_text"],
            description_box,
        )

        self.run_test_button = self.get_run_test_button(card_rect)
        pygame.draw.rect(
            self.screen, COLORS["panel_border"], self.run_test_button, border_radius=5
        )
        run_text = self.small_font.render("RUN TEST", True, COLORS["background"])
        self.screen.blit(run_text, run_text.get_rect(center=self.run_test_button.center))

        self.discard_button = self.get_discard_button(card_rect)
        pygame.draw.rect(
            self.screen,
            (205, 100, 100),
            self.discard_button,
            border_radius=5,
        )
        discard_text = self.small_font.render(
            "DISCARD",
            True,
            COLORS["background"],
        )
        self.screen.blit(
            discard_text,
            discard_text.get_rect(center=self.discard_button.center),
        )


    def draw_test_icon(self, test_name, icon, rarity_color):
        """Render a test symbol onto a clipped surface that cannot escape its frame."""

        icon_surface = pygame.Surface(icon.size, pygame.SRCALPHA)
        icon_area = icon_surface.get_rect()
        center_x, center_y = icon_area.center
        ink = COLORS["card_text"]
        test_name = test_name.upper()

        if test_name == "TEMPERATURE":
            pygame.draw.circle(icon_surface, rarity_color, (center_x, center_y + 8), 6)
            pygame.draw.rect(
                icon_surface,
                ink,
                pygame.Rect(center_x - 3, center_y - 13, 6, 20),
                border_radius=3,
            )
            pygame.draw.rect(
                icon_surface,
                rarity_color,
                pygame.Rect(center_x - 1, center_y - 9, 2, 16),
            )
            pygame.draw.circle(icon_surface, ink, (center_x, center_y + 8), 8, width=2)
        elif test_name == "ULTRASOUND":
            probe = pygame.Rect(center_x - 16, center_y - 8, 7, 16)
            pygame.draw.rect(icon_surface, ink, probe, border_radius=3)
            for wave_number, radius in enumerate((6, 10, 14)):
                wave = pygame.Rect(
                    center_x - 10,
                    center_y - radius,
                    radius * 2,
                    radius * 2,
                )
                pygame.draw.arc(
                    icon_surface,
                    rarity_color if wave_number == 2 else ink,
                    wave,
                    -math.pi / 3,
                    math.pi / 3,
                    width=2,
                )
        elif test_name == "X-RAY":
            for offset in (-4, 4):
                start = (center_x - 9, center_y + offset)
                end = (center_x + 9, center_y - offset)
                pygame.draw.line(icon_surface, ink, start, end, width=4)
                pygame.draw.circle(icon_surface, rarity_color, start, 4)
                pygame.draw.circle(icon_surface, rarity_color, end, 4)
                pygame.draw.circle(icon_surface, ink, start, 4, width=1)
                pygame.draw.circle(icon_surface, ink, end, 4, width=1)
        elif test_name == "ALLERGY":
            drop = (
                (center_x, center_y - 14),
                (center_x - 10, center_y + 3),
                (center_x - 8, center_y + 11),
                (center_x, center_y + 15),
                (center_x + 8, center_y + 11),
                (center_x + 10, center_y + 3),
            )
            pygame.draw.polygon(icon_surface, rarity_color, drop)
            pygame.draw.polygon(icon_surface, ink, drop, width=2)
            pygame.draw.circle(
                icon_surface,
                (238, 246, 228),
                (center_x + 3, center_y + 3),
                3,
            )
        else:
            icon_text = self.body_font.render(test_name[0], True, ink)
            icon_surface.blit(icon_text, icon_text.get_rect(center=icon_area.center))

        self.screen.blit(icon_surface, icon.topleft)


    def draw_diagnosis_cards(self):
        """Draw the diagnosis folder standing in a compact desktop file rack."""

        panel = self.layout["diagnosis"]
        mouse_position = pygame.mouse.get_pos()
        hovered = panel.collidepoint(mouse_position)
        folder_lift = 5 if hovered and not self.showing_diagnosis_hand else 0
        progress = self.get_diagnosis_folder_progress()

        rack = pygame.Rect(panel.x + 24, panel.y + 27, panel.width - 48, 105)
        pygame.draw.rect(self.screen, (8, 12, 20), rack.move(5, 6), border_radius=10)
        pygame.draw.rect(self.screen, (42, 37, 58), rack, border_radius=10)
        pygame.draw.rect(
            self.screen,
            (125, 98, 145),
            rack,
            width=2,
            border_radius=10,
        )
        for slot_offset in (20, 34):
            pygame.draw.line(
                self.screen,
                (76, 61, 94),
                (rack.x + slot_offset, rack.y + 12),
                (rack.x + slot_offset, rack.bottom - 10),
                width=2,
            )

        base = pygame.Rect(rack.x - 8, rack.bottom - 13, rack.width + 16, 19)
        pygame.draw.rect(self.screen, (31, 29, 45), base, border_radius=6)
        pygame.draw.rect(
            self.screen,
            (108, 92, 129),
            base,
            width=2,
            border_radius=6,
        )

        folder = pygame.Rect(
            rack.x + 18,
            rack.y + 25 - folder_lift,
            rack.width - 32,
            67,
        )
        folder_shadow = folder.move(4, 5)
        pygame.draw.rect(self.screen, (5, 10, 16), folder_shadow, border_radius=7)

        tab = pygame.Rect(folder.x + 5, folder.y - 13, folder.width - 18, 22)
        pygame.draw.rect(self.screen, (111, 72, 142), tab, border_radius=6)
        tab_text = self.card_font.render("DIAGNOSIS", True, COLORS["text"])
        self.screen.blit(tab_text, tab_text.get_rect(center=(tab.centerx, tab.y + 8)))

        pygame.draw.rect(self.screen, (92, 58, 119), folder, border_radius=7)
        pygame.draw.rect(self.screen, (181, 124, 207), folder, width=2, border_radius=7)

        page_rise = round(18 * progress)
        for page_number, page_color in enumerate(((215, 224, 204), (229, 235, 216))):
            page = pygame.Rect(
                folder.x + 10 + page_number * 5,
                folder.y + 11 - page_rise - page_number * 3,
                folder.width - 20,
                43,
            )
            pygame.draw.rect(self.screen, page_color, page, border_radius=4)
            pygame.draw.rect(
                self.screen,
                COLORS["card_text"],
                page,
                width=1,
                border_radius=4,
            )
            pygame.draw.line(
                self.screen,
                (146, 159, 144),
                (page.x + 7, page.y + 13),
                (page.right - 7, page.y + 13),
            )
            pygame.draw.line(
                self.screen,
                (146, 159, 144),
                (page.x + 7, page.y + 22),
                (page.right - 15, page.y + 22),
            )

        cover_y = folder.y + 20 + round(13 * progress)
        cover_height = max(27, folder.bottom - cover_y)
        cover = pygame.Rect(folder.x, cover_y, folder.width, cover_height)
        pygame.draw.rect(self.screen, (126, 78, 151), cover, border_radius=7)
        pygame.draw.rect(
            self.screen,
            (204, 145, 226),
            cover,
            width=2,
            border_radius=7,
        )

        seal_center = (cover.centerx, cover.y + min(16, cover.height // 2))
        pygame.draw.circle(self.screen, (216, 159, 238), seal_center, 8)
        warning_text = self.card_font.render("!", True, (43, 31, 60))
        self.screen.blit(warning_text, warning_text.get_rect(center=seal_center))

        if self.showing_diagnosis_hand:
            return_button = pygame.Rect(panel.x + 24, panel.bottom - 28, panel.width - 48, 23)
            return_hovered = return_button.collidepoint(mouse_position)
            button_color = COLORS["accent"] if return_hovered else (151, 101, 180)
            pygame.draw.rect(self.screen, button_color, return_button, border_radius=6)
            return_text = self.pile_font.render(
                "<  RETURN TO TESTS",
                True,
                COLORS["background"],
            )
            self.screen.blit(return_text, return_text.get_rect(center=return_button.center))
        elif hovered:
            open_text = self.pile_font.render("OPEN FILE", True, COLORS["accent"])
            self.screen.blit(
                open_text,
                open_text.get_rect(center=(panel.centerx, panel.bottom - 8)),
            )


    def get_diagnosis_folder_progress(self):
        """Return the eased opening progress for the diagnosis folder animation."""

        if not self.showing_diagnosis_hand:
            return 0.0
        if self.diagnosis_folder_animation_started_at is None:
            return 1.0
        elapsed = pygame.time.get_ticks() - self.diagnosis_folder_animation_started_at
        progress = min(1.0, elapsed / self.diagnosis_folder_animation_duration)
        return 1 - (1 - progress) ** 3


    def draw_diagnosis_confirmation(self):
        """Draw a modal that asks the player to confirm the selected diagnosis."""

        if self.selected_card_index is None:
            return

        diagnosis = self.player.diagnosis_hand[self.selected_card_index].value
        dim = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        dim.fill((3, 7, 12, 205))
        self.screen.blit(dim, (0, 0))

        panel = pygame.Rect(245, 155, 610, 335)
        pygame.draw.rect(self.screen, (3, 8, 12), panel.move(8, 9), border_radius=16)
        pygame.draw.rect(self.screen, (40, 28, 52), panel, border_radius=16)
        pygame.draw.rect(self.screen, (204, 145, 226), panel, width=3, border_radius=16)

        warning_circle = (panel.centerx, panel.y + 48)
        pygame.draw.circle(self.screen, (216, 159, 238), warning_circle, 22)
        warning_mark = self.heading_font.render("!", True, (43, 31, 60))
        self.screen.blit(warning_mark, warning_mark.get_rect(center=warning_circle))

        heading = self.heading_font.render(
            "FINAL DIAGNOSIS CONFIRMATION",
            True,
            COLORS["text"],
        )
        self.screen.blit(heading, heading.get_rect(center=(panel.centerx, panel.y + 93)))

        diagnosis_name = self.heading_font.render(
            diagnosis.name,
            True,
            (216, 159, 238),
        )
        self.screen.blit(
            diagnosis_name,
            diagnosis_name.get_rect(center=(panel.centerx, panel.y + 142)),
        )

        question = self.body_font.render(
            f"Submit {diagnosis.name} as your final diagnosis?",
            True,
            COLORS["text"],
        )
        self.screen.blit(question, question.get_rect(center=(panel.centerx, panel.y + 186)))

        warning = self.small_font.render(
            "An incorrect diagnosis will return you to the examination.",
            True,
            COLORS["muted"],
        )
        self.screen.blit(warning, warning.get_rect(center=(panel.centerx, panel.y + 222)))

        mouse_position = pygame.mouse.get_pos()
        cancel_color = (
            (120, 126, 139)
            if self.diagnosis_cancel_button.collidepoint(mouse_position)
            else (79, 83, 98)
        )
        confirm_color = (
            COLORS["accent"]
            if self.diagnosis_confirm_button.collidepoint(mouse_position)
            else (151, 101, 180)
        )
        pygame.draw.rect(
            self.screen,
            cancel_color,
            self.diagnosis_cancel_button,
            border_radius=8,
        )
        pygame.draw.rect(
            self.screen,
            confirm_color,
            self.diagnosis_confirm_button,
            border_radius=8,
        )

        cancel_text = self.body_font.render("GO BACK", True, COLORS["text"])
        confirm_text = self.body_font.render(
            "SUBMIT DIAGNOSIS",
            True,
            COLORS["background"],
        )
        self.screen.blit(
            cancel_text,
            cancel_text.get_rect(center=self.diagnosis_cancel_button.center),
        )
        self.screen.blit(
            confirm_text,
            confirm_text.get_rect(center=self.diagnosis_confirm_button.center),
        )

