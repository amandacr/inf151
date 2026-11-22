"""Reusable card interaction and rendering for The Cosmic Clinic GUI."""

import math
import random

import pygame

from Card import Card
from gui_state import GameState
from gui_theme import (
    COLORS,
    RARITY_CARD_COLORS,
    RARITY_COLORS,
    TEST_SUBTITLES,
    WINDOW_SIZE,
)
from Player import (
    DRAW_COST,
    MAX_TEST_HAND_SIZE,
    PATIENT_LEAVES_CHANCE,
    PATIENT_LEAVES_TEXT,
    PATIENT_WALKOUT_THRESHOLD,
    WRONG_DIAGNOSIS_PENALTY,
)

class CardMixin:
    CARD_SORT_MODES = ("type", "rarity", "cost")
    CARD_RARITY_ORDER = {"Common": 0, "Uncommon": 1, "Rare": 2}

    def get_max_test_hand_size(self):
        """Return the permanent card-case capacity for this campaign."""

        return MAX_TEST_HAND_SIZE + (
            1 if "expanded_case" in self.purchased_shop_upgrades else 0
        )


    def get_random_draw_cost(self):
        """Return the next draw fee after permanent card upgrades."""

        if (
            "diagnostic_grant" in self.purchased_shop_upgrades
            and not self.diagnostic_grant_used
        ):
            return 0
        if "smart_cards" in self.purchased_shop_upgrades:
            return max(0, DRAW_COST - 2)
        return DRAW_COST


    def get_recycler_limit(self):
        """Return how many free swaps are available during one patient case."""

        return 2 if "recycler_mk2" in self.purchased_shop_upgrades else 1


    def get_deck_scanner_preview(self):
        """Return the next random card name when the scanner is installed."""

        if "deck_scanner" not in self.purchased_shop_upgrades or not self.deck.contents:
            return None
        return getattr(self.deck.contents[-1].value, "name", None)

    def get_active_hand(self):
        """Return whichever card hand is currently displayed in the center panel."""

        if self.showing_diagnosis_hand:
            return self.player.diagnosis_hand
        return self.player.test_hand


    def get_card_display_groups(self):
        """Return visible card groups without changing the physical hand."""

        active_hand = self.get_active_hand()
        if self.showing_diagnosis_hand:
            return [
                {"card": card, "indices": [index], "count": 1}
                for index, card in enumerate(active_hand)
            ]

        grouped = {}
        for index, card in enumerate(active_hand):
            name = card.value.name
            group = grouped.setdefault(
                name,
                {"card": card, "indices": [], "count": 0},
            )
            group["indices"].append(index)
            group["count"] += 1

        for group in grouped.values():
            emergency_indices = [
                index
                for index in group["indices"]
                if active_hand[index] is self.emergency_test_card
            ]
            if emergency_indices:
                emergency_index = emergency_indices[0]
                group["indices"].remove(emergency_index)
                group["indices"].insert(0, emergency_index)
                group["card"] = active_hand[emergency_index]

        mode = getattr(self, "card_sort_mode", "type")

        def sort_key(group):
            test = group["card"].value
            name = test.name.casefold()
            rarity = self.CARD_RARITY_ORDER.get(test.rarity, 99)
            cost = self.player.get_test_cost(test)
            if mode == "rarity":
                return rarity, name, cost
            if mode == "cost":
                return cost, rarity, name
            return name, rarity, cost

        return sorted(grouped.values(), key=sort_key)


    def get_display_index_for_hand_index(self, hand_index):
        """Map one physical hand index to its visible stack position."""

        for display_index, group in enumerate(self.card_display_groups):
            if hand_index in group["indices"]:
                return display_index
        return None


    def get_card_rect_for_hand_index(self, hand_index):
        """Return the resting card rectangle for one physical hand card."""

        display_index = self.get_display_index_for_hand_index(hand_index)
        if display_index is None:
            self.refresh_hand_layout()
            display_index = self.get_display_index_for_hand_index(hand_index)
        if display_index is None or display_index >= len(self.card_rects):
            return None
        return self.card_rects[display_index]


    def get_card_sort_button(self):
        """Return the compact sort control inside the Available Tests tray."""

        tray = self.layout["active_hand"].inflate(-8, -8)
        tray.y += 3
        return pygame.Rect(tray.right - 128, tray.y + 5, 108, 24)


    def cycle_card_sort_mode(self):
        """Cycle test stacks through type, rarity, and operating-cost order."""

        current = getattr(self, "card_sort_mode", "type")
        index = self.CARD_SORT_MODES.index(current)
        self.card_sort_mode = self.CARD_SORT_MODES[
            (index + 1) % len(self.CARD_SORT_MODES)
        ]
        self.selected_card_index = None
        self.hovered_card_index = None
        self.refresh_hand_layout()
        self.play_sfx("button")


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
        # Give a normal five-card hand enough width for condition names such as
        # "Thermal-Lung Exchange Failure." Larger hands retain the narrower
        # overlapping layout so eight cards still fit inside the same tray.
        card_width = 116 if card_count <= 5 else 96
        card_height = 118

        if card_count == 0:
            return []

        usable_width = panel.width - 28
        if card_count == 1:
            card_step = 0
            total_width = card_width
        else:
            available_step = (usable_width - card_width) / (card_count - 1)
            # Normal five-card hands fit with a narrow breathing gap. Dense
            # six-to-nine-card hands still overlap so they remain contained.
            maximum_step = card_width + 2 if card_count <= 5 else card_width - 4
            card_step = min(maximum_step, available_step)
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

        self.card_display_groups = self.get_card_display_groups()
        self.card_rects = self.calculate_hand_layout(len(self.card_display_groups))
        if (
            self.selected_card_index is not None
            and self.get_display_index_for_hand_index(self.selected_card_index) is None
        ):
            self.selected_card_index = None


    def build_card_rects(self):
        """Return the current hand layout for compatibility with earlier GUI code."""

        return self.calculate_hand_layout(len(self.get_card_display_groups()))


    def handle_card_click(self, position):
        """Select or dismiss a card and run it when it belongs to the test hand."""

        if self.selected_card_index is not None:
            selected_rect = self.get_selected_card_rect(self.selected_card_index)
            if self.showing_diagnosis_hand:
                action_button = self.get_card_action_button(selected_rect)
                if action_button.collidepoint(position):
                    self.play_sfx("button")
                    self.open_diagnosis_confirmation()
                    return
            else:
                if ("recycler" in self.purchased_shop_upgrades
                        and self.get_recycler_button(selected_rect).collidepoint(position)):
                    self.recycle_selected_test()
                    return
                if self.get_run_test_button(selected_rect).collidepoint(position):
                    self.play_sfx("button")
                    self.run_selected_test()
                    return
                if self.get_discard_button(selected_rect).collidepoint(position):
                    self.play_sfx("button")
                    self.discard_selected_test()
                    return

            if selected_rect.collidepoint(position):
                self.selected_card_index = None
                return

        index = self.get_hovered_card_index(position)
        if index is not None:
            self.selected_card_index = self.card_display_groups[index]["indices"][0]
            self.play_sfx("card_select")
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
        allowed, charged_cost, emergency = self.get_test_charge_state(card.value)
        if not allowed:
            self.set_card_draw_notice(
                "CREDIT LIMIT REACHED  •  RUN A COMMON TEST"
                if not self.emergency_test_used
                else "CREDIT LIMIT REACHED  •  EMERGENCY TEST USED"
            )
            return False
        self.last_test_name = card.value.name
        self.last_test_cost = charged_cost
        self.last_test_was_emergency = emergency
        if emergency:
            self.emergency_test_granted = True
            self.emergency_test_used = True
            self.set_card_draw_notice("EMERGENCY BASIC TEST  •  NO CHARGE")
        else:
            self.player.consume_test_use(card.value)
        self.start_live_money_deduction(self.last_test_cost, "TEST COST")
        self.daily_test_count += 1
        self.daily_test_expenses += self.last_test_cost
        result = self.patient.perform_test(self.last_test_name)
        self.last_test_result = result.replace("RESULTS: ", "", 1)

        self.player.play(card)
        if card is self.emergency_test_card:
            self.emergency_test_card = None
        self.pending_test_discard = card
        self.selected_card_index = None
        self.run_test_button = None
        self.refresh_hand_layout()
        self.test_result_started_at = pygame.time.get_ticks()
        self.state = GameState.TEST_RESULT
        self.notebook.add_test(self.patient, self.last_test_name, self.last_test_result)
        self.play_sfx("scan")
        return True


    def get_recycler_button(self, rect):
        return pygame.Rect(rect.x + 16, rect.bottom - 70, rect.width - 32, 26)

    def recycle_selected_test(self):
        """Exchange one card per patient without charging or returning waste."""
        if ("recycler" not in self.purchased_shop_upgrades
                or self.recycler_used >= self.get_recycler_limit()
                or self.showing_diagnosis_hand or self.selected_card_index is None
                or self.discard_animation is not None):
            return False
        index = self.selected_card_index
        if not 0 <= index < len(self.player.test_hand):
            return False
        if self.player.test_hand[index] is self.emergency_test_card:
            self.set_card_draw_notice("EMERGENCY CARD  •  RUN THIS TEST OR KEEP IT")
            return False
        replacement = self.deck.draw()
        if replacement is None:
            self.set_card_draw_notice("RECYCLER: DECK EMPTY  •  NOT USED")
            return False
        old_card = self.player.test_hand[index]
        self.player.test_hand[index] = replacement
        self.discard_pile.append(old_card)
        self.recycler_used += 1
        self.selected_card_index = None
        self.refresh_hand_layout()
        self.play_sfx("card_select")
        remaining_uses = self.get_recycler_limit() - self.recycler_used
        self.set_card_draw_notice(
            f"RECYCLED FREE  •  {remaining_uses} SWAP"
            f"{'S' if remaining_uses != 1 else ''} LEFT"
        )
        return True


    def discard_selected_test(self):
        """Move the selected test card to the throwaway pile without running it."""

        if self.showing_diagnosis_hand or self.selected_card_index is None:
            return False
        if self.discard_animation is not None:
            self.set_card_draw_notice("MED-WASTE IN USE  •  PLEASE WAIT")
            return False
        if not 0 <= self.selected_card_index < len(self.player.test_hand):
            self.selected_card_index = None
            self.refresh_hand_layout()
            return False

        if self.player.test_hand[self.selected_card_index] is self.emergency_test_card:
            self.set_card_draw_notice("EMERGENCY CARD  •  CANNOT DISCARD")
            return False

        selected_rect = self.get_selected_card_rect(self.selected_card_index)
        card = self.player.test_hand.pop(self.selected_card_index)
        self.discard_pile.append(card)
        self.discard_animation = {
            "card": card,
            "start": selected_rect.center,
            "started_at": pygame.time.get_ticks(),
            "locks_input": True,
        }
        self.selected_card_index = None
        self.run_test_button = None
        self.discard_button = None
        self.refresh_hand_layout()
        self.set_card_draw_notice("SLOT OPEN  •  DRAW WHEN READY")
        return True


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


    def start_pending_diagnosis_discard_animation(self):
        """Throw a rejected diagnosis card into med-waste on return to the bay."""

        if self.pending_diagnosis_discard is None:
            return
        self.discard_animation = {
            "card": self.pending_diagnosis_discard["card"],
            "start": self.pending_diagnosis_discard["start"],
            "started_at": pygame.time.get_ticks(),
            "duration": self.test_discard_animation_duration,
            "add_to_pile_on_complete": True,
            "locks_input": True,
            "arc_height": 105,
        }
        self.pending_diagnosis_discard = None


    def get_selected_card_rect(self, index):
        """Return the larger rectangle used to display a selected test card."""

        preview = pygame.Rect(0, 0, 260, 218)
        display_index = self.get_display_index_for_hand_index(index)
        if display_index is None:
            display_index = index
        preview.midbottom = (
            self.card_rects[display_index].centerx,
            self.layout["active_hand"].bottom - 5,
        )
        panel = self.layout["active_hand"]
        preview.left = max(panel.left, min(preview.left, panel.right - preview.width))
        return preview


    def get_run_test_button(self, selected_rect):
        """Return the Run Test button rectangle for an enlarged card."""

        return pygame.Rect(
            selected_rect.x + 16,
            selected_rect.bottom - 38,
            (selected_rect.width - 42) // 2,
            28,
        )


    def get_discard_button(self, selected_rect):
        """Return the Discard button rectangle for an enlarged test card."""

        return pygame.Rect(
            selected_rect.centerx + 5,
            selected_rect.bottom - 38,
            (selected_rect.width - 42) // 2,
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

        selected_index = self.selected_card_index
        selected_rect = self.get_selected_card_rect(selected_index)
        card = self.player.diagnosis_hand[selected_index]
        self.diagnosis_confirmation_open = False
        self.patient_left = False
        self.last_diagnosis = card.value
        self.player.play(card)
        self.diagnosis_correct = self.patient.receive_diagnosis(card.value)
        performed_tests = set(self.notebook.get_entries(self.patient)) - {"No tests"}
        (
            self.last_diagnosis_evidence_count,
            self.last_diagnosis_evidence_total,
        ) = self.patient.get_evidence_progress(performed_tests)
        self.last_diagnosis_supported = self.patient.has_supporting_evidence(
            performed_tests
        )
        if self.diagnosis_correct:
            self.daily_correct_diagnoses += 1
            if self.last_diagnosis_supported:
                self.daily_evidence_cases += 1
            elif self.last_diagnosis_evidence_count > 0:
                self.daily_partial_evidence_cases += 1
            self.play_sfx("correct")
        else:
            self.start_live_money_deduction(
                WRONG_DIAGNOSIS_PENALTY,
                "WRONG DIAGNOSIS",
            )
            self.daily_wrong_diagnoses += 1
            self.player.diagnosis_hand.pop(selected_index)
            self.pending_diagnosis_discard = {
                "card": card,
                "start": selected_rect.center,
            }
            self.patient_wrong_diagnoses += 1
            self.patient_left = (
                not self.guided_tutorial_active
                and self.patient_wrong_diagnoses >= PATIENT_WALKOUT_THRESHOLD
                and random.random() < PATIENT_LEAVES_CHANCE
            )
            if self.patient_left:
                self.daily_patients_lost += 1
                self.patient_leave_text = random.choice(PATIENT_LEAVES_TEXT).format(
                    name=self.patient.name
                )
            self.play_sfx("incorrect")
        self.selected_card_index = None
        self.play_diagnosis_button = None
        self.refresh_hand_layout()
        self.state = GameState.OUTCOME


    def open_diagnosis_confirmation(self):
        """Open a confirmation dialog for the currently selected diagnosis card."""

        if self.showing_diagnosis_hand and self.selected_card_index is not None:
            self.diagnosis_confirmation_open = True


    def confirm_selected_diagnosis(self):
        """Confirm and play the diagnosis currently shown in the dialog."""

        if not self.diagnosis_confirmation_open:
            return
        self.play_sfx("button")
        self.diagnosis_confirmation_open = False
        self.play_selected_diagnosis()


    def handle_diagnosis_confirmation_click(self, position):
        """Handle the submit and return buttons in the diagnosis confirmation dialog."""

        if self.diagnosis_confirm_button.collidepoint(position):
            self.confirm_selected_diagnosis()
        elif self.diagnosis_cancel_button.collidepoint(position):
            self.play_sfx("button")
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

        if not self.showing_diagnosis_hand:
            self.draw_card_sort_control()

        for light_x, light_color in (
            (tray.x + 18, COLORS["accent"]),
            (tray.x + 29, (79, 151, 235)),
            (tray.right - 29, (79, 151, 235)),
            (tray.right - 18, COLORS["accent"]),
        ):
            pygame.draw.circle(self.screen, (8, 14, 21), (light_x, tray.y + 17), 4)
            pygame.draw.circle(self.screen, light_color, (light_x, tray.y + 17), 2)

        current_groups = self.get_card_display_groups()
        current_signature = [
            (group["card"].value.name, tuple(group["indices"]))
            for group in current_groups
        ]
        stored_signature = [
            (group["card"].value.name, tuple(group["indices"]))
            for group in self.card_display_groups
        ]
        if current_signature != stored_signature:
            self.refresh_hand_layout()
        groups = self.card_display_groups

        if not groups:
            empty_text = (
                "NO DIAGNOSIS CARDS"
                if self.showing_diagnosis_hand
                else "NO TEST CARDS"
            )
            empty = self.body_font.render(empty_text, True, COLORS["muted"])
            self.screen.blit(empty, empty.get_rect(center=panel.center))
            return

        mouse_position = self.get_mouse_position()
        self.hovered_card_index = (
            None
            if self.selected_card_index is not None
            else self.get_hovered_card_index(mouse_position)
        )

        selected_display_index = (
            None
            if self.selected_card_index is None
            else self.get_display_index_for_hand_index(self.selected_card_index)
        )

        for index, group in enumerate(groups):
            if index == selected_display_index or index == self.hovered_card_index:
                continue
            self.draw_duplicate_stack_layers(self.card_rects[index], group["count"])
            self.draw_hand_card(group["card"], self.card_rects[index])
            self.draw_duplicate_badge(self.card_rects[index], group["count"])
            if self.selected_card_index is not None:
                self.draw_card_dimming_overlay(self.card_rects[index])

        if self.hovered_card_index is not None:
            hovered_rect = self.get_hovered_card_rect(self.card_rects[self.hovered_card_index])
            hovered_group = groups[self.hovered_card_index]
            self.draw_duplicate_stack_layers(hovered_rect, hovered_group["count"])
            self.draw_hand_card(
                hovered_group["card"], hovered_rect, hovered=True
            )
            self.draw_duplicate_badge(hovered_rect, hovered_group["count"])

        if self.selected_card_index is not None:
            selected_group = groups[selected_display_index]
            selected_card = selected_group["card"]
            selected_rect = self.get_selected_card_rect(self.selected_card_index)
            self.draw_duplicate_stack_layers(selected_rect, selected_group["count"])
            if self.showing_diagnosis_hand:
                self.draw_diagnosis_card(selected_card, selected_rect, selected=True)
            else:
                self.draw_test_card(selected_card, selected_rect, selected=True)
                self.draw_duplicate_badge(
                    selected_rect,
                    selected_group["count"],
                    selected=True,
                )


    def draw_card_sort_control(self):
        """Draw the test-hand sorting button without competing with card titles."""

        rect = self.get_card_sort_button()
        hovered = rect.collidepoint(self.get_mouse_position())
        border = COLORS["accent"] if hovered else (112, 119, 142)
        fill = (31, 58, 61) if hovered else (26, 35, 48)
        pygame.draw.rect(self.screen, (3, 8, 13), rect.move(2, 2), border_radius=6)
        pygame.draw.rect(self.screen, fill, rect, border_radius=6)
        pygame.draw.rect(self.screen, border, rect, width=1, border_radius=6)
        label = self.readable_detail_font.render(
            f"SORT: {self.card_sort_mode.upper()}",
            True,
            COLORS["text"],
        )
        self.screen.blit(label, label.get_rect(center=rect.center))


    def draw_duplicate_stack_layers(self, card_rect, count):
        """Show up to two offset card edges behind a duplicate stack."""

        for layer in reversed(range(1, min(count, 3))):
            layer_rect = card_rect.move(layer * 4, -layer * 3)
            pygame.draw.polygon(
                self.screen,
                (35, 27, 47),
                self.get_card_shape_points(layer_rect, 7),
            )
            pygame.draw.polygon(
                self.screen,
                (187, 137, 211),
                self.get_card_shape_points(layer_rect, 7),
                width=1,
            )


    def draw_duplicate_badge(self, card_rect, count, selected=False):
        """Label one visible test card with the number of physical copies."""

        if count <= 1:
            return
        badge = pygame.Rect(0, 0, 32 if selected else 29, 20 if selected else 18)
        if selected:
            # Pin the count to the artwork corner. It remains visible without
            # obscuring the icon label or the test description.
            badge.topright = (card_rect.x + 90, card_rect.y + 72)
        else:
            badge.topright = (card_rect.right - 4, card_rect.y + 47)
        pygame.draw.rect(self.screen, (49, 31, 66), badge, border_radius=7)
        pygame.draw.rect(self.screen, (216, 159, 238), badge, width=2, border_radius=7)
        font = self.card_font if selected else self.readable_detail_font
        label = font.render(f"×{count}", True, (244, 225, 250))
        self.screen.blit(label, label.get_rect(center=badge.center))


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

    def draw_card_from_pile(self):
        """Move the top card of the deck into the player's hand for its current fee."""
        if self.discard_animation is not None:
            self.set_card_draw_notice("MED-WASTE IN USE  •  PLEASE WAIT")
            return False
        if len(self.player.test_hand) >= self.get_max_test_hand_size():
            self.set_card_draw_notice("HAND FULL  •  DISCARD FIRST")
            return False

        # Drawn cards belong to the test hand. Reveal that hand immediately so
        # the player never pays for a card hidden behind Diagnosis Options.
        if self.showing_diagnosis_hand:
            self.switch_active_hand(False)
        draw_cost = self.get_random_draw_cost()
        emergency_draw = draw_cost > 0 and not self.can_spend_clinic_funds(draw_cost)
        if emergency_draw:
            has_common_card = any(
                getattr(card.value, "rarity", None) == "Common"
                for card in self.player.test_hand
            )
            if self.emergency_test_granted or self.emergency_test_used:
                self.set_card_draw_notice(
                    "CREDIT LIMIT REACHED  •  EMERGENCY SUPPORT USED"
                )
                return False
            if has_common_card:
                self.set_card_draw_notice(
                    "CREDIT LIMIT REACHED  •  RUN A COMMON TEST FREE"
                )
                return False
            card = self.deck.draw_rarity("Common")
            if card is None:
                emergency_test = next(
                    (
                        test
                        for test in self.card_shop_catalog
                        if test.rarity == "Common"
                    ),
                    None,
                )
                if emergency_test is None:
                    self.set_card_draw_notice(
                        "CREDIT LIMIT REACHED  •  BASIC TEST UNAVAILABLE"
                    )
                    return False
                card = Card("Test", emergency_test)
            self.emergency_test_granted = True
            self.emergency_test_card = card
        else:
            if not self.deck.contents:
                self.set_card_draw_notice("DRAW DECK EMPTY  •  NO CHARGE")
                return False
            card = self.deck.draw()
        if card is None:
            self.set_card_draw_notice("DRAW DECK EMPTY  •  NO CHARGE")
            return False
        self.player.draw(card)
        if not emergency_draw:
            if draw_cost:
                self.start_live_money_deduction(draw_cost, "CARD DRAW")
                self.daily_draw_expenses += draw_cost
            if (
                draw_cost == 0
                and "diagnostic_grant" in self.purchased_shop_upgrades
            ):
                self.diagnostic_grant_used = True
            self.daily_random_draw_count += 1
        self.selected_card_index = None
        self.refresh_hand_layout()
        remaining = len(self.deck.contents)
        if emergency_draw:
            self.set_card_draw_notice("EMERGENCY BASIC CARD  •  NO DRAW FEE")
        elif draw_cost == 0:
            self.set_card_draw_notice("DIAGNOSTIC GRANT  •  FREE DRAW USED")
        elif remaining == 0:
            self.set_card_draw_notice("LAST CARD DRAWN  •  DECK EMPTY")
        elif remaining <= 5:
            self.set_card_draw_notice(f"LOW DECK  •  {remaining} CARDS LEFT")
        return True

    def set_card_draw_notice(self, message):
        """Show a short draw-pile status without changing cards or charging money."""

        self.card_draw_notice = message
        self.card_draw_notice_started_at = pygame.time.get_ticks()

    def get_hovered_card_index(self, position):
        """Return the single card under the mouse, or None."""

        count = len(self.card_rects)
        current = self.hovered_card_index

        # Sticky: keep the lifted card while the mouse is still over its lifted shape
        if current is not None and current < count:
            lifted = self.get_hovered_card_rect(self.card_rects[current])
            if lifted.collidepoint(position):
                return current

        for index in reversed(range(count)):
            if self.card_rects[index].collidepoint(position):
                return index
        return None

    def draw_hand_card(self, card, rect, hovered=False, selected=False):
        """Draw a test or diagnosis card depending on the active hand."""

        if self.showing_diagnosis_hand:
            self.draw_diagnosis_card(card, rect, hovered=hovered, selected=selected)
        else:
            self.draw_test_card(card, rect, hovered=hovered, selected=selected)


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


    def wrap_card_title(self, title, font, width):
        """Wrap a card title at word boundaries for a particular font and width."""

        lines = []
        current = []
        for word in title.split():
            candidate = " ".join(current + [word])
            if current and font.size(candidate)[0] > width:
                lines.append(" ".join(current))
                current = [word]
            else:
                current.append(word)
        if current:
            lines.append(" ".join(current))
        return lines or [title]

    def get_fitted_card_title_layout(self, title, area, selected=False, max_lines=2):
        """Return a font and wrapped lines guaranteed to fit a card header."""

        fonts = (
            (
                self.body_font,
                self.small_font,
                self.diagnosis_card_font,
                self.compact_card_title_font,
                self.legible_micro_font,
            )
            if selected
            else (
                self.diagnosis_card_font,
                self.compact_card_title_font,
            )
        )
        usable_width = max(1, area.width - 8)
        usable_height = max(1, area.height - 4)
        for font in fonts:
            lines = self.wrap_card_title(title, font, usable_width)
            line_height = font.get_linesize()
            if (
                len(lines) <= max_lines
                and len(lines) * line_height <= usable_height
                and all(font.size(line)[0] <= usable_width for line in lines)
            ):
                return font, lines

        # The clip used while drawing is the final safety net for an unusually
        # long unbroken word introduced by future content.
        fallback = fonts[-1]
        lines = self.wrap_card_title(title, fallback, usable_width)[:max_lines]
        return fallback, lines

    def draw_fitted_card_title(self, title, area, selected=False, max_lines=2):
        """Draw a wrapped title while strictly clipping it to the card header."""

        font, title_lines = self.get_fitted_card_title_layout(
            title,
            area,
            selected=selected,
            max_lines=max_lines,
        )
        line_height = font.get_linesize()
        first_y = area.centery - (len(title_lines) * line_height) / 2 + line_height / 2
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(area)
        try:
            for line_index, line_text in enumerate(title_lines):
                line = font.render(line_text, True, COLORS["card_text"])
                line_center = (area.centerx, round(first_y + line_index * line_height))
                self.screen.blit(line, line.get_rect(center=line_center))
        finally:
            self.screen.set_clip(previous_clip)

    def get_fitted_card_description_layout(self, text, area, line_spacing=2):
        """Return readable wrapped description text that fits its card area."""

        for font in (self.card_font, self.pile_font, self.legible_micro_font):
            lines = self.wrap_text(text, font, area.width)
            total_height = (
                len(lines) * font.get_height()
                + max(0, len(lines) - 1) * line_spacing
            )
            if total_height <= area.height:
                return font, lines
        return self.legible_micro_font, self.wrap_text(
            text,
            self.legible_micro_font,
            area.width,
        )

    def draw_fitted_card_description(self, text, area, color):
        """Draw a complete card description without allowing text to escape."""

        font, lines = self.get_fitted_card_description_layout(text, area)
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(area)
        try:
            y = area.y
            for line_text in lines:
                line = font.render(line_text, True, color)
                self.screen.blit(line, (area.x, y))
                y += line.get_height() + 2
        finally:
            self.screen.set_clip(previous_clip)


    def draw_rarity_badge(self, test, card_rect):
        """Show machine level, rarity, and the current operating cost."""

        rarity = test.rarity

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

        rarity_font = (
            self.readable_detail_font
            if self.readable_detail_font.size(
                f"{rarity.upper()}  ${self.player.get_test_cost(test)}"
            )[0] <= badge.width - 6
            else self.compact_card_title_font
        )
        rarity_text = rarity_font.render(
            f"{rarity.upper()}  ${self.player.get_test_cost(test)}",
            True,
            rarity_color,
        )
        self.screen.blit(
            rarity_text,
            rarity_text.get_rect(center=badge.center),
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

        # Present each option as a compact case file rather than a plain test
        # card. The tab and spine add hierarchy without consuming the space
        # needed by long condition names.
        spine = pygame.Rect(card_rect.x + 4, card_rect.y + 9, 4, card_rect.height - 18)
        pygame.draw.rect(self.screen, diagnosis_color, spine, border_radius=2)
        tab = pygame.Rect(card_rect.x + 10, card_rect.y + 3, 64, 16)
        pygame.draw.rect(self.screen, diagnosis_color, tab, border_radius=4)
        tab_label = self.pile_font.render("CASE FILE", True, (250, 239, 252))
        self.screen.blit(tab_label, tab_label.get_rect(center=tab.center))

        header = pygame.Rect(card_rect.x + 9, card_rect.y + 16, card_rect.width - 18, 58)
        pygame.draw.rect(self.screen, (218, 199, 226), header, border_radius=5)
        pygame.draw.line(
            self.screen,
            diagnosis_color,
            (header.x + 6, header.bottom),
            (header.right - 6, header.bottom),
        )
        # The shared fitter balances long condition names across stable lines,
        # so hovering never changes the title font or clips new cards.
        self.draw_fitted_card_title(diagnosis.name, header, max_lines=3)

        icon = pygame.Rect(card_rect.centerx - 28, card_rect.y + 79, 56, 31)
        pygame.draw.rect(self.screen, (210, 211, 216), icon, border_radius=6)
        pygame.draw.rect(self.screen, diagnosis_color, icon, width=2, border_radius=6)
        self.draw_diagnosis_file_icon(icon, diagnosis_color)

        for rivet_x in (card_rect.x + 13, card_rect.right - 13):
            pygame.draw.circle(
                self.screen,
                (205, 145, 226),
                (rivet_x, card_rect.bottom - 8),
                2,
            )


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

        self.play_diagnosis_button = self.get_card_action_button(card_rect)
        description_y = card_rect.y + 69
        description_box = pygame.Rect(
            card_rect.x + 80,
            description_y,
            card_rect.width - 90,
            self.play_diagnosis_button.y - description_y - 3,
        )
        self.draw_fitted_card_description(
            diagnosis.description,
            description_box,
            COLORS["card_text"],
        )

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
            card_rect.bottom - 26,
            card_rect.width - 14,
            20,
        )
        pygame.draw.rect(self.screen, (213, 205, 218), badge, border_radius=6)
        pygame.draw.rect(self.screen, diagnosis_color, badge, width=1, border_radius=6)
        label = self.diagnosis_card_font.render(
            "DIAGNOSIS",
            True,
            diagnosis_color,
        )
        self.screen.blit(
            label,
            label.get_rect(center=badge.center),
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

        # Two-line names such as Blood Chemistry need enough vertical space to
        # remain legible instead of falling back to the smallest UI font.
        header = pygame.Rect(card_rect.x + 3, card_rect.y + 5, card_rect.width - 6, 36)
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

        icon = pygame.Rect(card_rect.centerx - 23, card_rect.y + 44, 46, 38)
        pygame.draw.rect(self.screen, (201, 214, 205), icon, border_radius=6)
        pygame.draw.rect(self.screen, rarity_color, icon, width=2, border_radius=6)
        self.draw_test_icon(test.name, icon, rarity_color)

        subtitle_text = TEST_SUBTITLES.get(test.name.upper(), "MEDICAL TEST")
        subtitle_font = (
            self.readable_detail_font
            if self.readable_detail_font.size(subtitle_text)[0] <= card_rect.width - 8
            else self.compact_card_title_font
        )
        subtitle = subtitle_font.render(
            subtitle_text,
            True,
            COLORS["card_text"],
        )
        self.screen.blit(
            subtitle,
            subtitle.get_rect(center=(card_rect.centerx, card_rect.y + 89)),
        )
        self.draw_rarity_badge(test, card_rect)


    def draw_selected_card_details(self, test, card_rect, rarity_color):
        """Draw an enlarged test card with Run Test and Discard buttons."""

        header = pygame.Rect(card_rect.x + 9, card_rect.y + 8, card_rect.width - 18, 39)
        header_color = tuple(max(0, channel - 18) for channel in RARITY_CARD_COLORS.get(
            test.rarity,
            COLORS["card"],
        ))
        pygame.draw.rect(self.screen, header_color, header, border_radius=7)
        self.draw_fitted_card_title(test.name, header, selected=True)

        allowed, charged_cost, emergency = self.get_test_charge_state(test)
        cost_label = "EMERGENCY FREE" if emergency else f"COST ${charged_cost}"
        rarity = self.card_font.render(
            f"LV.{self.player.get_machine_level(test)} {test.rarity.upper()}  •  {cost_label}",
            True,
            rarity_color,
        )
        self.screen.blit(rarity, rarity.get_rect(center=(card_rect.centerx, card_rect.y + 55)))

        icon = pygame.Rect(card_rect.x + 18, card_rect.y + 74, 64, 58)
        pygame.draw.rect(self.screen, (201, 214, 205), icon, border_radius=7)
        pygame.draw.rect(self.screen, rarity_color, icon, width=2, border_radius=7)
        self.draw_test_icon(test.name, icon, rarity_color)

        subtitle_area = pygame.Rect(card_rect.x + 12, icon.bottom + 3, 76, 30)
        self.draw_fitted_card_title(
            TEST_SUBTITLES.get(test.name.upper(), "MEDICAL TEST"),
            subtitle_area,
            max_lines=2,
        )

        description_y = card_rect.y + 76
        action_top = (self.get_recycler_button(card_rect).y
                      if "recycler" in self.purchased_shop_upgrades
                      else self.get_run_test_button(card_rect).y)
        description_box = pygame.Rect(
            card_rect.x + 96,
            description_y,
            card_rect.width - 108,
            action_top - description_y - 3,
        )
        self.draw_fitted_card_description(
            test.description,
            description_box,
            COLORS["card_text"],
        )

        self.run_test_button = self.get_run_test_button(card_rect)
        run_color = COLORS["panel_border"] if allowed else (111, 86, 91)
        pygame.draw.rect(self.screen, run_color, self.run_test_button, border_radius=5)
        run_text = self.small_font.render(
            "RUN FREE"
            if emergency
            else f"RUN  ${charged_cost}"
            if allowed
            else "CREDIT LIMIT",
            True,
            COLORS["background"],
        )
        self.screen.blit(run_text, run_text.get_rect(center=self.run_test_button.center))

        if "recycler" in self.purchased_shop_upgrades:
            recycler_rect = self.get_recycler_button(card_rect)
            recycler_limit = self.get_recycler_limit()
            remaining_recycles = recycler_limit - self.recycler_used
            available = remaining_recycles > 0 and bool(self.deck.contents)
            pygame.draw.rect(self.screen, (105, 230, 180) if available else (150, 155, 150),
                             recycler_rect, border_radius=5)
            label = (
                f"RECYCLE FREE ({remaining_recycles}/{recycler_limit})"
                if available
                else f"RECYCLE USED (0/{recycler_limit})"
                if self.recycler_used >= recycler_limit
                else "RECYCLER: DECK EMPTY"
            )
            text = self.card_font.render(label, True, COLORS["background"])
            self.screen.blit(text, text.get_rect(center=recycler_rect.center))

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
        elif test_name == "BLOOD CHEMISTRY":
            vial = pygame.Rect(center_x - 8, center_y - 13, 16, 25)
            pygame.draw.rect(icon_surface, (238, 246, 228), vial, border_radius=4)
            pygame.draw.rect(icon_surface, ink, vial, width=2, border_radius=4)
            pygame.draw.line(
                icon_surface,
                ink,
                (vial.x - 2, vial.y),
                (vial.right + 2, vial.y),
                width=3,
            )
            fluid = pygame.Rect(vial.x + 3, vial.centery, vial.width - 6, 9)
            pygame.draw.rect(icon_surface, rarity_color, fluid, border_radius=3)
            pygame.draw.circle(
                icon_surface,
                (238, 246, 228),
                (fluid.x + 3, fluid.y + 3),
                2,
            )
        elif test_name == "OXYGEN SCAN":
            pygame.draw.line(
                icon_surface,
                ink,
                (center_x, center_y - 14),
                (center_x, center_y + 12),
                width=3,
            )
            for direction in (-1, 1):
                lung = pygame.Rect(
                    center_x + direction * 2 - (12 if direction < 0 else 0),
                    center_y - 7,
                    11,
                    22,
                )
                pygame.draw.ellipse(icon_surface, rarity_color, lung)
                pygame.draw.ellipse(icon_surface, ink, lung, width=2)
            for bubble_x, bubble_y, radius in ((8, -13, 3), (14, -7, 2), (-12, -15, 2)):
                pygame.draw.circle(
                    icon_surface,
                    rarity_color,
                    (center_x + bubble_x, center_y + bubble_y),
                    radius,
                    width=1,
                )
        elif test_name == "TOXIN SCREEN":
            flask_points = (
                (center_x - 5, center_y - 14),
                (center_x + 5, center_y - 14),
                (center_x + 5, center_y - 4),
                (center_x + 13, center_y + 12),
                (center_x - 13, center_y + 12),
                (center_x - 5, center_y - 4),
            )
            pygame.draw.polygon(icon_surface, (238, 246, 228), flask_points)
            pygame.draw.polygon(icon_surface, ink, flask_points, width=2)
            fluid_points = (
                (center_x - 9, center_y + 5),
                (center_x + 9, center_y + 5),
                (center_x + 12, center_y + 11),
                (center_x - 12, center_y + 11),
            )
            pygame.draw.polygon(icon_surface, rarity_color, fluid_points)
            pygame.draw.circle(icon_surface, ink, (center_x, center_y + 8), 2)
            pygame.draw.circle(icon_surface, rarity_color, (center_x + 13, center_y - 8), 3)
        elif test_name == "NEURAL SCAN":
            nodes = (
                (center_x, center_y - 13),
                (center_x - 13, center_y - 4),
                (center_x + 13, center_y - 4),
                (center_x - 9, center_y + 12),
                (center_x + 9, center_y + 12),
                (center_x, center_y + 4),
            )
            links = ((0, 1), (0, 2), (1, 3), (2, 4), (1, 5), (2, 5), (3, 5), (4, 5))
            for start, end in links:
                pygame.draw.line(icon_surface, ink, nodes[start], nodes[end], width=2)
            for index, node in enumerate(nodes):
                pygame.draw.circle(
                    icon_surface,
                    rarity_color if index in (0, 5) else (238, 246, 228),
                    node,
                    4,
                )
                pygame.draw.circle(icon_surface, ink, node, 4, width=1)
        else:
            icon_text = self.body_font.render(test_name[0], True, ink)
            icon_surface.blit(icon_text, icon_text.get_rect(center=icon_area.center))

        self.screen.blit(icon_surface, icon.topleft)


    def draw_diagnosis_cards(self):
        """Draw the diagnosis folder standing in a compact desktop file rack."""

        panel = self.layout["diagnosis"]
        mouse_position = self.get_mouse_position()
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

        diagnosis_name_font = self.heading_font
        for candidate in (self.heading_font, self.body_font, self.small_font):
            diagnosis_name_font = candidate
            if candidate.size(diagnosis.name)[0] <= panel.width - 70:
                break
        diagnosis_name = diagnosis_name_font.render(
            diagnosis.name,
            True,
            (216, 159, 238),
        )
        self.screen.blit(
            diagnosis_name,
            diagnosis_name.get_rect(center=(panel.centerx, panel.y + 142)),
        )

        question = self.body_font.render(
            "Submit this condition as your final diagnosis?",
            True,
            COLORS["text"],
        )
        self.screen.blit(question, question.get_rect(center=(panel.centerx, panel.y + 186)))

        evidence_text, evidence_color = self.get_diagnosis_clue_display()
        evidence_panel = pygame.Rect(panel.centerx - 235, panel.y + 203, 470, 49)
        pygame.draw.rect(self.screen, (19, 24, 34), evidence_panel, border_radius=12)
        pygame.draw.rect(
            self.screen,
            evidence_color,
            evidence_panel,
            width=2,
            border_radius=12,
        )
        evidence_heading = self.small_font.render(
            evidence_text,
            True,
            evidence_color,
        )
        self.screen.blit(
            evidence_heading,
            evidence_heading.get_rect(
                center=(evidence_panel.centerx, evidence_panel.y + 17),
            ),
        )
        evidence_caution = self.card_font.render(
            "Evidence quantity does not guarantee this diagnosis.",
            True,
            COLORS["muted"],
        )
        self.screen.blit(
            evidence_caution,
            evidence_caution.get_rect(
                center=(evidence_panel.centerx, evidence_panel.y + 34),
            ),
        )

        mouse_position = self.get_mouse_position()
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

