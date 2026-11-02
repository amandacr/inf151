"""Hidden screen navigator used to preview the vertical slice during development."""

import pygame

from gui_state import GameState
from gui_theme import COLORS, WINDOW_SIZE


DEVELOPER_SCREENS = (
    ("1", "intro", "OPENING CINEMATIC", GameState.INTRO),
    ("2", "dialogue", "ABDUCTION DIALOGUE", GameState.TITLE),
    ("3", "tutorial", "GUIDED TUTORIAL", GameState.TITLE),
    ("4", "reception", "RECEPTION", GameState.TITLE),
    ("5", "patient", "EXAM BAY", GameState.PATIENT),
    ("6", "test_result", "TEST RESULT", GameState.TEST_RESULT),
    ("7", "notebook", "NOTEBOOK", GameState.NOTEBOOK),
    ("8", "diagnosis_hand", "DIAGNOSIS HAND", GameState.PATIENT),
    ("9", "diagnosis_confirm", "CONFIRM DIAGNOSIS", GameState.PATIENT),
    ("C", "correct", "CORRECT RESULT", GameState.OUTCOME),
    ("W", "wrong", "WRONG RESULT", GameState.OUTCOME),
    ("P", "shutdown", "CLINIC POWER DOWN", GameState.TITLE),
    ("R", "recap", "SHIFT RECAP", GameState.DAY_COMPLETE),
    ("S", "shop", "SHOP", GameState.SHOP),
    ("U", "ending", "UFO ENDING", GameState.ENDING),
    ("F", "final", "FINAL REPORT", GameState.FINAL),
)

DEVELOPER_KEY_MAP = {
    pygame.K_1: "intro",
    pygame.K_2: "dialogue",
    pygame.K_3: "tutorial",
    pygame.K_4: "reception",
    pygame.K_5: "patient",
    pygame.K_6: "test_result",
    pygame.K_7: "notebook",
    pygame.K_8: "diagnosis_hand",
    pygame.K_9: "diagnosis_confirm",
    pygame.K_c: "correct",
    pygame.K_w: "wrong",
    pygame.K_p: "shutdown",
    pygame.K_r: "recap",
    pygame.K_s: "shop",
    pygame.K_u: "ending",
    pygame.K_f: "final",
}


