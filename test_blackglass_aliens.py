"""Tests for the eight Blackglass Outpost patients and Puter's custom tests."""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from PlanetData import (
    BLACKGLASS_DAY_ONE_PATIENTS,
    BLACKGLASS_DAY_TWO_PATIENTS,
    BLACKGLASS_DESTINATION,
    DESTINATIONS,
    get_blackglass_destination,
    validate_blackglass_destination,
)
from Tests.catalog import BONUS_TEST_TYPES, create_bonus_test, create_test_catalog
from gui_main import CosmicClinicGUI
from gui_state import GameState

BASE_TESTS = {test.name for test in create_test_catalog()}
ALL_SLOTS = BLACKGLASS_DAY_ONE_PATIENTS + BLACKGLASS_DAY_TWO_PATIENTS
EXPECTED = {
    "snelly", "gremolda", "urnblod", "mune",
    "ramdole", "deborah", "puter", "mycicle",
}


class BlackglassPatientDataTests(unittest.TestCase):
    def test_roster_is_the_requested_eight_in_two_shifts(self):
        self.assertEqual({s.asset for s in BLACKGLASS_DAY_ONE_PATIENTS},
                         {"snelly", "gremolda", "urnblod", "mune"})
        self.assertEqual({s.asset for s in BLACKGLASS_DAY_TWO_PATIENTS},
                         {"ramdole", "deborah", "puter", "mycicle"})
        for day, slots in ((1, BLACKGLASS_DAY_ONE_PATIENTS), (2, BLACKGLASS_DAY_TWO_PATIENTS)):
            self.assertEqual(
                [s.asset for s in get_blackglass_destination(day).patient_roster],
                [s.asset for s in slots],
            )
        self.assertTrue(validate_blackglass_destination())

    def test_serials_are_unique_across_the_whole_game(self):
        serials = [s.serial for d in DESTINATIONS for s in d.alien_population]
        serials += [s.serial for s in ALL_SLOTS]
        self.assertEqual(len(serials), len(set(serials)))

    def test_every_patient_is_complete(self):
        for slot in ALL_SLOTS:
            patient = slot.create()
            with self.subTest(patient=patient.name):
                self.assertEqual(len(patient.dialogue), 3)
                self.assertTrue(patient.profile and patient.medical_info)
                names = [d.name.strip().casefold() for d in patient.diagnosis_options]
                self.assertEqual(len(names), 5)
                self.assertEqual(len(set(names)), 5)
                self.assertIn(patient.diagnosis, patient.diagnosis_options)
                self.assertTrue(BASE_TESTS <= set(patient.test_results))
                self.assertTrue(patient.bespoke_voice)

    def test_evidence_only_uses_tests_the_patient_can_actually_run(self):
        for slot in ALL_SLOTS:
            patient = slot.create()
            available = set(patient.test_results)
            with self.subTest(patient=patient.name):
                self.assertTrue(patient.diagnosis.evidence_combinations)
                for combo in patient.diagnosis.evidence_combinations:
                    self.assertTrue(combo <= available)
                    self.assertTrue(1 <= len(combo) <= 2)

    def test_each_alien_needs_at_least_one_test_and_each_day_has_a_two_test_case(self):
        for slots in (BLACKGLASS_DAY_ONE_PATIENTS, BLACKGLASS_DAY_TWO_PATIENTS):
            two_test_cases = 0
            for slot in slots:
                patient = slot.create()
                smallest = min(len(c) for c in patient.diagnosis.evidence_combinations)
                self.assertGreaterEqual(smallest, 1)
                if smallest == 2:
                    two_test_cases += 1
            self.assertGreaterEqual(two_test_cases, 1)

    def test_wrong_diagnoses_reveal_reasons_only_after_the_right_tests(self):
        for slot in ALL_SLOTS:
            patient = slot.create()
            for diagnosis in patient.diagnosis_options:
                if diagnosis is patient.diagnosis:
                    self.assertIsNone(diagnosis.rejection_reason)
                    continue
                with self.subTest(patient=patient.name, diagnosis=diagnosis.name):
                    self.assertIsNone(diagnosis.get_rejection_reason(set()))
                    self.assertTrue(diagnosis.rejection_tests)
                    self.assertTrue(
                        diagnosis.get_rejection_reason(diagnosis.rejection_tests)
                    )
                    self.assertTrue(
                        set(diagnosis.rejection_tests) <= set(patient.test_results)
                    )


