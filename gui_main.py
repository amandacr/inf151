"""Pygame interface for The Cosmic Clinic.

Run the game through main.py or launch this module directly.
"""

import random

import pygame

from Tests.catalog import create_test_catalog
from gui_patient_assets import PatientAssetMixin
from gui_animations import AnimationMixin
from gui_audio import AudioMixin
from gui_card_shop import CardShopMixin
from gui_cards import CardMixin
from gui_developer import DeveloperMixin
from gui_display import DisplayMixin
from gui_ending import EndingMixin
from gui_examination import ExaminationMixin
from gui_intro import IntroMixin
from gui_notebook import NotebookMixin
from gui_reception import ReceptionMixin
from gui_results import ResultsMixin
from gui_shop import ShopMixin
from gui_state import GameState
from gui_tutorial import TutorialMixin
from gui_theme import (
    COLORS,
    FPS,
    WINDOW_SIZE,
)
from PlanetData import DESTINATIONS
from Player import Player, STARTING_TEST_HAND_SIZE
from RouteController import RouteController
from Notebook import Notebook
from Deck import Deck


class CosmicClinicGUI(
    PatientAssetMixin,
    AnimationMixin,
    AudioMixin,
    CardShopMixin,
    CardMixin,
    DeveloperMixin,
    DisplayMixin,
    EndingMixin,
    ExaminationMixin,
    IntroMixin,
    NotebookMixin,
    ReceptionMixin,
    ResultsMixin,
    ShopMixin,
    TutorialMixin,
):

    @property
    def day_number(self):
        """Expose the route day to existing screen code without duplicating state."""

        return self.route.current_day

    @property
    def current_destination(self):
        """Expose the active route destination to screens and tests."""

        return self.route.current_destination

    @property
    def destinations(self):
        """Expose the configured route without letting the GUI own it."""

        return self.route.destinations

    def get_location_subtitle(self):
        """Return the persistent day and destination label used by clinic screens."""

        return (
            f"DAY {self.day_number}  •  "
            f"{self.current_destination.planet_name.upper()}"
        )

    def __init__(self, card_seed=None):
        """Set up Pygame, shared game data, layout rectangles, and fonts."""

        pygame.init()
        pygame.display.set_caption("The Cosmic Clinic")

        self.setup_audio()
        self.start_music()
        self.setup_display()
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.INTRO
        self.intro_started_at = pygame.time.get_ticks()
        self.intro_duration = 13200
        intro_random = random.Random(151)
        self.intro_stars = [
            (
                intro_random.randrange(15, WINDOW_SIZE[0] - 15),
                intro_random.randrange(12, WINDOW_SIZE[1] - 12),
                intro_random.choice((1, 1, 1, 2)),
            )
            for _ in range(70)
        ]

        self.patient_sprite_cache = {}
        self.route = RouteController(DESTINATIONS)
        self.waiting_room_queue = self.roster_for_destination(
            self.route.current_destination
        )
        self.patients_called = 0
        self.daily_correct_diagnoses = 0
        self.daily_wrong_diagnoses = 0
        self.daily_test_count = 0
        self.daily_test_expenses = 0
        self.daily_evidence_cases = 0
        self.daily_payout_applied = False
        self.money_deduction_animation = None
        self.money_count_duration = 650
        self.money_popup_duration = 1350
        self.patient = self.waiting_room_queue[0]["create"]()
        self.patient_dialogue_index = 0
        self.player = Player("Dr GUI")
        if self.patient.diagnosis_options:
            self.player.set_diagnosis_hand(self.patient.diagnosis_options)
        self.notebook = Notebook()
        self.notebook.add_patient(self.patient)
        self.notebook_columns = []
        self.notebook_spread = 0
        self.notebook_preview_progress = 0.0
        self.notebook_preview_last_tick = pygame.time.get_ticks()
        self.notebook_preview_duration = 220
        self.deck = Deck(seed=card_seed)
        self.deck.populate(create_test_catalog())
        self.card_shop_catalog = tuple(create_test_catalog())
        self.deck.shuffle_cards(self.player.diagnosis_hand)
        self.deal_starting_test_hand(training_hand=True)
        self.hovered_card_index = None
        self.showing_health_id = False
        self.showing_diagnosis_hand = False
        self.recycler_used = False
        self.selected_card_index = None
        self.run_test_button = None
        self.discard_button = None
        self.play_diagnosis_button = None
        self.diagnosis_confirmation_open = False
        self.diagnosis_folder_animation_started_at = None
        self.diagnosis_folder_animation_duration = 360
        self.discard_pile = []
        self.discard_animation = None
        self.discard_animation_duration = 350
        self.test_discard_animation_duration = 700
        self.pending_test_discard = None
        self.pending_diagnosis_discard = None
        self.note_transfer_animation = None
        self.note_transfer_animation_duration = 650
        self.notebook_attention_started_at = None
        self.notebook_attention_duration = 420
        self.last_test_name = ""
        self.last_test_result = ""
        self.last_test_cost = 0
        self.test_result_started_at = None
        self.test_result_reveal_duration = 1400
        self.last_diagnosis = None
        self.diagnosis_correct = None
        self.last_diagnosis_supported = False
        self.patient_left = False
        self.patient_leave_text = ""
        self.patient_wrong_diagnoses = 0
        self.advance_case_after_discard = False
        self.card_draw_notice = ""
        self.card_draw_notice_started_at = None
        self.card_shop_open = False
        self.card_shop_button = pygame.Rect(53, 323, 134, 27)
        self.card_shop_panel = pygame.Rect(215, 370, 660, 205)
        self.card_shop_close_button = pygame.Rect(839, 382, 24, 24)
        self.card_shop_buy_button = pygame.Rect(614, 532, 239, 31)
        self.selected_card_shop_test = None
        self.card_shop_message = "Choose one card type from the live deck."
        self.card_shop_notice = ""
        self.card_shop_notice_started_at = None
        self.card_shop_patient_purchases = 0
        self.daily_card_shop_expenses = 0
        self.daily_card_shop_purchases = 0
        self.daily_patients_lost = 0
        self.daily_draw_expenses = 0
        self.reception_transition_started_at = None
        self.reception_transition_duration = 3350
        self.reception_fade_duration = 650
        self.end_day_shutdown_started_at = None
        self.end_day_shutdown_duration = 1750
        self.queue_shift_started_at = None
        self.queue_shift_duration = 900
        self.patient_fade_started_at = None
        self.patient_fade_duration = 650
        self.start_button = pygame.Rect(61, 505, 238, 43)
        self.continue_button = pygame.Rect(700, 472, 220, 44)
        self.outcome_button = pygame.Rect(410, 455, 280, 52)
        self.shop_purchase_button = pygame.Rect(250, 538, 290, 34)
        self.shop_button = pygame.Rect(560, 538, 290, 34)
        self.day_complete_button = pygame.Rect(370, 541, 360, 42)
        self.selected_shop_upgrade = None
        self.purchased_shop_upgrades = set()
        self.shop_scroll_row = 0
        self.shop_message = "Select an upgrade to inspect it."
        self.route_briefing_seen = False
        self.route_briefing_index = 0
        self.ending_started_at = None
        self.ending_duration = 4200
        self.arrival_started_at = None
        self.arrival_animation_duration = 2400
        self.arrival_begin_button = pygame.Rect(370, 570, 360, 48)
        self.exit_confirmation_open = False
        self.exit_confirmation_opened_at = None
        self.exit_continue_button = pygame.Rect(365, 300, 370, 46)
        self.exit_reception_button = pygame.Rect(365, 360, 370, 46)
        self.exit_quit_button = pygame.Rect(365, 420, 370, 46)
        self.final_replay_button = pygame.Rect(300, 500, 235, 48)
        self.final_quit_button = pygame.Rect(565, 500, 235, 48)
        self.tutorial_open = False
        self.tutorial_opened_at = None
        self.help_attention_started_at = None
        self.help_attention_seen = False
        self.help_attention_duration = 5000
        self.guided_tutorial_active = False
        self.guided_tutorial_step = None
        self.guided_tutorial_step_started_at = None
        self.guided_tutorial_nudge = ""
        self.guided_tutorial_nudge_started_at = None
        self.tutorial_skip_button = pygame.Rect(933, 58, 135, 28)
        self.intro_dialogue_active = False
        self.intro_dialogue_index = 0
        self.intro_dialogue_started_at = None
        self.help_button = pygame.Rect(972, 16, 112, 31)
        self.tutorial_begin_button = pygame.Rect(400, 510, 300, 48)
        self.diagnosis_cancel_button = pygame.Rect(315, 410, 210, 48)
        self.diagnosis_confirm_button = pygame.Rect(575, 410, 210, 48)
        self.layout = {
            "status_bar": pygame.Rect(30, 100, 1040, 50),
            "draw_deck": pygame.Rect(45, 180, 150, 175),
            "alien": pygame.Rect(233, 165, 230, 195),
            # Keep the ID fully inside the panoramic examination window.
            # Its previous 200px height crossed the lower window frame.
            "id_card": pygame.Rect(493, 170, 304, 188),
            "throwaway": pygame.Rect(923, 423, 100, 125),
            "notebook": pygame.Rect(35, 395, 180, 165),
            "active_hand": pygame.Rect(225, 390, 625, 170),
            "diagnosis": pygame.Rect(840, 175, 185, 180),
        }
        self.refresh_hand_layout()
        self.notebook_layout = self.build_notebook_rects()

        self.title_font = pygame.font.Font(None, 64)
        self.heading_font = pygame.font.Font(None, 38)
        self.body_font = pygame.font.Font(None, 26)
        self.small_font = pygame.font.Font(None, 20)
        self.card_font = pygame.font.Font(None, 17)
        self.pile_font = pygame.font.Font(None, 14)
        self.tiny_font = pygame.font.Font(None, 10)
        self.compact_ui_font = pygame.font.SysFont("Arial", 12, bold=True)
        self.compact_card_title_font = pygame.font.SysFont("Arial", 11, bold=True)
        self.legible_micro_font = pygame.font.SysFont("Arial", 9, bold=True)
        self.id_detail_font = pygame.font.SysFont("Arial", 12, bold=True)
        self.notebook_preview_font = pygame.font.Font(None, 15)
        self.diagnosis_name_font = pygame.font.SysFont("Arial", 21, bold=True)
        self.diagnosis_card_font = pygame.font.SysFont("Arial", 13, bold=True)
        self.notebook_title_font = pygame.font.Font(None, 28)
        self.notebook_body_font = pygame.font.Font(None, 22)
        self.logo_font = pygame.font.SysFont("Arial", 54, bold=True)
        self.logo_small_font = pygame.font.SysFont("Arial", 18, bold=True)
        self.tutorial_title_font = pygame.font.SysFont("Arial", 32, bold=True)
        self.tutorial_subtitle_font = pygame.font.SysFont("Arial", 16, bold=True)
        self.tutorial_step_font = pygame.font.SysFont("Arial", 17, bold=True)
        self.tutorial_body_font = pygame.font.SysFont("Arial", 15)
        self.tutorial_label_font = pygame.font.SysFont("Arial", 13, bold=True)
        self.dialogue_speaker_font = pygame.font.SysFont("Arial", 16, bold=True)
        self.dialogue_body_font = pygame.font.SysFont("Arial", 23)
        self.game_logo = self.create_game_logo_surface()
        intro_ufo_layer = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        self.draw_intro_clinic(intro_ufo_layer, beam_alpha=0)
        # Keep only the visible saucer pixels. Transforming the old full-screen
        # layer created a large rectangular artifact around the departing ship
        # on some displays. A transparent gutter prevents smooth scaling and
        # rotation from smearing the dome's top edge into a stray white line.
        intro_ufo_bounds = intro_ufo_layer.get_bounding_rect(min_alpha=1)
        cropped_ufo = intro_ufo_layer.subsurface(intro_ufo_bounds).copy()
        ufo_padding = 8
        self.intro_ufo_surface = pygame.Surface(
            (
                cropped_ufo.get_width() + ufo_padding * 2,
                cropped_ufo.get_height() + ufo_padding * 2,
            ),
            pygame.SRCALPHA,
        )
        self.intro_ufo_surface.blit(cropped_ufo, (ufo_padding, ufo_padding))
        self.intro_wake_active = False
        self.setup_developer_navigator()

    def run(self):
        """Run the GUI loop until the player closes the window."""

        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.present_frame()
            self.clock.tick(FPS)

        pygame.quit()

    def handle_events(self):
        """Process window events and controls."""

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.resize_display(event.size)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                position = self.window_to_game_position(event.pos)
                if (
                    self.help_attention_started_at is not None
                    and not self.guided_tutorial_active
                ):
                    self.dismiss_help_attention()
                if self.developer_navigator_open:
                    self.handle_developer_click(position)
                elif self.exit_confirmation_open:
                    self.handle_exit_confirmation_click(position)
                elif self.intro_dialogue_active:
                    self.play_sfx("button")
                    self.advance_intro_dialogue()
                elif self.guided_tutorial_active:
                    self.handle_guided_tutorial_click(position)
                elif self.state != GameState.INTRO and self.tutorial_open:
                    self.handle_tutorial_click(position)
                elif self.state != GameState.INTRO and self.audio_button.collidepoint(position):
                    self.toggle_audio_muted()
                elif self.state != GameState.INTRO and self.help_button.collidepoint(position):
                    self.play_sfx("button")
                    self.open_tutorial()
                elif self.state == GameState.INTRO:
                    self.play_sfx("button")
                    self.finish_intro()
                elif self.state == GameState.TITLE and self.start_button.collidepoint(position):
                    self.play_sfx("button")
                    self.begin_reception_transition()
                elif self.state == GameState.PATIENT:
                    self.handle_patient_click(position)
                elif self.state == GameState.TEST_RESULT:
                    self.handle_test_result_click(position)
                elif self.state == GameState.NOTEBOOK:
                    self.handle_notebook_click(position)
                elif self.state == GameState.OUTCOME:
                    self.handle_outcome_click(position)
                elif self.state == GameState.SHOP:
                    self.handle_shop_click(position)
                elif self.state == GameState.DAY_COMPLETE:
                    self.handle_day_complete_click(position)
                elif self.state == GameState.ROUTE_BRIEFING:
                    self.play_sfx("button")
                    self.advance_route_briefing()
                elif self.state == GameState.ENDING and self.can_skip_ending():
                    self.play_sfx("button")
                    self.finish_ending_sequence()
                elif self.state == GameState.ARRIVAL:
                    self.handle_arrival_click(position)
                elif self.state == GameState.FINAL:
                    self.handle_final_screen_click(position)
            elif event.type == pygame.MOUSEWHEEL:
                if (
                    self.state == GameState.SHOP
                    and not self.developer_navigator_open
                    and not self.exit_confirmation_open
                    and not self.tutorial_open
                ):
                    self.scroll_shop(-event.y)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                    continue
                if event.key == pygame.K_F10:
                    self.toggle_developer_navigator()
                    continue
                if self.developer_navigator_open:
                    if event.key == pygame.K_ESCAPE:
                        if self.developer_navigator_level == "screens":
                            self.return_to_developer_destinations()
                        else:
                            self.toggle_developer_navigator()
                    else:
                        self.handle_developer_key(event.key)
                    continue
                if event.key == pygame.K_m:
                    self.toggle_audio_muted()
                    continue
                if self.exit_confirmation_open:
                    if event.key == pygame.K_ESCAPE:
                        self.close_exit_confirmation()
                    continue
                if self.intro_dialogue_active:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.play_sfx("button")
                        self.advance_intro_dialogue()
                    elif event.key == pygame.K_ESCAPE:
                        self.finish_intro_dialogue()
                    continue
                if self.guided_tutorial_active:
                    self.handle_guided_tutorial_key(event.key)
                    continue
                if event.key == pygame.K_h and self.state != GameState.INTRO:
                    if self.tutorial_open:
                        self.close_tutorial()
                    else:
                        self.play_sfx("button")
                        self.open_tutorial()
                    continue
                if self.state != GameState.INTRO and self.tutorial_open:
                    if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                        self.close_tutorial()
                    continue
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.PATIENT and self.card_shop_open:
                        self.toggle_card_shop()
                    elif self.state == GameState.PATIENT and self.diagnosis_confirmation_open:
                        self.play_sfx("button")
                        self.diagnosis_confirmation_open = False
                    else:
                        self.open_exit_confirmation()
                elif (
                    event.key == pygame.K_RETURN
                    and self.state == GameState.PATIENT
                    and self.diagnosis_confirmation_open
                ):
                    self.confirm_selected_diagnosis()
                elif event.key == pygame.K_RETURN and self.state == GameState.INTRO:
                    self.play_sfx("button")
                    self.finish_intro()
                elif event.key == pygame.K_RETURN and self.state == GameState.TITLE:
                    self.play_sfx("button")
                    self.begin_reception_transition()
                elif event.key == pygame.K_RETURN and self.state == GameState.TEST_RESULT:
                    self.handle_test_result_click(self.continue_button.center)
                elif event.key == pygame.K_RETURN and self.state == GameState.OUTCOME:
                    self.handle_outcome_click(self.outcome_button.center)
                elif event.key == pygame.K_RETURN and self.state == GameState.SHOP:
                    self.handle_shop_click(self.shop_button.center)
                elif event.key == pygame.K_RETURN and self.state == GameState.DAY_COMPLETE:
                    self.handle_day_complete_click(self.day_complete_button.center)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE) and self.state == GameState.ROUTE_BRIEFING:
                    self.play_sfx("button")
                    self.advance_route_briefing()
                elif (event.key == pygame.K_RETURN and self.state == GameState.ENDING
                      and self.can_skip_ending()):
                    self.play_sfx("button")
                    self.finish_ending_sequence()
                elif event.key == pygame.K_RETURN and self.state == GameState.ARRIVAL:
                    self.handle_arrival_click(self.arrival_begin_button.center)
                elif event.key == pygame.K_LEFT and self.state == GameState.NOTEBOOK:
                    self.flip_notebook(-1)
                elif event.key == pygame.K_RIGHT and self.state == GameState.NOTEBOOK:
                    self.flip_notebook(1)

    def handle_patient_click(self, position):
        """Handle ID-card and test-card clicks on the patient screen."""

        note_sequence_active = (
            self.note_transfer_animation is not None
            or (
                self.notebook_attention_started_at is not None
                and self.pending_test_discard is not None
            )
        )
        if (
            note_sequence_active
            or (
                self.discard_animation
                and self.discard_animation.get("locks_input")
            )
        ):
            return
        if self.card_shop_open:
            self.handle_card_shop_click(position)
            return
        if self.diagnosis_confirmation_open:
            self.handle_diagnosis_confirmation_click(position)
            return
        if self.layout["id_card"].collidepoint(position):
            self.play_sfx("button")
            self.showing_health_id = not self.showing_health_id
            return
        if self.layout["alien"].collidepoint(position):
            self.advance_patient_dialogue()
            return
        if self.layout["notebook"].collidepoint(position):
            self.open_notebook()
            return
        if self.layout["diagnosis"].collidepoint(position):
            self.play_sfx("button")
            self.switch_active_hand(not self.showing_diagnosis_hand)
            return
        if self.card_shop_button.collidepoint(position):
            self.toggle_card_shop()
            return
        if self.layout["draw_deck"].collidepoint(position):
            card_drawn = self.draw_card_from_pile()
            self.play_sfx("card_select" if card_drawn else "button")
            return

        self.handle_card_click(position)

    def handle_test_result_click(self, position):
        """Return to the workspace and begin logging the result in patient notes."""

        if (
            self.get_test_result_reveal_progress() >= 1.0
            and self.continue_button.collidepoint(position)
        ):
            self.play_sfx("button")
            self.state = GameState.PATIENT
            if self.pending_test_discard is not None:
                self.note_transfer_animation = {
                    "test_name": self.last_test_name,
                    "result": self.last_test_result,
                    "started_at": pygame.time.get_ticks(),
                }

    def handle_outcome_click(self, position):
        """Continue to the next case, the daily recap, or the current patient."""

        if self.outcome_button.collidepoint(position):
            self.play_sfx("button")
            if self.diagnosis_correct:
                self.advance_completed_case()
            elif self.patient_left:
                self.switch_active_hand(False)
                self.state = GameState.PATIENT
                self.advance_case_after_discard = True
                self.start_pending_diagnosis_discard_animation()
                if self.discard_animation is None:
                    self.advance_case_after_discard = False
                    self.advance_completed_case()
            else:
                self.switch_active_hand(False)
                self.state = GameState.PATIENT
                self.start_pending_diagnosis_discard_animation()

    def advance_completed_case(self):
        """Move from a resolved or abandoned case to the next queue state."""

        if self.patients_waiting() == 0:
            self.state = GameState.TITLE
            self.begin_end_day_shutdown()
        else:
            self.reset_round()
            self.begin_queue_shift()
            self.state = GameState.TITLE

    def update(self):
        """Advance timed GUI transitions without pausing the event loop."""

        if self.exit_confirmation_open:
            return

        if self.intro_dialogue_active:
            return

        if self.state != GameState.INTRO and self.tutorial_open:
            return

        if self.state == GameState.ENDING:
            self.update_ending_sequence()
            return

        if self.state == GameState.ARRIVAL:
            return

        if self.state == GameState.FINAL:
            return

        if self.state == GameState.INTRO:
            elapsed = pygame.time.get_ticks() - self.intro_started_at
            if elapsed >= self.intro_duration:
                self.finish_intro()
            return

        self.update_guided_tutorial()

        now = pygame.time.get_ticks()
        if self.note_transfer_animation is not None:
            elapsed = now - self.note_transfer_animation["started_at"]
            if elapsed >= self.note_transfer_animation_duration:
                self.note_transfer_animation = None
                self.notebook_attention_started_at = now

        if (
            self.notebook_attention_started_at is not None
            and self.pending_test_discard is not None
        ):
            attention_elapsed = now - self.notebook_attention_started_at
            if attention_elapsed >= self.notebook_attention_duration:
                self.notebook_attention_started_at = None
                self.start_pending_test_discard_animation()

        if self.discard_animation is not None:
            elapsed = now - self.discard_animation["started_at"]
            duration = self.discard_animation.get(
                "duration",
                self.discard_animation_duration,
            )
            if elapsed >= duration:
                if self.discard_animation.get("add_to_pile_on_complete"):
                    self.discard_pile.append(self.discard_animation["card"])
                self.play_sfx("waste")
                self.discard_animation = None
                if self.advance_case_after_discard:
                    self.advance_case_after_discard = False
                    self.advance_completed_case()

        if self.state == GameState.TITLE and self.end_day_shutdown_started_at is not None:
            elapsed = now - self.end_day_shutdown_started_at
            if elapsed >= self.end_day_shutdown_duration:
                self.end_day()
            return

        if self.state == GameState.TITLE and self.queue_shift_started_at is not None:
            elapsed = pygame.time.get_ticks() - self.queue_shift_started_at
            if elapsed >= self.queue_shift_duration:
                self.queue_shift_started_at = None
            return

        if self.state == GameState.TITLE and self.reception_transition_started_at is not None:
            elapsed = pygame.time.get_ticks() - self.reception_transition_started_at
            if elapsed >= self.reception_transition_duration:
                self.reception_transition_started_at = None
                self.patients_called += 1
                self.patient_fade_started_at = pygame.time.get_ticks()
                self.state = GameState.PATIENT
            return

        if self.state == GameState.PATIENT and self.patient_fade_started_at is not None:
            elapsed = pygame.time.get_ticks() - self.patient_fade_started_at
            if elapsed >= self.patient_fade_duration:
                self.patient_fade_started_at = None

    def handle_shop_click(self, position):
        """Handle upgrade purchases or finish the current shift."""

        if self.handle_shop_scroll_click(position):
            return
        if self.shop_button.collidepoint(position):
            self.play_sfx("button")
            if self.should_show_route_briefing():
                self.start_route_briefing()
            else:
                self.begin_ending_sequence()
            return
        self.handle_shop_upgrade_click(position)

    def end_day(self):
        """Show the completed-day summary after every queued patient is treated."""

        self.reception_transition_started_at = None
        self.queue_shift_started_at = None
        self.patient_fade_started_at = None
        self.end_day_shutdown_started_at = None
        self.state = GameState.DAY_COMPLETE

    def handle_day_complete_click(self, position):
        """Deposit the completed shift's pay and open the end-of-day Shop."""

        if self.day_complete_button.collidepoint(position):
            self.play_sfx("button")
            self.settle_daily_pay()
            self.state = GameState.SHOP

    def reset_day(self):
        """Refill the patient queue and draw deck while preserving earned money."""

        self.player.free_tests_used.clear()
        self.patients_called = 0
        self.queue_shift_started_at = None
        self.end_day_shutdown_started_at = None
        self.daily_correct_diagnoses = 0
        self.daily_wrong_diagnoses = 0
        self.daily_test_count = 0
        self.daily_test_expenses = 0
        self.daily_card_shop_expenses = 0
        self.daily_card_shop_purchases = 0
        self.daily_evidence_cases = 0
        self.daily_payout_applied = False
        self.money_deduction_animation = None
        self.selected_shop_upgrade = None
        self.shop_scroll_row = 0
        self.shop_message = "Select an upgrade to inspect it."
        self.deck.populate(create_test_catalog())
        self.daily_patients_lost = 0
        self.daily_draw_expenses = 0
        self.reset_round(recycle_unused_cards=False)

    def deal_starting_test_hand(self, training_hand=False):
        """Deal five cards from the live deck without replacement.

        Zorpa's one-time guided lesson requires a Temperature card. Its
        position and the other four cards are still randomized; later hands
        are completely unconstrained.
        """

        self.player.test_hand = []
        if training_hand:
            training_card = self.deck.draw_matching("TEMPERATURE")
            if training_card is not None:
                self.player.draw(training_card)

        while len(self.player.test_hand) < STARTING_TEST_HAND_SIZE:
            card = self.deck.draw()
            if card is None:
                break
            self.player.draw(card)

        self.deck.shuffle_cards(self.player.test_hand)

    def reset_round(self, recycle_unused_cards=True):
        """Prepare a fresh patient encounter while preserving money and unused cards."""

        current_balance = self.player.balance
        if recycle_unused_cards:
            self.deck.return_cards(self.player.test_hand)
        next_slot = min(self.patients_called, len(self.waiting_room_queue) - 1)
        self.patient = self.waiting_room_queue[next_slot]["create"]()
        self.patient_dialogue_index = 0
        machine_levels = self.player.machine_levels.copy()
        test_discount = self.player.test_discount
        free_test_machines = self.player.free_test_machines.copy()
        free_tests_used = self.player.free_tests_used.copy()
        self.player = Player(self.player.name)
        self.player.balance = current_balance
        self.player.machine_levels = machine_levels
        self.player.test_discount = test_discount
        self.player.free_test_machines = free_test_machines
        self.player.free_tests_used = free_tests_used
        if self.patient.diagnosis_options:
            self.player.set_diagnosis_hand(self.patient.diagnosis_options)
        self.deck.shuffle_cards(self.player.diagnosis_hand)
        self.deal_starting_test_hand()
        self.notebook = Notebook()
        self.notebook.add_patient(self.patient)
        self.notebook_columns = []
        self.notebook_spread = 0
        self.notebook_preview_progress = 0.0
        self.notebook_preview_last_tick = pygame.time.get_ticks()
        self.showing_health_id = False
        self.showing_diagnosis_hand = False
        self.recycler_used = False
        self.selected_card_index = None
        self.run_test_button = None
        self.discard_button = None
        self.play_diagnosis_button = None
        self.diagnosis_confirmation_open = False
        self.diagnosis_folder_animation_started_at = None
        self.discard_pile = []
        self.discard_animation = None
        self.pending_test_discard = None
        self.pending_diagnosis_discard = None
        self.note_transfer_animation = None
        self.notebook_attention_started_at = None
        self.last_test_name = ""
        self.last_test_result = ""
        self.last_test_cost = 0
        self.test_result_started_at = None
        self.last_diagnosis = None
        self.diagnosis_correct = None
        self.last_diagnosis_supported = False
        self.patient_left = False
        self.patient_leave_text = ""
        self.patient_wrong_diagnoses = 0
        self.advance_case_after_discard = False
        self.card_draw_notice = ""
        self.card_draw_notice_started_at = None
        self.card_shop_open = False
        self.selected_card_shop_test = None
        self.card_shop_message = "Choose one card type from the live deck."
        self.card_shop_notice = ""
        self.card_shop_notice_started_at = None
        self.card_shop_patient_purchases = 0
        self.reception_transition_started_at = None
        self.patient_fade_started_at = None
        self.refresh_hand_layout()

    def draw(self):
        """Draws shell + active screen."""

        if self.state == GameState.INTRO:
            self.draw_intro_screen()
            if self.exit_confirmation_open:
                self.draw_exit_confirmation()
            if self.developer_navigator_open:
                self.draw_developer_navigator()
            return

        if self.state == GameState.ENDING:
            self.draw_ending_screen()
            self.draw_help_button()
            self.draw_audio_button()
            if self.tutorial_open:
                self.draw_tutorial_overlay()
            if self.exit_confirmation_open:
                self.draw_exit_confirmation()
            if self.developer_navigator_open:
                self.draw_developer_navigator()
            return

        if self.state == GameState.ROUTE_BRIEFING:
            self.draw_route_briefing_screen()
            self.draw_help_button()
            self.draw_audio_button()
            if self.tutorial_open:
                self.draw_tutorial_overlay()
            if self.exit_confirmation_open:
                self.draw_exit_confirmation()
            if self.developer_navigator_open:
                self.draw_developer_navigator()
            return

        if self.state == GameState.ARRIVAL:
            self.draw_planet_arrival_screen()
            self.draw_help_button()
            self.draw_audio_button()
            if self.tutorial_open:
                self.draw_tutorial_overlay()
            if self.exit_confirmation_open:
                self.draw_exit_confirmation()
            if self.developer_navigator_open:
                self.draw_developer_navigator()
            return

        if self.state == GameState.FINAL:
            self.draw_final_screen()
            self.draw_help_button()
            self.draw_audio_button()
            if self.tutorial_open:
                self.draw_tutorial_overlay()
            if self.exit_confirmation_open:
                self.draw_exit_confirmation()
            if self.developer_navigator_open:
                self.draw_developer_navigator()
            return

        self.screen.fill(COLORS["background"])
        self.draw_game_logo((WINDOW_SIZE[0] // 2, 38), scale=0.86)

        subtitle_text = self.get_location_subtitle()
        subtitle = self.small_font.render(subtitle_text, True, COLORS["muted"])
        self.screen.blit(subtitle, subtitle.get_rect(center=(WINDOW_SIZE[0] // 2, 76)))

        if self.state == GameState.TITLE:
            self.draw_title_screen()
        elif self.state == GameState.PATIENT:
            self.draw_patient_screen()
        elif self.state == GameState.TEST_RESULT:
            self.draw_test_result_screen()
        elif self.state == GameState.NOTEBOOK:
            self.draw_patient_screen()
            self.draw_notebook_screen()
        elif self.state == GameState.OUTCOME:
            self.draw_diagnosis_outcome()
        elif self.state == GameState.SHOP:
            self.draw_shop_screen()
        elif self.state == GameState.DAY_COMPLETE:
            self.draw_day_complete_screen()

        footer_text = (
            "Press Esc to go back"
            if self.diagnosis_confirmation_open
            else "Press Esc for exit options"
        )
        footer_text += f"  •  {self.get_fullscreen_hint()}"
        quit_hint = self.small_font.render(footer_text, True, COLORS["muted"])
        self.screen.blit(quit_hint, quit_hint.get_rect(center=(WINDOW_SIZE[0] // 2, 635)))
        self.draw_reception_transition_fade()
        if (
            self.state != GameState.INTRO
            and not self.intro_dialogue_active
            and not self.guided_tutorial_active
        ):
            self.draw_help_button()
        if not self.intro_dialogue_active and not self.guided_tutorial_active:
            self.draw_audio_button()
        if self.intro_dialogue_active:
            self.draw_intro_dialogue()
        elif self.state != GameState.INTRO and self.tutorial_open:
            self.draw_tutorial_overlay()
        if self.guided_tutorial_active:
            self.draw_guided_tutorial()
        if self.exit_confirmation_open:
            self.draw_exit_confirmation()
        if self.developer_navigator_open:
            self.draw_developer_navigator()

    def draw_centered_label(self, text, panel, y):
        """Draw a text label centered horizontally inside a panel."""

        label = self.small_font.render(text, True, COLORS["text"])
        self.screen.blit(label, label.get_rect(center=(panel.centerx, y)))

    def draw_panel(self, panel):
        """Draw a reusable dark panel with a rounded green border."""

        pygame.draw.rect(self.screen, COLORS["panel"], panel, border_radius=12)
        pygame.draw.rect(
            self.screen,
            COLORS["panel_border"],
            panel,
            width=2,
            border_radius=12,
        )

    def draw_wrapped_text(self, text, font, color, rect, line_spacing=2):
        """Wrap and draw text so it stays within the rectangle."""

        words = text.split()
        lines = []
        line = []

        for word in words:
            candidate = " ".join(line + [word])
            if font.size(candidate)[0] <= rect.width:
                line.append(word)
            else:
                lines.append(" ".join(line))
                line = [word]

        if line:
            lines.append(" ".join(line))

        y = rect.y
        for line_text in lines:
            surface = font.render(line_text, True, color)
            if y + surface.get_height() > rect.bottom:
                break
            self.screen.blit(surface, (rect.x, y))
            y += surface.get_height() + line_spacing

    def wrap_text(self, text, font, width):
        """Return a list of lines that fit within width pixels."""
        lines = []
        for paragraph in text.splitlines() or [""]:
            line = []
            for word in paragraph.split():
                if font.size(" ".join(line + [word]))[0] <= width:
                    line.append(word)
                else:
                    if line:
                        lines.append(" ".join(line))
                    line = [word]
            lines.append(" ".join(line))
        return lines

def main():
    """Create and start the game."""

    CosmicClinicGUI().run()


if __name__ == "__main__":
    main()