class DeveloperMixin:
    """Provide an F10-only navigator without exposing debug controls to players."""

    def setup_developer_navigator(self):
        self.developer_navigator_open = False
        self.developer_button_rects = []
        self.developer_scene_id = None

    def toggle_developer_navigator(self):
        """Open or close the hidden preview menu."""

        self.developer_navigator_open = not self.developer_navigator_open
        if self.developer_navigator_open:
            self.developer_scene_id = self.infer_developer_scene_id()
            self.finish_guided_tutorial()
            self.tutorial_open = False
            self.tutorial_opened_at = None
            self.exit_confirmation_open = False
            self.exit_confirmation_opened_at = None
            self.diagnosis_confirmation_open = False
        self.play_sfx("button")

    def infer_developer_scene_id(self):
        """Identify the precise visible scene before its modal is dismissed."""

        if self.state == GameState.INTRO:
            return "intro"
        if self.intro_dialogue_active:
            return "dialogue"
        if self.guided_tutorial_active:
            return "tutorial"
        if self.end_day_shutdown_started_at is not None:
            return "shutdown"
        if self.state == GameState.PATIENT:
            if self.diagnosis_confirmation_open:
                return "diagnosis_confirm"
            if self.showing_diagnosis_hand:
                return "diagnosis_hand"
            return "patient"
        if self.state == GameState.OUTCOME:
            return "correct" if self.diagnosis_correct else "wrong"
        preferred_scenes = {
            GameState.TITLE: "reception",
            GameState.TEST_RESULT: "test_result",
            GameState.NOTEBOOK: "notebook",
            GameState.DAY_COMPLETE: "recap",
            GameState.SHOP: "shop",
            GameState.ENDING: "ending",
            GameState.FINAL: "final",
        }
        return preferred_scenes.get(self.state, "intro")

    def get_developer_screen_rects(self):
        """Return the stable four-column scene-directory layout."""

        return [
            pygame.Rect(84 + column * 235, 185 + row * 72, 220, 56)
            for row in range(4)
            for column in range(4)
        ]

    def get_developer_scene_index(self, scene_id):
        """Return the directory position for a stable scene identifier."""

        return next(
            index
            for index, entry in enumerate(DEVELOPER_SCREENS)
            if entry[1] == scene_id
        )

    def handle_developer_key(self, key):
        """Navigate by number or cycle screens with the arrow keys."""

        if key in DEVELOPER_KEY_MAP:
            self.jump_to_developer_screen(
                self.get_developer_scene_index(DEVELOPER_KEY_MAP[key])
            )
            return
        if key in (pygame.K_LEFT, pygame.K_RIGHT):
            current_index = self.get_current_developer_scene_index()
            step = -1 if key == pygame.K_LEFT else 1
            self.jump_to_developer_screen(
                (current_index + step) % len(DEVELOPER_SCREENS)
            )

    def get_current_developer_scene_index(self):
        """Choose the current special scene, falling back to its base state."""

        if self.developer_scene_id is not None:
            index = self.get_developer_scene_index(self.developer_scene_id)
            if DEVELOPER_SCREENS[index][3] == self.state:
                return index
        return self.get_developer_scene_index(self.infer_developer_scene_id())

    def handle_developer_click(self, position):
        """Jump to the clicked preview destination."""

        for index, rect in enumerate(self.get_developer_screen_rects()):
            if rect.collidepoint(position):
                self.jump_to_developer_screen(index)
                return

    def jump_to_developer_screen(self, index):
        """Prepare any required preview data and display one selected screen."""

        _shortcut, scene_id, _label, target_state = DEVELOPER_SCREENS[index]
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
        self.end_day_shutdown_started_at = None
        self.test_result_started_at = None
        self.ending_started_at = None

        if scene_id == "intro":
            self.restart_game()
            self.state = GameState.INTRO
            self.intro_started_at = pygame.time.get_ticks()
            self.intro_wake_active = False
        elif scene_id == "dialogue":
            self.restart_game()
            self.state = GameState.TITLE
            self.start_intro_dialogue()
        elif scene_id == "tutorial":
            self.restart_game()
            self.state = GameState.TITLE
            self.start_guided_tutorial()
        elif scene_id == "reception":
            self.reset_day()
            self.state = GameState.TITLE
        elif scene_id in (
            "patient",
            "test_result",
            "notebook",
            "diagnosis_hand",
            "diagnosis_confirm",
            "correct",
            "wrong",
        ):
            self.prepare_developer_patient_preview()

        if scene_id == "test_result":
            self.last_test_name = "TEMPERATURE"
            self.last_test_result = "Current temperature: 1700°F"
            self.last_test_cost = self.player.get_test_cost(
                self.player.test_hand[0].value
            )
            self.test_result_started_at = pygame.time.get_ticks()
        elif scene_id == "notebook":
            self.notebook.add_test(
                self.patient,
                "TEMPERATURE",
                "Current temperature: 1700°F",
            )
            self.build_notebook_columns()
            self.notebook_spread = 0
        elif scene_id in ("diagnosis_hand", "diagnosis_confirm"):
            self.switch_active_hand(True)
            self.diagnosis_folder_animation_started_at = None
            if scene_id == "diagnosis_confirm":
                self.selected_card_index = self.get_hypothermia_card_index()
                self.open_diagnosis_confirmation()
        elif scene_id == "correct":
            self.last_diagnosis = self.patient.diagnosis
            self.diagnosis_correct = True
        elif scene_id == "wrong":
            self.last_diagnosis = next(
                card.value
                for card in self.player.diagnosis_hand
                if card.value != self.patient.diagnosis
            )
            self.diagnosis_correct = False

        if scene_id in ("shutdown", "recap", "shop", "ending", "final"):
            self.prepare_developer_shift_preview()

        if scene_id == "shutdown":
            self.patients_called = len(self.waiting_room_queue)
            self.begin_end_day_shutdown()
        if scene_id in ("shop", "ending", "final"):
            self.settle_daily_pay()
        if scene_id == "ending":
            self.ending_started_at = pygame.time.get_ticks()
        elif scene_id == "final":
            self.ending_started_at = None

        if scene_id not in ("intro", "dialogue", "tutorial"):
            self.state = target_state
        self.developer_scene_id = scene_id
        self.play_sfx("button")

    def prepare_developer_patient_preview(self):
        """Reset a complete Zorpa encounter for reliable mid-shift previews."""

        self.patients_called = 0
        self.reset_round()
        self.patients_called = 1
        self.state = GameState.PATIENT
        self.patient_left = False
        self.patient_leave_text = ""

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
            self.daily_evidence_cases = len(self.waiting_room_queue)
            self.daily_payout_applied = False

    def draw_developer_navigator(self):
        """Draw the hidden clinic screen directory over the current page."""

        dim = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        dim.fill((2, 6, 12, 224))
        self.screen.blit(dim, (0, 0))

        panel = pygame.Rect(65, 74, 970, 510)
        pygame.draw.rect(self.screen, (3, 8, 13), panel.move(8, 9), border_radius=18)
        pygame.draw.rect(self.screen, (27, 29, 45), panel, border_radius=18)
        pygame.draw.rect(self.screen, (187, 137, 211), panel, width=3, border_radius=18)

        tag = self.card_font.render("DEVELOPER TOOL", True, (216, 159, 238))
        self.screen.blit(tag, tag.get_rect(center=(panel.centerx, panel.y + 28)))
        heading = self.heading_font.render("SCREEN NAVIGATOR", True, COLORS["text"])
        self.screen.blit(heading, heading.get_rect(center=(panel.centerx, panel.y + 58)))
        hint = self.card_font.render(
            "CLICK A SCENE OR USE ITS KEY  •  LEFT/RIGHT CYCLES  •  F10 CLOSES",
            True,
            COLORS["muted"],
        )
        self.screen.blit(hint, hint.get_rect(center=(panel.centerx, panel.y + 88)))

        mouse_position = self.get_mouse_position()
        self.developer_button_rects = self.get_developer_screen_rects()
        current_index = self.get_current_developer_scene_index()
        for index, ((shortcut, _scene_id, label, _target_state), rect) in enumerate(zip(
            DEVELOPER_SCREENS,
            self.developer_button_rects,
        )):
            selected = index == current_index
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
            number_label = self.body_font.render(shortcut, True, border)
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
            "Development shortcut only  •  Every destination is interactive",
            True,
            COLORS["muted"],
        )
        self.screen.blit(footer, footer.get_rect(center=(panel.centerx, panel.bottom - 24)))
