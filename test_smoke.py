"""Smoke tests for shared game data and the GUI vertical slice."""

import os
import unittest
from unittest.mock import patch


# Pygame can render into memory during tests, so no game window or audio device is needed.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

import main as game_launcher
from Deck import Deck
from Notebook import Notebook
from PatientData import create_conmann, create_titus, create_zoogy, create_zorpa
from Player import (
    CLINIC_OPERATING_FEE,
    DIAGNOSIS_REWARD,
    PERFECT_DAY_BONUS,
    STARTING_BALANCE,
    WRONG_DIAGNOSIS_PENALTY,
    Player,
)
from Tests.AllergyTest import AllergyTest
from Tests.TemperatureTest import TemperatureTest
from Tests.UltrasoundTest import UltrasoundTest
from Tests.XrayTest import XrayTest
from Test import TEST_COSTS_BY_RARITY, get_test_cost
from gui_animations import AnimationMixin
from gui_audio import AudioMixin
from gui_cards import CardMixin
from gui_developer import DeveloperMixin
from gui_ending import EndingMixin
from gui_examination import ExaminationMixin
from gui_main import CosmicClinicGUI, GameState
from gui_notebook import NotebookMixin
from gui_reception import ReceptionMixin
from gui_results import ResultsMixin
from gui_shop import SHOP_UPGRADES, ShopMixin
from gui_tutorial import TutorialMixin


class SharedModelSmokeTests(unittest.TestCase):
    """Check the game data used by both interfaces."""

    def test_zorpa_results_are_recorded_in_the_notebook(self):
        """A completed test should replace the notebook's empty-state entry."""

        patient = create_zorpa()
        notebook = Notebook()
        notebook.add_patient(patient)

        result = patient.perform_test("TEMPERATURE").removeprefix("RESULTS: ")
        notebook.add_test(patient, "TEMPERATURE", result)

        self.assertEqual(result, "Current temperature: 1700°F")
        self.assertEqual(patient.medical_info["Normal temperature"], "2,000°F")
        self.assertEqual(notebook.get_entries(patient), {"TEMPERATURE": result})

    def test_main_launches_the_cosmic_clinic_gui(self):
        """The official main.py entry point should start the GUI build."""

        with patch.object(game_launcher, "CosmicClinicGUI") as gui_class:
            game_launcher.main()

        gui_class.assert_called_once_with()
        gui_class.return_value.run.assert_called_once_with()

    def test_deck_rarity_counts_match_the_design(self):
        """The generated deck should contain each test according to its rarity."""

        deck = Deck()
        deck.populate(
            [TemperatureTest(), XrayTest(), UltrasoundTest(), AllergyTest()]
        )
        counts = {}
        for card in deck.contents:
            counts[card.value.name] = counts.get(card.value.name, 0) + 1

        self.assertEqual(
            counts,
            {
                "TEMPERATURE": 8,
                "X-RAY": 8,
                "ULTRASOUND": 5,
                "ALLERGY": 3,
            },
        )
        self.assertEqual(len(deck.contents), 24)

    def test_starting_diagnosis_hand_has_five_options_and_all_patient_answers(self):
        """The fixed hand should contain five unique options and every current correct answer."""

        player = Player("Test Doctor")
        diagnosis_names = [card.value.name for card in player.diagnosis_hand]

        self.assertEqual(len(diagnosis_names), 5)
        self.assertEqual(len(set(diagnosis_names)), 5)
        self.assertEqual(
            diagnosis_names,
            [
                "Hypothermia",
                "Acute Water Reaction",
                "Skeletal Resonance",
                "Lava-Flow Blockage",
                "Lactose Intolerance",
            ],
        )
        for patient in (
            create_zorpa(),
            create_zoogy(),
            create_titus(),
            create_conmann(),
        ):
            self.assertEqual(
                sum(card.value == patient.diagnosis for card in player.diagnosis_hand),
                1,
            )


