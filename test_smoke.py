"""Smoke tests for shared game data and The Cosmic Clinic interface."""

import os
import unittest
from dataclasses import replace
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
from PatientData import (
    create_conmann,
    create_gribble,
    create_krix,
    create_oola,
    create_titus,
    create_velli,
    create_zoogy,
    create_zorpa,
)
from PlanetData import (
    DESTINATIONS,
    LUMORA_PATIENTS,
    get_destination,
    validate_destinations,
)
from Player import (
    CLINIC_OPERATING_FEE,
    DIAGNOSIS_REWARD,
    DRAW_COST,
    LIMITED_EVIDENCE_REWARD,
    MAX_TEST_HAND_SIZE,
    PATIENT_WALKOUT_THRESHOLD,
    PERFECT_DAY_BONUS,
    RETURN_PASSAGE_COST,
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
from gui_card_shop import (
    CARD_SHOP_BASE_PRICE,
    CARD_SHOP_PRICE_STEP,
    CARD_SHOP_PURPOSES,
    CardShopMixin,
)
from gui_cards import CardMixin
from gui_developer import DeveloperMixin
from gui_display import DisplayMixin
from gui_ending import (
    ROUTE_BRIEFING_DIALOGUE,
    ROUTE_COMPLETE_HEADING,
    ROUTE_COMPLETE_MESSAGE,
    EndingMixin,
)
from gui_examination import ExaminationMixin
from gui_intro import IntroMixin
from gui_main import CosmicClinicGUI, GameState
from gui_notebook import NotebookMixin
from gui_reception import ReceptionMixin
from gui_results import ResultsMixin
from gui_shop import SHOP_UPGRADES, ShopMixin
from gui_theme import TEST_SUBTITLES, WINDOW_SIZE
from gui_tutorial import TutorialMixin
from RouteController import RouteController, ShiftPerformance


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

    def test_route_controller_tracks_destinations_and_campaign_performance(self):
        """Route state should advance, aggregate shifts, and reset cleanly."""

        route = RouteController()
        self.assertEqual(route.current_destination, get_destination(1))
        self.assertEqual(route.next_destination, get_destination(2))
        self.assertEqual(route.current_patient_roster, get_destination(1).patient_roster)
        self.assertEqual(route.completed_destinations, ())

        day_one = ShiftPerformance(
            destination_key="training_orbit",
            day_number=1,
            patients_seen=4,
            correct_diagnoses=3,
            supported_diagnoses=2,
            wrong_diagnoses=1,
            patients_lost=0,
            tests_run=7,
            net_pay=35,
            ending_balance=135,
        )
        self.assertTrue(route.record_current_shift(day_one))
        self.assertFalse(route.record_current_shift(day_one))
        self.assertEqual(route.completed_destinations, (get_destination(1),))
        self.assertEqual(route.overall_performance["shifts_completed"], 1)
        self.assertEqual(route.overall_performance["correct_diagnoses"], 3)

        self.assertEqual(route.complete_current_shift(day_one), get_destination(2))
        self.assertTrue(route.arrival_pending)
        self.assertEqual(route.begin_current_shift(), get_destination(2))
        self.assertFalse(route.arrival_pending)
        self.assertEqual(route.next_destination, get_destination(3))
        self.assertFalse(route.route_is_complete)
        day_two = ShiftPerformance(
            destination_key="triska_station",
            day_number=2,
            patients_seen=4,
            correct_diagnoses=4,
            supported_diagnoses=4,
            wrong_diagnoses=0,
            patients_lost=0,
            tests_run=8,
            net_pay=75,
            ending_balance=210,
        )
        self.assertEqual(route.complete_current_shift(day_two), get_destination(3))
        self.assertEqual(route.begin_current_shift(), get_destination(3))
        self.assertIsNone(route.next_destination)
        day_three = ShiftPerformance(
            destination_key="lumora_canopy",
            day_number=3,
            patients_seen=4,
            correct_diagnoses=4,
            supported_diagnoses=3,
            wrong_diagnoses=1,
            patients_lost=0,
            tests_run=9,
            net_pay=50,
            ending_balance=260,
        )
        self.assertIsNone(route.complete_current_shift(day_three))
        self.assertTrue(route.route_is_complete)
        self.assertEqual(route.overall_performance["patients_seen"], 12)
        self.assertEqual(route.overall_performance["net_pay"], 160)

        self.assertEqual(route.reset(), get_destination(1))
        self.assertEqual(route.completed_destinations, ())
        self.assertEqual(route.shift_history, ())

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

    def test_dooski_case_requires_complementary_clues_and_preserves_other_patients(self):
        from PatientData import create_dooski, create_flersch
        patient = create_dooski()
        self.assertEqual(patient.name, 'Dooski')
        self.assertEqual(patient.profile, {
            'Species': 'Verdani', 'Occupation': 'Space Station Horticulturist',
            'Home Planet': 'Verdara',
        })
        self.assertEqual(patient.medical_info['Normal temperature'], '84°F')
        self.assertEqual(patient.medical_info['Hearing'], 'Paired inner-ear balance crystals')
        self.assertEqual(patient.medical_info['Medical alert'], 'Sensitive to strong magnetic fields')
        self.assertEqual(patient.diagnosis.name, 'Mineral-Energy Imbalance')
        self.assertEqual(len(patient.diagnosis_options), 5)
        self.assertEqual(sum(d == patient.diagnosis for d in patient.diagnosis_options), 1)
        self.assertEqual(set(patient.test_results), {t.name for t in create_test_catalog()})
        pair = {'NEURAL SCAN', 'BLOOD CHEMISTRY'}
        self.assertTrue(patient.has_supporting_evidence(pair))
        for test_name in pair:
            self.assertFalse(patient.has_supporting_evidence({test_name}))
            self.assertFalse(patient.has_supporting_evidence(set(patient.test_results) - {test_name}))
        for keyword in ('mineral', 'energy', 'imbalance'):
            self.assertNotIn(keyword, patient.test_results['BLOOD CHEMISTRY'].lower())
        for diagnosis in patient.diagnosis_options:
            self.assertTrue(diagnosis.treatment)
            if diagnosis != patient.diagnosis:
                self.assertIsNone(diagnosis.get_rejection_reason(set()))
                self.assertTrue(diagnosis.get_rejection_reason(diagnosis.rejection_tests))
        self.assertIn('Arcedian', create_zoogy().diagnosis_options[-1].rejection_reason)
        self.assertIn('Triskelid', create_flersch().diagnosis_options[3].treatment)
        self.assertIn('Verdani', patient.diagnosis_options[1].treatment)

    def test_roldi_case_requires_imaging_and_preserves_conmann(self):
        from PatientData import create_roldi
        patient = create_roldi()
        self.assertEqual(patient.name, 'Roldi')
        self.assertEqual(patient.profile['Species'], 'Craggan')
        self.assertEqual(patient.profile['Occupation'], 'Space Station Baker')
        self.assertEqual(patient.medical_info['Normal temperature'], '55°F')
        self.assertEqual(patient.medical_info['Digestion'], '3 fermentation chambers')
        self.assertIn('55°F', patient.test_results['TEMPERATURE'])
        self.assertEqual(patient.diagnosis.name, 'Fermentation Chamber Blockage')
        self.assertEqual(len(patient.dialogue), 3)
        self.assertEqual(set(patient.test_results), {t.name for t in create_test_catalog()})
        self.assertEqual(len(patient.diagnosis_options), 5)
        self.assertEqual(sum(d == patient.diagnosis for d in patient.diagnosis_options), 1)
        self.assertTrue(patient.has_supporting_evidence({'ULTRASOUND', 'X-RAY'}))
        for test_name in ('ULTRASOUND', 'X-RAY'):
            self.assertFalse(patient.has_supporting_evidence(set(patient.test_results) - {test_name}))
        self.assertIsNone(patient.diagnosis.rejection_reason)
        for diagnosis in patient.diagnosis_options:
            self.assertTrue(diagnosis.description)
            self.assertTrue(diagnosis.treatment)
            if diagnosis != patient.diagnosis:
                self.assertIsNone(diagnosis.get_rejection_reason(set()))
                self.assertTrue(diagnosis.get_rejection_reason(diagnosis.rejection_tests))
        original = create_conmann()
        self.assertEqual(original.diagnosis.name, 'Lactose Intolerance')
        blockage = next(d for d in original.diagnosis_options if d.name == patient.diagnosis.name)
        self.assertIsNot(blockage, patient.diagnosis)
        self.assertTrue(blockage.rejection_reason)

    def test_flump_case_requires_scans_and_gates_rejection_feedback(self):
        from PatientData import create_flump
        patient = create_flump()
        self.assertEqual(patient.name, 'Flump')
        self.assertEqual(patient.profile['Species'], 'Veloran')
        self.assertEqual(patient.profile['Occupation'], 'Nebula Cartographer')
        self.assertEqual(patient.medical_info['Normal temperature'], '60°F')
        self.assertEqual(patient.medical_info['Digestion'], '2 stomachs; slow metabolism')
        self.assertIn('60°F', patient.test_results['TEMPERATURE'])
        self.assertEqual(patient.diagnosis.name, 'Air-Sac Compression')
        self.assertEqual(len(patient.dialogue), 3)
        self.assertEqual(set(patient.test_results), {t.name for t in create_test_catalog()})
        self.assertEqual(len(patient.diagnosis_options), 5)
        self.assertEqual(sum(d == patient.diagnosis for d in patient.diagnosis_options), 1)
        pair = {'OXYGEN SCAN', 'ULTRASOUND'}
        self.assertTrue(patient.has_supporting_evidence(pair))
        for test_name in pair:
            self.assertFalse(patient.has_supporting_evidence(set(patient.test_results) - {test_name}))
        for diagnosis in patient.diagnosis_options:
            self.assertTrue(diagnosis.description)
            self.assertTrue(diagnosis.treatment)
            if diagnosis != patient.diagnosis:
                self.assertIsNone(diagnosis.get_rejection_reason(set()))
                self.assertTrue(diagnosis.get_rejection_reason(diagnosis.rejection_tests))
                for test_name in diagnosis.rejection_tests:
                    self.assertIsNone(diagnosis.get_rejection_reason(diagnosis.rejection_tests - {test_name}))
        self.assertEqual(create_titus().diagnosis.name, 'Acute Water Reaction')

    def test_flersch_case_and_evidence_require_both_tests(self):
        from PatientData import create_flersch
        patient = create_flersch()
        self.assertEqual(patient.profile['Occupation'], 'Triskan Council Aide')
        self.assertEqual(patient.profile['Home Planet'], 'Triska')
        self.assertEqual(patient.medical_info['Normal temperature'], '72°F')
        self.assertEqual(patient.medical_info['Vision'], '3 independently focusing eyes')
        self.assertEqual(patient.diagnosis.name, 'Motor-Nerve Degeneration')
        self.assertEqual(len(patient.diagnosis_options), 5)
        self.assertEqual(sum(d == patient.diagnosis for d in patient.diagnosis_options), 1)
        self.assertFalse(patient.has_supporting_evidence({'NEURAL SCAN'}))
        self.assertFalse(patient.has_supporting_evidence({'BLOOD CHEMISTRY'}))
        self.assertFalse(patient.has_supporting_evidence({'X-RAY', 'ULTRASOUND'}))
        self.assertTrue(patient.has_supporting_evidence({'NEURAL SCAN', 'BLOOD CHEMISTRY'}))
        blood_result = patient.test_results['BLOOD CHEMISTRY'].lower()
        self.assertNotIn('degeneration', blood_result)
        self.assertNotIn('deterioration', blood_result)
        self.assertIn('axonal-protein fragments', blood_result)
        self.assertEqual(set(patient.test_results), {t.name for t in create_test_catalog()})
        for diagnosis in patient.diagnosis_options:
            self.assertTrue(diagnosis.treatment)
            if diagnosis != patient.diagnosis:
                self.assertIsNone(diagnosis.get_rejection_reason(set()))
                self.assertTrue(diagnosis.get_rejection_reason(diagnosis.rejection_tests))

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

    def test_velli_has_complete_medical_content(self):
        """Velli should provide a complete validated Day 3 case."""

        patient = create_velli()
        test_names = {test.name for test in create_test_catalog()}

        self.assertEqual(patient.name, "Velli Mosswhistle")
        self.assertEqual(
            patient.profile,
            {
                "Species": "Luminari Floran",
                "Occupation": "Canopy Lightkeeper",
                "Home Planet": "Lumora",
            },
        )
        self.assertEqual(patient.medical_info["Normal temperature"], "78°F")
        self.assertEqual(
            patient.medical_info["Circulation"],
            "2 sap hearts; chlorophyll-rich plasma",
        )
        self.assertEqual(len(patient.dialogue), 3)
        self.assertEqual(set(patient.test_results), test_names)
        self.assertEqual(len(patient.diagnosis_options), 5)
        self.assertEqual(len({item.name for item in patient.diagnosis_options}), 5)
        self.assertEqual(
            sum(item is patient.diagnosis for item in patient.diagnosis_options),
            1,
        )

        evidence_pair = {"BLOOD CHEMISTRY", "OXYGEN SCAN"}
        self.assertTrue(patient.has_supporting_evidence(evidence_pair))
        for test_name in evidence_pair:
            self.assertFalse(patient.has_supporting_evidence({test_name}))
            self.assertFalse(
                patient.has_supporting_evidence(test_names - {test_name})
            )

        combined_results = " ".join(patient.test_results.values()).casefold()
        self.assertNotIn("photosynthetic circulation failure", combined_results)
        for diagnosis in patient.diagnosis_options:
            self.assertTrue(diagnosis.description)
            self.assertTrue(diagnosis.treatment)
            self.assertTrue(diagnosis.evidence_combinations)
            if diagnosis is patient.diagnosis:
                self.assertIsNone(diagnosis.rejection_reason)
                continue
            self.assertIsNone(diagnosis.get_rejection_reason(set()))
            self.assertTrue(diagnosis.rejection_tests)
            self.assertTrue(
                diagnosis.get_rejection_reason(diagnosis.rejection_tests)
            )
            for test_name in diagnosis.rejection_tests:
                self.assertIsNone(
                    diagnosis.get_rejection_reason(
                        diagnosis.rejection_tests - {test_name}
                    )
                )

    def test_lumora_has_a_complete_fixed_day_three_roster(self):
        """Every validated Lumora record should belong to the configured route."""

        self.assertEqual(len(LUMORA_PATIENTS), 4)
        self.assertEqual(get_destination(3).patient_roster, LUMORA_PATIENTS)
        self.assertEqual(
            [slot.create().name for slot in LUMORA_PATIENTS],
            [
                "Velli Mosswhistle",
                "Gribble Sporekin",
                "Oola Dewdrop",
                "Krix Lanternback",
            ],
        )
        self.assertEqual(
            {slot.serial for slot in LUMORA_PATIENTS},
            {"LUM-014-VM", "MYC-073-GS", "DEW-228-OD", "LTN-091-KL"},
        )

    def test_velli_has_complete_visual_metadata(self):
        """Velli should retain its approved art settings inside Day 3."""

        slot = LUMORA_PATIENTS[0]
        self.assertEqual(slot.asset, "velli")
        self.assertEqual(slot.create().name, "Velli Mosswhistle")
        self.assertEqual(slot.serial, "LUM-014-VM")
        self.assertEqual(len(slot.portrait), 4)
        self.assertGreater(slot.presentation_scale, 0)

    def test_gribble_has_complete_medical_content(self):
        """Gribble's close diagnoses must require complementary observations."""

        patient = create_gribble()
        test_names = {test.name for test in create_test_catalog()}

        self.assertEqual(patient.profile["Species"], "Mycori Sporekin")
        self.assertEqual(patient.profile["Home Planet"], "Lumora")
        self.assertEqual(patient.medical_info["Normal temperature"], "64°F")
        self.assertEqual(len(patient.dialogue), 3)
        self.assertEqual(set(patient.test_results), test_names)
        self.assertEqual(len(patient.diagnosis_options), 5)
        self.assertEqual(len({item.name for item in patient.diagnosis_options}), 5)
        self.assertEqual(
            sum(item is patient.diagnosis for item in patient.diagnosis_options),
            1,
        )
        evidence_pair = {"NEURAL SCAN", "ULTRASOUND"}
        self.assertTrue(patient.has_supporting_evidence(evidence_pair))
        for test_name in evidence_pair:
            self.assertFalse(patient.has_supporting_evidence({test_name}))
            self.assertFalse(
                patient.has_supporting_evidence(test_names - {test_name})
            )
        combined_results = " ".join(patient.test_results.values()).casefold()
        self.assertNotIn("mycelial neural cross-talk", combined_results)
        for diagnosis in patient.diagnosis_options:
            self.assertTrue(diagnosis.description)
            self.assertTrue(diagnosis.treatment)
            self.assertTrue(diagnosis.evidence_combinations)
            if diagnosis is patient.diagnosis:
                self.assertIsNone(diagnosis.rejection_reason)
                continue
            self.assertIsNone(diagnosis.get_rejection_reason(set()))
            self.assertTrue(diagnosis.rejection_tests)
            self.assertTrue(
                diagnosis.get_rejection_reason(diagnosis.rejection_tests)
            )
            for test_name in diagnosis.rejection_tests:
                self.assertIsNone(
                    diagnosis.get_rejection_reason(
                        diagnosis.rejection_tests - {test_name}
                    )
                )

    def test_oola_has_complete_medical_content(self):
        """Oola's respiratory reaction must require both immune and airflow clues."""

        patient = create_oola()
        test_names = {test.name for test in create_test_catalog()}

        self.assertEqual(patient.profile["Species"], "Dewfin Amphibian")
        self.assertEqual(patient.profile["Home Planet"], "Lumora")
        self.assertEqual(patient.medical_info["Normal temperature"], "58°F")
        self.assertEqual(len(patient.dialogue), 3)
        self.assertEqual(set(patient.test_results), test_names)
        self.assertEqual(len(patient.diagnosis_options), 5)
        self.assertEqual(len({item.name for item in patient.diagnosis_options}), 5)
        self.assertEqual(
            sum(item is patient.diagnosis for item in patient.diagnosis_options),
            1,
        )
        evidence_pair = {"ALLERGY", "OXYGEN SCAN"}
        self.assertTrue(patient.has_supporting_evidence(evidence_pair))
        for test_name in evidence_pair:
            self.assertFalse(patient.has_supporting_evidence({test_name}))
            self.assertFalse(
                patient.has_supporting_evidence(test_names - {test_name})
            )
        combined_results = " ".join(patient.test_results.values()).casefold()
        self.assertNotIn("night-spore respiratory reaction", combined_results)
        for diagnosis in patient.diagnosis_options:
            self.assertTrue(diagnosis.description)
            self.assertTrue(diagnosis.treatment)
            self.assertTrue(diagnosis.evidence_combinations)
            if diagnosis is patient.diagnosis:
                self.assertIsNone(diagnosis.rejection_reason)
                continue
            self.assertIsNone(diagnosis.get_rejection_reason(set()))
            self.assertTrue(diagnosis.rejection_tests)
            self.assertTrue(
                diagnosis.get_rejection_reason(diagnosis.rejection_tests)
            )
            for test_name in diagnosis.rejection_tests:
                self.assertIsNone(
                    diagnosis.get_rejection_reason(
                        diagnosis.rejection_tests - {test_name}
                    )
                )

    def test_krix_has_complete_medical_content(self):
        """Krix's thermal gradient and displaced core must form one clue pair."""

        patient = create_krix()
        test_names = {test.name for test in create_test_catalog()}

        self.assertEqual(patient.profile["Species"], "Lanternback Coniferid")
        self.assertEqual(patient.profile["Home Planet"], "Lumora")
        self.assertEqual(
            patient.medical_info["Normal temperature"],
            "102°F, evenly distributed",
        )
        self.assertEqual(len(patient.dialogue), 3)
        self.assertEqual(set(patient.test_results), test_names)
        self.assertEqual(len(patient.diagnosis_options), 5)
        self.assertEqual(len({item.name for item in patient.diagnosis_options}), 5)
        self.assertEqual(
            sum(item is patient.diagnosis for item in patient.diagnosis_options),
            1,
        )
        evidence_pair = {"TEMPERATURE", "X-RAY"}
        self.assertTrue(patient.has_supporting_evidence(evidence_pair))
        for test_name in evidence_pair:
            self.assertFalse(patient.has_supporting_evidence({test_name}))
            self.assertFalse(
                patient.has_supporting_evidence(test_names - {test_name})
            )
        combined_results = " ".join(patient.test_results.values()).casefold()
        self.assertNotIn("bioluminescent core instability", combined_results)
        for diagnosis in patient.diagnosis_options:
            self.assertTrue(diagnosis.description)
            self.assertTrue(diagnosis.treatment)
            self.assertTrue(diagnosis.evidence_combinations)
            if diagnosis is patient.diagnosis:
                self.assertIsNone(diagnosis.rejection_reason)
                continue
            self.assertIsNone(diagnosis.get_rejection_reason(set()))
            self.assertTrue(diagnosis.rejection_tests)
            self.assertTrue(
                diagnosis.get_rejection_reason(diagnosis.rejection_tests)
            )
            for test_name in diagnosis.rejection_tests:
                self.assertIsNone(
                    diagnosis.get_rejection_reason(
                        diagnosis.rejection_tests - {test_name}
                    )
                )

    def test_lumora_patient_copy_fits_every_compact_medical_surface(self):
        """Day 3 copy must remain complete in interviews, reports, and outcomes."""

        game = CosmicClinicGUI(card_seed=151)
        result_box = pygame.Rect(0, 0, 514, 78)
        outcome_box = pygame.Rect(0, 0, 514, 88)
        report_fonts = (
            game.body_font,
            game.small_font,
            game.card_font,
            game.legible_micro_font,
        )

        def assert_complete_and_fitted(text, fonts, rect, spacing):
            font, lines = game.get_fitted_wrapped_text_layout(
                text,
                fonts,
                rect,
                line_spacing=spacing,
            )
            self.assertEqual(" ".join(lines), " ".join(text.split()))
            heights = [
                font.render(line, True, (0, 0, 0)).get_height()
                for line in lines
            ]
            self.assertLessEqual(
                sum(heights) + max(0, len(lines) - 1) * spacing,
                rect.height,
            )

        for slot in LUMORA_PATIENTS:
            patient = slot.create()
            for statement in patient.dialogue:
                font, lines = game.fit_interview_statement(statement, 89, 54)
                self.assertEqual(" ".join(lines), " ".join(statement.split()))
                self.assertLessEqual(len(lines) * font.get_linesize(), 54)

            for result in patient.test_results.values():
                assert_complete_and_fitted(result, report_fonts, result_box, 7)

            for diagnosis in patient.diagnosis_options:
                assert_complete_and_fitted(
                    diagnosis.treatment,
                    report_fonts,
                    outcome_box,
                    6,
                )
                if diagnosis is patient.diagnosis:
                    continue
                rejection = (
                    f"{diagnosis.rejection_reason} Return to the examination "
                    "and collect more information."
                )
                assert_complete_and_fitted(
                    rejection,
                    report_fonts,
                    outcome_box,
                    6,
                )

    def test_all_lumora_patients_are_available_only_on_day_three(self):
        """Lumora's new roster must not leak into either earlier destination."""

        live_patient_names = {
            slot.create().name
            for destination in DESTINATIONS
            for slot in destination.alien_population
        }
        lumora_names = {
            create_velli().name,
            create_gribble().name,
            create_oola().name,
            create_krix().name,
        }
        earlier_names = {
            slot.create().name
            for destination in DESTINATIONS[:2]
            for slot in destination.alien_population
        }
        day_three_names = {
            slot.create().name for slot in get_destination(3).alien_population
        }
        self.assertTrue(lumora_names.isdisjoint(earlier_names))
        self.assertEqual(day_three_names, lumora_names)
        self.assertEqual(len(live_patient_names), 12)
        self.assertEqual(len(DESTINATIONS), 3)

    def test_existing_conditions_define_two_card_clue_paths(self):
        """Every diagnosis defines valid two-test evidence routes."""

        from Diagnosis import DIAGNOSES

        available_tests = {test.name for test in create_test_catalog()}
        for diagnosis in DIAGNOSES.values():
            self.assertGreaterEqual(len(diagnosis.evidence_combinations), 1)
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
    """Exercise the current playable game loop with headless Pygame."""

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

    def test_departure_requires_final_stop_and_full_price_then_ends_campaign(self):
        g = self.game
        g.state = GameState.SHOP
        g.player.balance = 500
        g.selected_shop_upgrade = "return_passage"
        g.handle_shop_upgrade_click(g.shop_purchase_button.center)
        self.assertEqual(g.player.balance, 500)
        self.assertNotIn("return_passage", g.purchased_shop_upgrades)
        g.route.select_day(3)
        g.player.balance = 399
        g.handle_shop_upgrade_click(g.shop_purchase_button.center)
        self.assertEqual(g.player.balance, 399)
        g.player.balance = 400
        g.handle_shop_upgrade_click(g.shop_purchase_button.center)
        self.assertEqual(g.player.balance, 0)
        self.assertIn("return_passage", g.purchased_shop_upgrades)
        self.assertEqual(g.state, GameState.FINAL)
        self.assertFalse(g.homecoming_started)
        g.handle_final_screen_click(g.final_replay_button.center)
        self.assertEqual(g.state, GameState.TITLE)
        self.assertEqual(g.day_number, 3)
        self.assertEqual(g.player.balance, 0)
        self.assertTrue(g.has_return_passage())
        g.state = GameState.SHOP
        g.handle_shop_click(g.shop_button.center)
        self.assertEqual(g.state, GameState.FINAL)
        g.handle_final_screen_click(g.final_quit_button.center)
        self.assertEqual(g.state, GameState.ENDING)
        self.assertTrue(g.homecoming_started)
        pygame.event.post(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=(100, 100),
        ))
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        g.handle_events()
        self.assertEqual(g.state, GameState.ENDING)
        for progress in (0, 0.2, 0.4, 0.6, 0.8, 0.99):
            g.ending_started_at = pygame.time.get_ticks() - round(progress * g.ending_duration)
            g.draw_ending_screen()
        g.ending_started_at = pygame.time.get_ticks() - g.ending_duration
        g.update_ending_sequence()
        g.draw_final_screen()
        self.assertEqual(g.state, GameState.FINAL)
        g.handle_final_screen_click(g.final_replay_button.center)
        self.assertEqual(g.day_number, 1)
        self.assertNotIn("return_passage", g.purchased_shop_upgrades)

    def test_machine_shelf_has_both_purchase_paths_and_blocks_second_choice(self):
        g = self.game
        g.player.balance = 100
        g.state = GameState.SHOP
        visible = g.get_visible_shop_upgrades()
        self.assertTrue(all(item.get("path") != "free_use" for item in visible))
        buttons = g.get_machine_path_buttons(g.get_shop_upgrade_rects()[0])
        g.handle_shop_click(buttons[1].center)
        self.assertIn("temperature_free", g.purchased_shop_upgrades)
        self.assertEqual(g.player.balance, 75)
        g.handle_shop_click(buttons[0].center)
        self.assertEqual(g.player.balance, 75)
        self.assertNotIn("temperature", g.purchased_shop_upgrades)
        g.draw_shop_screen()
        g.handle_shop_click(g.get_machine_path_buttons(g.get_shop_upgrade_rects()[1])[0].center)
        self.assertIn("xray", g.purchased_shop_upgrades)
        self.assertEqual(g.player.balance, 50)

    def test_free_machine_allowance_persists_between_patients_and_resets_per_shift(self):
        g = self.game
        g.player.balance = 1000
        g.selected_shop_upgrade = "temperature_free"
        g.handle_shop_upgrade_click(g.shop_purchase_button.center)
        self.assertIn("TEMPERATURE", g.player.free_test_machines)
        test = TemperatureTest()
        self.assertEqual(g.player.get_test_cost(test), 0)
        self.assertEqual(g.player.get_test_cost(test), 0)  # previews don't consume it
        g.player.consume_test_use(test)
        self.assertEqual(g.player.get_test_cost(test), 10)
        g.reset_round()
        self.assertEqual(g.player.get_test_cost(test), 10)
        balance = g.player.balance
        g.selected_shop_upgrade = "temperature"
        g.handle_shop_upgrade_click(g.shop_purchase_button.center)
        self.assertEqual(g.player.balance, balance)
        self.assertNotIn("temperature", g.purchased_shop_upgrades)
        g.reset_day()
        self.assertEqual(g.player.get_test_cost(test), 0)

    def test_efficiency_blocks_free_path_and_running_consumes_only_matching_allowance(self):
        g = self.game
        g.player.balance = 1000
        g.selected_shop_upgrade = "temperature"
        g.handle_shop_upgrade_click(g.shop_purchase_button.center)
        balance = g.player.balance
        g.selected_shop_upgrade = "temperature_free"
        g.handle_shop_upgrade_click(g.shop_purchase_button.center)
        self.assertEqual(g.player.balance, balance)
        self.assertEqual(g.player.get_test_cost(TemperatureTest()), 5)
        card = g.player.test_hand[0]
        g.player.free_test_machines.add(card.value.name)
        g.player.free_test_machines.add("UNRELATED")
        g.selected_card_index = 0
        expenses = g.daily_test_expenses
        g.run_selected_test()
        self.assertEqual(g.last_test_cost, 0)
        self.assertEqual(g.daily_test_expenses, expenses)
        self.assertIn(card.value.name, g.player.free_tests_used)
        self.assertNotIn("UNRELATED", g.player.free_tests_used)

    def test_recycler_exchanges_once_free_and_recharges_next_patient(self):
        game = self.game
        game.purchased_shop_upgrades.add("recycler")
        game.selected_card_index = 0
        old = game.player.test_hand[0]
        replacement = game.deck.contents[-1]
        balance = game.player.balance
        expenses = game.daily_draw_expenses
        hand_size = len(game.player.test_hand)
        self.assertTrue(game.recycle_selected_test())
        self.assertIs(game.player.test_hand[0], replacement)
        self.assertIn(old, game.discard_pile)
        self.assertEqual(len(game.player.test_hand), hand_size)
        self.assertEqual(game.player.balance, balance)
        self.assertEqual(game.daily_draw_expenses, expenses)
        game.selected_card_index = 0
        self.assertFalse(game.recycle_selected_test())
        game.reset_round()
        self.assertFalse(game.recycler_used)
        self.assertIn("recycler", game.purchased_shop_upgrades)
        game.selected_card_index = 0
        self.assertTrue(game.recycle_selected_test())

    def test_recycler_requires_purchase_and_preserves_use_when_empty(self):
        game = self.game
        game.selected_card_index = 0
        self.assertFalse(game.recycle_selected_test())
        game.purchased_shop_upgrades.add("recycler")
        game.deck.contents.clear()
        before = list(game.player.test_hand)
        self.assertFalse(game.recycle_selected_test())
        self.assertFalse(game.recycler_used)
        self.assertEqual(game.player.test_hand, before)

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
        self.assertIsInstance(self.game, CardShopMixin)
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
        self.assertEqual(self.game.draw_card_shop_overlay.__module__, "gui_card_shop")
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
        ufo_width, ufo_height = self.game.intro_ufo_surface.get_size()
        for edge_point in (
            (ufo_width // 2, 0),
            (ufo_width // 2, ufo_height - 1),
            (0, ufo_height // 2),
            (ufo_width - 1, ufo_height // 2),
        ):
            self.assertEqual(self.game.intro_ufo_surface.get_at(edge_point).a, 0)
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

        for expected_dialogue_index in range(1, len(self.game.patient.dialogue)):
            self.game.handle_guided_tutorial_click(self.game.layout["alien"].center)
            self.assertEqual(self.game.patient_dialogue_index, expected_dialogue_index)
            self.assertEqual(self.game.guided_tutorial_step, "symptom")
        self.assertEqual(
            self.game.notebook.get_interview(self.game.patient),
            self.game.patient.dialogue,
        )
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

        # Force the missing-clue branch so training also teaches the targeted
        # Card Shop rather than relying on a lucky opening hand.
        blood_cards = [
            card
            for card in self.game.player.test_hand
            if card.value.name == "BLOOD CHEMISTRY"
        ]
        for card in blood_cards:
            self.game.player.test_hand.remove(card)
        self.game.deck.return_cards(blood_cards)
        self.game.refresh_hand_layout()
        self.game.handle_guided_tutorial_click((1090, 680))
        self.assertEqual(self.game.guided_tutorial_step, "card_shop_open")
        self.game.handle_guided_tutorial_click(self.game.card_shop_button.center)
        self.assertTrue(self.game.card_shop_open)
        self.assertEqual(self.game.guided_tutorial_step, "card_shop_select")
        self.game.handle_guided_tutorial_click(
            self.game.get_blood_chemistry_shop_rect().center
        )
        self.assertEqual(self.game.selected_card_shop_test, "BLOOD CHEMISTRY")
        self.assertEqual(self.game.guided_tutorial_step, "card_shop_buy")
        self.game.handle_guided_tutorial_click(self.game.card_shop_buy_button.center)
        self.assertFalse(self.game.card_shop_open)
        self.assertEqual(self.game.guided_tutorial_step, "blood_select")

        blood_index = self.game.get_blood_chemistry_card_index()
        self.game.handle_guided_tutorial_click(self.game.card_rects[blood_index].center)
        self.assertEqual(self.game.guided_tutorial_step, "blood_run")
        selected = self.game.get_selected_card_rect(self.game.selected_card_index)
        self.game.handle_guided_tutorial_click(
            self.game.get_run_test_button(selected).center
        )
        self.assertEqual(self.game.state, GameState.TEST_RESULT)
        self.assertEqual(self.game.daily_test_count, 2)
        self.game.test_result_started_at -= self.game.test_result_reveal_duration + 1
        self.game.draw()
        self.game.handle_guided_tutorial_click(self.game.continue_button.center)
        self.assertEqual(self.game.guided_tutorial_step, "second_note_transfer")

        self.game.note_transfer_animation["started_at"] -= self.game.note_transfer_animation_duration + 1
        self.game.update()
        self.game.notebook_attention_started_at -= self.game.notebook_attention_duration + 1
        self.game.update()
        self.game.discard_animation["started_at"] -= self.game.test_discard_animation_duration + 1
        self.game.update()
        self.game.update()
        self.assertEqual(self.game.guided_tutorial_step, "second_open_notebook")
        self.game.handle_guided_tutorial_click(self.game.layout["notebook"].center)
        self.assertEqual(self.game.guided_tutorial_step, "second_review_notebook")
        self.game.handle_guided_tutorial_click((1090, 680))
        self.assertEqual(self.game.guided_tutorial_step, "diagnosis_folder")
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
        self.assertEqual(self.game.daily_evidence_cases, 1)
        self.assertTrue(self.game.last_diagnosis_supported)
        self.assertEqual(self.game.daily_card_shop_expenses, CARD_SHOP_BASE_PRICE)
        self.assertIsNotNone(self.game.help_attention_started_at)
        self.assertFalse(self.game.help_attention_seen)
        self.game.draw()
        pygame.event.post(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {
                    "button": 1,
                    "pos": self.game.game_to_window_position((10, 10)),
                },
            )
        )
        self.game.handle_events()
        self.assertIsNone(self.game.help_attention_started_at)
        self.assertTrue(self.game.help_attention_seen)

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
        self.assertIn("CARD SHOP", help_copy)
        self.assertIn("CARRYOVER", help_copy)
        self.assertIn("PLANET ROUTE", help_copy)
        self.assertIn("unused cards return", help_copy)
        self.assertIn("carry between planets", help_copy)
        self.assertIn("new destination", help_copy)
        self.assertIn("different aliens and conditions", help_copy)
        self.assertIn("Lumora", help_copy)
        self.assertIn("Day 3", help_copy)
        self.assertIn("H Help", self.game.get_help_controls())
        self.assertNotIn("F10", self.game.get_help_controls())

        self.game.route.select_day(3)
        self.game.load_current_destination()
        self.assertIn("Lumora Canopy Haven", self.game.get_help_context()[1])

        self.assertFalse(self.game.tutorial_open)
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_h))
        self.game.handle_events()
        self.assertTrue(self.game.tutorial_open)
        self.assertTrue(self.game.help_attention_seen)
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_h))
        self.game.handle_events()
        self.assertFalse(self.game.tutorial_open)

    def test_guided_tutorial_cannot_restart_after_leaving_training_orbit(self):
        """Later planets should retain Help without replaying Zorpa's training."""

        self.game.start_guided_tutorial()
        self.assertTrue(self.game.guided_tutorial_active)
        self.game.finish_guided_tutorial()
        self.game.begin_ending_sequence()
        self.game.finish_ending_sequence()
        self.game.handle_arrival_click(self.game.arrival_begin_button.center)

        self.assertEqual(self.game.day_number, 2)
        self.assertEqual(self.game.current_destination, get_destination(2))
        self.assertFalse(self.game.guided_tutorial_active)
        self.assertFalse(self.game.start_guided_tutorial())
        self.assertFalse(self.game.guided_tutorial_active)

        self.game.open_tutorial()
        self.assertTrue(self.game.tutorial_open)
        self.assertIn("carry between planets", " ".join(
            detail for _heading, detail in self.game.get_help_rules()
        ))

    def test_tutorial_spotlights_have_clickable_hitboxes_and_wrapped_text(self):
        """Highlighted reading targets and lifted card edges should never feel inert."""

        self.game.start_guided_tutorial()
        self.game.state = GameState.PATIENT

        self.game.set_guided_tutorial_step("symptom")
        symptom_target = self.game.get_guided_tutorial_target()
        self.assertEqual(symptom_target.size, (105, 84))
        self.assertEqual(self.game.patient_dialogue_index, 0)
        for expected_dialogue_index in range(1, len(self.game.patient.dialogue)):
            self.game.handle_guided_tutorial_click(self.game.layout["alien"].center)
            self.assertEqual(self.game.patient_dialogue_index, expected_dialogue_index)
            self.assertEqual(self.game.guided_tutorial_step, "symptom")
            prompt, _prompt_rect, _click_anywhere = (
                self.game.get_guided_tutorial_prompt()
            )
            self.assertIn(
                f"INTERVIEW {expected_dialogue_index + 1}/{len(self.game.patient.dialogue)}",
                prompt,
            )
        self.game.handle_guided_tutorial_click(self.game.layout["alien"].center)
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

        for report_step in ("test_result", "second_test_result"):
            self.game.set_guided_tutorial_step(report_step)
            self.assertIsNone(self.game.get_guided_tutorial_target())

        for transfer_step in ("note_transfer", "second_note_transfer"):
            self.game.set_guided_tutorial_step(transfer_step)
            self.assertIsNone(self.game.get_guided_tutorial_target())
            self.assertIsNone(self.game.get_guided_tutorial_prompt())

        self.game.open_notebook()
        self.game.guided_tutorial_active = True
        self.game.set_guided_tutorial_step("review_notebook")
        self.game.handle_guided_tutorial_click((1090, 680))
        self.assertIn(
            self.game.guided_tutorial_step,
            ("blood_select", "card_shop_open"),
        )

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
            "open_notebook",
            "review_notebook",
            "card_shop_open",
            "card_shop_select",
            "card_shop_buy",
            "blood_select",
            "blood_run",
            "second_test_result",
            "second_open_notebook",
            "second_review_notebook",
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

    def test_card_shop_opens_as_a_modal_and_resets_for_each_patient(self):
        """The Card Shop should block the workspace and reset its rising price."""

        self.assertFalse(self.game.card_shop_open)
        self.game.draw()
        self.game.handle_patient_click(self.game.card_shop_button.center)
        self.assertTrue(self.game.card_shop_open)
        self.assertIsNone(self.game.selected_card_index)
        self.assertEqual(self.game.get_card_shop_price(), CARD_SHOP_BASE_PRICE)
        self.assertEqual(len(self.game.get_card_shop_slot_rects()), 8)

        showing_health_id = self.game.showing_health_id
        self.game.handle_patient_click(self.game.layout["id_card"].center)
        self.assertEqual(self.game.showing_health_id, showing_health_id)
        self.assertTrue(self.game.card_shop_open)

        self.game.handle_patient_click(self.game.card_shop_close_button.center)
        self.assertFalse(self.game.card_shop_open)

        self.game.handle_patient_click(self.game.card_shop_button.center)
        self.game.card_shop_patient_purchases = 2
        self.game.reset_round()
        self.assertFalse(self.game.card_shop_open)
        self.assertEqual(self.game.card_shop_patient_purchases, 0)
        self.assertEqual(self.game.get_card_shop_price(), CARD_SHOP_BASE_PRICE)

    def test_card_shop_purchase_uses_live_inventory_and_rising_prices(self):
        """Targeted cards should leave the deck, enter the hand, and cost more."""

        selected = next(
            test
            for test in self.game.card_shop_catalog
            if self.game.get_card_shop_inventory_count(test.name) >= 2
        )
        self.game.selected_card_shop_test = selected.name
        purpose, details = self.game.get_card_shop_information()
        self.assertEqual(purpose, CARD_SHOP_PURPOSES[selected.name])
        self.assertIn(f"RUN TEST: ${self.game.player.get_test_cost(selected)}", details)
        inventory_before = self.game.get_card_shop_inventory_count(selected.name)
        hand_before = len(self.game.player.test_hand)
        balance_before = self.game.get_live_balance()
        pay_before = self.game.get_daily_pay_breakdown()[3]

        self.assertTrue(self.game.purchase_selected_card_shop_test())
        self.assertEqual(len(self.game.player.test_hand), hand_before + 1)
        self.assertEqual(
            self.game.get_card_shop_inventory_count(selected.name),
            inventory_before - 1,
        )
        self.assertEqual(self.game.daily_card_shop_expenses, CARD_SHOP_BASE_PRICE)
        self.assertEqual(self.game.daily_card_shop_purchases, 1)
        self.assertEqual(
            self.game.card_shop_notice,
            f"{selected.name.title()} added to your hand.",
        )
        self.assertIsNotNone(self.game.card_shop_notice_started_at)
        self.assertIn(
            "NEXT CARD $20",
            self.game.get_card_shop_purchase_state()[1],
        )
        self.assertEqual(
            self.game.get_card_shop_price(),
            CARD_SHOP_BASE_PRICE + CARD_SHOP_PRICE_STEP,
        )
        self.assertEqual(
            self.game.get_live_balance(),
            balance_before - CARD_SHOP_BASE_PRICE,
        )
        self.assertEqual(
            self.game.get_daily_pay_breakdown()[3],
            pay_before - CARD_SHOP_BASE_PRICE,
        )

        self.assertTrue(self.game.purchase_selected_card_shop_test())
        self.assertEqual(
            self.game.daily_card_shop_expenses,
            CARD_SHOP_BASE_PRICE + CARD_SHOP_BASE_PRICE + CARD_SHOP_PRICE_STEP,
        )
        self.assertEqual(self.game.daily_card_shop_purchases, 2)
        self.assertEqual(self.game.get_card_shop_price(), 20)

    def test_card_shop_blocks_full_hand_sold_out_stock_and_low_funds(self):
        """Failed targeted purchases must never consume cards or charge money."""

        selected = self.game.card_shop_catalog[0]
        self.game.selected_card_shop_test = selected.name
        while len(self.game.player.test_hand) < MAX_TEST_HAND_SIZE:
            self.game.player.draw(self.game.deck.draw())
        deck_before = len(self.game.deck.contents)
        self.assertFalse(self.game.purchase_selected_card_shop_test())
        self.assertEqual(len(self.game.deck.contents), deck_before)
        self.assertEqual(self.game.daily_card_shop_expenses, 0)
        self.assertIn("Hand Full", self.game.card_shop_message)

        self.game.player.test_hand.pop()
        self.game.deck.contents = [
            card
            for card in self.game.deck.contents
            if card.value.name != selected.name
        ]
        deck_before = len(self.game.deck.contents)
        self.assertFalse(self.game.purchase_selected_card_shop_test())
        self.assertEqual(len(self.game.deck.contents), deck_before)
        self.assertEqual(self.game.daily_card_shop_expenses, 0)
        self.assertIn("Sold Out", self.game.card_shop_message)

        available = next(
            test
            for test in self.game.card_shop_catalog
            if self.game.get_card_shop_inventory_count(test.name)
        )
        self.game.selected_card_shop_test = available.name
        self.game.player.balance = CARD_SHOP_BASE_PRICE - 1
        deck_before = len(self.game.deck.contents)
        self.assertFalse(self.game.purchase_selected_card_shop_test())
        self.assertEqual(len(self.game.deck.contents), deck_before)
        self.assertEqual(self.game.daily_card_shop_expenses, 0)
        self.assertIn("Need $1 More", self.game.card_shop_message)

    def test_card_shop_explains_every_test_and_draw_stack_stays_in_its_tray(self):
        """Every shop option needs guidance and every deck layer must remain clipped."""

        catalog_names = {test.name for test in self.game.card_shop_catalog}
        self.assertEqual(set(CARD_SHOP_PURPOSES), catalog_names)

        tray = self.game.get_draw_deck_tray().inflate(-3, -3)
        for remaining in (1, 5, 12, len(self.game.deck.contents)):
            stack = self.game.get_draw_deck_stack_rects(remaining)
            self.assertTrue(stack)
            self.assertTrue(all(tray.contains(rect) for rect in stack))
            self.assertTrue(tray.contains(stack[0].move(0, -4)))
            self.assertTrue(
                all(not rect.colliderect(self.game.card_shop_button) for rect in stack)
            )

    def test_patient_id_details_fit_the_larger_readable_font(self):
        """Wrapped ID details should stay readable and above the flip control."""

        _card, _portrait, detail_area = self.game.get_id_card_layout()
        available_width = detail_area.width
        available_height = detail_area.height
        all_destination_entries = [
            entry
            for destination in DESTINATIONS
            for entry in self.game.roster_for_destination(destination)
        ]
        for entry in all_destination_entries:
            patient = entry["create"]()
            for rows in (
                [("Name", patient.name)] + list(patient.profile.items()),
                list(patient.medical_info.items()),
            ):
                wrapped_lines = []
                for label, value in rows:
                    wrapped_lines.extend(
                        self.game.wrap_text(
                            f"{label}: {value}",
                            self.game.id_detail_font,
                            available_width,
                        )
                    )
                self.assertTrue(wrapped_lines)
                self.assertTrue(all(
                    self.game.id_detail_font.size(line)[0] <= available_width
                    for line in wrapped_lines
                ))
                self.assertLessEqual(
                    len(wrapped_lines) * self.game.id_detail_font.get_linesize(),
                    available_height,
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
        self.assertEqual(self.game.developer_navigator_level, "destinations")
        self.assertEqual(
            len(self.game.get_developer_day_rects()),
            len(self.game.destinations),
        )
        self.game.draw()

        pygame.event.post(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_1})
        )
        self.game.handle_events()
        self.assertEqual(self.game.developer_navigator_level, "screens")
        pygame.event.post(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_c})
        )
        self.game.handle_events()
        self.assertEqual(self.game.state, GameState.DAY_COMPLETE)
        self.assertFalse(self.game.developer_navigator_open)
        self.assertEqual(self.game.daily_correct_diagnoses, 4)
        self.assertEqual(self.game.get_daily_pay_breakdown()[3], 75)
        self.game.draw()

        pygame.event.post(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_F10})
        )
        self.game.handle_events()
        pygame.event.post(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_1})
        )
        self.game.handle_events()
        pygame.event.post(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_s})
        )
        self.game.handle_events()
        self.assertEqual(self.game.state, GameState.SHOP)
        self.assertTrue(self.game.daily_payout_applied)
        self.assertEqual(self.game.player.balance, 175)
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

        self.game.developer_selected_day = 3
        self.game.jump_to_developer_screen(
            self.game.get_developer_scene_index("arrival")
        )
        self.assertEqual(self.game.state, GameState.ARRIVAL)
        self.assertEqual(self.game.current_destination, get_destination(3))
        self.assertTrue(self.game.route.arrival_pending)
        self.assertEqual(
            self.game.route.completed_destinations,
            (get_destination(1), get_destination(2)),
        )
        self.game.draw()

        self.game.jump_to_developer_screen(
            self.game.get_developer_scene_index("final")
        )
        self.assertEqual(self.game.state, GameState.FINAL)
        self.assertEqual(self.game.current_destination, get_destination(3))
        self.assertTrue(self.game.route.route_is_complete)
        self.game.draw()

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

    def test_f10_navigator_selects_day_two_without_duplicating_checkpoints(self):
        """Destination selection should open only Day 2's valid checkpoints."""

        self.game.toggle_developer_navigator()
        self.assertTrue(self.game.developer_navigator_open)
        self.assertEqual(self.game.developer_navigator_level, "destinations")
        self.game.handle_developer_click(self.game.get_developer_day_rects()[1].center)
        self.assertEqual(self.game.developer_selected_day, 2)
        self.assertEqual(self.game.developer_navigator_level, "screens")
        self.assertTrue(self.game.developer_navigator_open)
        self.assertEqual(
            [entry[1] for entry in self.game.get_developer_screen_entries()],
            [
                "arrival",
                "reception",
                "patient_1",
                "patient_2",
                "patient_3",
                "patient_4",
                "recap",
                "shop",
                "ending",
            ],
        )
        self.assertIn(
            "FLERSCH",
            self.game.get_developer_checkpoint_label("patient_1", "PATIENT 1"),
        )

        self.game.handle_developer_click(self.game.get_developer_screen_rects()[2].center)
        self.assertFalse(self.game.developer_navigator_open)
        self.assertEqual(self.game.day_number, 2)
        self.assertEqual(self.game.state, GameState.PATIENT)
        self.assertEqual(self.game.patient.name, "Flersch")
        self.assertEqual(len(self.game.player.test_hand), 5)
        self.game.draw()
        self.game.jump_to_developer_screen(
            self.game.get_developer_scene_index("patient_2")
        )
        self.assertEqual(self.game.patient.name, "Dooski")
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

    def test_unused_hand_returns_to_deck_but_consumed_cards_stay_spent(self):
        """Changing patients should preserve unused stock without restoring used tests."""

        deck_size = len(self.game.deck.contents)
        self.assertEqual(len(self.game.player.test_hand), STARTING_TEST_HAND_SIZE)

        self.game.reset_round()
        self.assertEqual(len(self.game.deck.contents), deck_size)
        self.assertEqual(len(self.game.player.test_hand), STARTING_TEST_HAND_SIZE)

        self.game.selected_card_index = 0
        self.game.run_selected_test()
        self.assertEqual(len(self.game.player.test_hand), STARTING_TEST_HAND_SIZE - 1)
        self.game.reset_round()
        self.assertEqual(len(self.game.deck.contents), deck_size - 1)
        self.assertEqual(len(self.game.player.test_hand), STARTING_TEST_HAND_SIZE)

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

    def test_rebalanced_economy_allows_early_investment(self):
        """An efficient shift can fund several investments at the new prices."""

        self.assertEqual(self.game.player.balance, STARTING_BALANCE)
        self.assertEqual(STARTING_BALANCE, 100)
        self.assertEqual(DIAGNOSIS_REWARD, 50)
        self.assertEqual(LIMITED_EVIDENCE_REWARD, 10)
        self.assertEqual(WRONG_DIAGNOSIS_PENALTY, 35)
        self.assertEqual(CLINIC_OPERATING_FEE, 50)

        self.game.daily_correct_diagnoses = len(self.game.waiting_room_queue)
        self.game.daily_test_count = 8
        self.game.daily_test_expenses = 100
        self.game.daily_evidence_cases = len(self.game.waiting_room_queue)
        self.assertEqual(
            self.game.get_daily_pay_breakdown(),
            (200, 0, PERFECT_DAY_BONUS, 75),
        )

        projected_balance = STARTING_BALANCE + 75
        two_cheapest_upgrades = sorted(
            upgrade["cost"] for upgrade in SHOP_UPGRADES
        )[:2]
        self.assertLessEqual(two_cheapest_upgrades[0], projected_balance)
        self.assertLessEqual(sum(two_cheapest_upgrades), projected_balance)

    def test_perfect_bonus_requires_test_evidence_for_every_case(self):
        """Unsupported answers lose money and cannot earn the perfect bonus."""

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
        self.assertLess(projected_balance, STARTING_BALANCE)

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

        status, status_color = self.game.get_evidence_status_display()
        self.assertEqual(status, "EVIDENCE 0/2")
        self.assertEqual(status_color, (112, 70, 145))
        self.game.notebook.add_test(
            self.game.patient,
            "TEMPERATURE",
            "Current temperature: 1700°F",
        )
        status, status_color = self.game.get_evidence_status_display()
        self.assertEqual(status, "EVIDENCE 1/2")
        self.assertEqual(status_color, (171, 101, 30))
        self.game.notebook.add_test(
            self.game.patient,
            "BLOOD CHEMISTRY",
            "Lava circulation is unusually slow.",
        )
        status, status_color = self.game.get_evidence_status_display()
        self.assertEqual(status, "EVIDENCE SUFFICIENT")
        self.assertEqual(status_color, (24, 122, 87))
        self.assertEqual(
            self.game.get_diagnosis_clue_display()[0],
            "2/2 CLUES COLLECTED",
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
        self.game.player.balance = placeholder["cost"] - 1
        self.game.handle_shop_click(self.game.shop_purchase_button.center)
        self.assertNotIn(placeholder["id"], self.game.purchased_shop_upgrades)

        # Supply the exact purchase price to exercise buying and the ending.
        self.game.player.balance = placeholder["cost"]
        self.game.handle_shop_click(self.game.shop_purchase_button.center)
        self.assertIn(placeholder["id"], self.game.purchased_shop_upgrades)
        self.assertEqual(self.game.player.balance, 0)

        self.game.handle_shop_click(self.game.shop_button.center)
        self.assertEqual(self.game.state, GameState.ROUTE_BRIEFING)
        self.assertEqual(len(ROUTE_BRIEFING_DIALOGUE), 3)
        for _ in ROUTE_BRIEFING_DIALOGUE:
            self.game.advance_route_briefing()
        self.assertEqual(self.game.state, GameState.ENDING)
        self.game.draw()
        self.game.ending_started_at = (
            pygame.time.get_ticks() - self.game.ending_duration - 1
        )
        self.game.update()
        self.assertEqual(self.game.state, GameState.ARRIVAL)
        self.game.draw()
        self.assertEqual(self.game.daily_correct_diagnoses, len(expected_names))
        self.assertIn(placeholder["id"], self.game.purchased_shop_upgrades)

        self.game.handle_arrival_click(self.game.arrival_begin_button.center)
        self.assertEqual(self.game.state, GameState.TITLE)
        self.assertEqual(self.game.patients_called, 0)
        self.assertEqual(self.game.patient.name, "Flersch")
        self.assertEqual(self.game.day_number, 2)
        self.assertEqual(self.game.player.balance, 0)
        self.assertEqual(
            len(self.game.deck.contents),
            sum(test.occurrences for test in create_test_catalog())
            - STARTING_TEST_HAND_SIZE,
        )
        self.assertEqual(self.game.daily_correct_diagnoses, 0)
        self.assertEqual(self.game.daily_wrong_diagnoses, 0)
        self.assertIsNone(self.game.selected_shop_upgrade)
        self.assertIn(placeholder["id"], self.game.purchased_shop_upgrades)

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
        self.assertEqual(self.game.player.balance, 725)
        self.assertEqual(self.game.daily_correct_diagnoses, 0)
        self.assertIn(
            SHOP_UPGRADES[0]["id"],
            self.game.purchased_shop_upgrades,
        )
        self.assertEqual(self.game.current_destination, get_destination(2))
        self.assertEqual(
            self.game.route.completed_destinations,
            (get_destination(1),),
        )
        self.assertEqual(len(self.game.route.shift_history), 1)
        self.assertFalse(self.game.route.arrival_pending)

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

    def test_planet_catalog_defines_valid_consecutive_campaign_days(self):
        """Planet metadata should own all fixed rosters in campaign order."""

        self.assertTrue(validate_destinations())
        self.assertEqual(
            [destination.day_number for destination in DESTINATIONS],
            [1, 2, 3],
        )
        self.assertEqual(
            [destination.planet_name for destination in DESTINATIONS],
            [
                "Cosmic Clinic Training Orbit",
                "Triska Orbital Station",
                "Lumora Canopy Haven",
            ],
        )
        self.assertEqual(
            [slot.create().name for slot in get_destination(1).patient_roster],
            [
                "Zorpa Voidwalker",
                "Zoogy Zinglestar",
                "Titus McMightus",
                "Conmann Cheester",
            ],
        )
        self.assertEqual(
            [slot.create().name for slot in get_destination(2).patient_roster],
            ["Flersch", "Dooski", "Flump", "Roldi"],
        )
        self.assertEqual(
            [slot.create().name for slot in get_destination(3).patient_roster],
            [
                "Velli Mosswhistle",
                "Gribble Sporekin",
                "Oola Dewdrop",
                "Krix Lanternback",
            ],
        )
        for destination in DESTINATIONS:
            self.assertEqual(len(destination.patient_roster), 4)
            self.assertEqual(destination.alien_population, destination.patient_roster)
            self.assertTrue(destination.theme.scene)
            self.assertTrue(destination.theme.decor_style)
            self.assertTrue(destination.theme.particle_style)
            self.assertIn(destination.theme.alien_render_style, {"pixel", "smooth"})
            self.assertTrue(destination.arrival_message)

        training_theme = get_destination(1).theme
        triska_theme = get_destination(2).theme
        self.assertNotEqual(training_theme.wall_color, triska_theme.wall_color)
        self.assertNotEqual(training_theme.chair_color, triska_theme.chair_color)
        self.assertNotEqual(training_theme.sign_color, triska_theme.sign_color)

        duplicate_day = replace(DESTINATIONS[1], day_number=1)
        with self.assertRaises(ValueError):
            validate_destinations((DESTINATIONS[0], duplicate_day))

    def test_gui_rosters_are_built_from_planet_destination_data(self):
        """Runtime chair entries should preserve the central roster metadata."""

        self.assertEqual(self.game.current_destination, get_destination(1))
        for destination in DESTINATIONS:
            roster = self.game.roster_for_destination(destination)
            self.assertEqual(
                [entry["asset"] for entry in roster],
                [slot.asset for slot in destination.patient_roster],
            )
            self.assertEqual(
                [entry["serial"] for entry in roster],
                [slot.serial for slot in destination.patient_roster],
            )
            self.assertEqual(
                {entry["destination_key"] for entry in roster},
                {destination.key},
            )
            self.assertEqual(
                {entry["render_style"] for entry in roster},
                {destination.theme.alien_render_style},
            )
            self.assertEqual(
                [entry["presentation_scale"] for entry in roster],
                [slot.presentation_scale for slot in destination.patient_roster],
            )

    def test_velli_visuals_render_in_every_required_patient_context(self):
        """Velli's approved sprite and interview face should share one silhouette."""

        slot = LUMORA_PATIENTS[0]
        neutral = self.game.patient_source(slot.asset)
        interview = self.game.patient_source(slot.asset, "interview")
        self.assertEqual(neutral.get_size(), interview.get_size())
        self.assertGreater(pygame.mask.from_surface(neutral).count(), 0)
        self.assertGreater(pygame.mask.from_surface(interview).count(), 0)
        self.assertNotEqual(
            bytes(pygame.image.tobytes(neutral, "RGBA")),
            bytes(pygame.image.tobytes(interview, "RGBA")),
        )

        self.game.screen.fill((0, 0, 0))
        with patch("pygame.time.get_ticks", return_value=0):
            self.game.draw_waiting_asset(
                slot.asset,
                450,
                render_style="smooth",
                presentation_scale=slot.presentation_scale,
            )
        first_idle_frame = bytes(pygame.image.tobytes(self.game.screen, "RGB"))
        self.game.screen.fill((0, 0, 0))
        with patch("pygame.time.get_ticks", return_value=900):
            self.game.draw_waiting_asset(
                slot.asset,
                450,
                render_style="smooth",
                presentation_scale=slot.presentation_scale,
            )
        second_idle_frame = bytes(pygame.image.tobytes(self.game.screen, "RGB"))
        self.assertNotEqual(first_idle_frame, second_idle_frame)
        head = self.game.draw_exam_asset(
            slot.asset,
            pygame.Rect(250, 210, 340, 210),
            420,
            pygame.Rect(350, 382, 140, 18),
            0,
            0,
            False,
            render_style="smooth",
            presentation_scale=slot.presentation_scale,
        )
        self.assertGreater(head.width, 0)
        self.assertGreater(head.height, 0)

        portrait = pygame.Rect(610, 220, 48, 60)
        fitted = self.game.fit_patient_sprite(
            slot.asset,
            portrait.inflate(-8, -8),
            render_style="smooth",
            presentation_scale=0.92,
            anchor="center",
        )
        self.assertTrue(portrait.colliderect(fitted))

    def test_gribble_visuals_render_in_every_required_patient_context(self):
        """Gribble should replace placeholder art with a matching expressive sprite."""

        slot = LUMORA_PATIENTS[1]
        neutral = self.game.patient_source(slot.asset)
        interview = self.game.patient_source(slot.asset, "interview")
        self.assertEqual(neutral.get_height(), 512)
        self.assertEqual(interview.get_height(), 512)
        self.assertLessEqual(abs(neutral.get_width() - interview.get_width()), 1)
        self.assertGreater(pygame.mask.from_surface(neutral).count(), 0)
        self.assertGreater(pygame.mask.from_surface(interview).count(), 0)
        neutral_sample = pygame.transform.smoothscale(neutral, (96, 96))
        interview_sample = pygame.transform.smoothscale(interview, (96, 96))
        self.assertNotEqual(
            bytes(pygame.image.tobytes(neutral_sample, "RGBA")),
            bytes(pygame.image.tobytes(interview_sample, "RGBA")),
        )

        self.game.screen.fill((0, 0, 0))
        with patch("pygame.time.get_ticks", return_value=0):
            self.game.draw_waiting_asset(
                slot.asset,
                450,
                render_style="smooth",
                presentation_scale=slot.presentation_scale,
            )
        first_idle_frame = bytes(pygame.image.tobytes(self.game.screen, "RGB"))
        self.game.screen.fill((0, 0, 0))
        with patch("pygame.time.get_ticks", return_value=1100):
            self.game.draw_waiting_asset(
                slot.asset,
                450,
                render_style="smooth",
                presentation_scale=slot.presentation_scale,
            )
        second_idle_frame = bytes(pygame.image.tobytes(self.game.screen, "RGB"))
        self.assertNotEqual(first_idle_frame, second_idle_frame)

        head = self.game.draw_exam_asset(
            slot.asset,
            pygame.Rect(250, 210, 340, 210),
            420,
            pygame.Rect(350, 382, 140, 18),
            0,
            0,
            False,
            render_style="smooth",
            presentation_scale=slot.presentation_scale,
        )
        self.assertGreater(head.width, 0)
        self.assertGreater(head.height, 0)

        portrait = pygame.Rect(610, 220, 48, 60)
        fitted = self.game.fit_patient_sprite(
            slot.asset,
            portrait.inflate(-8, -8),
            render_style="smooth",
            presentation_scale=0.92,
            anchor="center",
        )
        self.assertTrue(portrait.colliderect(fitted))

    def test_oola_and_krix_replace_placeholders_with_complete_sprite_sets(self):
        """The final Lumora pair should match its roster in every patient view."""

        for slot in LUMORA_PATIENTS[2:]:
            neutral = self.game.patient_source(slot.asset)
            interview = self.game.patient_source(slot.asset, "interview")
            self.assertEqual(neutral.get_height(), 512)
            self.assertEqual(interview.get_height(), 512)
            self.assertLessEqual(abs(neutral.get_width() - interview.get_width()), 1)
            self.assertGreater(pygame.mask.from_surface(neutral).count(), 0)
            self.assertGreater(pygame.mask.from_surface(interview).count(), 0)
            neutral_sample = pygame.transform.smoothscale(neutral, (96, 96))
            interview_sample = pygame.transform.smoothscale(interview, (96, 96))
            self.assertNotEqual(
                pygame.image.tobytes(neutral_sample, "RGBA"),
                pygame.image.tobytes(interview_sample, "RGBA"),
            )

            self.game.screen.fill((0, 0, 0))
            with patch("pygame.time.get_ticks", return_value=0):
                self.game.draw_waiting_asset(
                    slot.asset,
                    450,
                    render_style="smooth",
                    presentation_scale=slot.presentation_scale,
                )
            first_idle_frame = pygame.image.tobytes(self.game.screen, "RGB")
            self.game.screen.fill((0, 0, 0))
            with patch("pygame.time.get_ticks", return_value=950):
                self.game.draw_waiting_asset(
                    slot.asset,
                    450,
                    render_style="smooth",
                    presentation_scale=slot.presentation_scale,
                )
            second_idle_frame = pygame.image.tobytes(self.game.screen, "RGB")
            self.assertNotEqual(first_idle_frame, second_idle_frame)

            head = self.game.draw_exam_asset(
                slot.asset,
                pygame.Rect(250, 210, 340, 210),
                420,
                pygame.Rect(350, 382, 140, 18),
                0,
                0,
                False,
                render_style="smooth",
                presentation_scale=slot.presentation_scale,
            )
            self.assertGreater(head.width, 0)
            self.assertGreater(head.height, 0)

    def test_reception_environment_follows_the_selected_destination(self):
        """Configured reception themes should render through one shared layout."""

        self.assertEqual(self.game.get_reception_theme().scene, "training_orbit")
        self.game.draw_title_screen()
        training_snapshot = bytes(pygame.image.tobytes(self.game.screen, "RGB"))

        self.game.route.select_day(2)
        self.game.load_current_destination()
        self.assertEqual(self.game.get_reception_theme().scene, "triska_orbit")
        self.game.draw_title_screen()
        triska_snapshot = bytes(pygame.image.tobytes(self.game.screen, "RGB"))

        self.assertNotEqual(training_snapshot, triska_snapshot)

    def test_lumora_reception_keeps_shared_controls_and_animates_its_jungle(self):
        """Day 3 scenery should move without relocating reception gameplay."""

        shared_start_button = self.game.start_button.copy()
        self.game.route.select_day(3)
        self.game.load_current_destination()
        self.assertEqual(self.game.get_reception_theme().scene, "lumora_orbit")

        with (
            patch.object(
                self.game,
                "draw_lumora_waiting_room_windows",
                wraps=self.game.draw_lumora_waiting_room_windows,
            ) as draw_lumora,
            patch("pygame.time.get_ticks", return_value=1_000),
        ):
            self.game.draw_title_screen()
            first_window = pygame.image.tobytes(
                self.game.screen.subsurface(pygame.Rect(37, 164, 792, 239)),
                "RGB",
            )

        draw_lumora.assert_called_once()
        self.assertEqual(self.game.start_button, shared_start_button)

        with patch("pygame.time.get_ticks", return_value=2_800):
            self.game.draw_title_screen()
            later_window = pygame.image.tobytes(
                self.game.screen.subsurface(pygame.Rect(37, 164, 792, 239)),
                "RGB",
            )

        self.assertNotEqual(first_window, later_window)

    def test_lumora_destination_loads_with_safe_review_stage_art(self):
        """Day 3 should render before every final patient sprite is approved."""

        self.game.route.select_day(3)
        self.game.load_current_destination()
        destination = self.game.current_destination
        self.assertEqual(destination.key, "lumora_canopy")
        self.assertEqual(destination.ambience, "lumora_canopy_hum")
        self.assertEqual(destination.theme.scene, "lumora_orbit")
        self.assertEqual(destination.theme.decor_style, "lumora_vines")
        self.assertEqual(destination.theme.particle_style, "glow_spores")
        self.assertEqual(
            [entry["create"]().name for entry in self.game.waiting_room_queue],
            [
                "Velli Mosswhistle",
                "Gribble Sporekin",
                "Oola Dewdrop",
                "Krix Lanternback",
            ],
        )
        for entry in self.game.waiting_room_queue:
            sprite = self.game.patient_sprite(
                entry["asset"],
                (64, 96),
                render_style=entry["render_style"],
            )
            self.assertGreater(pygame.mask.from_surface(sprite).count(), 0)
        self.game.draw_title_screen()

    def test_new_asset_patients_join_from_day_two_and_restart_resets_roster(self):
        originals = {entry['create']().name for entry in self.game.waiting_room_queue}
        new_names = {'Flersch', 'Dooski', 'Flump', 'Roldi'}
        expected_serials = {'TRI-031-FL', 'VRD-112-DS', 'VEL-064-FP', 'CRG-209-RD'}
        day_two_roster = self.game.roster_for_day(2)
        self.assertTrue(originals.isdisjoint(new_names))
        self.assertEqual({entry['create']().name for entry in day_two_roster}, new_names)
        self.assertEqual({entry['serial'] for entry in day_two_roster}, expected_serials)
        self.assertEqual(
            {entry['asset'] for entry in day_two_roster},
            {'flersch', 'dooski', 'flump', 'roldi'},
        )
        self.game.begin_ending_sequence()
        self.game.finish_ending_sequence()
        self.assertEqual(self.game.state, GameState.ARRIVAL)
        self.game.handle_arrival_click(self.game.arrival_begin_button.center)
        self.assertEqual(self.game.day_number, 2)
        self.assertEqual(len(self.game.waiting_room_queue), 4)
        for entry in self.game.waiting_room_queue:
            patient = entry['create']()
            self.assertIn(patient.diagnosis, patient.diagnosis_options)
            self.assertEqual(len(patient.test_results), 8)
            self.game.patient_sprite(entry['asset'], (32, 48))
        self.assertEqual(
            {entry['create']().name for entry in self.game.waiting_room_queue},
            new_names,
        )
        self.assertEqual(
            [entry['create']().name for entry in self.game.roster_for_day(3)],
            [
                "Velli Mosswhistle",
                "Gribble Sporekin",
                "Oola Dewdrop",
                "Krix Lanternback",
            ],
        )
        self.game.restart_game()
        self.assertEqual(self.game.day_number, 1)
        self.assertEqual({entry['create']().name for entry in self.game.waiting_room_queue}, originals)

    def test_complete_day_two_shift_reaches_recap_with_all_new_patients(self):
        """Automatically play all four Day 2 cases to guard the full shift loop."""

        self.game.begin_ending_sequence()
        self.game.start_next_shift()
        expected_names = ['Flersch', 'Dooski', 'Flump', 'Roldi']
        self.assertEqual(self.game.day_number, 2)
        self.assertEqual(
            [entry['create']().name for entry in self.game.waiting_room_queue],
            expected_names,
        )

        for index, expected_name in enumerate(expected_names):
            self.assertEqual(self.game.patient.name, expected_name)
            self.game.begin_reception_transition()
            self.game.reception_transition_started_at = (
                pygame.time.get_ticks() - self.game.reception_transition_duration - 1
            )
            self.game.update()
            self.assertEqual(self.game.state, GameState.PATIENT)

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
                self.game.queue_shift_started_at = (
                    pygame.time.get_ticks() - self.game.queue_shift_duration - 1
                )
                self.game.update()

        self.assertEqual(self.game.state, GameState.TITLE)
        self.assertIsNotNone(self.game.end_day_shutdown_started_at)
        self.game.end_day_shutdown_started_at = (
            pygame.time.get_ticks() - self.game.end_day_shutdown_duration - 1
        )
        self.game.update()

        self.assertEqual(self.game.state, GameState.DAY_COMPLETE)
        self.assertEqual(self.game.daily_correct_diagnoses, 4)
        self.assertEqual(self.game.daily_wrong_diagnoses, 0)
        self.game.draw()

    def test_future_shift_can_load_a_new_patient_roster(self):
        """Route advancement should preserve progression and campaign totals."""

        self.game.player.balance = 175
        self.game.player.machine_levels["TEMPERATURE"] = 2
        self.game.player.test_discount = 3
        self.game.purchased_shop_upgrades.update({"temperature", "smart_cards"})
        self.game.daily_correct_diagnoses = 3
        self.game.daily_evidence_cases = 2
        self.game.daily_wrong_diagnoses = 1
        self.game.daily_test_count = 7
        self.game.daily_patients_lost = 1
        self.game.begin_ending_sequence()
        self.assertEqual(
            self.game.route.completed_destinations,
            (get_destination(1),),
        )
        self.assertEqual(self.game.route.overall_performance["patients_seen"], 4)
        self.assertEqual(self.game.route.overall_performance["wrong_diagnoses"], 1)

        self.game.start_next_shift()
        self.assertEqual(self.game.state, GameState.TITLE)
        self.assertEqual(self.game.current_destination, get_destination(2))
        self.assertEqual(
            [entry["create"]().name for entry in self.game.waiting_room_queue],
            [slot.create().name for slot in get_destination(2).patient_roster],
        )
        self.assertEqual(self.game.patients_called, 0)
        self.assertEqual(self.game.patient.name, "Flersch")
        self.assertEqual(self.game.player.balance, 175)
        self.assertEqual(self.game.player.machine_levels["TEMPERATURE"], 2)
        self.assertEqual(self.game.player.test_discount, 3)
        self.assertEqual(
            self.game.purchased_shop_upgrades,
            {"temperature", "smart_cards"},
        )
        self.assertEqual(len(self.game.route.shift_history), 1)

    def test_planet_arrival_starts_day_two_when_a_roster_is_available(self):
        """The arrival screen should become a working Day 2 entry point."""

        self.game.player.balance = 175
        self.game.begin_ending_sequence()
        self.game.finish_ending_sequence()
        self.assertEqual(self.game.state, GameState.ARRIVAL)
        self.assertEqual(self.game.get_tutorial_action_label(), "RETURN TO ARRIVAL")
        self.assertEqual(self.game.get_help_context()[0], "PLANET ARRIVAL")
        self.game.draw()
        self.game.handle_arrival_click(self.game.arrival_begin_button.center)

        self.assertEqual(self.game.state, GameState.TITLE)
        self.assertEqual(self.game.current_destination, get_destination(2))
        self.assertEqual(self.game.patient.name, "Flersch")
        self.assertEqual(self.game.player.balance, 175)

    def test_lumora_arrival_uses_its_animated_planet_art_and_ufo_approach(self):
        """Day 3 should keep its distinct arrival art and visible clinic approach."""

        self.game.developer_selected_day = 3
        self.game.prepare_developer_arrival_checkpoint()
        self.assertEqual(self.game.current_destination, get_destination(3))
        self.assertEqual(self.game.current_destination.theme.scene, "lumora_orbit")

        self.game.arrival_started_at = 1_000
        with (
            patch.object(
                self.game,
                "draw_lumora_destination_planet",
                wraps=self.game.draw_lumora_destination_planet,
            ) as draw_lumora,
            patch.object(
                self.game,
                "draw_arrival_ufo",
                wraps=self.game.draw_arrival_ufo,
            ) as draw_ufo,
            patch("pygame.time.get_ticks", return_value=1_000),
        ):
            self.game.draw_planet_arrival_screen()
            first_frame = pygame.image.tobytes(self.game.screen, "RGB")

        draw_lumora.assert_called_once()
        draw_ufo.assert_called_once()

        with patch("pygame.time.get_ticks", return_value=2_800):
            self.game.draw_planet_arrival_screen()
            later_frame = pygame.image.tobytes(self.game.screen, "RGB")

        self.assertNotEqual(first_frame, later_frame)

    def test_end_of_day_flow_runs_recap_shop_departure_and_arrival_in_order(self):
        """A completed shift should travel only through the configured route."""

        self.game.state = GameState.DAY_COMPLETE
        self.game.handle_day_complete_click(self.game.day_complete_button.center)
        self.assertEqual(self.game.state, GameState.SHOP)

        self.game.handle_shop_click(self.game.shop_button.center)
        self.assertEqual(self.game.state, GameState.ROUTE_BRIEFING)
        for _ in ROUTE_BRIEFING_DIALOGUE:
            self.game.advance_route_briefing()
        self.assertEqual(self.game.state, GameState.ENDING)
        self.assertTrue(self.game.route.arrival_pending)

        self.game.finish_ending_sequence()
        self.assertEqual(self.game.state, GameState.ARRIVAL)
        self.assertEqual(self.game.current_destination, get_destination(2))

        self.game.handle_arrival_click(self.game.arrival_begin_button.center)
        self.assertEqual(self.game.state, GameState.TITLE)
        self.assertEqual(self.game.day_number, 2)
        self.assertEqual(self.game.patient.name, "Flersch")

    def test_final_destination_finishes_without_a_nonexistent_arrival(self):
        """Completing Lumora should show Route Complete rather than another stop."""

        self.game.begin_ending_sequence()
        self.game.finish_ending_sequence()
        self.game.handle_arrival_click(self.game.arrival_begin_button.center)
        self.assertEqual(self.game.current_destination, get_destination(2))

        self.game.begin_ending_sequence()
        self.game.finish_ending_sequence()
        self.assertEqual(self.game.state, GameState.ARRIVAL)
        self.game.handle_arrival_click(self.game.arrival_begin_button.center)
        self.assertEqual(self.game.current_destination, get_destination(3))

        self.game.begin_ending_sequence()
        self.game.finish_ending_sequence()
        self.assertEqual(self.game.state, GameState.FINAL)
        self.assertTrue(self.game.route.route_is_complete)
        self.assertFalse(self.game.route.arrival_pending)
        self.assertIsNone(self.game.route.next_destination)
        self.assertEqual(self.game.day_number, 3)
        self.assertEqual(ROUTE_COMPLETE_HEADING, "CURRENT ROUTE COMPLETE")
        self.assertEqual(
            ROUTE_COMPLETE_MESSAGE,
            "The next clinic destination is being prepared.",
        )
        self.game.draw()

        self.game.handle_final_screen_click(self.game.final_replay_button.center)
        self.assertEqual(self.game.state, GameState.TITLE)
        self.assertEqual(self.game.day_number, 1)
        self.assertEqual(self.game.patient.name, "Zorpa Voidwalker")

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

    def test_return_passage_is_a_real_persistent_shop_purchase(self):
        """The Earth-ticket objective should show progress and be purchasable."""

        passage = next(
            upgrade
            for upgrade in SHOP_UPGRADES
            if upgrade["id"] == "return_passage"
        )
        self.assertEqual(passage["cost"], RETURN_PASSAGE_COST)
        self.game.route.select_day(3)
        self.game.state = GameState.SHOP
        self.game.player.balance = RETURN_PASSAGE_COST
        passage_index = SHOP_UPGRADES.index(passage)
        self.game.shop_scroll_row = min(
            passage_index // 3,
            self.game.get_shop_max_scroll_row(),
        )
        visible_index = self.game.get_visible_shop_upgrades().index(passage)

        self.game.handle_shop_click(
            self.game.get_shop_upgrade_rects()[visible_index].center
        )
        self.game.handle_shop_click(self.game.shop_purchase_button.center)

        self.assertTrue(self.game.has_return_passage())
        self.assertEqual(self.game.player.balance, 0)
        self.assertEqual(self.game.state, GameState.FINAL)
        self.game.draw()

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
        """Every card title and description should remain inside its text area."""

        compact_test_header = pygame.Rect(0, 0, 96, 31)
        compact_diagnosis_header = pygame.Rect(0, 0, 96, 44)
        selected_header = pygame.Rect(0, 0, 202, 39)
        description_area = pygame.Rect(0, 0, 130, 108)

        for test in create_test_catalog():
            font, lines = self.game.get_fitted_card_title_layout(
                test.name,
                compact_test_header,
            )
            self.assertLessEqual(len(lines), 2)
            self.assertEqual(" ".join(lines), test.name)
            self.assertLessEqual(
                len(lines) * font.get_linesize(),
                compact_test_header.height - 4,
            )
            self.assertTrue(
                all(font.size(line)[0] <= compact_test_header.width - 8 for line in lines)
            )
            if test.name == "BLOOD CHEMISTRY":
                self.assertIs(font, self.game.compact_card_title_font)
            detail_font, detail_lines = self.game.get_fitted_card_description_layout(
                test.description,
                description_area,
            )
            detail_height = len(detail_lines) * detail_font.get_height() + max(
                0,
                len(detail_lines) - 1,
            ) * 2
            self.assertLessEqual(detail_height, description_area.height)

        for diagnosis in DIAGNOSES.values():
            font, lines = self.game.get_fitted_card_title_layout(
                diagnosis.name,
                compact_diagnosis_header,
                max_lines=3,
            )
            self.assertLessEqual(len(lines), 3)
            self.assertEqual(" ".join(lines), diagnosis.name)
            self.assertIn(
                font,
                (self.game.diagnosis_card_font, self.game.compact_card_title_font),
            )
            self.assertLessEqual(
                len(lines) * font.get_linesize(),
                compact_diagnosis_header.height - 4,
            )
            self.assertTrue(
                all(
                    font.size(line)[0] <= compact_diagnosis_header.width - 8
                    for line in lines
                )
            )
            selected_font, selected_lines = self.game.get_fitted_card_title_layout(
                diagnosis.name,
                selected_header,
                selected=True,
            )
            self.assertLessEqual(len(selected_lines), 2)
            self.assertEqual(" ".join(selected_lines), diagnosis.name)
            self.assertLessEqual(
                len(selected_lines) * selected_font.get_linesize(),
                selected_header.height - 4,
            )
            self.assertTrue(
                all(
                    selected_font.size(line)[0] <= selected_header.width - 8
                    for line in selected_lines
                )
            )
            detail_font, detail_lines = self.game.get_fitted_card_description_layout(
                diagnosis.description,
                description_area,
            )
            detail_height = len(detail_lines) * detail_font.get_height() + max(
                0,
                len(detail_lines) - 1,
            ) * 2
            self.assertLessEqual(detail_height, description_area.height)

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
