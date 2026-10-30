"""Interactive first-patient training and compact reusable Help."""

import math

import pygame

from gui_state import GameState
from gui_theme import COLORS, WINDOW_SIZE


class TutorialMixin:
    """Guide the player through Zorpa using the real clinic controls."""

    def start_guided_tutorial(self):
        """Begin the first-shift walkthrough at the reception call button."""

        self.tutorial_open = False
        self.tutorial_opened_at = None
        self.guided_tutorial_active = True
        self.guided_tutorial_step = "call_patient"
        self.guided_tutorial_nudge = ""
        self.guided_tutorial_nudge_started_at = None
        self.guided_tutorial_step_started_at = pygame.time.get_ticks()

    def finish_guided_tutorial(self):
        """Release every control after Zorpa's training case or a manual skip."""

        self.guided_tutorial_active = False
        self.guided_tutorial_step = None
        self.guided_tutorial_nudge = ""
        self.guided_tutorial_nudge_started_at = None
        self.guided_tutorial_step_started_at = None

    def set_guided_tutorial_step(self, step):
        """Move training to a new action and clear the previous correction."""

        self.guided_tutorial_step = step
        self.guided_tutorial_nudge = ""
        self.guided_tutorial_nudge_started_at = None
        self.guided_tutorial_step_started_at = pygame.time.get_ticks()

    def nudge_guided_tutorial(self, message="Follow the highlighted control first."):
        """Briefly correct an out-of-order click without interrupting the game."""

        self.guided_tutorial_nudge = message
        self.guided_tutorial_nudge_started_at = pygame.time.get_ticks()
        self.play_sfx("button")

    def get_temperature_card_index(self):
        """Return the first Temperature card in the current test hand."""

        for index, card in enumerate(self.player.test_hand):
            if card.value.name == "TEMPERATURE":
                return index
        return None

    def get_hypothermia_card_index(self):
        """Return the Hypothermia card in the current diagnosis hand."""

        for index, card in enumerate(self.player.diagnosis_hand):
            if card.value.name == "Hypothermia":
                return index
        return None

    def get_guided_tutorial_target(self):
        """Return the screen rectangle currently receiving the player's attention."""

        step = self.guided_tutorial_step
        if step == "call_patient":
            return self.start_button
        if step == "symptom":
            alien = self.layout["alien"]
            # Match the speech-bubble rectangle exactly so the halo and arrow
            # remain centered on what the player is being asked to read.
            return pygame.Rect(alien.right - 112, alien.y + 49, 91, 55)
        if step == "inspect_id":
            return self.layout["id_card"]
        if step == "review_health_id":
            card = self.layout["id_card"]
            return pygame.Rect(card.x + 70, card.y + 92, card.width - 82, 21)
        if step == "temperature_select":
            index = self.get_temperature_card_index()
            if index is not None and index < len(self.card_rects):
                resting = self.card_rects[index]
                return resting.union(self.get_hovered_card_rect(resting))
        if step == "temperature_run" and self.selected_card_index is not None:
            selected = self.get_selected_card_rect(self.selected_card_index)
            return self.get_run_test_button(selected)
        if step == "test_result":
            if self.get_test_result_reveal_progress() >= 1.0:
                return self.continue_button
            return pygame.Rect(105, 105, 890, 455)
        if step in ("note_transfer", "open_notebook"):
            return self.layout["notebook"]
        if step == "review_notebook":
            return self.notebook_layout["book"]
        if step == "diagnosis_folder":
            return self.layout["diagnosis"]
        if step == "diagnosis_select":
            index = self.get_hypothermia_card_index()
            if index is not None and index < len(self.card_rects):
                resting = self.card_rects[index]
                return resting.union(self.get_hovered_card_rect(resting))
        if step == "diagnosis_play" and self.selected_card_index is not None:
            selected = self.get_selected_card_rect(self.selected_card_index)
            return self.get_card_action_button(selected)
        if step == "diagnosis_confirm":
            return self.diagnosis_confirm_button
        return None

    def get_guided_tutorial_step_number(self):
        """Group the detailed click states into nine player-facing lessons."""

        groups = {
            "call_patient": 1,
            "patient_arrival": 1,
            "symptom": 2,
            "inspect_id": 3,
            "review_health_id": 3,
            "temperature_select": 4,
            "temperature_run": 4,
            "test_result": 5,
            "note_transfer": 6,
            "open_notebook": 6,
            "review_notebook": 6,
            "diagnosis_folder": 7,
            "diagnosis_select": 8,
            "diagnosis_play": 8,
            "diagnosis_confirm": 8,
            "complete": 9,
        }
        return groups.get(self.guided_tutorial_step, 1)

    def get_guided_tutorial_prompt(self):
        """Return instruction text, position, and whether any click advances it."""

        prompts = {
            "symptom": ("Start with what the patient is telling you.", pygame.Rect(620, 168, 400, 104), True),
            "inspect_id": ("Inspect Zorpa's Intergalactic ID.", pygame.Rect(62, 178, 375, 92), False),
            "review_health_id": ("Normal temperature: 2,000°F. Remember this baseline.", pygame.Rect(62, 174, 410, 104), True),
            "temperature_select": ("Shaking may be temperature-related. Select TEMPERATURE.", pygame.Rect(650, 174, 400, 92), False),
            "temperature_run": ("Run the selected test. Tests are billed at shift end.", pygame.Rect(650, 174, 400, 92), False),
            "test_result": ("Read the observed result, then return to Zorpa.", pygame.Rect(120, 462, 400, 92), False),
            "note_transfer": ("The clinic is filing this result in Patient Notes...", pygame.Rect(650, 172, 400, 92), False),
            "open_notebook": ("The result is recorded. Open Patient Notes.", pygame.Rect(265, 401, 410, 92), False),
            "review_notebook": ("Compare 2,000°F normal with the current 1,700°F result.", pygame.Rect(350, 12, 400, 104), True),
            "diagnosis_folder": ("The evidence points to hypothermia. Open Diagnosis.", pygame.Rect(405, 173, 410, 92), False),
            "diagnosis_select": ("Select the Hypothermia case file.", pygame.Rect(650, 173, 400, 92), False),
            "diagnosis_play": ("Submit the selected condition as your diagnosis.", pygame.Rect(650, 173, 400, 92), False),
            "diagnosis_confirm": ("Diagnoses are final. Confirm when you are certain.", pygame.Rect(105, 174, 400, 92), False),
            "complete": ("Adequate work, Doctor. Three patients remain.", pygame.Rect(350, 12, 400, 104), True),
        }
        return prompts.get(self.guided_tutorial_step)

    def handle_guided_tutorial_click(self, position):
        """Allow only the real control required by the current training step."""

        if self.tutorial_skip_button.collidepoint(position):
            self.play_sfx("button")
            self.finish_guided_tutorial()
            return

        step = self.guided_tutorial_step
        if step == "call_patient" and self.start_button.collidepoint(position):
            self.play_sfx("button")
            self.begin_reception_transition()
            self.set_guided_tutorial_step("patient_arrival")
            return
        target = self.get_guided_tutorial_target()
        target_clicked = target is not None and target.collidepoint(position)
        # Reading steps deliberately consume the click instead of passing it
        # through to the dimmed game screen underneath the tutorial.
        if step == "symptom":
            self.play_sfx("button")
            self.set_guided_tutorial_step("inspect_id")
            return
        if step == "inspect_id" and self.layout["id_card"].collidepoint(position):
            self.play_sfx("button")
            self.showing_health_id = True
            self.set_guided_tutorial_step("review_health_id")
            return
        if step == "review_health_id":
            self.play_sfx("button")
            self.set_guided_tutorial_step("temperature_select")
            return
        if step == "temperature_select":
            index = self.get_temperature_card_index()
            if index is not None and target_clicked:
                self.selected_card_index = index
                self.play_sfx("card_select")
                self.set_guided_tutorial_step("temperature_run")
                return
        if step == "temperature_run" and self.selected_card_index is not None:
            selected = self.get_selected_card_rect(self.selected_card_index)
            if self.get_run_test_button(selected).collidepoint(position):
                self.play_sfx("button")
                self.run_selected_test()
                self.set_guided_tutorial_step("test_result")
                return
        if step == "test_result":
            if self.get_test_result_reveal_progress() >= 1.0 and self.continue_button.collidepoint(position):
                self.handle_test_result_click(position)
                self.set_guided_tutorial_step("note_transfer")
                return
            self.nudge_guided_tutorial("Wait for the scanner to finish.")
            return
        if step == "open_notebook" and self.layout["notebook"].collidepoint(position):
            self.open_notebook()
            self.set_guided_tutorial_step("review_notebook")
            return
        if step == "review_notebook":
            self.play_sfx("button")
            self.state = GameState.PATIENT
            self.set_guided_tutorial_step("diagnosis_folder")
            return
        if step == "diagnosis_folder" and self.layout["diagnosis"].collidepoint(position):
            self.play_sfx("button")
            self.switch_active_hand(True)
            self.set_guided_tutorial_step("diagnosis_select")
            return
        if step == "diagnosis_select":
            index = self.get_hypothermia_card_index()
            if index is not None and target_clicked:
                self.selected_card_index = index
                self.play_sfx("card_select")
                self.set_guided_tutorial_step("diagnosis_play")
                return
        if step == "diagnosis_play" and self.selected_card_index is not None:
            selected = self.get_selected_card_rect(self.selected_card_index)
            if self.get_card_action_button(selected).collidepoint(position):
                self.play_sfx("button")
                self.open_diagnosis_confirmation()
                self.set_guided_tutorial_step("diagnosis_confirm")
                return
        if step == "diagnosis_confirm" and self.diagnosis_confirm_button.collidepoint(position):
            self.confirm_selected_diagnosis()
            self.set_guided_tutorial_step("complete")
            return
        if step == "complete":
            self.play_sfx("button")
            self.finish_guided_tutorial()
            return

        if step not in ("patient_arrival", "note_transfer"):
            self.nudge_guided_tutorial()

    def handle_guided_tutorial_key(self, key):
        """Provide keyboard equivalents for tutorial actions and message advances."""

        if key == pygame.K_ESCAPE:
            self.open_exit_confirmation()
            return
        if key not in (pygame.K_RETURN, pygame.K_SPACE):
            return
        step = self.guided_tutorial_step
        if step == "call_patient":
            self.handle_guided_tutorial_click(self.start_button.center)
        elif step in ("symptom", "review_health_id", "review_notebook", "complete"):
            self.handle_guided_tutorial_click((10, 10))
        else:
            self.nudge_guided_tutorial("Use the highlighted clinic control.")

    def update_guided_tutorial(self):
        """Advance tutorial steps that depend on existing timed animations."""

        if not self.guided_tutorial_active:
            return
        if (
            self.guided_tutorial_step == "patient_arrival"
            and self.state == GameState.PATIENT
            and self.patient_fade_started_at is None
        ):
            self.set_guided_tutorial_step("symptom")
        elif (
            self.guided_tutorial_step == "note_transfer"
            and self.state == GameState.PATIENT
            and self.note_transfer_animation is None
            and self.notebook_attention_started_at is None
            and self.pending_test_discard is None
            and self.discard_animation is None
        ):
            self.set_guided_tutorial_step("open_notebook")

    def open_tutorial(self):
        """Open compact reference Help without restarting forced training."""

        if not self.tutorial_open:
            self.tutorial_opened_at = pygame.time.get_ticks()
        self.tutorial_open = True

    def close_tutorial(self):
        """Close Help and compensate any animations for the paused duration."""

        if self.tutorial_opened_at is not None:
            paused_for = pygame.time.get_ticks() - self.tutorial_opened_at
            self.offset_animation_timers(paused_for)
        self.play_sfx("button")
        self.tutorial_open = False
        self.tutorial_opened_at = None

    def handle_tutorial_click(self, position):
        """Close compact Help from its return button."""

        if self.tutorial_begin_button.collidepoint(position):
            self.close_tutorial()

    def get_tutorial_action_label(self):
        """Describe the screen restored after closing Help."""

        if self.state == GameState.TITLE:
            return "RETURN TO RECEPTION"
        return {
            GameState.PATIENT: "RETURN TO PATIENT",
            GameState.TEST_RESULT: "RETURN TO TEST RESULT",
            GameState.NOTEBOOK: "RETURN TO NOTEBOOK",
            GameState.OUTCOME: "RETURN TO CASE RESULT",
            GameState.DAY_COMPLETE: "RETURN TO SHIFT RECAP",
            GameState.SHOP: "RETURN TO SHOP",
            GameState.ENDING: "CONTINUE ENDING",
            GameState.FINAL: "RETURN TO SUMMARY",
        }.get(self.state, "CLOSE HELP")

    def draw_help_button(self):
        """Draw the purple top-right Help control."""

        rect = self.help_button
        hovered = rect.collidepoint(self.get_mouse_position())
        border = (206, 158, 233) if hovered else (155, 116, 190)
        fill = (50, 37, 68) if hovered else (27, 29, 45)
        pygame.draw.rect(self.screen, (3, 8, 13), rect.move(2, 3), border_radius=8)
        pygame.draw.rect(self.screen, fill, rect, border_radius=8)
        pygame.draw.rect(self.screen, border, rect, width=2, border_radius=8)
        label = self.card_font.render("?  HELP", True, (232, 211, 242))
        self.screen.blit(label, label.get_rect(center=rect.center))

    def draw_tutorial_overlay(self):
        """Draw compact reference Help, replacing the old full-screen briefing."""

        dim = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        dim.fill((2, 6, 12, 218))
        self.screen.blit(dim, (0, 0))
        panel = pygame.Rect(270, 130, 560, 390)
        pygame.draw.rect(self.screen, (3, 8, 13), panel.move(8, 9), border_radius=16)
        pygame.draw.rect(self.screen, (23, 29, 42), panel, border_radius=16)
        pygame.draw.rect(self.screen, (187, 137, 211), panel, width=3, border_radius=16)
        title = self.heading_font.render("CLINIC QUICK GUIDE", True, (232, 211, 242))
        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 42)))
        subtitle = self.card_font.render("FOLLOW THE EVIDENCE  •  PROTECT YOUR PAY", True, COLORS["muted"])
        self.screen.blit(subtitle, subtitle.get_rect(center=(panel.centerx, panel.y + 68)))
        rows = (
            ("1", "INSPECT", "Read symptoms and flip the patient's ID."),
            ("2", "TEST", "Run useful tests; every machine use has a cost."),
            ("3", "COMPARE", "Patient Notes keeps anatomy and results together."),
            ("4", "DIAGNOSE", "Submit the condition best supported by the clues."),
        )
        for index, (number, heading, detail) in enumerate(rows):
            row = pygame.Rect(panel.x + 34, panel.y + 91 + index * 57, panel.width - 68, 47)
            pygame.draw.rect(self.screen, (35, 42, 55), row, border_radius=8)
            pygame.draw.rect(self.screen, (92, 72, 111), row, width=1, border_radius=8)
            pygame.draw.circle(self.screen, (151, 101, 180), (row.x + 24, row.centery), 14)
            number_label = self.card_font.render(number, True, COLORS["text"])
            self.screen.blit(number_label, number_label.get_rect(center=(row.x + 24, row.centery)))
            heading_label = self.card_font.render(heading, True, (216, 159, 238))
            self.screen.blit(heading_label, (row.x + 49, row.y + 7))
            detail_label = self.card_font.render(detail, True, COLORS["text"])
            self.screen.blit(detail_label, (row.x + 49, row.y + 25))
        self.tutorial_begin_button = pygame.Rect(panel.centerx - 145, panel.bottom - 55, 290, 38)
        hovered = self.tutorial_begin_button.collidepoint(self.get_mouse_position())
        color = COLORS["accent"] if hovered else (151, 101, 180)
        pygame.draw.rect(self.screen, color, self.tutorial_begin_button, border_radius=8)
        label = self.small_font.render(self.get_tutorial_action_label(), True, COLORS["background"])
        self.screen.blit(label, label.get_rect(center=self.tutorial_begin_button.center))

    def draw_guided_tutorial(self):
        """Spotlight the current real control and add a compact movable prompt."""

        if not self.guided_tutorial_active:
            return
        step = self.guided_tutorial_step
        target = self.get_guided_tutorial_target()
        pulse = (math.sin(pygame.time.get_ticks() / 210) + 1) / 2
        if step != "patient_arrival":
            dim = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
            dim.fill((2, 6, 12, 178))
            if target is not None:
                pygame.draw.rect(dim, (0, 0, 0, 0), target.inflate(18, 18), border_radius=12)
            self.screen.blit(dim, (0, 0))
        if target is not None:
            glow = target.inflate(round(13 + 5 * pulse), round(13 + 5 * pulse))
            pygame.draw.rect(self.screen, (106, 246, 198), glow, width=2 + round(pulse), border_radius=11)
            arrow_x = target.centerx
            if target.y > 145:
                tip_y = target.y - 8
                base_y = tip_y - 15 - round(4 * pulse)
            else:
                tip_y = target.bottom + 8
                base_y = tip_y + 15 + round(4 * pulse)
            pygame.draw.polygon(self.screen, (106, 246, 198), ((arrow_x, tip_y), (arrow_x - 9, base_y), (arrow_x + 9, base_y)))

        # Keep training controls above the clinic status bar so the patient's
        # money and case information remain visible throughout the walkthrough.
        self.tutorial_skip_button = pygame.Rect(933, 58, 135, 28)
        skip_hovered = self.tutorial_skip_button.collidepoint(self.get_mouse_position())
        pygame.draw.rect(self.screen, (46, 36, 60) if skip_hovered else (24, 29, 43), self.tutorial_skip_button, border_radius=7)
        pygame.draw.rect(self.screen, (183, 130, 207), self.tutorial_skip_button, width=1, border_radius=7)
        skip = self.pile_font.render("SKIP TRAINING", True, (224, 202, 234))
        self.screen.blit(skip, skip.get_rect(center=self.tutorial_skip_button.center))

        # The first action is intentionally communicated only by light and motion.
        prompt = self.get_guided_tutorial_prompt()
        if prompt is None or step == "patient_arrival":
            return
        message, panel, click_anywhere = prompt
        accent = (106, 246, 198)
        points = ((panel.x + 10, panel.y), (panel.right - 10, panel.y), (panel.right, panel.y + 10), (panel.right, panel.bottom - 10), (panel.right - 10, panel.bottom), (panel.x + 10, panel.bottom), (panel.x, panel.bottom - 10), (panel.x, panel.y + 10))
        pygame.draw.polygon(self.screen, (2, 7, 12), tuple((x + 4, y + 5) for x, y in points))
        pygame.draw.polygon(self.screen, (11, 29, 36), points)
        pygame.draw.lines(self.screen, accent, True, points, width=2)
        step_label = self.tutorial_label_font.render(f"TRAINING CASE  •  STEP {self.get_guided_tutorial_step_number()} OF 9", True, accent)
        self.screen.blit(step_label, (panel.x + 16, panel.y + 10))
        message_box = pygame.Rect(
            panel.x + 16,
            panel.y + 34,
            panel.width - 32,
            panel.height - (61 if click_anywhere else 44),
        )
        self.draw_wrapped_text(
            message,
            self.tutorial_body_font,
            COLORS["text"],
            message_box,
            line_spacing=2,
        )
        if click_anywhere:
            continue_text = self.tutorial_label_font.render(
                "CLICK ANYWHERE TO CONTINUE",
                True,
                accent,
            )
            self.screen.blit(
                continue_text,
                continue_text.get_rect(
                    center=(panel.centerx, panel.bottom - 17),
                ),
            )
        if self.guided_tutorial_nudge and self.guided_tutorial_nudge_started_at is not None and pygame.time.get_ticks() - self.guided_tutorial_nudge_started_at < 1800:
            nudge = self.card_font.render(self.guided_tutorial_nudge, True, (255, 157, 139))
            nudge_rect = nudge.get_rect()
            nudge_panel = nudge_rect.inflate(18, 10)
            nudge_panel.x = max(8, min(panel.x + 14, WINDOW_SIZE[0] - nudge_panel.width - 8))
            if panel.bottom + nudge_panel.height + 6 < WINDOW_SIZE[1] - 8:
                nudge_panel.y = panel.bottom + 6
            else:
                nudge_panel.bottom = panel.y - 6
            pygame.draw.rect(self.screen, (45, 24, 31), nudge_panel, border_radius=6)
            pygame.draw.rect(self.screen, (216, 105, 95), nudge_panel, width=1, border_radius=6)
            self.screen.blit(nudge, nudge.get_rect(center=nudge_panel.center))
