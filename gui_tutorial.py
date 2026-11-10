"""Interactive first-patient training and compact reusable Help."""

import math

import pygame

from gui_card_shop import CARD_SHOP_BASE_PRICE, CARD_SHOP_PRICE_STEP
from gui_state import GameState
from gui_theme import COLORS, WINDOW_SIZE
from Player import (
    DIAGNOSIS_REWARD,
    DRAW_COST,
    LIMITED_EVIDENCE_REWARD,
    MAX_TEST_HAND_SIZE,
    RETURN_PASSAGE_COST,
    WRONG_DIAGNOSIS_PENALTY,
)
from Test import TEST_COSTS_BY_RARITY


class TutorialMixin:
    """Guide the player through Zorpa using the real clinic controls."""

    def is_training_destination(self):
        """Return whether the active route stop owns the guided first case."""

        return self.current_destination.key == self.destinations[0].key

    def start_guided_tutorial(self):
        """Begin training only at the route's first destination."""

        if not self.is_training_destination():
            self.finish_guided_tutorial()
            return False

        self.tutorial_open = False
        self.tutorial_opened_at = None
        self.guided_tutorial_active = True
        self.guided_tutorial_step = "call_patient"
        self.guided_tutorial_nudge = ""
        self.guided_tutorial_nudge_started_at = None
        self.guided_tutorial_step_started_at = pygame.time.get_ticks()
        self.help_attention_started_at = None
        return True

    def finish_guided_tutorial(self, show_help_reminder=False):
        """Release every control after Zorpa's training case or a manual skip."""

        self.card_shop_open = False
        self.guided_tutorial_active = False
        self.guided_tutorial_step = None
        self.guided_tutorial_nudge = ""
        self.guided_tutorial_nudge_started_at = None
        self.guided_tutorial_step_started_at = None
        if (
            show_help_reminder
            and not self.help_attention_seen
            and self.help_attention_started_at is None
        ):
            self.help_attention_started_at = pygame.time.get_ticks()

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

        return self.get_test_card_index("TEMPERATURE")

    def get_test_card_index(self, test_name):
        """Return the first matching test card in the current hand."""

        for index, card in enumerate(self.player.test_hand):
            if card.value.name == test_name:
                return index
        return None

    def get_blood_chemistry_card_index(self):
        """Return Zorpa's second supporting test card when it is in hand."""

        return self.get_test_card_index("BLOOD CHEMISTRY")

    def get_blood_chemistry_shop_rect(self):
        """Return the Card Shop slot that sells Blood Chemistry."""

        for test, rect in zip(self.card_shop_catalog, self.get_card_shop_slot_rects()):
            if test.name == "BLOOD CHEMISTRY":
                return rect
        return None

    def get_correct_diagnosis_card_index(self):
        """Return the current patient's correct diagnosis card."""

        for index, card in enumerate(self.player.diagnosis_hand):
            if card.value == self.patient.diagnosis:
                return index
        return None

    def get_diagnosis_choice_area(self):
        """Return one spotlight covering every visible diagnosis option.

        Training should teach the player to compare the case files, so the
        tutorial deliberately highlights the whole hand instead of revealing
        the correct card's shuffled position.
        """

        if not self.card_rects:
            return None
        choice_area = self.card_rects[0].copy()
        for card_rect in self.card_rects[1:]:
            choice_area.union_ip(card_rect)
        return choice_area

    def get_diagnosis_card_index_at(self, position):
        """Return the diagnosis card clicked during the guided comparison."""

        for index, card_rect in enumerate(self.card_rects):
            if card_rect.collidepoint(position):
                return index
        return None

    def get_guided_tutorial_target(self):
        """Return the screen rectangle currently receiving the player's attention."""

        step = self.guided_tutorial_step
        if step == "call_patient":
            return self.start_button
        if step == "symptom":
            return self.get_symptom_bubble_rect()
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
            return None
        if step == "open_notebook":
            return self.layout["notebook"]
        if step == "review_notebook":
            return self.notebook_layout["book"]
        if step == "card_shop_open":
            return self.card_shop_button
        if step == "card_shop_select":
            return self.get_blood_chemistry_shop_rect()
        if step == "card_shop_buy":
            return self.card_shop_buy_button
        if step == "blood_select":
            index = self.get_blood_chemistry_card_index()
            if index is not None and index < len(self.card_rects):
                resting = self.card_rects[index]
                return resting.union(self.get_hovered_card_rect(resting))
        if step == "blood_run" and self.selected_card_index is not None:
            selected = self.get_selected_card_rect(self.selected_card_index)
            return self.get_run_test_button(selected)
        if step == "second_test_result":
            return None
        if step == "second_open_notebook":
            return self.layout["notebook"]
        if step == "second_review_notebook":
            return self.notebook_layout["book"]
        if step == "diagnosis_folder":
            return self.layout["diagnosis"]
        if step == "diagnosis_select":
            return self.get_diagnosis_choice_area()
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
            "card_shop_open": 7,
            "card_shop_select": 7,
            "card_shop_buy": 7,
            "blood_select": 7,
            "blood_run": 7,
            "second_test_result": 7,
            "second_note_transfer": 7,
            "second_open_notebook": 7,
            "second_review_notebook": 7,
            "diagnosis_folder": 8,
            "diagnosis_select": 8,
            "diagnosis_play": 8,
            "diagnosis_confirm": 8,
            "complete": 9,
        }
        return groups.get(self.guided_tutorial_step, 1)

    def get_guided_tutorial_prompt(self):
        """Return instruction text, position, and whether any click advances it."""

        if self.guided_tutorial_step == "symptom":
            current = self.patient_dialogue_index + 1
            total = len(self.patient.dialogue)
            if current >= total:
                message = (
                    f"INTERVIEW {current}/{total}  •  You have heard every response. "
                    "Click Zorpa once more to continue."
                )
            else:
                message = (
                    f"INTERVIEW {current}/{total}  •  Read Zorpa's response, then "
                    "click the patient to ask another follow-up."
                )
            return message, pygame.Rect(620, 168, 400, 104), False

        prompts = {
            "inspect_id": ("Inspect Zorpa's Intergalactic ID.", pygame.Rect(62, 178, 375, 92), False),
            "review_health_id": ("Normal temperature: 2,000°F. Remember this baseline.", pygame.Rect(62, 174, 410, 104), True),
            "temperature_select": (
                "Shaking may be temperature-related. Select TEMPERATURE. Random draws cost $5; Card Shop lets you choose a missing card for $10 or more.",
                pygame.Rect(650, 174, 400, 104),
                False,
            ),
            "temperature_run": ("Run the selected test. Its cost is deducted immediately.", pygame.Rect(650, 174, 400, 92), False),
            "test_result": ("Read the observed result, then return to Zorpa.", pygame.Rect(120, 462, 400, 92), False),
            "open_notebook": ("The result is recorded. Open Patient Notes.", pygame.Rect(265, 401, 410, 92), False),
            "review_notebook": ("Temperature is one clue, so Evidence reads 1/2. Two matching clues earn full case pay.", pygame.Rect(350, 12, 400, 104), True),
            "card_shop_open": ("One clue is not enough. Open Card Shop to request BLOOD CHEMISTRY from the live deck.", pygame.Rect(650, 174, 400, 104), False),
            "card_shop_select": ("Choose BLOOD CHEMISTRY. The shop is useful when a needed test is missing from your hand.", pygame.Rect(38, 174, 410, 104), False),
            "card_shop_buy": ("Buy the card. Targeted cards cost more each time, and running the test has its own fee.", pygame.Rect(38, 174, 410, 104), False),
            "blood_select": ("Now select BLOOD CHEMISTRY for a second, independent clue.", pygame.Rect(650, 174, 400, 92), False),
            "blood_run": ("Run Blood Chemistry and compare it with the temperature result.", pygame.Rect(650, 174, 400, 92), False),
            "second_test_result": ("Read the blood analysis, then return to Zorpa.", pygame.Rect(120, 462, 400, 92), False),
            "second_open_notebook": ("Open Patient Notes again to confirm the evidence pair.", pygame.Rect(265, 401, 410, 92), False),
            "second_review_notebook": ("Evidence is now 2/2. A supported correct diagnosis earns the full $50 case pay.", pygame.Rect(350, 12, 400, 104), True),
            "diagnosis_folder": ("You have enough evidence. Open Diagnosis and compare the five case files.", pygame.Rect(405, 173, 410, 92), False),
            "diagnosis_select": (
                "Zorpa is 1,700°F—300°F below the 2,000°F baseline. Choose the case file that best explains dangerous cooling and shivering; the other conditions need neural, blood, lung, or toxin evidence.",
                pygame.Rect(620, 158, 430, 132),
                False,
            ),
            "diagnosis_play": ("Submit the selected condition as your diagnosis.", pygame.Rect(650, 173, 400, 92), False),
            "diagnosis_confirm": (f"Confirm when you are ready. Incorrect diagnoses cost ${WRONG_DIAGNOSIS_PENALTY}, and repeated mistakes may cause a patient to leave.", pygame.Rect(350, 38, 400, 104), False),
            "complete": ("Correct and fully supported. Matching evidence protects patients—and earns full case pay.", pygame.Rect(350, 12, 400, 104), True),
        }
        return prompts.get(self.guided_tutorial_step)

    def handle_guided_tutorial_click(self, position):
        """Allow only the real control required by the current training step."""

        if self.tutorial_skip_button.collidepoint(position):
            self.play_sfx("button")
            self.finish_guided_tutorial(show_help_reminder=True)
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
            if self.layout["alien"].collidepoint(position):
                if self.patient_dialogue_index < len(self.patient.dialogue) - 1:
                    self.advance_patient_dialogue()
                else:
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
            if self.get_blood_chemistry_card_index() is None:
                self.set_guided_tutorial_step("card_shop_open")
            else:
                self.set_guided_tutorial_step("blood_select")
            return
        if step == "card_shop_open" and self.card_shop_button.collidepoint(position):
            self.toggle_card_shop()
            self.set_guided_tutorial_step("card_shop_select")
            return
        if step == "card_shop_select":
            shop_rect = self.get_blood_chemistry_shop_rect()
            if shop_rect is not None and shop_rect.collidepoint(position):
                self.selected_card_shop_test = "BLOOD CHEMISTRY"
                self.play_sfx("card_select")
                self.set_guided_tutorial_step("card_shop_buy")
                return
        if step == "card_shop_buy" and self.card_shop_buy_button.collidepoint(position):
            if self.purchase_selected_card_shop_test():
                self.card_shop_open = False
                self.set_guided_tutorial_step("blood_select")
                return
        if step == "blood_select":
            index = self.get_blood_chemistry_card_index()
            if index is not None and target_clicked:
                self.selected_card_index = index
                self.play_sfx("card_select")
                self.set_guided_tutorial_step("blood_run")
                return
        if step == "blood_run" and self.selected_card_index is not None:
            selected = self.get_selected_card_rect(self.selected_card_index)
            if self.get_run_test_button(selected).collidepoint(position):
                self.play_sfx("button")
                self.run_selected_test()
                self.set_guided_tutorial_step("second_test_result")
                return
        if step == "second_test_result":
            if self.get_test_result_reveal_progress() >= 1.0 and self.continue_button.collidepoint(position):
                self.handle_test_result_click(position)
                self.set_guided_tutorial_step("second_note_transfer")
                return
            self.nudge_guided_tutorial("Wait for the analyzer to finish.")
            return
        if step == "second_open_notebook" and self.layout["notebook"].collidepoint(position):
            self.open_notebook()
            self.set_guided_tutorial_step("second_review_notebook")
            return
        if step == "second_review_notebook":
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
            index = self.get_diagnosis_card_index_at(position)
            if (
                index is not None
                and self.player.diagnosis_hand[index].value == self.patient.diagnosis
            ):
                self.selected_card_index = index
                self.play_sfx("card_select")
                self.set_guided_tutorial_step("diagnosis_play")
                return
            if index is not None:
                self.nudge_guided_tutorial(
                    "That file needs evidence you have not collected. Follow the 300°F temperature drop."
                )
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
            self.finish_guided_tutorial(show_help_reminder=True)
            return

        if step not in ("patient_arrival", "note_transfer", "second_note_transfer"):
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
        elif step == "symptom":
            self.handle_guided_tutorial_click(self.layout["alien"].center)
        elif step in ("review_health_id", "review_notebook", "second_review_notebook", "complete"):
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
        elif (
            self.guided_tutorial_step == "second_note_transfer"
            and self.state == GameState.PATIENT
            and self.note_transfer_animation is None
            and self.notebook_attention_started_at is None
            and self.pending_test_discard is None
            and self.discard_animation is None
        ):
            self.set_guided_tutorial_step("second_open_notebook")

    def open_tutorial(self):
        """Open compact reference Help without restarting forced training."""

        if not self.tutorial_open:
            self.tutorial_opened_at = pygame.time.get_ticks()
        self.tutorial_open = True
        self.help_attention_seen = True
        self.help_attention_started_at = None

    def dismiss_help_attention(self):
        """Dismiss the one-time post-training reminder without blocking input."""

        if self.help_attention_started_at is not None:
            self.help_attention_started_at = None
            self.help_attention_seen = True

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
            GameState.ROUTE_BRIEFING: "RETURN TO ROUTE BRIEFING",
            GameState.ENDING: "CONTINUE ENDING",
            GameState.ARRIVAL: "RETURN TO ARRIVAL",
            GameState.FINAL: "RETURN TO SUMMARY",
        }.get(self.state, "CLOSE HELP")

    def get_help_context(self):
        """Return a concise label and instruction for the visible game screen."""

        if self.state == GameState.TITLE:
            return (
                "RECEPTION",
                "Call the next patient and watch the waiting-room queue move toward the examination bay.",
            )
        if self.state == GameState.PATIENT:
            if self.diagnosis_confirmation_open:
                return (
                    "DIAGNOSIS CONFIRMATION",
                    "Review the selected condition carefully. Submit it only when the collected clues support it.",
                )
            if self.showing_diagnosis_hand:
                return (
                    "DIAGNOSIS OPTIONS",
                    "Compare the case files with the patient interview, Health ID, and recorded test evidence.",
                )
            return (
                "EXAMINATION BAY",
                "Interview the patient, inspect both IDs, run useful tests, and record the results in Patient Notes.",
            )
        return {
            GameState.TEST_RESULT: (
                "TEST RESULT",
                "Review the scan, then continue so the result can be filed automatically in Patient Notes.",
            ),
            GameState.NOTEBOOK: (
                "PATIENT NOTES",
                "Compare symptoms, alien anatomy, and every recorded test result before choosing a diagnosis.",
            ),
            GameState.OUTCOME: (
                "CASE RESULT",
                "Review the outcome and its financial effect, then continue or return to testing when allowed.",
            ),
            GameState.DAY_COMPLETE: (
                "SHIFT RECAP",
                "Review patient revenue, test and card expenses, diagnosis penalties, overhead, and net pay.",
            ),
            GameState.SHOP: (
                "SUPPLY SHOP",
                "Buy upgrades that carry between planets, or save for Return Passage after the final shift.",
            ),
            GameState.ROUTE_BRIEFING: (
                "ROUTE BRIEFING",
                "The clinic visits a new destination after every shift. Earn credits while traveling toward passage home.",
            ),
            GameState.ENDING: (
                "DESTINATION TRAVEL" if self.route.arrival_pending else "FINAL DEPARTURE",
                (
                    "The clinic is traveling to its next destination. Click or press Enter to skip the journey."
                    if self.route.arrival_pending
                    else "Your ticket is paid. The UFO is taking you home." if not self.can_skip_ending() else "The configured route is complete. Click or press Enter to continue."
                ),
            ),
            GameState.ARRIVAL: (
                "PLANET ARRIVAL",
                "Review the next destination and patient roster, then begin the new clinic shift.",
            ),
            GameState.FINAL: (
                "ROUTE COMPLETE",
                "The configured route is complete. Restart it or quit while the next destination is prepared.",
            ),
        }.get(
            self.state,
            ("CLINIC", "Follow the evidence and protect the clinic's pay."),
        )

    def get_help_rules(self):
        """Return the permanent gameplay and economy reminders shown in Help."""

        return (
            (
                "TEST COSTS",
                (
                    f"Common ${TEST_COSTS_BY_RARITY['Common']}  •  "
                    f"Uncommon ${TEST_COSTS_BY_RARITY['Uncommon']}  •  "
                    f"Rare ${TEST_COSTS_BY_RARITY['Rare']} per use."
                ),
            ),
            (
                "CARD SHOP",
                (
                    f"Choose a test from the live deck. Starts at ${CARD_SHOP_BASE_PRICE}; "
                    f"+${CARD_SHOP_PRICE_STEP} after each purchase."
                ),
            ),
            (
                "CARD HAND",
                (
                    f"Random draws cost ${DRAW_COST}; max {MAX_TEST_HAND_SIZE}. "
                    "Used/discarded cards leave; unused cards return."
                ),
            ),
            (
                "CARRYOVER",
                (
                    "Money and permanent upgrades carry between planets. "
                    f"Save ${RETURN_PASSAGE_COST} for passage home."
                ),
            ),
            ("EVIDENCE", "Patient Notes tracks progress toward a hidden two-card clue path."),
            (
                "DIAGNOSIS PAY",
                (
                    f"Correct: ${LIMITED_EVIDENCE_REWARD} limited evidence / "
                    f"${DIAGNOSIS_REWARD} full evidence."
                ),
            ),
            (
                "MISTAKES",
                (
                    f"Wrong: -${WRONG_DIAGNOSIS_PENALTY} and discard that diagnosis. "
                    "Repeated errors may lose the patient."
                ),
            ),
            (
                "PLANET ROUTE",
                "Each shift visits a new destination with different aliens and conditions.",
            ),
        )

    def get_help_controls(self):
        """Return player-facing shortcuts; developer controls stay hidden."""

        return "H Help  •  M Sound  •  F11 Fullscreen  •  Esc Menu"

    def draw_help_button(self):
        """Draw the purple top-right Help control."""

        rect = self.help_button
        hovered = rect.collidepoint(self.get_mouse_position())
        now = pygame.time.get_ticks()
        pulse_active = self.help_attention_started_at is not None
        if pulse_active and now - self.help_attention_started_at >= self.help_attention_duration:
            self.dismiss_help_attention()
            pulse_active = False
        pulse = (math.sin(now / 180) + 1) / 2 if pulse_active else 0
        draw_rect = (
            rect.inflate(round(4 + pulse * 6), round(2 + pulse * 3))
            if pulse_active
            else rect.inflate(4, 2)
            if hovered
            else rect
        )
        border = (
            (232, 183, 251)
            if pulse_active
            else (206, 158, 233)
            if hovered
            else (155, 116, 190)
        )
        fill = (66, 43, 84) if pulse_active else (50, 37, 68) if hovered else (27, 29, 45)
        if pulse_active:
            halo = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
            halo_rect = draw_rect.inflate(round(12 + pulse * 8), round(8 + pulse * 6))
            pygame.draw.rect(
                halo,
                (206, 158, 233, round(45 + pulse * 60)),
                halo_rect,
                width=3,
                border_radius=12,
            )
            self.screen.blit(halo, (0, 0))
        pygame.draw.rect(self.screen, (3, 8, 13), draw_rect.move(2, 3), border_radius=8)
        pygame.draw.rect(self.screen, fill, draw_rect, border_radius=8)
        pygame.draw.rect(self.screen, border, draw_rect, width=2, border_radius=8)
        icon_center = (draw_rect.x + 18, draw_rect.centery)
        pygame.draw.circle(self.screen, border, icon_center, 8, width=1)
        icon = self.card_font.render("?", True, (232, 211, 242))
        self.screen.blit(icon, icon.get_rect(center=icon_center))
        label = self.card_font.render("HELP   H", True, (232, 211, 242))
        self.screen.blit(
            label,
            label.get_rect(midleft=(draw_rect.x + 32, draw_rect.centery)),
        )
        if pulse_active:
            self.draw_help_attention_tooltip(rect, pulse)

    def draw_help_attention_tooltip(self, help_rect, pulse):
        """Explain the pulsing Help button after training without blocking play."""

        tooltip = pygame.Rect(help_rect.right - 304, help_rect.bottom + 10, 304, 56)
        glow = pygame.Surface(tooltip.inflate(8, 8).size, pygame.SRCALPHA)
        pygame.draw.rect(
            glow,
            (206, 158, 233, round(30 + pulse * 35)),
            glow.get_rect(),
            border_radius=11,
        )
        self.screen.blit(glow, tooltip.inflate(8, 8).topleft)
        pygame.draw.polygon(
            self.screen,
            (50, 37, 68),
            (
                (help_rect.centerx - 7, tooltip.y),
                (help_rect.centerx + 7, tooltip.y),
                (help_rect.centerx, tooltip.y - 8),
            ),
        )
        pygame.draw.rect(self.screen, (50, 37, 68), tooltip, border_radius=9)
        pygame.draw.rect(
            self.screen,
            (216, 159, 238),
            tooltip,
            width=2,
            border_radius=9,
        )
        heading = self.tutorial_label_font.render(
            "NEED A REFRESHER?",
            True,
            (232, 211, 242),
        )
        detail = self.card_font.render(
            "Open Help anytime or press H.",
            True,
            COLORS["text"],
        )
        self.screen.blit(heading, (tooltip.x + 14, tooltip.y + 9))
        self.screen.blit(detail, (tooltip.x + 14, tooltip.y + 31))

    def draw_tutorial_overlay(self):
        """Draw compact reference Help, replacing the old full-screen briefing."""

        dim = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        dim.fill((2, 6, 12, 218))
        self.screen.blit(dim, (0, 0))
        panel = pygame.Rect(150, 28, 800, 584)
        pygame.draw.rect(self.screen, (3, 8, 13), panel.move(8, 9), border_radius=16)
        pygame.draw.rect(self.screen, (23, 29, 42), panel, border_radius=16)
        pygame.draw.rect(self.screen, (187, 137, 211), panel, width=3, border_radius=16)
        title = self.heading_font.render("CLINIC QUICK GUIDE", True, (232, 211, 242))
        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 33)))
        subtitle = self.card_font.render(
            "CONTEXT HELP  •  ECONOMY RULES  •  CONTROLS",
            True,
            COLORS["muted"],
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(panel.centerx, panel.y + 58)))

        context_name, context_detail = self.get_help_context()
        context = pygame.Rect(panel.x + 28, panel.y + 76, panel.width - 56, 82)
        pygame.draw.rect(self.screen, (25, 49, 55), context, border_radius=10)
        pygame.draw.rect(self.screen, COLORS["accent"], context, width=2, border_radius=10)
        current_label = self.tutorial_label_font.render(
            "CURRENT SCREEN",
            True,
            COLORS["accent"],
        )
        context_heading_y = context.y + 20
        self.screen.blit(
            current_label,
            current_label.get_rect(midleft=(context.x + 18, context_heading_y)),
        )
        context_title = self.small_font.render(context_name, True, COLORS["text"])
        self.screen.blit(
            context_title,
            context_title.get_rect(midleft=(context.x + 145, context_heading_y)),
        )
        context_text_box = pygame.Rect(
            context.x + 18,
            context.y + 38,
            context.width - 36,
            38,
        )
        self.draw_wrapped_text(
            context_detail,
            self.card_font,
            COLORS["text"],
            context_text_box,
            line_spacing=2,
        )

        rules_heading = self.tutorial_label_font.render(
            "CLINIC RULES",
            True,
            (216, 159, 238),
        )
        self.screen.blit(rules_heading, (panel.x + 29, panel.y + 174))
        rules = self.get_help_rules()
        for index, (heading, detail) in enumerate(rules):
            column = index % 2
            row_index = index // 2
            rule = pygame.Rect(
                panel.x + 28 + column * 382,
                panel.y + 194 + row_index * 68,
                370,
                62,
            )
            pygame.draw.rect(self.screen, (35, 42, 55), rule, border_radius=8)
            pygame.draw.rect(self.screen, (92, 72, 111), rule, width=1, border_radius=8)
            heading_label = self.tutorial_label_font.render(
                heading,
                True,
                (216, 159, 238),
            )
            self.screen.blit(heading_label, (rule.x + 14, rule.y + 8))
            detail_box = pygame.Rect(rule.x + 14, rule.y + 27, rule.width - 28, 31)
            self.draw_wrapped_text(
                detail,
                self.card_font,
                COLORS["text"],
                detail_box,
                line_spacing=1,
            )
        controls = pygame.Rect(panel.x + 28, panel.y + 472, panel.width - 56, 34)
        pygame.draw.rect(self.screen, (14, 22, 34), controls, border_radius=8)
        pygame.draw.rect(self.screen, (92, 72, 111), controls, width=1, border_radius=8)
        controls_label = self.tutorial_label_font.render(
            "CONTROLS",
            True,
            (216, 159, 238),
        )
        controls_text = self.card_font.render(
            self.get_help_controls(),
            True,
            COLORS["text"],
        )
        self.screen.blit(
            controls_label,
            controls_label.get_rect(midleft=(controls.x + 14, controls.centery)),
        )
        self.screen.blit(
            controls_text,
            controls_text.get_rect(midright=(controls.right - 14, controls.centery)),
        )
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
        # The used card already communicates its own discard with a visible
        # flight into med-waste. Do not cover that animation with another
        # tutorial message; the timed update advances training when it ends.
        if step in ("note_transfer", "second_note_transfer"):
            return
        target = self.get_guided_tutorial_target()
        reading_report = step in ("test_result", "second_test_result")
        pulse = (math.sin(pygame.time.get_ticks() / 210) + 1) / 2
        if step != "patient_arrival" and not reading_report:
            dim = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
            # Reception remains visible during the first lesson so the player
            # understands where the highlighted call control lives.
            dim_alpha = 108 if step == "call_patient" else 158
            dim.fill((2, 6, 12, dim_alpha))
            if target is not None:
                clear_padding = 28 if step == "call_patient" else 18
                pygame.draw.rect(
                    dim,
                    (0, 0, 0, 0),
                    target.inflate(clear_padding, clear_padding),
                    border_radius=14,
                )
            self.screen.blit(dim, (0, 0))
        if target is not None:
            if step == "call_patient":
                halo = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
                for padding, halo_alpha, width in (
                    (38 + round(8 * pulse), 28, 8),
                    (25 + round(6 * pulse), 62, 5),
                    (14 + round(4 * pulse), 150, 3),
                ):
                    pygame.draw.rect(
                        halo,
                        (106, 246, 198, halo_alpha),
                        target.inflate(padding, padding),
                        width=width,
                        border_radius=16,
                    )
                self.screen.blit(halo, (0, 0))
            glow = target.inflate(round(15 + 7 * pulse), round(15 + 7 * pulse))
            glow_width = 3 + round(2 * pulse) if step == "call_patient" else 2 + round(pulse)
            pygame.draw.rect(
                self.screen,
                (106, 246, 198),
                glow,
                width=glow_width,
                border_radius=12,
            )
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

        if reading_report:
            self.draw_guided_report_hint()
            return

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
        step_label = self.tutorial_label_font.render(
            f"TRAINING ORBIT CASE  •  STEP {self.get_guided_tutorial_step_number()} OF 9",
            True,
            accent,
        )
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

    def draw_guided_report_hint(self):
        """Show non-blocking guidance while leaving the diagnostic report bright."""

        revealed = self.get_test_result_reveal_progress() >= 1.0
        message = (
            "READ THE REPORT  •  RETURN TO PATIENT WHEN READY"
            if revealed
            else "LET THE SCAN FINISH  •  THEN READ THE REPORT"
        )
        hint = pygame.Rect(330, 592, 440, 28)
        pygame.draw.rect(self.screen, (3, 8, 13), hint.move(3, 4), border_radius=8)
        pygame.draw.rect(self.screen, (13, 31, 38), hint, border_radius=8)
        pygame.draw.rect(self.screen, COLORS["accent"], hint, width=1, border_radius=8)
        label = self.tutorial_label_font.render(message, True, COLORS["accent"])
        self.screen.blit(label, label.get_rect(center=hint.center))
