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
from Diagnosis import DIAGNOSES
from Notebook import Notebook
from PatientData import create_conmann, create_titus, create_zoogy, create_zorpa
from Player import (
    CLINIC_OPERATING_FEE,
    DIAGNOSIS_REWARD,
    DRAW_COST,
    LIMITED_EVIDENCE_REWARD,
    MAX_TEST_HAND_SIZE,
    PATIENT_WALKOUT_THRESHOLD,
    PERFECT_DAY_BONUS,
    STARTING_BALANCE,
    STARTING_TEST_HAND_SIZE,
    WRONG_DIAGNOSIS_PENALTY,
    Player,
)
from Tests.AllergyTest import AllergyTest
from Tests.BloodChemistryTest import BloodChemistryTest
from Tests.NeuralScanTest import NeuralScanTest
from Tests.OxygenScanTest import OxygenScanTest
from Tests.TemperatureTest import TemperatureTest
from Tests.ToxinScreenTest import ToxinScreenTest
from Tests.UltrasoundTest import UltrasoundTest
from Tests.XrayTest import XrayTest
from Tests.catalog import create_test_catalog
from Test import TEST_COSTS_BY_RARITY, get_test_cost
from gui_animations import AnimationMixin
from gui_audio import AudioMixin
from gui_cards import CardMixin
from gui_developer import DeveloperMixin
from gui_display import DisplayMixin
from gui_ending import EndingMixin
from gui_examination import ExaminationMixin
from gui_intro import IntroMixin
from gui_main import CosmicClinicGUI, GameState
from gui_notebook import NotebookMixin
from gui_reception import ReceptionMixin
from gui_results import ResultsMixin
from gui_shop import SHOP_UPGRADES, ShopMixin
from gui_theme import TEST_SUBTITLES, WINDOW_SIZE
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

    def test_patient_records_and_interviews_keep_new_allergies_discoverable(self):
        """Health IDs should build alien context without revealing Titus's answer."""

        titus = create_titus()
        self.assertEqual(titus.profile["Species"], "Goopian Ectomorph")
        self.assertNotIn(
            "water",
            " ".join(titus.medical_info.values()).lower(),
        )
        self.assertIn("None documented", titus.medical_info.values())
        allergy_result = titus.test_results["ALLERGY"].lower()
        self.assertNotIn("water", allergy_result)
        self.assertIn("sprinkler-residue", allergy_result)

        notebook = Notebook()
        notebook.add_patient(titus)
        self.assertEqual(notebook.get_interview(titus), titus.dialogue[:1])
        notebook.add_interview(titus, titus.dialogue[1])
        notebook.add_interview(titus, titus.dialogue[1])
        self.assertEqual(notebook.get_interview(titus), titus.dialogue[:2])

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

    def test_new_test_cards_have_balanced_metadata_and_rendering_support(self):
        """New tests should use the same rarity, cost, and visual systems as existing cards."""

        tests = [
            BloodChemistryTest(),
            OxygenScanTest(),
            ToxinScreenTest(),
            NeuralScanTest(),
        ]

        self.assertEqual(
            [(test.name, test.rarity, test.occurrences) for test in tests],
            [
                ("BLOOD CHEMISTRY", "Common", 8),
                ("OXYGEN SCAN", "Common", 8),
                ("TOXIN SCREEN", "Uncommon", 5),
                ("NEURAL SCAN", "Rare", 3),
            ],
        )
        self.assertEqual([get_test_cost(test) for test in tests], [10, 10, 15, 20])
        for test in tests:
            self.assertTrue(test.description)
            self.assertIn(test.name, TEST_SUBTITLES)

    def test_full_test_catalog_populates_the_live_deck(self):
        """Every basic test should be drawable using its configured rarity count."""

        deck = Deck()
        deck.populate(create_test_catalog())
        counts = {}
        for card in deck.contents:
            counts[card.value.name] = counts.get(card.value.name, 0) + 1

        self.assertEqual(
            counts,
            {
                "TEMPERATURE": 8,
                "X-RAY": 8,
                "BLOOD CHEMISTRY": 8,
                "OXYGEN SCAN": 8,
                "ULTRASOUND": 5,
                "TOXIN SCREEN": 5,
                "ALLERGY": 3,
                "NEURAL SCAN": 3,
            },
        )
        self.assertEqual(len(deck.contents), 48)

    def test_deck_seed_is_random_in_gameplay_and_reproducible_in_tests(self):
        """A private seeded RNG should control every shuffle and draw."""

        sequences = []
        for seed in (151, 151, 815):
            deck = Deck(seed=seed)
            deck.populate(create_test_catalog())
            sequences.append([deck.draw().value.name for _ in range(16)])

        self.assertEqual(sequences[0], sequences[1])
        self.assertNotEqual(sequences[0], sequences[2])
        self.assertEqual(Deck(seed=151).seed, 151)
        with patch("Deck.secrets.randbits", side_effect=(111, 222)):
            self.assertNotEqual(Deck().seed, Deck().seed)

    def test_every_patient_supports_every_basic_test(self):
        """A drawable test must always produce a patient-specific result."""

        test_names = {test.name for test in create_test_catalog()}
        for patient in (
            create_zorpa(),
            create_zoogy(),
            create_titus(),
            create_conmann(),
        ):
            self.assertEqual(set(patient.test_results), test_names)
            for test_name in test_names:
                self.assertTrue(patient.perform_test(test_name).startswith("RESULTS: "))

    def test_key_results_describe_clues_without_naming_the_answer(self):
        """Later cases should require inference instead of printing diagnoses."""

        zoogy_ultrasound = create_zoogy().test_results["ULTRASOUND"].lower()
        titus_allergy = create_titus().test_results["ALLERGY"].lower()
        conmann = create_conmann()
        conmann_allergy = conmann.test_results["ALLERGY"].lower()
        conmann_blood = conmann.test_results["BLOOD CHEMISTRY"].lower()

        self.assertNotIn("skeletal resonance", zoogy_ultrasound)
        self.assertNotIn("skeleton", zoogy_ultrasound)
        self.assertNotIn("water", titus_allergy)
        self.assertNotIn("lactose", conmann_allergy)
        self.assertNotIn("intolerance", conmann_allergy)
        self.assertNotIn("lactose", conmann_blood)

    def test_existing_conditions_define_two_card_clue_paths(self):
        """Every diagnosis should expose at least two valid two-test evidence routes."""

        from Diagnosis import DIAGNOSES

        available_tests = {test.name for test in create_test_catalog()}
        for diagnosis in DIAGNOSES.values():
            self.assertGreaterEqual(len(diagnosis.evidence_combinations), 2)
            self.assertTrue(
                all(len(combination) == 2 for combination in diagnosis.evidence_combinations)
            )
            for combination in diagnosis.evidence_combinations:
                self.assertTrue(combination.issubset(available_tests))
                self.assertTrue(diagnosis.has_supporting_evidence(combination))

        patients_and_evidence = (
            (create_zorpa(), {"TEMPERATURE", "BLOOD CHEMISTRY"}),
            (create_zoogy(), {"X-RAY", "NEURAL SCAN"}),
            (create_titus(), {"ALLERGY", "TOXIN SCREEN"}),
            (create_conmann(), {"ULTRASOUND", "BLOOD CHEMISTRY"}),
        )
        for patient, evidence in patients_and_evidence:
            self.assertTrue(patient.has_supporting_evidence(evidence))
            self.assertFalse(patient.has_supporting_evidence({next(iter(evidence))}))

    def test_evidence_progress_tracks_the_best_hidden_two_card_path(self):
        """The UI should expose clue strength without revealing valid card names."""

        patient = create_zorpa()
        self.assertEqual(patient.get_evidence_progress(set()), (0, 2))
        self.assertEqual(
            patient.get_evidence_progress({"TEMPERATURE"}),
            (1, 2),
        )
        self.assertEqual(
            patient.get_evidence_progress({"TEMPERATURE", "BLOOD CHEMISTRY"}),
            (2, 2),
        )
        self.assertEqual(
            patient.get_evidence_progress({"X-RAY", "ALLERGY"}),
            (0, 2),
        )

    def test_legacy_diagnosis_hand_remains_available_for_future_patient_sets(self):
        """The original five conditions remain available while sets are expanded."""

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
        self.assertIn("hypothermia", DIAGNOSES)

    def test_zorpa_has_five_curated_diagnosis_options(self):
        """Zorpa should receive one answer and four evidence-based distractors."""

        patient = create_zorpa()
        diagnosis_names = [diagnosis.name for diagnosis in patient.diagnosis_options]

        self.assertEqual(
            diagnosis_names,
            [
                "Neural Tremor Syndrome",
                "Lava-Blood Coagulation",
                "Thermal-Core Hypothermia",
                "Thermal-Lung Exchange Failure",
                "Event-Horizon Toxin Exposure",
            ],
        )
        self.assertEqual(len(set(diagnosis_names)), 5)
        self.assertEqual(
            sum(diagnosis == patient.diagnosis for diagnosis in patient.diagnosis_options),
            1,
        )
        self.assertIsNot(patient.diagnosis, DIAGNOSES["hypothermia"])
        distractors = [
            diagnosis
            for diagnosis in patient.diagnosis_options
            if diagnosis != patient.diagnosis
        ]
        self.assertTrue(
            all(diagnosis.rejection_reason for diagnosis in distractors)
        )
        self.assertTrue(
            all(diagnosis.rejection_tests for diagnosis in distractors)
        )

    def test_detailed_rejection_feedback_requires_every_referenced_test(self):
        """A wrong guess must not reveal findings from tests never performed."""

        cases = (
            (
                DIAGNOSES["neural_tremor_syndrome"],
                {"NEURAL SCAN", "TEMPERATURE"},
            ),
            (
                DIAGNOSES["lava_blood_coagulation"],
                {"ULTRASOUND", "BLOOD CHEMISTRY", "TEMPERATURE"},
            ),
            (
                DIAGNOSES["thermal_lung_exchange_failure"],
                {"OXYGEN SCAN", "BLOOD CHEMISTRY"},
            ),
            (
                DIAGNOSES["event_horizon_toxin_exposure"],
                {"TOXIN SCREEN", "BLOOD CHEMISTRY"},
            ),
            (
                DIAGNOSES["neural_oscillation_disorder"],
                {"NEURAL SCAN", "X-RAY"},
            ),
            (
                DIAGNOSES["crystal_lattice_microfracture"],
                {"X-RAY", "ULTRASOUND"},
            ),
            (
                DIAGNOSES["resonant_lung_compression"],
                {"OXYGEN SCAN"},
            ),
            (
                DIAGNOSES["mineral_energy_imbalance"],
                {"BLOOD CHEMISTRY"},
            ),
            (
                DIAGNOSES["membrane_toxin_absorption"],
                {"TOXIN SCREEN"},
            ),
            (
                DIAGNOSES["ectomorphic_hypothermia"],
                {"TEMPERATURE"},
            ),
            (
                DIAGNOSES["neural_shock_tremor"],
                {"NEURAL SCAN"},
            ),
            (
                DIAGNOSES["respiratory_anaphylaxis"],
                {"OXYGEN SCAN"},
            ),
            (
                DIAGNOSES["moon_cheese_allergy"],
                {"ALLERGY"},
            ),
            (
                DIAGNOSES["fermentation_chamber_blockage"],
                {"ULTRASOUND"},
            ),
            (
                DIAGNOSES["foodborne_toxin_exposure"],
                {"TOXIN SCREEN"},
            ),
            (
                DIAGNOSES["oil_blood_metabolic_failure"],
                {"BLOOD CHEMISTRY"},
            ),
        )
        for diagnosis, required_tests in cases:
            with self.subTest(diagnosis=diagnosis.name):
                partial_tests = set(required_tests)
                partial_tests.pop()
                self.assertIsNone(diagnosis.get_rejection_reason(set()))
                self.assertIsNone(
                    diagnosis.get_rejection_reason(partial_tests)
                )
                self.assertEqual(
                    diagnosis.get_rejection_reason(required_tests),
                    diagnosis.rejection_reason,
                )

    def test_zoogy_has_five_curated_diagnosis_options(self):
        """Zoogy should receive one answer and four evidence-based distractors."""

        patient = create_zoogy()
        diagnosis_names = [diagnosis.name for diagnosis in patient.diagnosis_options]

        self.assertEqual(
            diagnosis_names,
            [
                "Neural Oscillation Disorder",
                "Crystal-Lattice Microfracture",
                "Skeletal Resonance",
                "Resonant Lung Compression",
                "Mineral-Energy Imbalance",
            ],
        )
        self.assertEqual(len(set(diagnosis_names)), 5)
        self.assertEqual(
            sum(diagnosis == patient.diagnosis for diagnosis in patient.diagnosis_options),
            1,
        )
        distractors = [
            diagnosis
            for diagnosis in patient.diagnosis_options
            if diagnosis != patient.diagnosis
        ]
        self.assertTrue(all(diagnosis.rejection_reason for diagnosis in distractors))
        self.assertTrue(all(diagnosis.rejection_tests for diagnosis in distractors))

    def test_titus_has_five_curated_diagnosis_options(self):
        """Titus should receive one answer and four evidence-based distractors."""

        patient = create_titus()
        diagnosis_names = [diagnosis.name for diagnosis in patient.diagnosis_options]

        self.assertEqual(
            diagnosis_names,
            [
                "Membrane Toxin Absorption",
                "Ectomorphic Hypothermia",
                "Acute Water Reaction",
                "Neural Shock Tremor",
                "Respiratory Anaphylaxis",
            ],
        )
        self.assertEqual(len(set(diagnosis_names)), 5)
        self.assertEqual(
            sum(diagnosis == patient.diagnosis for diagnosis in patient.diagnosis_options),
            1,
        )
        distractors = [
            diagnosis
            for diagnosis in patient.diagnosis_options
            if diagnosis != patient.diagnosis
        ]
        self.assertTrue(all(diagnosis.rejection_reason for diagnosis in distractors))
        self.assertTrue(all(diagnosis.rejection_tests for diagnosis in distractors))

    def test_conmann_has_five_curated_diagnosis_options(self):
        """Conmann should receive one answer and four evidence-based distractors."""

        patient = create_conmann()
        diagnosis_names = [diagnosis.name for diagnosis in patient.diagnosis_options]

        self.assertEqual(
            diagnosis_names,
            [
                "Moon-Cheese Allergy",
                "Fermentation Chamber Blockage",
                "Lactose Intolerance",
                "Foodborne Toxin Exposure",
                "Oil-Blood Metabolic Failure",
            ],
        )
        self.assertEqual(len(set(diagnosis_names)), 5)
        self.assertEqual(
            sum(diagnosis == patient.diagnosis for diagnosis in patient.diagnosis_options),
            1,
        )
        distractors = [
            diagnosis
            for diagnosis in patient.diagnosis_options
            if diagnosis != patient.diagnosis
        ]
        self.assertTrue(all(diagnosis.rejection_reason for diagnosis in distractors))
        self.assertTrue(all(diagnosis.rejection_tests for diagnosis in distractors))