class BlackglassTextFitTests(unittest.TestCase):
    """Every line must fit the compact interview, report, and outcome surfaces."""

    @classmethod
    def setUpClass(cls):
        cls.game = CosmicClinicGUI(card_seed=151)

    @classmethod
    def tearDownClass(cls):
        pygame.event.clear()

    def test_copy_fits_every_compact_medical_surface(self):
        game = self.game
        result_box = pygame.Rect(0, 0, 514, 78)
        outcome_box = pygame.Rect(0, 0, 514, 88)
        fonts = (game.body_font, game.small_font, game.card_font, game.legible_micro_font)

        def assert_fitted(text, rect, spacing):
            font, lines = game.get_fitted_wrapped_text_layout(text, fonts, rect, line_spacing=spacing)
            self.assertEqual(" ".join(lines), " ".join(text.split()), text)
            heights = [font.render(line, True, (0, 0, 0)).get_height() for line in lines]
            self.assertLessEqual(sum(heights) + max(0, len(lines) - 1) * spacing, rect.height, text)

        for slot in ALL_SLOTS:
            patient = slot.create()
            for statement in patient.dialogue:
                font, lines = game.fit_interview_statement(statement, 114, 58)
                self.assertEqual(" ".join(lines), " ".join(statement.split()), statement)
                self.assertLessEqual(len(lines) * font.get_linesize(), 58, statement)
            for result in patient.test_results.values():
                assert_fitted(result, result_box, 7)
            for diagnosis in patient.diagnosis_options:
                assert_fitted(diagnosis.treatment, outcome_box, 6)
                if diagnosis is patient.diagnosis:
                    continue
                assert_fitted(
                    f"{diagnosis.rejection_reason} Return to the examination "
                    "and collect more information.",
                    outcome_box,
                    6,
                )


class PuterCustomTestTests(unittest.TestCase):
    def setUp(self):
        self.game = CosmicClinicGUI(card_seed=11)
        self.game.finish_guided_tutorial()

    def tearDown(self):
        pygame.event.clear()

    def start_blackglass(self, day):
        game = self.game
        game.blackglass_detour = {
            "day": day,
            "return_key": DESTINATIONS[0].key,
            "return_planet": DESTINATIONS[0].planet_name,
            "entry_balance": -120,
            "destination": get_blackglass_destination(day),
        }
        game.waiting_room_queue = game.roster_for_destination(game.current_destination)
        game.load_current_destination()

    def call_patient(self, index):
        """Advance to the Nth patient the same way the reception does."""

        game = self.game
        game.patients_called = index
        game.reset_round()
        return game.patient

    def test_custom_tests_are_not_in_the_everyday_catalog(self):
        self.assertTrue(BASE_TESTS.isdisjoint(BONUS_TEST_TYPES))
        for name in BONUS_TEST_TYPES:
            self.assertEqual(create_bonus_test(name).name, name)

    def test_puter_gets_her_custom_tests_and_nobody_else_does(self):
        self.start_blackglass(2)
        game = self.game
        base_size = len(game.deck.contents) + len(game.player.test_hand)
        for index in range(4):
            patient = self.call_patient(index)
            cards = game.deck.contents + game.player.test_hand
            custom = [c for c in cards if c.value.name in BONUS_TEST_TYPES]
            if patient.name == "Puter":
                self.assertTrue(custom)
                hand = {c.value.name for c in game.player.test_hand}
                self.assertEqual(hand & set(BONUS_TEST_TYPES), set(BONUS_TEST_TYPES))
                self.assertEqual(len(game.player.test_hand), 5)
            else:
                self.assertFalse(custom, patient.name)
                self.assertEqual(len(cards), base_size)

    def test_custom_tests_run_and_file_results(self):
        self.start_blackglass(2)
        game = self.game
        self.call_patient(2)
        self.assertEqual(game.patient.name, "Puter")
        game.state = GameState.PATIENT
        for test_name in ("VIRUS SCAN", "SYSTEM LOG"):
            index = next(
                i for i, c in enumerate(game.player.test_hand) if c.value.name == test_name
            )
            game.selected_card_index = index
            game.player.balance = 100
            self.assertTrue(game.run_selected_test())
            self.assertIn(test_name, game.last_test_name)
            self.assertNotIn("does not apply", game.last_test_result)
            game.state = GameState.PATIENT
        progress = game.patient.get_evidence_progress({"VIRUS SCAN", "SYSTEM LOG"})
        self.assertEqual(progress, (2, 2))
        self.assertTrue(game.patient.has_supporting_evidence({"VIRUS SCAN", "SYSTEM LOG"}))
        self.assertFalse(game.patient.has_supporting_evidence({"VIRUS SCAN"}))

    def test_tests_that_do_not_apply_return_a_safe_default(self):
        from PatientData import create_snelly

        text = create_snelly().perform_test("VIRUS SCAN")
        self.assertIn("does not apply", text)

    def test_custom_tests_are_priced_and_explained(self):
        self.start_blackglass(2)
        self.call_patient(2)
        for card in self.game.player.test_hand:
            self.assertGreaterEqual(self.game.player.get_test_cost(card.value), 1)