class GuiFlowSmokeTests(unittest.TestCase):
    """Exercise the current vertical-slice state changes with headless Pygame."""

    def setUp(self):
        """Create a fresh GUI session for every flow test."""

        self.game = CosmicClinicGUI()
        self.game.finish_intro()
        self.game.tutorial_open = False
        self.game.tutorial_opened_at = None
        self.game.patients_called = 1
        self.game.state = GameState.PATIENT

    def tearDown(self):
        """Release Pygame resources after each test."""

        pygame.quit()

    def test_gui_uses_the_extracted_feature_modules(self):
        """The main GUI should receive extracted feature behavior from mixins."""

        self.assertIsInstance(self.game, AnimationMixin)
        self.assertIsInstance(self.game, AudioMixin)
        self.assertIsInstance(self.game, CardMixin)
        self.assertIsInstance(self.game, DeveloperMixin)
        self.assertIsInstance(self.game, EndingMixin)
        self.assertIsInstance(self.game, ExaminationMixin)
        self.assertIsInstance(self.game, NotebookMixin)
        self.assertIsInstance(self.game, ReceptionMixin)
        self.assertIsInstance(self.game, ResultsMixin)
        self.assertIsInstance(self.game, ShopMixin)
        self.assertIsInstance(self.game, TutorialMixin)
        self.assertEqual(self.game.draw_discard_animation.__module__, "gui_animations")
        self.assertEqual(self.game.draw_audio_button.__module__, "gui_audio")
        self.assertEqual(self.game.draw_test_card.__module__, "gui_cards")
        self.assertEqual(
            self.game.draw_developer_navigator.__module__,
            "gui_developer",
        )
        self.assertEqual(self.game.run_selected_test.__module__, "gui_cards")
        self.assertEqual(self.game.draw_patient_screen.__module__, "gui_examination")
        self.assertEqual(self.game.draw_id_card.__module__, "gui_examination")
        self.assertEqual(self.game.draw_notebook.__module__, "gui_notebook")
        self.assertEqual(self.game.draw_intro_screen.__module__, "gui_reception")
        self.assertEqual(self.game.draw_title_screen.__module__, "gui_reception")
        self.assertEqual(self.game.draw_test_result_screen.__module__, "gui_results")
        self.assertEqual(self.game.draw_diagnosis_outcome.__module__, "gui_results")
        self.assertEqual(self.game.draw_shop_screen.__module__, "gui_shop")
        self.assertEqual(self.game.draw_day_complete_screen.__module__, "gui_shop")
        self.assertEqual(self.game.draw_ending_screen.__module__, "gui_ending")
        self.assertEqual(self.game.draw_exit_confirmation.__module__, "gui_ending")
        self.assertEqual(self.game.draw_tutorial_overlay.__module__, "gui_tutorial")

    def test_first_launch_briefing_blocks_reception_until_dismissed(self):
        """The tutorial should appear once and remain available from gameplay Help."""

        self.game.state = GameState.TITLE
        self.game.patients_called = 0
        self.game.tutorial_open = True
        self.game.tutorial_opened_at = None
        self.game.reception_transition_started_at = None
        self.assertTrue(self.game.tutorial_open)
        self.assertEqual(self.game.get_tutorial_action_label(), "BEGIN SHIFT")
        self.game.draw()

        self.game.handle_tutorial_click(self.game.start_button.center)
        self.assertTrue(self.game.tutorial_open)
        self.assertIsNone(self.game.reception_transition_started_at)

        self.game.handle_tutorial_click(self.game.tutorial_begin_button.center)
        self.assertFalse(self.game.tutorial_open)
        self.game.open_tutorial()
        self.assertTrue(self.game.tutorial_open)
        self.game.close_tutorial()
        self.assertFalse(self.game.tutorial_open)

        self.game.state = GameState.PATIENT
        self.game.patients_called = 1
        self.assertEqual(self.game.get_tutorial_action_label(), "RETURN TO PATIENT")
        pygame.event.post(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {"button": 1, "pos": self.game.help_button.center},
            )
        )
        self.game.handle_events()
        self.assertTrue(self.game.tutorial_open)
        self.game.draw()
        self.game.handle_tutorial_click(self.game.tutorial_begin_button.center)
        self.assertFalse(self.game.tutorial_open)
        self.assertEqual(self.game.state, GameState.PATIENT)

        self.game.state = GameState.TITLE
        self.game.patients_called = 1
        self.assertEqual(self.game.get_tutorial_action_label(), "CONTINUE SHIFT")
        self.game.state = GameState.TEST_RESULT
        self.assertEqual(self.game.get_tutorial_action_label(), "RETURN TO TEST RESULT")
        self.game.state = GameState.NOTEBOOK
        self.assertEqual(self.game.get_tutorial_action_label(), "RETURN TO NOTEBOOK")
        self.game.state = GameState.SHOP
        self.assertEqual(self.game.get_tutorial_action_label(), "RETURN TO SHOP")

    def test_gameplay_help_pauses_timers_and_works_on_ending_screens(self):
        """Help should freeze transitions and remain visible through the finale."""

        self.game.tutorial_open = False
        self.game.state = GameState.TITLE
        self.game.reception_transition_started_at = (
            pygame.time.get_ticks() - self.game.reception_transition_duration - 1
        )
        self.game.open_tutorial()
        self.game.update()
        self.assertEqual(self.game.state, GameState.TITLE)
        self.assertIsNotNone(self.game.reception_transition_started_at)

        self.game.close_tutorial()
        self.game.reception_transition_started_at = None
        self.game.state = GameState.ENDING
        self.game.ending_started_at = pygame.time.get_ticks()
        pygame.event.post(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {"button": 1, "pos": self.game.help_button.center},
            )
        )
        self.game.handle_events()
        self.assertTrue(self.game.tutorial_open)
        self.assertEqual(self.game.get_tutorial_action_label(), "CONTINUE ENDING")
        self.game.draw()

        pygame.event.post(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {"button": 1, "pos": self.game.tutorial_begin_button.center},
            )
        )
        self.game.handle_events()
        self.assertFalse(self.game.tutorial_open)
        self.assertEqual(self.game.state, GameState.ENDING)

        self.game.state = GameState.FINAL
        self.game.draw()

    def test_f10_developer_navigator_previews_late_game_screens(self):
        """The hidden navigator should safely prepare recap and shop previews."""

        pygame.event.post(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_F10})
        )
        self.game.handle_events()
        self.assertTrue(self.game.developer_navigator_open)
        self.game.draw()

        pygame.event.post(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_6})
        )
        self.game.handle_events()
        self.assertEqual(self.game.state, GameState.DAY_COMPLETE)
        self.assertFalse(self.game.developer_navigator_open)
        self.assertEqual(self.game.daily_correct_diagnoses, 4)
        self.assertEqual(self.game.get_daily_pay_breakdown()[3], 95)
        self.game.draw()

        pygame.event.post(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_F10})
        )
        self.game.handle_events()
        pygame.event.post(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_7})
        )
        self.game.handle_events()
        self.assertEqual(self.game.state, GameState.SHOP)
        self.assertTrue(self.game.daily_payout_applied)
        self.assertEqual(self.game.player.balance, 195)
        self.game.draw()

        pygame.event.post(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_F10})
        )
        self.game.handle_events()
        pygame.event.post(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
        )
        self.game.handle_events()
        self.assertFalse(self.game.developer_navigator_open)

    def test_test_cards_accumulate_end_of_day_operating_expenses(self):
        """Running machines should charge by rarity without changing cash immediately."""

        starting_balance = self.game.player.balance
        self.assertEqual(
            TEST_COSTS_BY_RARITY,
            {"Common": 10, "Uncommon": 15, "Rare": 20},
        )

        self.game.selected_card_index = 0
        first_test = self.game.player.test_hand[0].value
        self.game.run_selected_test()
        self.assertEqual(self.game.daily_test_count, 1)
        self.assertEqual(self.game.daily_test_expenses, get_test_cost(first_test))
        self.assertEqual(self.game.player.balance, starting_balance)

        self.game.daily_correct_diagnoses = len(self.game.waiting_room_queue)
        self.assertEqual(
            self.game.get_daily_pay_breakdown()[3],
            len(self.game.waiting_room_queue) * DIAGNOSIS_REWARD
            - get_test_cost(first_test)
            - CLINIC_OPERATING_FEE
            + PERFECT_DAY_BONUS,
        )

        self.game.daily_wrong_diagnoses = 1
        self.game.daily_test_count = 16
        self.game.daily_test_expenses = 220
        self.assertLess(self.game.get_daily_pay_breakdown()[3], 0)

    def test_rebalanced_economy_allows_one_efficient_shift_upgrade(self):
        """An efficient first shift should fund one upgrade, not a shopping spree."""

        self.assertEqual(self.game.player.balance, STARTING_BALANCE)
        self.assertEqual(STARTING_BALANCE, 100)
        self.assertEqual(DIAGNOSIS_REWARD, 40)
        self.assertEqual(WRONG_DIAGNOSIS_PENALTY, 25)
        self.assertEqual(CLINIC_OPERATING_FEE, 50)

        self.game.daily_correct_diagnoses = len(self.game.waiting_room_queue)
        self.game.daily_test_count = 4
        self.game.daily_test_expenses = 40
        self.assertEqual(
            self.game.get_daily_pay_breakdown(),
            (160, 0, PERFECT_DAY_BONUS, 95),
        )

        projected_balance = STARTING_BALANCE + 95
        two_cheapest_upgrades = sorted(
            upgrade["cost"] for upgrade in SHOP_UPGRADES
        )[:2]
        self.assertLessEqual(two_cheapest_upgrades[0], projected_balance)
        self.assertGreater(sum(two_cheapest_upgrades), projected_balance)

    def test_audio_controls_balance_music_and_cover_core_interactions(self):
        """The slice should expose every requested effect and a working global mute."""

        self.assertTrue(self.game.audio_available)
        self.assertLess(self.game.music_volume, self.game.sfx_volume)
        self.assertEqual(
            set(self.game.sound_effects),
            {
                "button",
                "card_select",
                "scan",
                "waste",
                "notebook",
                "correct",
                "incorrect",
                "door",
            },
        )

        self.game.draw()
        self.assertFalse(self.game.audio_muted)
        self.game.toggle_audio_muted()
        self.assertTrue(self.game.audio_muted)
        self.assertEqual(pygame.mixer.music.get_volume(), 0.0)
        self.game.toggle_audio_muted()
        self.assertFalse(self.game.audio_muted)
        self.assertAlmostEqual(
            pygame.mixer.music.get_volume(),
            self.game.music_volume,
            delta=0.01,
        )

    def test_cards_and_tests_request_their_distinct_sound_effects(self):
        """Card focus should click lightly while running a test starts its scanner."""

        with patch.object(self.game, "play_sfx") as play_sfx:
            self.game.handle_card_click(self.game.card_rects[0].center)
            play_sfx.assert_called_once_with("card_select")

        with patch.object(self.game, "play_sfx") as play_sfx:
            self.game.run_selected_test()
            play_sfx.assert_called_once_with("scan")

    def test_correct_diagnosis_returns_to_reception_without_early_payment(self):
        """A resolved early case should queue its pay and return to reception."""

        starting_balance = self.game.player.balance
        self.game.selected_card_index = 0
        self.game.run_selected_test()

        self.assertEqual(self.game.state, GameState.TEST_RESULT)
        self.assertEqual(len(self.game.player.test_hand), 4)
        self.assertEqual(len(self.game.discard_pile), 0)
        self.assertIsNotNone(self.game.pending_test_discard)
        self.assertIn("TEMPERATURE", self.game.notebook.get_entries(self.game.patient))

        self.game.test_result_started_at = (
            pygame.time.get_ticks() - self.game.test_result_reveal_duration - 1
        )
        self.game.draw()
        self.game.handle_test_result_click(self.game.continue_button.center)
        self.assertEqual(self.game.state, GameState.PATIENT)
        self.assertIsNotNone(self.game.note_transfer_animation)
        self.assertIsNotNone(self.game.pending_test_discard)
        self.assertIsNone(self.game.discard_animation)

        self.game.note_transfer_animation["started_at"] = (
            pygame.time.get_ticks() - self.game.note_transfer_animation_duration - 1
        )
        self.game.update()
        self.assertIsNone(self.game.note_transfer_animation)
        self.assertIsNotNone(self.game.notebook_attention_started_at)
        self.assertIsNone(self.game.discard_animation)

        self.game.notebook_attention_started_at = (
            pygame.time.get_ticks() - self.game.notebook_attention_duration - 1
        )
        self.game.update()
        self.assertIsNotNone(self.game.discard_animation)
        self.assertIsNone(self.game.pending_test_discard)

        self.game.discard_animation["started_at"] = (
            pygame.time.get_ticks() - self.game.test_discard_animation_duration - 1
        )
        self.game.update()
        self.assertIsNone(self.game.discard_animation)
        self.assertEqual(len(self.game.discard_pile), 1)

        self.game.switch_active_hand(True)
        self.game.selected_card_index = 0
        self.game.play_selected_diagnosis()
        self.assertEqual(self.game.state, GameState.OUTCOME)
        self.assertTrue(self.game.diagnosis_correct)
        self.assertEqual(self.game.player.balance, starting_balance)
        self.assertEqual(self.game.daily_correct_diagnoses, 1)

        self.game.draw()
        self.game.handle_outcome_click(self.game.outcome_button.center)
        self.assertEqual(self.game.state, GameState.TITLE)
        self.assertEqual(self.game.patient.name, "Zoogy Zinglestar")
        self.assertEqual(self.game.player.balance, starting_balance)
        self.assertEqual(len(self.game.player.test_hand), 5)
        self.assertIsNotNone(self.game.queue_shift_started_at)

    def test_incorrect_diagnosis_returns_to_test_hand(self):
        """A wrong diagnosis should be discarded before returning to test cards."""

        starting_balance = self.game.player.balance
        self.game.switch_active_hand(True)
        self.game.selected_card_index = 1
        wrong_card = self.game.player.diagnosis_hand[1]
        self.game.play_selected_diagnosis()

        self.assertEqual(self.game.state, GameState.OUTCOME)
        self.assertFalse(self.game.diagnosis_correct)
        self.assertEqual(self.game.player.balance, starting_balance)
        self.assertEqual(self.game.daily_wrong_diagnoses, 1)
        self.assertNotIn(wrong_card, self.game.player.diagnosis_hand)
        self.assertEqual(len(self.game.player.diagnosis_hand), 4)
        self.assertIsNotNone(self.game.pending_diagnosis_discard)

        self.game.draw()
        self.game.handle_outcome_click(self.game.outcome_button.center)
        self.assertEqual(self.game.state, GameState.PATIENT)
        self.assertFalse(self.game.showing_diagnosis_hand)
        self.assertIsNone(self.game.pending_diagnosis_discard)
        self.assertIsNotNone(self.game.discard_animation)
        self.assertIs(self.game.discard_animation["card"], wrong_card)
        self.game.draw()
        self.game.discard_animation["started_at"] = (
            pygame.time.get_ticks() - self.game.test_discard_animation_duration - 1
        )
        self.game.update()
        self.assertIsNone(self.game.discard_animation)
        self.assertIs(self.game.discard_pile[-1], wrong_card)

    def test_reception_transition_reaches_the_patient_workspace(self):
        """Calling the next patient should finish in the examination workspace."""

        self.game.state = GameState.TITLE
        self.game.reception_transition_started_at = None
        self.game.begin_reception_transition()

        self.assertIsNotNone(self.game.reception_transition_started_at)
        self.game.reception_transition_started_at = (
            pygame.time.get_ticks() - self.game.reception_transition_duration - 1
        )
        self.game.update()

        self.assertEqual(self.game.state, GameState.PATIENT)
        self.assertIsNotNone(self.game.patient_fade_started_at)

    def test_miniature_notebook_uses_a_compact_test_count(self):
        """The notebook preview should show a short count instead of overflowing notes."""

        self.assertEqual(self.game.get_notebook_test_count_label(), "NO TESTS")
        self.assertFalse(self.game.notebook_has_test_results())
        result = self.game.patient.perform_test("TEMPERATURE").removeprefix("RESULTS: ")
        self.game.notebook.add_test(self.game.patient, "TEMPERATURE", result)
        self.assertEqual(self.game.get_notebook_test_count_label(), "1 TEST")
        self.assertTrue(self.game.notebook_has_test_results())
        self.game.notebook.add_test(self.game.patient, "X-RAY", "No damage found.")
        self.assertEqual(self.game.get_notebook_test_count_label(), "2 TESTS")

    def test_zorpa_notebook_portrait_renders_without_crashing(self):
        """Opening the first patient's notebook should render Zorpa's portrait."""

        portrait = pygame.Rect(0, 0, 44, 44)
        self.game.draw_notebook_patient_stamp(portrait)

    def test_four_patient_day_reaches_the_shop_and_slice_ending(self):
        """A full shift should end after the Shop and support a clean replay."""

        starting_balance = self.game.player.balance
        expected_names = [entry["create"]().name for entry in self.game.waiting_room_queue]
        self.game.state = GameState.TITLE
        self.game.patients_called = 0
        self.game.reset_round()

        for index, expected_name in enumerate(expected_names):
            self.assertEqual(self.game.patient.name, expected_name)
            self.game.begin_reception_transition()
            self.game.reception_transition_started_at = (
                pygame.time.get_ticks() - self.game.reception_transition_duration - 1
            )
            self.game.update()

            self.assertEqual(self.game.state, GameState.PATIENT)
            self.assertEqual(self.game.patients_called, index + 1)
            self.game.draw()
            self.game.draw_notebook_patient_stamp(pygame.Rect(0, 0, 44, 44))

            self.game.switch_active_hand(True)
            self.game.selected_card_index = next(
                card_index
                for card_index, card in enumerate(self.game.player.diagnosis_hand)
                if card.value == self.game.patient.diagnosis
            )
            self.game.play_selected_diagnosis()
            self.assertTrue(self.game.diagnosis_correct)
            self.game.handle_outcome_click(self.game.outcome_button.center)

            if index < len(expected_names) - 1:
                self.assertEqual(self.game.state, GameState.TITLE)
                self.assertIsNotNone(self.game.queue_shift_started_at)
                self.game.queue_shift_started_at = (
                    pygame.time.get_ticks() - self.game.queue_shift_duration - 1
                )
                self.game.update()
                self.assertIsNone(self.game.queue_shift_started_at)

        self.assertEqual(self.game.state, GameState.DAY_COMPLETE)
        self.assertEqual(self.game.player.balance, starting_balance)
        self.assertEqual(
            self.game.get_daily_pay_breakdown(),
            (
                len(expected_names) * DIAGNOSIS_REWARD,
                0,
                PERFECT_DAY_BONUS,
                len(expected_names) * DIAGNOSIS_REWARD
                - CLINIC_OPERATING_FEE
                + PERFECT_DAY_BONUS,
            ),
        )
        self.game.draw()
        self.game.handle_day_complete_click(self.game.day_complete_button.center)
        self.assertEqual(self.game.state, GameState.SHOP)
        self.assertEqual(
            self.game.player.balance,
            starting_balance
            + len(expected_names) * DIAGNOSIS_REWARD
            - CLINIC_OPERATING_FEE
            + PERFECT_DAY_BONUS,
        )
        paid_balance = self.game.player.balance
        self.game.settle_daily_pay()
        self.assertEqual(self.game.player.balance, paid_balance)

        self.game.draw()
        placeholder = SHOP_UPGRADES[-1]
        placeholder_rect = self.game.get_shop_upgrade_rects()[-1]
        self.game.handle_shop_click(placeholder_rect.center)
        self.assertEqual(self.game.selected_shop_upgrade, placeholder["id"])
        self.game.handle_shop_click(self.game.shop_purchase_button.center)
        self.assertIn(placeholder["id"], self.game.purchased_shop_upgrades)
        self.assertEqual(
            self.game.player.balance,
            paid_balance - placeholder["cost"],
        )

        self.game.handle_shop_click(self.game.shop_button.center)
        self.assertEqual(self.game.state, GameState.ENDING)
        self.game.draw()
        self.game.ending_started_at = (
            pygame.time.get_ticks() - self.game.ending_duration - 1
        )
        self.game.update()
        self.assertEqual(self.game.state, GameState.FINAL)
        self.game.draw()
        self.assertEqual(self.game.daily_correct_diagnoses, len(expected_names))
        self.assertIn(placeholder["id"], self.game.purchased_shop_upgrades)

        self.game.handle_final_screen_click(self.game.final_replay_button.center)
        self.assertEqual(self.game.state, GameState.TITLE)
        self.assertEqual(self.game.patients_called, 0)
        self.assertEqual(self.game.patient.name, expected_names[0])
        self.assertEqual(self.game.player.balance, starting_balance)
        self.assertEqual(len(self.game.deck.contents), 24)
        self.assertEqual(self.game.daily_correct_diagnoses, 0)
        self.assertEqual(self.game.daily_wrong_diagnoses, 0)
        self.assertIsNone(self.game.selected_shop_upgrade)
        self.assertNotIn(placeholder["id"], self.game.purchased_shop_upgrades)

    def test_escape_confirmation_can_continue_restart_or_quit(self):
        """The exit modal should safely expose all three promised choices."""

        original_state = self.game.state
        self.game.open_exit_confirmation()
        self.assertTrue(self.game.exit_confirmation_open)
        self.game.draw()
        self.game.handle_exit_confirmation_click(self.game.exit_continue_button.center)
        self.assertFalse(self.game.exit_confirmation_open)
        self.assertEqual(self.game.state, original_state)

        self.game.state = GameState.SHOP
        self.game.open_exit_confirmation()
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.game.handle_events()
        self.assertTrue(self.game.exit_confirmation_open)
        self.assertEqual(self.game.state, GameState.SHOP)
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.game.handle_events()
        self.assertFalse(self.game.exit_confirmation_open)

        self.game.begin_ending_sequence()
        original_ending_start = self.game.ending_started_at
        self.game.open_exit_confirmation()
        self.game.exit_confirmation_opened_at -= 1000
        self.game.close_exit_confirmation()
        self.assertGreaterEqual(
            self.game.ending_started_at,
            original_ending_start + 1000,
        )

        self.game.player.balance = 725
        self.game.daily_correct_diagnoses = 3
        self.game.purchased_shop_upgrades.add(SHOP_UPGRADES[0]["id"])
        self.game.open_exit_confirmation()
        self.game.handle_exit_confirmation_click(self.game.exit_reception_button.center)
        self.assertEqual(self.game.state, GameState.TITLE)
        self.assertEqual(self.game.player.balance, STARTING_BALANCE)
        self.assertEqual(self.game.daily_correct_diagnoses, 0)
        self.assertFalse(self.game.purchased_shop_upgrades)

        self.game.open_exit_confirmation()
        self.game.handle_exit_confirmation_click(self.game.exit_quit_button.center)
        self.assertFalse(self.game.running)

    def test_remaining_patients_slide_forward_before_the_next_call(self):
        """After Zorpa, the other three patients should move into the open chairs."""

        self.game.state = GameState.TITLE
        self.game.patients_called = 1
        self.game.begin_queue_shift()

        self.assertEqual(self.game.patients_waiting(), 3)
        self.assertIsNotNone(self.game.queue_shift_started_at)
        self.game.queue_shift_started_at = pygame.time.get_ticks()
        self.assertLessEqual(self.game.get_waiting_patient_x(1), 642)

        self.game.queue_shift_started_at = (
            pygame.time.get_ticks() - self.game.queue_shift_duration // 2
        )
        halfway_x = self.game.get_waiting_patient_x(1)
        self.assertGreater(halfway_x, 640)
        self.assertLess(halfway_x, 782)
        self.game.draw()

        self.game.begin_reception_transition()
        self.assertIsNone(self.game.reception_transition_started_at)

        self.game.queue_shift_started_at = (
            pygame.time.get_ticks() - self.game.queue_shift_duration - 1
        )
        self.game.update()
        self.assertIsNone(self.game.queue_shift_started_at)
        self.assertEqual(self.game.get_waiting_patient_x(1), 782)
        self.assertEqual(self.game.get_waiting_patient_x(2), 640)
        self.assertEqual(self.game.get_waiting_patient_x(3), 498)

        self.game.begin_reception_transition()
        self.assertIsNotNone(self.game.reception_transition_started_at)

    def test_wrong_diagnoses_reduce_end_of_day_pay(self):
        """Mistakes should reduce pending pay and remove the perfect-day bonus."""

        self.game.daily_correct_diagnoses = len(self.game.waiting_room_queue)
        self.game.daily_wrong_diagnoses = 2

        self.assertEqual(
            self.game.get_daily_pay_breakdown(),
            (
                len(self.game.waiting_room_queue) * DIAGNOSIS_REWARD,
                2 * WRONG_DIAGNOSIS_PENALTY,
                0,
                len(self.game.waiting_room_queue) * DIAGNOSIS_REWARD
                - 2 * WRONG_DIAGNOSIS_PENALTY
                - CLINIC_OPERATING_FEE,
            ),
        )

    def test_machine_purchase_updates_cards_costs_and_survives_resets(self):
        self.game.state = GameState.SHOP
        upgrade = SHOP_UPGRADES[0]
        self.game.player.balance = upgrade["cost"] + 100
        balance = self.game.player.balance
        self.game.handle_shop_click(self.game.get_shop_upgrade_rects()[0].center)
        self.game.handle_shop_click(self.game.shop_purchase_button.center)
        self.assertEqual(self.game.player.balance, balance - upgrade["cost"])
        for card in self.game.player.test_hand + self.game.deck.contents:
            if card.value.name == "TEMPERATURE":
                self.assertEqual(self.game.player.get_machine_level(card.value), 2)
                self.assertEqual(self.game.player.get_test_cost(card.value), 5)
        self.game.handle_shop_click(self.game.shop_purchase_button.center)
        self.assertEqual(self.game.player.balance, balance - upgrade["cost"])
        self.game.reset_day()
        for card in self.game.player.test_hand + self.game.deck.contents:
            if card.value.name == "TEMPERATURE":
                self.assertEqual(self.game.player.get_machine_level(card.value), 2)
        self.game.selected_card_index = 0
        before = self.game.daily_test_expenses
        self.game.run_selected_test()
        self.assertEqual(self.game.daily_test_expenses - before, 5)
        self.assertEqual(self.game.last_test_cost, 5)

    def test_shared_upgrades_stack_and_apply_to_future_draws(self):
        self.game.state = GameState.SHOP
        purchase_cost = sum(SHOP_UPGRADES[index]["cost"] for index in (0, 4, 5))
        self.game.player.balance = purchase_cost + 100
        for index in (0, 4, 5):
            self.game.handle_shop_click(self.game.get_shop_upgrade_rects()[index].center)
            self.game.handle_shop_click(self.game.shop_purchase_button.center)
        self.assertEqual(self.game.player.balance, 100)
        self.assertEqual(self.game.player.get_test_cost(TemperatureTest()), 2)
        self.assertEqual(self.game.player.get_test_cost(AllergyTest()), 17)
        card = __import__("Card").Card("Test", TemperatureTest())
        self.game.player.draw(card)
        self.assertEqual(self.game.player.get_machine_level(card.value), 2)
        self.game.reset_round()
        self.assertEqual(self.game.player.get_test_cost(TemperatureTest()), 2)
        rects = self.game.get_shop_upgrade_rects()
        self.assertEqual(len(rects), 6)
        for index, rect in enumerate(rects):
            self.assertFalse(rect.colliderect(self.game.shop_purchase_button))
            self.assertFalse(rect.colliderect(self.game.shop_button))
            self.assertFalse(any(rect.colliderect(other) for other in rects[index + 1:]))
        self.game.draw_shop_screen()
        self.game.restart_vertical_slice()
        self.assertEqual(self.game.player.machine_levels, {})
        self.assertEqual(self.game.player.test_discount, 0)

    def test_shop_blocks_an_unaffordable_upgrade_purchase(self):
        """A selected upgrade should not charge or unlock when money is too low."""

        self.game.state = GameState.SHOP
        upgrade = SHOP_UPGRADES[0]
        upgrade_rect = self.game.get_shop_upgrade_rects()[0]
        self.game.handle_shop_click(upgrade_rect.center)
        self.assertEqual(self.game.selected_shop_upgrade, upgrade["id"])

        self.game.player.balance = upgrade["cost"] - 1
        starting_balance = self.game.player.balance
        self.game.handle_shop_click(self.game.shop_purchase_button.center)

        self.assertEqual(self.game.player.balance, starting_balance)
        self.assertNotIn(upgrade["id"], self.game.purchased_shop_upgrades)
        self.assertIn("Not enough money", self.game.shop_message)

    def test_workspace_tools_use_the_swapped_non_overlapping_layout(self):
        """Diagnosis should sit above med-waste while the larger notebook clears the hand."""

        diagnosis = self.game.layout["diagnosis"]
        throwaway = self.game.layout["throwaway"]
        notebook = self.game.layout["notebook"]
        active_hand = self.game.layout["active_hand"]
        right_window = pygame.Rect(794, 157, 277, 210)

        self.assertLess(diagnosis.centery, throwaway.centery)
        self.assertLessEqual(abs(diagnosis.centerx - right_window.centerx), 1)
        self.assertGreaterEqual(notebook.width, 180)
        self.assertLess(throwaway.width, notebook.width)
        self.assertLess(throwaway.height, notebook.height)
        self.assertFalse(throwaway.colliderect(active_hand))
        self.assertFalse(notebook.colliderect(active_hand))

    def test_hovered_cards_lift_and_expand_without_shifting_sideways(self):
        """Hover feedback should enlarge a card while preserving its horizontal center."""

        resting = self.game.card_rects[0]
        hovered = self.game.get_hovered_card_rect(resting)

        self.assertGreater(hovered.width, resting.width)
        self.assertGreater(hovered.height, resting.height)
        self.assertLess(hovered.y, resting.y)
        self.assertEqual(hovered.centerx, resting.centerx)

    def test_used_test_card_follows_an_arc_to_med_waste(self):
        """The midpoint of the disposal path should rise above a straight-line flight."""

        start = self.game.layout["active_hand"].center
        target = (
            self.game.layout["throwaway"].centerx,
            self.game.layout["throwaway"].y + 45,
        )
        control = ((start[0] + target[0]) / 2, min(start[1], target[1]) - 105)
        midpoint = self.game.get_quadratic_curve_point(start, control, target, 0.5)
        straight_midpoint_y = (start[1] + target[1]) / 2

        self.assertLess(midpoint[1], straight_midpoint_y)


if __name__ == "__main__":
    unittest.main()