class GuiFlowSmokeTests(unittest.TestCase):
    """Exercise the current vertical-slice state changes with headless Pygame."""

    def setUp(self):
        """Create a fresh GUI session for every flow test."""

        self.game = CosmicClinicGUI()
        self.game.finish_intro()
        self.game.finish_intro_dialogue()
        self.game.finish_guided_tutorial()
        self.game.tutorial_open = False
        self.game.tutorial_opened_at = None
        self.game.patients_called = 1
        self.game.state = GameState.PATIENT

    def test_patient_specific_diagnosis_hand_switches_with_the_case(self):
        """Each completed patient set should replace the legacy case files."""

        self.assertEqual(
            set(card.value for card in self.game.player.diagnosis_hand),
            set(self.game.patient.diagnosis_options),
        )
        self.assertEqual(
            len(self.game.player.diagnosis_hand),
            len(self.game.patient.diagnosis_options),
        )
        self.assertEqual(
            sum(
                card.value == self.game.patient.diagnosis
                for card in self.game.player.diagnosis_hand
            ),
            1,
        )

        self.game.patients_called = 3
        self.game.reset_round()
        self.assertEqual(self.game.patient.name, "Conmann Cheester")
        self.assertEqual(
            set(card.value for card in self.game.player.diagnosis_hand),
            set(self.game.patient.diagnosis_options),
        )
        self.assertEqual(
            len(self.game.player.diagnosis_hand),
            len(self.game.patient.diagnosis_options),
        )
        self.assertEqual(
            sum(
                card.value == self.game.patient.diagnosis
                for card in self.game.player.diagnosis_hand
            ),
            1,
        )

        self.game.patients_called = 2
        self.game.reset_round()
        self.assertEqual(self.game.patient.name, "Titus McMightus")
        self.assertEqual(
            set(card.value for card in self.game.player.diagnosis_hand),
            set(self.game.patient.diagnosis_options),
        )
        self.assertEqual(
            len(self.game.player.diagnosis_hand),
            len(self.game.patient.diagnosis_options),
        )
        self.assertEqual(
            sum(
                card.value == self.game.patient.diagnosis
                for card in self.game.player.diagnosis_hand
            ),
            1,
        )

        self.game.patients_called = 1
        self.game.reset_round()
        self.assertEqual(self.game.patient.name, "Zoogy Zinglestar")
        self.assertEqual(
            set(card.value for card in self.game.player.diagnosis_hand),
            set(self.game.patient.diagnosis_options),
        )
        self.assertEqual(
            len(self.game.player.diagnosis_hand),
            len(self.game.patient.diagnosis_options),
        )
        self.assertEqual(
            sum(
                card.value == self.game.patient.diagnosis
                for card in self.game.player.diagnosis_hand
            ),
            1,
        )

    def test_diagnosis_hand_shuffle_is_random_and_seed_reproducible(self):
        """Case-file order should vary without breaking deterministic tests."""

        orders = []
        correct_slots = []
        for seed in (1, 1, 2, 7):
            game = CosmicClinicGUI(card_seed=seed)
            order = tuple(card.value.name for card in game.player.diagnosis_hand)
            orders.append(order)
            correct_slots.append(order.index(game.patient.diagnosis.name))

        self.assertEqual(orders[0], orders[1])
        self.assertNotEqual(orders[0], orders[2])
        self.assertGreaterEqual(len(set(orders)), 3)
        self.assertGreaterEqual(len(set(correct_slots)), 2)

    def tearDown(self):
        """Release Pygame resources after each test."""

        pygame.quit()

    def test_opening_hand_is_dealt_from_the_live_randomized_deck(self):
        """The training hand should consume five deck cards, not create fixed copies."""

        catalog_total = sum(test.occurrences for test in create_test_catalog())
        hand_names = [card.value.name for card in self.game.player.test_hand]
        combined_cards = self.game.player.test_hand + self.game.deck.contents
        combined_counts = {}
        for card in combined_cards:
            combined_counts[card.value.name] = (
                combined_counts.get(card.value.name, 0) + 1
            )

        self.assertEqual(len(hand_names), STARTING_TEST_HAND_SIZE)
        self.assertIn("TEMPERATURE", hand_names)
        self.assertEqual(
            len(self.game.deck.contents),
            catalog_total - STARTING_TEST_HAND_SIZE,
        )
        self.assertEqual(
            combined_counts,
            {test.name: test.occurrences for test in create_test_catalog()},
        )

    def test_gui_uses_the_extracted_feature_modules(self):
        """The main GUI should receive extracted feature behavior from mixins."""

        self.assertIsInstance(self.game, AnimationMixin)
        self.assertIsInstance(self.game, AudioMixin)
        self.assertIsInstance(self.game, CardMixin)
        self.assertIsInstance(self.game, DeveloperMixin)
        self.assertIsInstance(self.game, DisplayMixin)
        self.assertIsInstance(self.game, EndingMixin)
        self.assertIsInstance(self.game, ExaminationMixin)
        self.assertIsInstance(self.game, IntroMixin)
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
        self.assertEqual(self.game.present_frame.__module__, "gui_display")
        self.assertEqual(self.game.run_selected_test.__module__, "gui_cards")
        self.assertEqual(self.game.draw_patient_screen.__module__, "gui_examination")
        self.assertEqual(self.game.draw_id_card.__module__, "gui_examination")
        self.assertEqual(self.game.draw_notebook.__module__, "gui_notebook")
        self.assertEqual(self.game.draw_intro_screen.__module__, "gui_intro")
        self.assertEqual(self.game.draw_title_screen.__module__, "gui_reception")
        self.assertEqual(self.game.draw_test_result_screen.__module__, "gui_results")
        self.assertEqual(self.game.draw_diagnosis_outcome.__module__, "gui_results")
        self.assertEqual(self.game.draw_shop_screen.__module__, "gui_shop")
        self.assertEqual(self.game.draw_day_complete_screen.__module__, "gui_shop")
        self.assertEqual(self.game.draw_ending_screen.__module__, "gui_ending")
        self.assertEqual(self.game.draw_exit_confirmation.__module__, "gui_ending")
        self.assertEqual(self.game.draw_tutorial_overlay.__module__, "gui_tutorial")

    def test_resizable_window_maps_input_and_f11_toggles_fullscreen(self):
        """Scaling should preserve click coordinates in windowed and fullscreen modes."""

        self.game.resize_display((1500, 900))
        logical_position = (550, 325)
        window_position = self.game.game_to_window_position(logical_position)
        mapped_position = self.game.window_to_game_position(window_position)
        self.assertAlmostEqual(mapped_position[0], logical_position[0], delta=1)
        self.assertAlmostEqual(mapped_position[1], logical_position[1], delta=1)
        self.assertEqual(
            self.game.window_to_game_position((0, 0)),
            (-10000, -10000),
        )

        self.game.draw()
        self.game.present_frame()
        pygame.event.post(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_F11})
        )
        self.game.handle_events()
        self.assertTrue(self.game.fullscreen)
        self.game.draw()
        self.game.present_frame()

        pygame.event.post(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_F11})
        )
        self.game.handle_events()
        self.assertFalse(self.game.fullscreen)
        self.assertEqual(self.game.windowed_size, (1500, 900))

    def test_abduction_intro_renders_each_story_stage_and_can_be_skipped(self):
        """Earth, beam, blinking reception, and the skip path should stay playable."""

        self.assertLess(self.game.intro_ufo_surface.get_width(), WINDOW_SIZE[0])
        self.assertLess(self.game.intro_ufo_surface.get_height(), WINDOW_SIZE[1])
        self.assertEqual(self.game.intro_ufo_surface.get_at((0, 0)).a, 0)
        self.game.state = GameState.INTRO
        self.game.finish_guided_tutorial()
        self.game.tutorial_open = False
        now = pygame.time.get_ticks()
        for elapsed in (0, 2500, 6400, 7600, 8350, 9000, 9700, 10800, 12600):
            self.game.intro_started_at = now - elapsed
            self.game.draw()

        self.assertEqual(self.game.get_intro_blink_openness(0), 0.0)
        self.assertGreater(self.game.get_intro_blink_openness(1000), 0.3)
        self.assertEqual(self.game.get_intro_blink_openness(2500), 1.0)

        pygame.event.post(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {
                    "button": 1,
                    "pos": self.game.game_to_window_position(
                        self.game.audio_button.center
                    ),
                },
            )
        )
        self.game.handle_events()
        self.assertEqual(self.game.state, GameState.TITLE)
        self.assertTrue(self.game.intro_dialogue_active)
        self.assertFalse(self.game.tutorial_open)

        self.game.draw()
        for expected_index in range(1, len(self.game.INTRO_DIALOGUE)):
            self.game.advance_intro_dialogue()
            self.assertEqual(self.game.intro_dialogue_index, expected_index)
            self.game.draw()
        self.game.advance_intro_dialogue()
        self.assertFalse(self.game.intro_dialogue_active)
        self.assertTrue(self.game.guided_tutorial_active)
        self.assertEqual(self.game.guided_tutorial_step, "call_patient")
        self.assertFalse(self.game.tutorial_open)

    def test_guided_zorpa_case_uses_real_controls_from_reception_to_diagnosis(self):
        """The interactive tutorial should complete one real, billed patient case."""

        self.game.state = GameState.TITLE
        self.game.patients_called = 0
        self.game.reception_transition_started_at = None
        self.game.start_guided_tutorial()
        self.assertEqual(self.game.guided_tutorial_step, "call_patient")
        self.game.draw()

        self.game.handle_guided_tutorial_click(self.game.start_button.center)
        self.assertEqual(self.game.guided_tutorial_step, "patient_arrival")
        self.game.reception_transition_started_at -= self.game.reception_transition_duration + 1
        self.game.update()
        self.game.patient_fade_started_at -= self.game.patient_fade_duration + 1
        self.game.update()
        self.game.update()
        self.assertEqual(self.game.state, GameState.PATIENT)
        self.assertEqual(self.game.guided_tutorial_step, "symptom")

        self.game.handle_guided_tutorial_click(self.game.layout["alien"].center)
        self.assertEqual(self.game.guided_tutorial_step, "inspect_id")
        self.game.handle_guided_tutorial_click(self.game.layout["id_card"].center)
        self.assertTrue(self.game.showing_health_id)
        self.assertEqual(self.game.guided_tutorial_step, "review_health_id")
        self.game.handle_guided_tutorial_click((1090, 680))

        temperature_index = self.game.get_temperature_card_index()
        self.game.handle_guided_tutorial_click(self.game.card_rects[temperature_index].center)
        self.assertEqual(self.game.guided_tutorial_step, "temperature_run")
        selected = self.game.get_selected_card_rect(self.game.selected_card_index)
        self.game.handle_guided_tutorial_click(self.game.get_run_test_button(selected).center)
        self.assertEqual(self.game.state, GameState.TEST_RESULT)
        self.assertEqual(self.game.daily_test_count, 1)
        self.game.test_result_started_at -= self.game.test_result_reveal_duration + 1
        self.game.draw()
        self.game.handle_guided_tutorial_click(self.game.continue_button.center)
        self.assertEqual(self.game.guided_tutorial_step, "note_transfer")

        self.game.note_transfer_animation["started_at"] -= self.game.note_transfer_animation_duration + 1
        self.game.update()
        self.game.notebook_attention_started_at -= self.game.notebook_attention_duration + 1
        self.game.update()
        self.game.discard_animation["started_at"] -= self.game.test_discard_animation_duration + 1
        self.game.update()
        self.game.update()
        self.assertEqual(self.game.guided_tutorial_step, "open_notebook")

        self.game.handle_guided_tutorial_click(self.game.layout["notebook"].center)
        self.assertEqual(self.game.state, GameState.NOTEBOOK)
        self.assertEqual(self.game.guided_tutorial_step, "review_notebook")
        self.game.handle_guided_tutorial_click((1090, 680))
        self.game.handle_guided_tutorial_click(self.game.layout["diagnosis"].center)
        prompt_text, _prompt_rect, _click_anywhere = (
            self.game.get_guided_tutorial_prompt()
        )
        self.assertNotIn("Thermal-Core Hypothermia", prompt_text)
        self.assertIn("300°F below", prompt_text)
        choice_area = self.game.get_guided_tutorial_target()
        self.assertTrue(
            all(choice_area.contains(rect) for rect in self.game.card_rects)
        )
        wrong_index = next(
            index
            for index, card in enumerate(self.game.player.diagnosis_hand)
            if card.value != self.game.patient.diagnosis
        )
        self.game.handle_guided_tutorial_click(
            self.game.card_rects[wrong_index].center
        )
        self.assertEqual(self.game.guided_tutorial_step, "diagnosis_select")
        self.assertIn("evidence you have not collected", self.game.guided_tutorial_nudge)
        hypothermia_index = self.game.get_correct_diagnosis_card_index()
        self.game.handle_guided_tutorial_click(self.game.card_rects[hypothermia_index].center)
        selected = self.game.get_selected_card_rect(self.game.selected_card_index)
        self.game.handle_guided_tutorial_click(self.game.get_card_action_button(selected).center)
        self.assertTrue(self.game.diagnosis_confirmation_open)
        self.game.handle_guided_tutorial_click(self.game.diagnosis_confirm_button.center)
        self.assertEqual(self.game.state, GameState.OUTCOME)
        self.assertTrue(self.game.diagnosis_correct)
        self.assertEqual(self.game.guided_tutorial_step, "complete")
        self.game.handle_guided_tutorial_click((1090, 680))
        self.assertFalse(self.game.guided_tutorial_active)
        self.assertEqual(self.game.daily_correct_diagnoses, 1)
        self.assertEqual(self.game.daily_evidence_cases, 0)
        self.assertFalse(self.game.last_diagnosis_supported)

    def test_compact_help_remains_available_after_training(self):
        """The deleted briefing should be replaced by compact reusable Help."""

        self.assertEqual(self.game.get_tutorial_action_label(), "RETURN TO PATIENT")
        self.game.open_tutorial()
        self.assertTrue(self.game.tutorial_open)
        self.game.draw()
        self.game.handle_tutorial_click(self.game.tutorial_begin_button.center)
        self.assertFalse(self.game.tutorial_open)
        self.game.state = GameState.TITLE
        self.assertEqual(self.game.get_tutorial_action_label(), "RETURN TO RECEPTION")
        self.game.state = GameState.TEST_RESULT
        self.assertEqual(self.game.get_tutorial_action_label(), "RETURN TO TEST RESULT")
        self.game.state = GameState.NOTEBOOK
        self.assertEqual(self.game.get_tutorial_action_label(), "RETURN TO NOTEBOOK")
        self.game.state = GameState.SHOP
        self.assertEqual(self.game.get_tutorial_action_label(), "RETURN TO SHOP")

    def test_help_is_context_sensitive_and_h_toggles_it(self):
        """Help should explain the current screen and remain one keypress away."""

        self.game.state = GameState.TITLE
        self.assertEqual(self.game.get_help_context()[0], "RECEPTION")
        self.game.state = GameState.PATIENT
        self.assertEqual(self.game.get_help_context()[0], "EXAMINATION BAY")
        self.game.switch_active_hand(True)
        self.assertEqual(self.game.get_help_context()[0], "DIAGNOSIS OPTIONS")
        self.game.state = GameState.TEST_RESULT
        self.assertEqual(self.game.get_help_context()[0], "TEST RESULT")
        self.game.state = GameState.SHOP
        self.assertEqual(self.game.get_help_context()[0], "SUPPLY SHOP")

        help_copy = " ".join(
            heading + " " + detail
            for heading, detail in self.game.get_help_rules()
        )
        self.assertIn(f"${DRAW_COST}", help_copy)
        self.assertIn(str(MAX_TEST_HAND_SIZE), help_copy)
        self.assertIn(f"${WRONG_DIAGNOSIS_PENALTY}", help_copy)
        self.assertIn("H Help", help_copy)

        self.assertFalse(self.game.tutorial_open)
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_h))
        self.game.handle_events()
        self.assertTrue(self.game.tutorial_open)
        self.assertTrue(self.game.help_attention_seen)
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_h))
        self.game.handle_events()
        self.assertFalse(self.game.tutorial_open)

    def test_tutorial_spotlights_have_clickable_hitboxes_and_wrapped_text(self):
        """Highlighted reading targets and lifted card edges should never feel inert."""

        self.game.start_guided_tutorial()
        self.game.state = GameState.PATIENT

        self.game.set_guided_tutorial_step("symptom")
        symptom_target = self.game.get_guided_tutorial_target()
        self.assertEqual(symptom_target.size, (105, 76))
        self.assertEqual(self.game.patient_dialogue_index, 0)
        self.game.handle_guided_tutorial_click(self.game.layout["alien"].center)
        self.assertEqual(self.game.patient_dialogue_index, 1)
        self.assertEqual(self.game.guided_tutorial_step, "inspect_id")

        self.game.showing_health_id = True
        self.game.set_guided_tutorial_step("review_health_id")
        self.game.handle_guided_tutorial_click((1090, 680))
        self.assertEqual(self.game.guided_tutorial_step, "temperature_select")

        temperature_target = self.game.get_guided_tutorial_target()
        temperature_index = self.game.get_temperature_card_index()
        self.assertTrue(
            temperature_target.contains(self.game.card_rects[temperature_index])
        )
        self.game.handle_guided_tutorial_click(
            (temperature_target.x + 1, temperature_target.y + 1)
        )
        self.assertEqual(self.game.guided_tutorial_step, "temperature_run")

        self.game.open_notebook()
        self.game.guided_tutorial_active = True
        self.game.set_guided_tutorial_step("review_notebook")
        self.game.handle_guided_tutorial_click((1090, 680))
        self.assertEqual(self.game.guided_tutorial_step, "diagnosis_folder")

        self.game.set_guided_tutorial_step("complete")
        self.game.handle_guided_tutorial_click((1090, 680))
        self.assertFalse(self.game.guided_tutorial_active)

        for step in (
            "symptom",
            "inspect_id",
            "review_health_id",
            "temperature_select",
            "temperature_run",
            "test_result",
            "note_transfer",
            "open_notebook",
            "review_notebook",
            "diagnosis_folder",
            "diagnosis_select",
            "diagnosis_play",
            "diagnosis_confirm",
            "complete",
        ):
            self.game.guided_tutorial_step = step
            message, panel, _click_anywhere = self.game.get_guided_tutorial_prompt()
            for line in self.game.wrap_text(
                message,
                self.game.tutorial_body_font,
                panel.width - 32,
            ):
                self.assertLessEqual(
                    self.game.tutorial_body_font.size(line)[0],
                    panel.width - 32,
                )

        self.game.guided_tutorial_step = "diagnosis_confirm"
        _message, confirmation_prompt, _click_anywhere = (
            self.game.get_guided_tutorial_prompt()
        )
        confirmation_modal = pygame.Rect(245, 155, 610, 335)
        self.assertFalse(confirmation_prompt.colliderect(confirmation_modal))

    def test_patient_interview_cycles_and_files_each_unique_statement(self):
        """Clicking the patient should reveal questions without losing notes."""

        self.assertEqual(self.game.patient_dialogue_index, 0)
        self.assertEqual(
            self.game.notebook.get_interview(self.game.patient),
            self.game.patient.dialogue[:1],
        )

        for expected_index in (1, 2, 0):
            self.game.handle_patient_click(self.game.layout["alien"].center)
            self.assertEqual(self.game.patient_dialogue_index, expected_index)

        self.assertEqual(
            self.game.notebook.get_interview(self.game.patient),
            self.game.patient.dialogue,
        )

        self.game.reset_round()
        self.assertEqual(self.game.patient_dialogue_index, 0)
        self.assertEqual(
            self.game.notebook.get_interview(self.game.patient),
            self.game.patient.dialogue[:1],
        )

    def test_patient_id_details_fit_the_larger_readable_font(self):
        """Every current profile and medical line should fit the widened ID card."""

        panel = self.game.layout["id_card"]
        card = pygame.Rect(
            panel.x + 8,
            panel.y + 10,
            panel.width - 16,
            panel.height - 18,
        )
        available_width = card.right - 10 - (card.x + 70)
        for entry in self.game.waiting_room_queue:
            patient = entry["create"]()
            rows = [("Name", patient.name)] + list(patient.profile.items())
            rows.extend(patient.medical_info.items())
            for label, value in rows:
                self.assertLessEqual(
                    self.game.id_detail_font.size(f"{label}: {value}")[0],
                    available_width,
                )

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
        self.game.start_live_money_deduction(10, "TEST COST")
        money_started_at = self.game.money_deduction_animation["started_at"]
        self.game.open_tutorial()
        self.game.tutorial_opened_at -= 500
        self.game.close_tutorial()
        self.assertGreaterEqual(
            self.game.money_deduction_animation["started_at"],
            money_started_at + 500,
        )
        self.game.state = GameState.ENDING
        self.game.ending_started_at = pygame.time.get_ticks()
        pygame.event.post(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {
                    "button": 1,
                    "pos": self.game.game_to_window_position(
                        self.game.help_button.center
                    ),
                },
            )
        )
        self.game.handle_events()
        self.assertTrue(self.game.tutorial_open)
        self.assertEqual(self.game.get_tutorial_action_label(), "CONTINUE ENDING")
        self.game.draw()

        pygame.event.post(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {
                    "button": 1,
                    "pos": self.game.game_to_window_position(
                        self.game.tutorial_begin_button.center
                    ),
                },
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
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_r})
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
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_s})
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

    def test_f10_jump_closes_the_opening_dialogue(self):
        """A preview jump must not carry the abduction dialogue onto another screen."""

        self.game.state = GameState.TITLE
        self.game.start_intro_dialogue()
        self.assertTrue(self.game.intro_dialogue_active)

        self.game.toggle_developer_navigator()
        self.game.jump_to_developer_screen(
            self.game.get_developer_scene_index("shop")
        )

        self.assertEqual(self.game.state, GameState.SHOP)
        self.assertFalse(self.game.intro_dialogue_active)
        self.assertIsNone(self.game.intro_dialogue_started_at)

    def test_f10_navigator_builds_clean_patient_checkpoints(self):
        """Each patient shortcut should start from one complete clean deal."""

        self.game.jump_to_developer_screen(
            self.game.get_developer_scene_index("intro")
        )
        self.assertEqual(self.game.state, GameState.INTRO)
        self.game.draw()

        expected_names = [entry["create"]().name for entry in self.game.waiting_room_queue]
        for patient_number, expected_name in enumerate(expected_names, start=1):
            self.game.jump_to_developer_screen(
                self.game.get_developer_scene_index(f"patient_{patient_number}")
            )
            self.assertEqual(self.game.state, GameState.PATIENT)
            self.assertEqual(self.game.patient.name, expected_name)
            self.assertEqual(self.game.patients_called, patient_number)
            self.assertEqual(len(self.game.player.test_hand), 5)
            self.assertEqual(len(self.game.deck.contents), 43)
            self.game.draw()

        self.game.jump_to_developer_screen(
            self.game.get_developer_scene_index("patient_2")
        )
        self.assertEqual(len(self.game.deck.contents), 43)
        self.game.jump_to_developer_screen(
            self.game.get_developer_scene_index("patient_2")
        )
        self.assertEqual(len(self.game.deck.contents), 43)

    def test_test_cards_accumulate_end_of_day_operating_expenses(self):
        """Running machines should charge by rarity without settling cash early."""

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
            len(self.game.waiting_room_queue) * LIMITED_EVIDENCE_REWARD
            - get_test_cost(first_test)
            - CLINIC_OPERATING_FEE,
        )

        self.game.daily_wrong_diagnoses = 1
        self.game.daily_test_count = 16
        self.game.daily_test_expenses = 220
        self.assertLess(self.game.get_daily_pay_breakdown()[3], 0)

    def test_live_balance_animates_costs_without_double_charging_at_payday(self):
        """Tests and mistakes should lower the HUD once and remain in the recap."""

        starting_balance = self.game.player.balance
        self.game.selected_card_index = 0
        test_cost = self.game.player.get_test_cost(
            self.game.player.test_hand[0].value
        )
        self.game.run_selected_test()

        self.assertEqual(self.game.player.balance, starting_balance)
        self.assertEqual(self.game.get_live_balance(), starting_balance - test_cost)
        self.assertEqual(self.game.money_deduction_animation["amount"], test_cost)
        self.assertEqual(self.game.money_deduction_animation["reason"], "TEST COST")
        self.game.money_deduction_animation["started_at"] -= (
            self.game.money_count_duration + 1
        )
        self.assertEqual(
            self.game.get_displayed_balance(),
            starting_balance - test_cost,
        )

        self.game.state = GameState.PATIENT
        self.game.showing_diagnosis_hand = True
        self.game.selected_card_index = next(
            index
            for index, card in enumerate(self.game.player.diagnosis_hand)
            if card.value != self.game.patient.diagnosis
        )
        self.game.play_selected_diagnosis()
        expected_live_balance = (
            starting_balance - test_cost - WRONG_DIAGNOSIS_PENALTY
        )
        self.assertEqual(self.game.player.balance, starting_balance)
        self.assertEqual(self.game.get_live_balance(), expected_live_balance)
        self.assertEqual(
            self.game.money_deduction_animation["amount"],
            WRONG_DIAGNOSIS_PENALTY,
        )
        self.assertEqual(
            self.game.money_deduction_animation["reason"],
            "WRONG DIAGNOSIS",
        )

        expected_final_balance = (
            starting_balance + self.game.get_daily_pay_breakdown()[3]
        )
        self.game.settle_daily_pay()
        self.assertEqual(self.game.player.balance, expected_final_balance)
        self.assertEqual(self.game.get_live_balance(), expected_final_balance)
        self.assertIsNone(self.game.money_deduction_animation)

    def test_drawn_cards_are_charged_live_and_in_the_shift_recap(self):
        """A paid draw should remain deducted after its HUD animation finishes."""

        starting_balance = self.game.player.balance
        starting_hand = len(self.game.player.test_hand)
        starting_deck = len(self.game.deck.contents)
        starting_total = self.game.get_daily_pay_breakdown()[3]

        self.assertTrue(self.game.draw_card_from_pile())

        self.assertEqual(len(self.game.player.test_hand), starting_hand + 1)
        self.assertEqual(len(self.game.deck.contents), starting_deck - 1)
        self.assertEqual(self.game.daily_draw_expenses, DRAW_COST)
        self.assertEqual(
            self.game.get_live_balance(),
            starting_balance - DRAW_COST,
        )
        self.assertEqual(
            self.game.get_daily_pay_breakdown()[3],
            starting_total - DRAW_COST,
        )
        self.game.money_deduction_animation["started_at"] -= (
            self.game.money_count_duration + 1
        )
        self.assertEqual(
            self.game.get_displayed_balance(),
            starting_balance - DRAW_COST,
        )

    def test_paid_draw_reveals_test_hand_and_full_hand_blocks_extra_charge(self):
        """Drawn cards stay visible, while a full readable hand refuses the draw."""

        self.game.switch_active_hand(True)
        starting_hand = len(self.game.player.test_hand)
        self.assertTrue(self.game.draw_card_from_pile())
        self.assertFalse(self.game.showing_diagnosis_hand)
        self.assertEqual(len(self.game.player.test_hand), starting_hand + 1)

        while len(self.game.player.test_hand) < MAX_TEST_HAND_SIZE:
            self.assertTrue(self.game.draw_card_from_pile())
        expenses_before_block = self.game.daily_draw_expenses
        deck_before_block = len(self.game.deck.contents)

        self.assertFalse(self.game.draw_card_from_pile())
        self.assertEqual(len(self.game.player.test_hand), MAX_TEST_HAND_SIZE)
        self.assertEqual(len(self.game.deck.contents), deck_before_block)
        self.assertEqual(self.game.daily_draw_expenses, expenses_before_block)
        self.assertIn("HAND FULL", self.game.card_draw_notice)
        self.assertIsNotNone(self.game.card_draw_notice_started_at)

    def test_empty_draw_deck_is_safe_visible_and_free(self):
        """An exhausted deck should refuse draws without charging or mutating the hand."""

        self.game.deck.contents.clear()
        starting_hand = list(self.game.player.test_hand)
        starting_expenses = self.game.daily_draw_expenses
        starting_balance = self.game.get_live_balance()

        self.assertFalse(self.game.draw_card_from_pile())
        self.assertEqual(self.game.player.test_hand, starting_hand)
        self.assertEqual(self.game.daily_draw_expenses, starting_expenses)
        self.assertEqual(self.game.get_live_balance(), starting_balance)
        self.assertIn("DECK EMPTY", self.game.card_draw_notice)
        self.game.draw()

    def test_discard_safely_opens_one_slot_before_a_paid_draw(self):
        """Discarding should remove one card, lock overlapping input, then permit a draw."""

        while len(self.game.player.test_hand) < MAX_TEST_HAND_SIZE:
            self.assertTrue(self.game.draw_card_from_pile())
        discarded_card = self.game.player.test_hand[0]
        self.game.selected_card_index = 0
        expenses_before_discard = self.game.daily_draw_expenses
        deck_before_discard = len(self.game.deck.contents)

        self.assertTrue(self.game.discard_selected_test())
        self.assertEqual(len(self.game.player.test_hand), MAX_TEST_HAND_SIZE - 1)
        self.assertIs(self.game.discard_pile[-1], discarded_card)
        self.assertTrue(self.game.discard_animation["locks_input"])
        self.assertFalse(self.game.draw_card_from_pile())
        self.assertEqual(self.game.daily_draw_expenses, expenses_before_discard)
        self.assertEqual(len(self.game.deck.contents), deck_before_discard)

        self.game.discard_animation["started_at"] -= self.game.discard_animation_duration + 1
        self.game.update()
        self.assertIsNone(self.game.discard_animation)
        self.assertTrue(self.game.draw_card_from_pile())
        self.assertEqual(len(self.game.player.test_hand), MAX_TEST_HAND_SIZE)
        self.assertEqual(self.game.daily_draw_expenses, expenses_before_discard + DRAW_COST)
        self.assertEqual(len(self.game.deck.contents), deck_before_discard - 1)

    def test_rebalanced_economy_allows_one_efficient_shift_upgrade(self):
        """An efficient first shift should fund one upgrade, not a shopping spree."""

        self.assertEqual(self.game.player.balance, STARTING_BALANCE)
        self.assertEqual(STARTING_BALANCE, 100)
        self.assertEqual(DIAGNOSIS_REWARD, 40)
        self.assertEqual(LIMITED_EVIDENCE_REWARD, 25)
        self.assertEqual(WRONG_DIAGNOSIS_PENALTY, 25)
        self.assertEqual(CLINIC_OPERATING_FEE, 50)

        self.game.daily_correct_diagnoses = len(self.game.waiting_room_queue)
        self.game.daily_test_count = 4
        self.game.daily_test_expenses = 40
        self.game.daily_evidence_cases = len(self.game.waiting_room_queue)
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

    def test_perfect_bonus_requires_test_evidence_for_every_case(self):
        """Guessing every answer should not fund two first-shift upgrades."""

        patient_count = len(self.game.waiting_room_queue)
        self.game.daily_correct_diagnoses = patient_count
        self.game.daily_test_count = 0
        self.game.daily_test_expenses = 0
        self.game.daily_evidence_cases = 0

        self.assertEqual(
            self.game.get_daily_pay_breakdown(),
            (
                patient_count * LIMITED_EVIDENCE_REWARD,
                0,
                0,
                patient_count * LIMITED_EVIDENCE_REWARD
                - CLINIC_OPERATING_FEE,
            ),
        )
        projected_balance = (
            STARTING_BALANCE + self.game.get_daily_pay_breakdown()[3]
        )
        two_cheapest_upgrades = sorted(
            upgrade["cost"] for upgrade in SHOP_UPGRADES
        )[:2]
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

    def test_each_test_result_visualization_draws(self):
        """Every machine-specific diagnostic readout should render safely."""

        previews = {
            "TEMPERATURE": "Current temperature: 1700°F",
            "ULTRASOUND": "Ultrasound imaging found no unusual internal changes.",
            "X-RAY": "X-ray imaging found no fractures or visible bone damage.",
            "ALLERGY": "Severe allergic response detected from: water.",
            "BLOOD CHEMISTRY": "Lava-blood viscosity is elevated.",
            "OXYGEN SCAN": "Thermal-lung exchange is slightly slowed.",
            "TOXIN SCREEN": "No toxic compounds were detected.",
            "NEURAL SCAN": "Continuous shivering reflexes are firing.",
        }
        self.game.state = GameState.TEST_RESULT
        self.game.test_result_started_at = None
        self.game.last_test_cost = 10
        for test_name, result in previews.items():
            with self.subTest(test_name=test_name):
                self.game.last_test_name = test_name
                self.game.last_test_result = result
                self.game.draw()
                self.assertEqual(self.game.continue_button.size, (208, 44))

    def test_correct_diagnosis_returns_to_reception_without_early_payment(self):
        """A resolved early case should queue its pay and return to reception."""

        starting_balance = self.game.player.balance
        selected_test_name = self.game.player.test_hand[0].value.name
        self.game.selected_card_index = 0
        self.game.run_selected_test()

        self.assertEqual(self.game.state, GameState.TEST_RESULT)
        self.assertEqual(len(self.game.player.test_hand), 4)
        self.assertEqual(len(self.game.discard_pile), 0)
        self.assertIsNotNone(self.game.pending_test_discard)
        self.assertIn(
            selected_test_name,
            self.game.notebook.get_entries(self.game.patient),
        )

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
        self.game.selected_card_index = next(
            index
            for index, card in enumerate(self.game.player.diagnosis_hand)
            if card.value == self.game.patient.diagnosis
        )
        self.game.play_selected_diagnosis()
        self.assertEqual(self.game.state, GameState.OUTCOME)
        self.assertTrue(self.game.diagnosis_correct)
        self.assertEqual(self.game.player.balance, starting_balance)
        self.assertEqual(self.game.daily_correct_diagnoses, 1)
        self.assertFalse(self.game.last_diagnosis_supported)
        self.assertEqual(
            self.game.get_daily_pay_breakdown()[0],
            LIMITED_EVIDENCE_REWARD,
        )

        self.game.draw()
        self.game.handle_outcome_click(self.game.outcome_button.center)
        self.assertEqual(self.game.state, GameState.TITLE)
        self.assertEqual(self.game.patient.name, "Zoogy Zinglestar")
        self.assertEqual(self.game.player.balance, starting_balance)
        self.assertEqual(len(self.game.player.test_hand), 5)
        self.assertIsNotNone(self.game.queue_shift_started_at)

    def test_supported_diagnosis_earns_full_pay_and_updates_evidence_ui(self):
        """A valid clue pair should upgrade a correct case from limited to full pay."""

        self.assertEqual(self.game.get_evidence_status_display()[0], "EVIDENCE 0/2")
        self.game.notebook.add_test(
            self.game.patient,
            "TEMPERATURE",
            "Current temperature: 1700°F",
        )
        self.assertEqual(self.game.get_evidence_status_display()[0], "EVIDENCE 1/2")
        self.game.notebook.add_test(
            self.game.patient,
            "BLOOD CHEMISTRY",
            "Lava circulation is unusually slow.",
        )
        self.assertEqual(
            self.game.get_evidence_status_display()[0],
            "EVIDENCE SUFFICIENT",
        )

        self.game.open_notebook()
        self.game.draw()
        self.game.state = GameState.PATIENT
        self.game.switch_active_hand(True)
        self.game.selected_card_index = next(
            index
            for index, card in enumerate(self.game.player.diagnosis_hand)
            if card.value == self.game.patient.diagnosis
        )
        self.game.open_diagnosis_confirmation()
        self.game.draw()
        self.game.confirm_selected_diagnosis()

        self.assertTrue(self.game.diagnosis_correct)
        self.assertTrue(self.game.last_diagnosis_supported)
        self.assertEqual(self.game.daily_evidence_cases, 1)
        self.assertEqual(self.game.get_daily_pay_breakdown()[0], DIAGNOSIS_REWARD)
        self.game.draw()

    def test_incorrect_diagnosis_returns_to_test_hand(self):
        """A wrong diagnosis should be discarded before returning to test cards."""

        starting_balance = self.game.player.balance
        self.game.switch_active_hand(True)
        self.game.selected_card_index = next(
            index
            for index, card in enumerate(self.game.player.diagnosis_hand)
            if card.value != self.game.patient.diagnosis
        )
        wrong_card = self.game.player.diagnosis_hand[self.game.selected_card_index]
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

    def test_patient_walkout_requires_repeated_errors_and_finishes_discard(self):
        """Walkouts begin after repeated errors and still show med-waste disposal."""

        self.assertEqual(PATIENT_WALKOUT_THRESHOLD, 2)
        first_patient = self.game.patient.name

        with patch("gui_cards.random.random", return_value=0.0):
            self.game.switch_active_hand(True)
            self.game.selected_card_index = next(
                index
                for index, card in enumerate(self.game.player.diagnosis_hand)
                if card.value != self.game.patient.diagnosis
            )
            self.game.play_selected_diagnosis()

        self.assertFalse(self.game.patient_left)
        self.assertEqual(self.game.patient_wrong_diagnoses, 1)
        self.game.draw()
        self.game.handle_outcome_click(self.game.outcome_button.center)
        self.game.discard_animation["started_at"] -= (
            self.game.test_discard_animation_duration + 1
        )
        self.game.update()

        with patch("gui_cards.random.random", return_value=0.0):
            self.game.switch_active_hand(True)
            wrong_index = next(
                index
                for index, card in enumerate(self.game.player.diagnosis_hand)
                if card.value != self.game.patient.diagnosis
            )
            self.game.selected_card_index = wrong_index
            self.game.play_selected_diagnosis()

        self.assertTrue(self.game.patient_left)
        self.assertEqual(self.game.patient_wrong_diagnoses, 2)
        self.assertEqual(self.game.daily_patients_lost, 1)
        self.game.draw()
        self.game.handle_outcome_click(self.game.outcome_button.center)
        self.assertEqual(self.game.state, GameState.PATIENT)
        self.assertTrue(self.game.advance_case_after_discard)
        self.assertIsNotNone(self.game.discard_animation)

        self.game.discard_animation["started_at"] -= (
            self.game.test_discard_animation_duration + 1
        )
        self.game.update()

        self.assertFalse(self.game.advance_case_after_discard)
        self.assertEqual(self.game.state, GameState.TITLE)
        self.assertNotEqual(self.game.patient.name, first_patient)
        self.assertEqual(self.game.patient_wrong_diagnoses, 0)
        self.assertIsNotNone(self.game.queue_shift_started_at)

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

        self.assertEqual(self.game.state, GameState.TITLE)
        self.assertIsNotNone(self.game.end_day_shutdown_started_at)
        self.game.draw()
        self.game.end_day_shutdown_started_at = (
            pygame.time.get_ticks() - self.game.end_day_shutdown_duration - 1
        )
        self.game.update()
        self.assertEqual(self.game.state, GameState.DAY_COMPLETE)
        self.assertIsNone(self.game.end_day_shutdown_started_at)
        self.assertEqual(self.game.player.balance, starting_balance)
        self.assertEqual(
            self.game.get_daily_pay_breakdown(),
            (
                len(expected_names) * LIMITED_EVIDENCE_REWARD,
                0,
                0,
                len(expected_names) * LIMITED_EVIDENCE_REWARD
                - CLINIC_OPERATING_FEE,
            ),
        )
        self.game.draw()
        self.game.handle_day_complete_click(self.game.day_complete_button.center)
        self.assertEqual(self.game.state, GameState.SHOP)
        self.assertEqual(
            self.game.player.balance,
            starting_balance
            + len(expected_names) * LIMITED_EVIDENCE_REWARD
            - CLINIC_OPERATING_FEE,
        )
        paid_balance = self.game.player.balance
        self.game.settle_daily_pay()
        self.assertEqual(self.game.player.balance, paid_balance)

        self.game.draw()
        placeholder = self.game.get_visible_shop_upgrades()[-1]
        placeholder_rect = self.game.get_shop_upgrade_rects()[
            len(self.game.get_visible_shop_upgrades()) - 1
        ]
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
        self.assertEqual(
            len(self.game.deck.contents),
            sum(test.occurrences for test in create_test_catalog())
            - STARTING_TEST_HAND_SIZE,
        )
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

    def test_return_to_reception_restarts_interrupted_training(self):
        """Restarting during training should return to its first valid action."""

        self.game.start_guided_tutorial()
        self.game.set_guided_tutorial_step("temperature_select")
        self.game.state = GameState.PATIENT
        self.game.open_exit_confirmation()

        self.game.handle_exit_confirmation_click(
            self.game.exit_reception_button.center
        )

        self.assertEqual(self.game.state, GameState.TITLE)
        self.assertTrue(self.game.guided_tutorial_active)
        self.assertEqual(self.game.guided_tutorial_step, "call_patient")
        self.assertEqual(self.game.patients_called, 0)
        self.assertFalse(self.game.exit_confirmation_open)

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
                len(self.game.waiting_room_queue) * LIMITED_EVIDENCE_REWARD,
                2 * WRONG_DIAGNOSIS_PENALTY,
                0,
                len(self.game.waiting_room_queue) * LIMITED_EVIDENCE_REWARD
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
        temperature_index = next(
            (
                index
                for index, card in enumerate(self.game.player.test_hand)
                if card.value.name == "TEMPERATURE"
            ),
            None,
        )
        if temperature_index is None:
            self.game.player.draw(self.game.deck.draw_matching("TEMPERATURE"))
            temperature_index = len(self.game.player.test_hand) - 1
        self.game.selected_card_index = temperature_index
        before = self.game.daily_test_expenses
        self.game.run_selected_test()
        self.assertEqual(self.game.daily_test_expenses - before, 5)
        self.assertEqual(self.game.last_test_cost, 5)

    def test_shared_upgrades_stack_and_apply_to_future_draws(self):
        self.game.state = GameState.SHOP
        upgrade_ids = ("temperature", "power", "smart_cards")
        upgrades = [
            next(upgrade for upgrade in SHOP_UPGRADES if upgrade["id"] == upgrade_id)
            for upgrade_id in upgrade_ids
        ]
        purchase_cost = sum(upgrade["cost"] for upgrade in upgrades)
        self.game.player.balance = purchase_cost + 100
        for upgrade in upgrades:
            upgrade_index = SHOP_UPGRADES.index(upgrade)
            self.game.shop_scroll_row = min(
                upgrade_index // 3,
                self.game.get_shop_max_scroll_row(),
            )
            visible_index = self.game.get_visible_shop_upgrades().index(upgrade)
            self.game.handle_shop_click(
                self.game.get_shop_upgrade_rects()[visible_index].center
            )
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
        self.game.restart_game()
        self.assertEqual(self.game.player.machine_levels, {})
        self.assertEqual(self.game.player.test_discount, 0)

    def test_shop_scroll_reveals_and_installs_new_machine_upgrades(self):
        """The expanded catalog should scroll and upgrade every new test machine."""

        self.game.state = GameState.SHOP
        self.assertEqual(self.game.shop_scroll_row, 0)
        self.assertEqual(len(self.game.get_visible_shop_upgrades()), 6)

        pygame.event.post(pygame.event.Event(pygame.MOUSEWHEEL, {"y": -1}))
        self.game.handle_events()
        self.assertEqual(self.game.shop_scroll_row, 1)
        pygame.event.post(pygame.event.Event(pygame.MOUSEWHEEL, {"y": -1}))
        self.game.handle_events()
        self.assertEqual(self.game.shop_scroll_row, 2)
        final_page_ids = {
            upgrade["id"] for upgrade in self.game.get_visible_shop_upgrades()
        }
        self.assertTrue({"toxin", "neural", "power", "smart_cards"} <= final_page_ids)

        new_machine_tests = {
            "blood": BloodChemistryTest,
            "oxygen": OxygenScanTest,
            "toxin": ToxinScreenTest,
            "neural": NeuralScanTest,
        }
        total_cost = sum(
            next(
                upgrade["cost"]
                for upgrade in SHOP_UPGRADES
                if upgrade["id"] == upgrade_id
            )
            for upgrade_id in new_machine_tests
        )
        self.game.player.balance = total_cost
        for upgrade_id, test_type in new_machine_tests.items():
            upgrade = next(
                item for item in SHOP_UPGRADES if item["id"] == upgrade_id
            )
            upgrade_index = SHOP_UPGRADES.index(upgrade)
            self.game.shop_scroll_row = min(
                upgrade_index // 3,
                self.game.get_shop_max_scroll_row(),
            )
            visible_index = self.game.get_visible_shop_upgrades().index(upgrade)
            self.game.handle_shop_click(
                self.game.get_shop_upgrade_rects()[visible_index].center
            )
            self.game.handle_shop_click(self.game.shop_purchase_button.center)
            self.assertEqual(self.game.player.get_machine_level(test_type()), 2)
            self.assertEqual(
                self.game.player.get_test_cost(test_type()),
                (get_test_cost(test_type()) + 1) // 2,
            )

        self.assertEqual(self.game.player.balance, 0)

    def test_future_shift_can_load_a_new_patient_roster(self):
        """A later day can replace the queue without erasing earned upgrades."""

        next_roster = [self.game.waiting_room_queue[1]]
        self.game.player.balance = 175
        self.game.player.machine_levels["TEMPERATURE"] = 2
        self.game.start_next_shift(next_roster)
        self.assertEqual(self.game.state, GameState.TITLE)
        self.assertEqual(self.game.waiting_room_queue, next_roster)
        self.assertEqual(self.game.patients_called, 0)
        self.assertEqual(self.game.patient.name, next_roster[0]["create"]().name)
        self.assertEqual(self.game.player.balance, 175)
        self.assertEqual(self.game.player.machine_levels["TEMPERATURE"], 2)

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

    def test_long_test_card_title_renders_without_tiny_fallback(self):
        """Blood Chemistry should use the crisp wrapped-title path on compact cards."""

        header_width = 84
        self.assertGreater(
            self.game.pile_font.size("BLOOD CHEMISTRY")[0],
            header_width - 8,
        )
        self.assertLessEqual(
            self.game.compact_card_title_font.size("CHEMISTRY")[0],
            header_width - 8,
        )
        self.game.draw_fitted_card_title(
            "BLOOD CHEMISTRY",
            pygame.Rect(0, 0, header_width, 25),
        )

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