class BlackglassPresentationTests(unittest.TestCase):
    def setUp(self):
        self.game = CosmicClinicGUI(card_seed=21)
        self.game.finish_guided_tutorial()
        self.game.tutorial_open = False

    def tearDown(self):
        pygame.event.clear()

    def test_every_patient_renders_in_reception_exam_and_id(self):
        game = self.game
        for day in (1, 2):
            game.blackglass_detour = {
                "day": day, "return_key": "training_orbit",
                "return_planet": "Cosmic Clinic Training Orbit",
                "entry_balance": -120, "destination": get_blackglass_destination(day),
            }
            game.waiting_room_queue = game.roster_for_destination(game.current_destination)
            game.load_current_destination()
            game.draw()
            for index in range(4):
                game.patients_called = index
                game.reset_round()
                game.state = GameState.PATIENT
                for _ in range(2):
                    game.draw()
                    game.showing_health_id = not game.showing_health_id
                game.showing_health_id = False

    def test_f10_exposes_both_blackglass_debt_shifts(self):
        """Blackglass previews all eight patients without touching live progress."""

        game = self.game
        game.state = GameState.PATIENT
        game.player.balance = 73
        live_fingerprint = game.get_campaign_state_fingerprint()

        game.toggle_developer_navigator()
        game.select_developer_day(0)
        self.assertEqual(
            [entry["create"]().name for entry in game.get_developer_roster()],
            ["Snelly Gumshoe", "Gremolda Stillwater", "Urnblod Vandermere III", "Mune"],
        )

        game.draw()
        game.handle_developer_click(game.developer_blackglass_shift_rects[1].center)
        self.assertEqual(game.developer_blackglass_day, 2)
        self.assertEqual(
            [entry["create"]().name for entry in game.get_developer_roster()],
            ["Ramdole Mellowby", "Deborah", "Puter", "Mycicle"],
        )
        self.assertEqual(
            game.get_selected_developer_destination().patient_roster,
            get_blackglass_destination(2).patient_roster,
        )

        for patient_number, expected_name in enumerate(
            ("Ramdole Mellowby", "Deborah", "Puter", "Mycicle"),
            start=1,
        ):
            game.jump_to_developer_screen(
                game.get_developer_scene_index(f"patient_{patient_number}")
            )
            self.assertEqual(game.patient.name, expected_name)
            self.assertEqual(game.blackglass_detour["day"], 2)
            self.assertEqual(len(game.player.test_hand), 5)

        game.toggle_developer_navigator()
        game.handle_developer_click(game.developer_return_button.center)
        self.assertEqual(game.get_campaign_state_fingerprint(), live_fingerprint)

    def test_speech_styles_and_levitation(self):
        from gui_patient_assets import blackglass_idle
        from PatientData import create_deborah, create_puter, create_snelly

        self.assertEqual(create_deborah().speech_style, "toe_tap")
        self.assertEqual(create_puter().speech_style, "terminal")
        self.assertIsNone(create_snelly().speech_style)
        for tick in (0, 350, 700, 1400, 2100):
            bob, _, lift = blackglass_idle("gremolda", tick)
            self.assertGreater(lift, 0)
            self.assertLess(bob, 0)  # always floating above the chair
        self.assertEqual(blackglass_idle("snelly", 0)[2], 0)
        self.assertIsNone(blackglass_idle("zorpa", 0))

    def test_deborah_does_not_speak_in_ordinary_sentences(self):
        from PatientData import create_deborah

        for line in create_deborah().dialogue:
            self.assertIn("TRANSLATION:", line)

    def test_urnblod_card_explains_the_surgery_is_illegal(self):
        from PatientData import create_urnblod

        info = " ".join(f"{k} {v}" for k, v in create_urnblod().medical_info.items())
        self.assertIn("ILLEGAL", info)

    def test_mune_treatment_is_the_requested_gentle_detonation(self):
        from PatientData import create_mune

        self.assertIn("detonation", create_mune().diagnosis.treatment)

    def test_ramdole_asks_you_not_to_tell(self):
        from PatientData import create_ramdole

        self.assertTrue(any("won't tell anyone" in line for line in create_ramdole().dialogue))


if __name__ == "__main__":
    unittest.main()
