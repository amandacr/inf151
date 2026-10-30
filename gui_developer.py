"""Hidden screen navigator used to preview the vertical slice during development."""

import pygame

from gui_state import GameState
from gui_theme import COLORS, WINDOW_SIZE


DEVELOPER_SCREENS = (
    ("1", "RECEPTION", GameState.TITLE),
    ("2", "EXAM BAY", GameState.PATIENT),
    ("3", "TEST RESULT", GameState.TEST_RESULT),
    ("4", "NOTEBOOK", GameState.NOTEBOOK),
    ("5", "DIAGNOSIS", GameState.OUTCOME),
    ("6", "SHIFT RECAP", GameState.DAY_COMPLETE),
    ("7", "SHOP", GameState.SHOP),
    ("8", "UFO ENDING", GameState.ENDING),
    ("9", "FINAL REPORT", GameState.FINAL),
)


class DeveloperMixin:
    """Provide an F10-only navigator without exposing debug controls to players."""

    def setup_developer_navigator(self):
        self.developer_navigator_open = False
        self.developer_button_rects = []

    def toggle_developer_navigator(self):
        """Open or close the hidden preview menu."""

        self.developer_navigator_open = not self.developer_navigator_open
        if self.developer_navigator_open:
            self.finish_guided_tutorial()
            self.tutorial_open = False
            self.tutorial_opened_at = None
            self.exit_confirmation_open = False
            self.exit_confirmation_opened_at = None
            self.diagnosis_confirmation_open = False
        self.play_sfx("button")

    def get_developer_screen_rects(self):
        """Return the stable three-column button layout for preview destinations."""

        return [
            pygame.Rect(252 + column * 202, 230 + row * 72, 192, 56)
            for row in range(3)
            for column in range(3)
        ]

    def handle_developer_key(self, key):
        """Navigate by number or cycle screens with the arrow keys."""

        number_keys = (
            pygame.K_1,
            pygame.K_2,
            pygame.K_3,
            pygame.K_4,
            pygame.K_5,
            pygame.K_6,
            pygame.K_7,
            pygame.K_8,
            pygame.K_9,
        )
        if key in number_keys:
            self.jump_to_developer_screen(number_keys.index(key))
            return
        if key in (pygame.K_LEFT, pygame.K_RIGHT):
            states = [entry[2] for entry in DEVELOPER_SCREENS]
            try:
                current_index = states.index(self.state)
            except ValueError:
                current_index = 0
            step = -1 if key == pygame.K_LEFT else 1
            self.jump_to_developer_screen((current_index + step) % len(states))

    def handle_developer_click(self, position):
        """Jump to the clicked preview destination."""

        for index, rect in enumerate(self.get_developer_screen_rects()):
            if rect.collidepoint(position):
                self.jump_to_developer_screen(index)
                return

    def jump_to_developer_screen(self, index):
        """Prepare any required preview data and display one selected screen."""

        _number, _label, target_state = DEVELOPER_SCREENS[index]
        # A developer jump intentionally leaves the opening story. Without
        # clearing it here, its dialogue overlay keeps intercepting input on
        # whichever preview screen was selected.
        self.intro_dialogue_active = False
        self.intro_dialogue_started_at = None
        self.developer_navigator_open = False
        self.exit_confirmation_open = False
        self.tutorial_open = False
        self.diagnosis_confirmation_open = False
        self.reception_transition_started_at = None
        self.queue_shift_started_at = None
        self.patient_fade_started_at = None

        if target_state == GameState.TEST_RESULT:
            self.last_test_name = "TEMPERATURE"
            self.last_test_result = "Current temperature: 1700°F"
            self.last_test_cost = self.player.get_test_cost(
                self.player.test_hand[0].value
            )
            self.test_result_started_at = None
        elif target_state == GameState.NOTEBOOK:
            self.build_notebook_columns()
            self.notebook_spread = 0
        elif target_state == GameState.OUTCOME:
            self.last_diagnosis = self.patient.diagnosis
            self.diagnosis_correct = True

        if target_state in (
            GameState.DAY_COMPLETE,
            GameState.SHOP,
            GameState.ENDING,
            GameState.FINAL,
        ):
            self.prepare_developer_shift_preview()

        if target_state in (GameState.SHOP, GameState.ENDING, GameState.FINAL):
            self.settle_daily_pay()
        if target_state == GameState.ENDING:
            self.ending_started_at = pygame.time.get_ticks()
        elif target_state == GameState.FINAL:
            self.ending_started_at = None

        self.state = target_state
        self.play_sfx("button")

    def prepare_developer_shift_preview(self):
        """Seed a believable recap only when no real shift activity exists yet."""

        if (
            self.daily_correct_diagnoses == 0
            and self.daily_wrong_diagnoses == 0
            and self.daily_test_count == 0
        ):
            self.daily_correct_diagnoses = len(self.waiting_room_queue)
            self.daily_test_count = len(self.waiting_room_queue)
            self.daily_test_expenses = 40
            self.daily_payout_applied = False

    def draw_developer_navigator(self):
        """Draw the hidden clinic screen directory over the current page."""

        dim = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        dim.fill((2, 6, 12, 224))
        self.screen.blit(dim, (0, 0))

        panel = pygame.Rect(220, 118, 660, 410)
        pygame.draw.rect(self.screen, (3, 8, 13), panel.move(8, 9), border_radius=18)
        pygame.draw.rect(self.screen, (27, 29, 45), panel, border_radius=18)
        pygame.draw.rect(self.screen, (187, 137, 211), panel, width=3, border_radius=18)

        tag = self.card_font.render("DEVELOPER TOOL", True, (216, 159, 238))
        self.screen.blit(tag, tag.get_rect(center=(panel.centerx, panel.y + 28)))
        heading = self.heading_font.render("SCREEN NAVIGATOR", True, COLORS["text"])
        self.screen.blit(heading, heading.get_rect(center=(panel.centerx, panel.y + 58)))
        hint = self.card_font.render(
            "CLICK A SCREEN OR PRESS 1-9  •  LEFT/RIGHT CYCLES  •  F10 CLOSES",
            True,
            COLORS["muted"],
        )
        self.screen.blit(hint, hint.get_rect(center=(panel.centerx, panel.y + 88)))

        mouse_position = self.get_mouse_position()
        self.developer_button_rects = self.get_developer_screen_rects()
        for (number, label, target_state), rect in zip(
            DEVELOPER_SCREENS,
            self.developer_button_rects,
        ):
            selected = self.state == target_state
            hovered = rect.collidepoint(mouse_position)
            border = (
                COLORS["accent"]
                if selected
                else (216, 159, 238) if hovered else (126, 91, 153)
            )
            fill = (
                (19, 54, 49)
                if selected
                else (50, 37, 68) if hovered else (21, 27, 39)
            )
            pygame.draw.rect(self.screen, (3, 8, 13), rect.move(2, 3), border_radius=8)
            pygame.draw.rect(self.screen, fill, rect, border_radius=8)
            pygame.draw.rect(self.screen, border, rect, width=2, border_radius=8)
            number_label = self.body_font.render(number, True, border)
            screen_label = self.card_font.render(label, True, COLORS["text"])
            self.screen.blit(
                number_label,
                number_label.get_rect(midleft=(rect.x + 14, rect.centery)),
            )
            self.screen.blit(
                screen_label,
                screen_label.get_rect(midleft=(rect.x + 46, rect.centery)),
            )

        footer = self.card_font.render(
            "Development shortcut only — hidden during normal play",
            True,
            COLORS["muted"],
        )
        self.screen.blit(footer, footer.get_rect(center=(panel.centerx, panel.bottom - 24)))
