"""Focused regression tests for The Cosmic Clinic destination route."""

import os
import unittest
from dataclasses import replace


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from PlanetData import DESTINATIONS, get_destination, validate_destinations
from gui_main import CosmicClinicGUI
from gui_ending import ROUTE_BRIEFING_DIALOGUE
from gui_state import GameState


class RouteRegressionTests(unittest.TestCase):
    """Protect campaign data and travel behavior as destinations are added."""

    def setUp(self):
        self.game = CosmicClinicGUI(card_seed=151)
        self.game.finish_guided_tutorial()

    def tearDown(self):
        pygame.event.clear()
        pygame.quit()

    def travel_to_day_two(self):
        """Complete Day 1's route record and load Triska reception."""

        self.game.begin_ending_sequence()
        self.assertTrue(self.game.route.arrival_pending)
        self.game.start_next_shift()

    def test_every_destination_contains_a_valid_fixed_alpha_roster(self):
        self.assertTrue(validate_destinations())
        self.assertGreaterEqual(len(DESTINATIONS), 2)
        for destination in DESTINATIONS:
            roster = destination.patient_roster
            self.assertEqual(len(roster), 4)
            self.assertEqual(len({slot.asset for slot in roster}), 4)
            self.assertEqual(len({slot.serial for slot in roster}), 4)
            self.assertEqual(len({slot.create().name for slot in roster}), 4)
            self.assertTrue(all(slot.create().test_results for slot in roster))

    def test_every_patient_has_five_unique_choices_and_the_correct_answer(self):
        for destination in DESTINATIONS:
            for slot in destination.alien_population:
                patient = slot.create()
                choices = patient.diagnosis_options
                names = [choice.name.strip().casefold() for choice in choices]
                self.assertEqual(len(choices), 5, patient.name)
                self.assertEqual(len(set(names)), 5, patient.name)
                self.assertIn(patient.diagnosis, choices, patient.name)
                self.assertEqual(
                    sum(choice is patient.diagnosis for choice in choices),
                    1,
                    patient.name,
                )

    def test_destination_validation_rejects_duplicate_diagnosis_choices(self):
        original_slot = get_destination(1).patient_roster[0]

        def create_invalid_patient():
            patient = original_slot.create()
            patient.diagnosis_options = (patient.diagnosis,) * 5
            return patient

        invalid_slot = replace(original_slot, create=create_invalid_patient)
        invalid_destination = replace(
            get_destination(1),
            patient_roster=(invalid_slot,) + get_destination(1).patient_roster[1:],
        )
        with self.assertRaisesRegex(ValueError, "must be unique"):
            validate_destinations((invalid_destination, get_destination(2)))

    def test_money_and_permanent_upgrades_survive_planet_travel(self):
        self.game.player.balance = 347
        self.game.player.machine_levels.update({"TEMPERATURE": 2, "NEURAL SCAN": 2})
        self.game.player.test_discount = 3
        self.game.purchased_shop_upgrades.update(
            {"temperature", "neural", "smart_cards"}
        )

        self.travel_to_day_two()

        self.assertEqual(self.game.player.balance, 347)
        self.assertEqual(
            self.game.player.machine_levels,
            {"TEMPERATURE": 2, "NEURAL SCAN": 2},
        )
        self.assertEqual(self.game.player.test_discount, 3)
        self.assertEqual(
            self.game.purchased_shop_upgrades,
            {"temperature", "neural", "smart_cards"},
        )

    def test_return_to_reception_preserves_day_two_campaign_progress(self):
        """Reception restart must never silently create a new campaign."""

        self.game.player.balance = 347
        self.game.player.machine_levels["TEMPERATURE"] = 2
        self.game.player.test_discount = 2
        self.game.purchased_shop_upgrades.update(
            {"temperature", "smart_cards"}
        )
        self.travel_to_day_two()
        self.game.daily_correct_diagnoses = 2

        self.game.restart_current_shift()

        self.assertEqual(self.game.current_destination, get_destination(2))
        self.assertEqual(self.game.state, GameState.TITLE)
        self.assertEqual(self.game.player.balance, 347)
        self.assertEqual(self.game.player.machine_levels, {"TEMPERATURE": 2})
        self.assertEqual(self.game.player.test_discount, 2)
        self.assertEqual(
            self.game.purchased_shop_upgrades,
            {"temperature", "smart_cards"},
        )
        self.assertEqual(self.game.daily_correct_diagnoses, 0)
        self.assertEqual(
            self.game.route.completed_destinations,
            (get_destination(1),),
        )

    def test_replaying_a_paid_shift_cannot_collect_pay_twice(self):
        """A reception restart after payroll should retain the paid flag."""

        self.game.state = GameState.DAY_COMPLETE
        self.game.daily_payout_applied = True
        self.game.player.balance = 180

        self.game.restart_current_shift()

        self.assertTrue(self.game.daily_payout_applied)
        self.assertEqual(self.game.player.balance, 180)

    def test_location_subtitle_tracks_the_active_destination(self):
        self.assertEqual(
            self.game.get_location_subtitle(),
            "DAY 1  •  COSMIC CLINIC TRAINING ORBIT",
        )
        self.travel_to_day_two()
        self.assertEqual(
            self.game.get_location_subtitle(),
            "DAY 2  •  TRISKA ORBITAL STATION",
        )

    def test_day_two_roster_loads_immediately_after_day_one(self):
        day_one_names = {
            slot.create().name for slot in get_destination(1).patient_roster
        }
        self.travel_to_day_two()
        day_two_names = [entry["create"]().name for entry in self.game.waiting_room_queue]

        self.assertEqual(self.game.state, GameState.TITLE)
        self.assertEqual(self.game.current_destination, get_destination(2))
        self.assertEqual(day_two_names, ["Flersch", "Dooski", "Flump", "Roldi"])
        self.assertTrue(day_one_names.isdisjoint(day_two_names))

    def test_training_shop_uses_one_short_route_briefing_before_travel(self):
        self.game.state = GameState.SHOP
        self.game.handle_shop_click(self.game.shop_button.center)

        self.assertEqual(self.game.state, GameState.ROUTE_BRIEFING)
        self.assertEqual(
            ROUTE_BRIEFING_DIALOGUE,
            (
                (
                    "CLINIC SYSTEM",
                    "Training shift complete. The Cosmic Clinic travels to a new destination after every shift.",
                ),
                ("YOU", "And when do I get to go home?"),
                (
                    "CLINIC SYSTEM",
                    "Earn enough credits to purchase return passage to Earth.",
                ),
            ),
        )
        self.game.advance_route_briefing()
        self.assertEqual(self.game.route_briefing_index, 1)
        self.game.advance_route_briefing()
        self.assertEqual(self.game.route_briefing_index, 2)
        self.game.advance_route_briefing()

        self.assertTrue(self.game.route_briefing_seen)
        self.assertEqual(self.game.state, GameState.ENDING)
        self.assertTrue(self.game.route.arrival_pending)

    def test_route_briefing_does_not_repeat_after_the_training_destination(self):
        self.game.route_briefing_seen = True
        self.game.begin_ending_sequence()
        self.game.start_next_shift()
        self.game.state = GameState.SHOP

        self.game.handle_shop_click(self.game.shop_button.center)

        self.assertEqual(self.game.state, GameState.ENDING)
        self.assertTrue(self.game.route.route_is_complete)

    def test_restarting_the_route_restores_the_training_briefing(self):
        self.game.route_briefing_seen = True
        self.game.route_briefing_index = 2

        self.game.restart_game()

        self.assertFalse(self.game.route_briefing_seen)
        self.assertEqual(self.game.route_briefing_index, 0)

    def test_first_patient_tutorial_does_not_repeat_on_day_two(self):
        self.game.start_guided_tutorial()
        self.assertTrue(self.game.guided_tutorial_active)
        self.game.finish_guided_tutorial()

        self.travel_to_day_two()

        self.assertFalse(self.game.guided_tutorial_active)
        self.assertFalse(self.game.start_guided_tutorial())
        self.assertFalse(self.game.guided_tutorial_active)

    def test_final_destination_ends_route_without_repeating_patients(self):
        self.travel_to_day_two()
        day_two_names = tuple(
            entry["create"]().name for entry in self.game.waiting_room_queue
        )

        self.game.begin_ending_sequence()
        self.game.finish_ending_sequence()

        self.assertEqual(self.game.state, GameState.FINAL)
        self.assertTrue(self.game.route.route_is_complete)
        self.assertIsNone(self.game.route.next_destination)
        self.assertEqual(self.game.day_number, 2)
        self.assertEqual(
            tuple(entry["create"]().name for entry in self.game.waiting_room_queue),
            day_two_names,
        )
        self.assertEqual(self.game.roster_for_day(3), [])

    def test_f10_preview_restores_the_live_campaign_exactly(self):
        self.game.state = GameState.PATIENT
        self.game.patients_called = 1
        self.game.player.balance = 263
        self.game.player.machine_levels["BLOOD CHEMISTRY"] = 2
        self.game.player.test_discount = 2
        self.game.player.free_test_machines.add("OXYGEN SCAN")
        self.game.player.free_tests_used.add("OXYGEN SCAN")
        self.game.purchased_shop_upgrades.update(
            {"blood", "smart_cards", "recycler"}
        )
        self.game.recycler_used = True
        self.game.daily_correct_diagnoses = 1
        self.game.daily_test_count = 3
        self.game.daily_test_expenses = 35
        self.game.notebook.add_test(
            self.game.patient,
            "TEMPERATURE",
            self.game.patient.test_results["TEMPERATURE"],
        )
        live_fingerprint = self.game.get_campaign_state_fingerprint()

        self.game.toggle_developer_navigator()
        self.game.select_developer_day(2)
        self.game.jump_to_developer_screen(
            self.game.get_developer_scene_index("patient_3")
        )
        self.assertTrue(self.game.developer_preview_active)
        self.assertNotEqual(
            self.game.get_campaign_state_fingerprint(),
            live_fingerprint,
        )

        self.game.toggle_developer_navigator()
        self.game.handle_developer_click(self.game.developer_return_button.center)

        self.assertFalse(self.game.developer_preview_active)
        self.assertFalse(self.game.developer_navigator_open)
        self.assertIsNone(self.game.developer_campaign_snapshot)
        self.assertEqual(self.game.get_campaign_state_fingerprint(), live_fingerprint)

    def test_f10_homecoming_uses_the_real_ending_without_mutating_campaign(self):
        """The final destination should preview Go Home in an isolated snapshot."""

        self.game.state = GameState.PATIENT
        self.game.player.balance = 263
        live_fingerprint = self.game.get_campaign_state_fingerprint()

        self.game.toggle_developer_navigator()
        self.game.select_developer_day(2)
        self.game.jump_to_developer_screen(
            self.game.get_developer_scene_index("homecoming")
        )

        self.assertEqual(self.game.state, GameState.ENDING)
        self.assertTrue(self.game.homecoming_started)
        self.assertTrue(self.game.has_return_passage())
        self.assertTrue(self.game.route.route_is_complete)
        self.assertEqual(self.game.ending_duration, 14000)
        self.game.draw()

        self.game.toggle_developer_navigator()
        self.game.handle_developer_click(
            self.game.developer_return_button.center
        )

        self.assertFalse(self.game.developer_preview_active)
        self.assertEqual(
            self.game.get_campaign_state_fingerprint(),
            live_fingerprint,
        )


if __name__ == "__main__":
    unittest.main()
