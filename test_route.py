"""Focused regression tests for The Cosmic Clinic destination route."""

import os
import unittest
from dataclasses import replace


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from PlanetData import (
    BLACKGLASS_MAP_DESTINATION,
    DESTINATIONS,
    EARTH_MAP_DESTINATION,
    LUMORA_TICKET_COST,
    MAP_DESTINATIONS,
    TRISKA_TICKET_COST,
    DestinationType,
    get_destination,
    get_map_destination,
    validate_destinations,
    validate_map_destinations,
)
from Player import (
    CLINIC_OPERATING_FEE,
    DIAGNOSIS_REWARD,
    PERFECT_DAY_BONUS,
    RETURN_PASSAGE_COST,
    STARTING_BALANCE,
)
from Test import get_test_cost
from Tests.catalog import create_test_catalog
from gui_main import CosmicClinicGUI
from gui_display import MIN_WINDOW_SIZE
from gui_ending import ROUTE_BRIEFING_DIALOGUE
from gui_state import GameState
from gui_theme import WINDOW_SIZE
from RouteController import DestinationState, RouteController, ShiftPerformance


class RouteRegressionTests(unittest.TestCase):
    """Protect campaign data and travel behavior as destinations are added."""

    def setUp(self):
        self.game = CosmicClinicGUI(card_seed=151)
        self.game.finish_guided_tutorial()

    def tearDown(self):
        pygame.event.clear()
        pygame.quit()

    def travel_to_day_two(self):
        """Complete Day 1, authorize Triska travel, and load reception."""

        self.game.begin_ending_sequence()
        self.assertEqual(self.game.state, GameState.ROUTE_MAP)
        self.assertEqual(self.game.current_destination, get_destination(1))
        next_destination = self.game.route.next_destination
        self.game.route.record_ticket_purchase(next_destination.key)
        self.game.begin_ending_sequence(next_destination.key)
        self.assertTrue(self.game.route.arrival_pending)
        self.game.start_next_shift()

    def travel_to_day_three(self):
        """Complete two shifts, authorize Lumora travel, and load reception."""

        self.travel_to_day_two()
        self.game.begin_ending_sequence()
        self.assertEqual(self.game.state, GameState.ROUTE_MAP)
        next_destination = self.game.route.next_destination
        self.game.route.record_ticket_purchase(next_destination.key)
        self.game.begin_ending_sequence(next_destination.key)
        self.assertTrue(self.game.route.arrival_pending)
        self.game.start_next_shift()

    def open_first_route_map_with_balance(self, balance):
        """Complete the training stop through its real one-time map briefing."""

        self.game.player.balance = balance
        self.game.state = GameState.SHOP
        self.game.route_briefing_seen = False
        self.game.handle_shop_click(self.game.shop_button.center)
        while self.game.state is GameState.ROUTE_BRIEFING:
            self.game.advance_route_briefing()
        self.assertEqual(self.game.state, GameState.ROUTE_MAP)
        return self.game

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

    def test_route_map_catalog_contains_clinics_earth_and_blackglass(self):
        self.assertTrue(validate_map_destinations())
        self.assertEqual(
            {destination.key for destination in MAP_DESTINATIONS},
            {
                "training_orbit",
                "triska_station",
                "lumora_canopy",
                "earth",
                "blackglass_outpost",
            },
        )
        self.assertEqual(
            {
                destination.key
                for destination in MAP_DESTINATIONS
                if destination.map_data.destination_type is DestinationType.CLINIC
            },
            {destination.key for destination in DESTINATIONS},
        )
        self.assertIs(get_map_destination("earth"), EARTH_MAP_DESTINATION)
        self.assertIs(
            get_map_destination("blackglass_outpost"),
            BLACKGLASS_MAP_DESTINATION,
        )

    def test_clinic_map_data_forms_a_ticketed_route(self):
        training, triska, lumora = DESTINATIONS
        self.assertEqual(training.map_data.ticket_price, 0)
        self.assertIsNone(training.map_data.previous_destination)
        self.assertIsNone(training.map_data.unlock_requirement)
        self.assertEqual(triska.map_data.ticket_price, TRISKA_TICKET_COST)
        self.assertEqual(triska.map_data.previous_destination, training.key)
        self.assertEqual(triska.map_data.unlock_requirement, training.key)
        self.assertEqual(lumora.map_data.ticket_price, LUMORA_TICKET_COST)
        self.assertEqual(lumora.map_data.previous_destination, triska.key)
        self.assertEqual(lumora.map_data.unlock_requirement, triska.key)
        self.assertEqual(
            len({destination.map_data.position for destination in MAP_DESTINATIONS}),
            len(MAP_DESTINATIONS),
        )

    def test_efficient_supported_shifts_can_afford_the_ticketed_route(self):
        """Perfect play should bypass fallback work without trivializing fares."""

        tests_by_name = {
            test.name.upper(): test
            for test in create_test_catalog()
        }
        balance = STARTING_BALANCE
        for destination, next_destination in zip(DESTINATIONS, DESTINATIONS[1:]):
            minimum_evidence_cost = 0
            for slot in destination.patient_roster:
                patient = slot.create()
                combination_costs = (
                    sum(get_test_cost(tests_by_name[name]) for name in combination)
                    for combination in patient.diagnosis.evidence_combinations
                )
                minimum_evidence_cost += min(combination_costs)
            balance += (
                len(destination.patient_roster) * DIAGNOSIS_REWARD
                - minimum_evidence_cost
                - CLINIC_OPERATING_FEE
                + PERFECT_DAY_BONUS
            )
            fare = next_destination.map_data.ticket_price
            self.assertGreaterEqual(
                balance,
                fare,
                f"Perfect Day {destination.day_number} play cannot fund {next_destination.planet_name}.",
            )
            balance -= fare

    def test_earth_and_blackglass_contracts_are_distinct(self):
        earth = EARTH_MAP_DESTINATION.map_data
        self.assertEqual(earth.destination_type, DestinationType.EARTH)
        self.assertEqual(earth.ticket_price, RETURN_PASSAGE_COST)
        self.assertFalse(earth.has_patients)
        self.assertTrue(earth.content_ready)

        blackglass = BLACKGLASS_MAP_DESTINATION.map_data
        self.assertEqual(blackglass.destination_type, DestinationType.BLACKGLASS)
        self.assertEqual(blackglass.ticket_price, 0)
        self.assertTrue(blackglass.has_patients)
        self.assertFalse(blackglass.content_ready)

    def test_map_validation_rejects_broken_destination_links(self):
        broken_earth = replace(
            EARTH_MAP_DESTINATION,
            map_data=replace(
                EARTH_MAP_DESTINATION.map_data,
                unlock_requirement="missing_planet",
            ),
        )
        broken_catalog = tuple(
            broken_earth if destination.key == "earth" else destination
            for destination in MAP_DESTINATIONS
        )
        with self.assertRaisesRegex(ValueError, "reference configured locations"):
            validate_map_destinations(broken_catalog)

    def test_campaign_travel_state_tracks_unlocks_tickets_and_credits(self):
        route = RouteController(starting_credits=100)
        initial = route.travel_state
        self.assertEqual(initial.current_location_key, "training_orbit")
        self.assertEqual(initial.completed_destination_keys, ())
        self.assertEqual(initial.unlocked_destination_keys, {"training_orbit"})
        self.assertEqual(initial.available_credits, 100)
        self.assertFalse(initial.return_passage_purchased)

        route.select_map_destination("triska_station")
        self.assertEqual(
            route.travel_state.selected_map_destination_key,
            "triska_station",
        )
        route.complete_current_shift(
            ShiftPerformance(
                destination_key="training_orbit",
                day_number=1,
                patients_seen=4,
                correct_diagnoses=4,
                supported_diagnoses=3,
                wrong_diagnoses=0,
                patients_lost=0,
                tests_run=6,
                net_pay=124,
                ending_balance=224,
            )
        )

        after_training = route.travel_state
        self.assertEqual(after_training.current_location_key, "training_orbit")
        self.assertEqual(
            after_training.completed_destination_keys,
            ("training_orbit",),
        )
        self.assertEqual(
            after_training.unlocked_destination_keys,
            {"training_orbit", "triska_station", "blackglass_outpost"},
        )
        self.assertEqual(after_training.available_credits, 224)
        self.assertEqual(
            after_training.selected_map_destination_key,
            "triska_station",
        )

        route.record_ticket_purchase("triska_station")
        self.assertEqual(route.purchased_ticket_keys, {"triska_station"})
        route.begin_travel("triska_station")
        self.assertEqual(route.current_location_key, "triska_station")
        self.assertTrue(route.arrival_pending)
        self.assertEqual(route.purchased_ticket_keys, set())
        self.assertEqual(route.used_ticket_keys, {"triska_station"})

        route.record_return_passage_purchase()
        self.assertTrue(route.return_passage_purchased)
        self.assertIn("earth", route.unlocked_destination_keys)
        self.assertIn("earth", route.purchased_ticket_keys)
        route.use_ticket("earth")
        self.assertEqual(route.current_location_key, "earth")
        self.assertIn("earth", route.used_ticket_keys)
        self.assertTrue(route.return_passage_purchased)

        route.reset(starting_credits=100)
        self.assertEqual(
            route.travel_state,
            RouteController(starting_credits=100).travel_state,
        )

    def test_ticket_purchase_is_destination_bound_debt_safe_and_consumed(self):
        """The route controller should own every invariant of paid travel."""

        route = RouteController(starting_credits=99)
        route.complete_current_shift(
            ShiftPerformance(
                destination_key="training_orbit",
                day_number=1,
                patients_seen=4,
                correct_diagnoses=4,
                supported_diagnoses=4,
                wrong_diagnoses=0,
                patients_lost=0,
                tests_run=8,
                net_pay=-1,
                ending_balance=99,
            )
        )
        with self.assertRaisesRegex(ValueError, "cannot be purchased with debt"):
            route.purchase_ticket("triska_station", 99)
        self.assertEqual(route.available_credits, 99)
        self.assertEqual(route.purchased_ticket_keys, set())

        charge = route.purchase_ticket("triska_station", 100)
        self.assertEqual(charge, TRISKA_TICKET_COST)
        self.assertEqual(route.available_credits, 0)
        self.assertEqual(route.purchased_ticket_keys, {"triska_station"})
        with self.assertRaisesRegex(ValueError, "already owned"):
            route.purchase_ticket("triska_station", 100)
        with self.assertRaisesRegex(ValueError, "locked"):
            route.purchase_ticket("lumora_canopy", 999)

        route.begin_travel("triska_station")
        self.assertNotIn("triska_station", route.purchased_ticket_keys)
        self.assertIn("triska_station", route.used_ticket_keys)
        with self.assertRaisesRegex(ValueError, "no new ticket inventory"):
            route.purchase_ticket("training_orbit", 999)

    def test_map_purchases_charge_each_route_fare_exactly_once(self):
        """The visible wallet should pay the configured fare for every stop."""

        game = self.open_first_route_map_with_balance(1000)
        game.finish_route_map_tutorial()

        expected_balance = 1000
        for destination_key, fare in (
            ("triska_station", TRISKA_TICKET_COST),
            ("lumora_canopy", LUMORA_TICKET_COST),
            ("earth", RETURN_PASSAGE_COST),
        ):
            self.assertEqual(
                game.route.selected_map_destination.key,
                destination_key,
            )
            game.handle_route_map_click(game.route_map_purchase_button.center)
            expected_balance -= fare
            self.assertEqual(game.player.balance, expected_balance)
            self.assertEqual(game.route.available_credits, expected_balance)
            self.assertEqual(
                game.route.purchased_ticket_keys,
                {destination_key},
            )

            if destination_key == "triska_station":
                self.assertEqual(
                    game.route.get_destination_state("lumora_canopy"),
                    DestinationState.LOCKED,
                )

            game.handle_route_map_click(game.route_map_travel_button.center)
            if destination_key == "earth":
                self.assertTrue(game.homecoming_started)
                self.assertIn("earth", game.route.used_ticket_keys)
                break

            game.finish_ending_sequence()
            game.start_next_shift()
            game.begin_ending_sequence()
            self.assertEqual(game.state, GameState.ROUTE_MAP)

    def test_map_purchase_refuses_debt_without_mutating_the_wallet(self):
        """A map click must enforce the same no-debt rule as the controller."""

        game = self.open_first_route_map_with_balance(TRISKA_TICKET_COST - 1)
        game.finish_route_map_tutorial()
        starting_state = game.route.travel_state

        game.handle_route_map_click(game.route_map_purchase_button.center)

        self.assertEqual(game.player.balance, TRISKA_TICKET_COST - 1)
        self.assertEqual(game.route.travel_state, starting_state)
        self.assertNotIn("triska_station", game.route.purchased_ticket_keys)

    def test_completed_planet_panel_cannot_reopen_its_shift(self):
        """Inspecting a closed clinic should never rewind campaign progress."""

        self.travel_to_day_two()
        self.game.begin_ending_sequence()
        training = get_map_destination("training_orbit")
        self.game.handle_route_map_click(
            self.game.get_route_map_node_center(training)
        )
        starting_fingerprint = self.game.get_campaign_state_fingerprint()

        self.game.handle_route_map_click(
            self.game.route_map_purchase_button.center
        )

        self.assertEqual(self.game.state, GameState.ROUTE_MAP)
        self.assertEqual(self.game.current_destination, get_destination(2))
        self.assertIn(get_destination(1), self.game.route.completed_destinations)
        self.assertEqual(
            self.game.get_campaign_state_fingerprint(),
            starting_fingerprint,
        )

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
        self.assertEqual(self.game.route.available_credits, 347)
        self.assertEqual(
            self.game.route.unlocked_destination_keys,
            {"training_orbit", "triska_station", "blackglass_outpost"},
        )
        self.assertEqual(
            self.game.purchased_shop_upgrades,
            {"temperature", "neural", "smart_cards"},
        )

    def test_full_day_two_to_lumora_sequence_preserves_campaign_progress(self):
        """Payroll, Shop, departure, arrival, and Day 3 must form one safe chain."""

        self.travel_to_day_two()
        self.assertEqual(self.game.current_destination, get_destination(2))

        # These represent permanent purchases made before the Triska shift.
        self.game.player.balance = 225
        self.game.player.machine_levels.update(
            {"TEMPERATURE": 2, "NEURAL SCAN": 2}
        )
        self.game.player.free_test_machines.add("OXYGEN SCAN")
        self.game.player.test_discount = 3
        permanent_upgrades = {
            "temperature",
            "neural",
            "oxygen_free",
            "power",
            "smart_cards",
            "recycler",
        }
        self.game.purchased_shop_upgrades.update(permanent_upgrades)
        self.game.recycler_used = True

        # File a completed Triska shift through the real payroll screen.
        self.game.daily_correct_diagnoses = 4
        self.game.daily_evidence_cases = 4
        self.game.daily_wrong_diagnoses = 0
        self.game.daily_test_count = 8
        self.game.daily_test_expenses = 60
        self.game.daily_draw_expenses = 5
        self.game.daily_card_shop_expenses = 10
        expected_net_pay = self.game.get_daily_pay_breakdown()[3]
        self.game.state = GameState.DAY_COMPLETE
        self.game.handle_day_complete_click(self.game.day_complete_button.center)

        self.assertEqual(self.game.state, GameState.SHOP)
        self.assertTrue(self.game.daily_payout_applied)
        payroll_balance = 225 + expected_net_pay
        self.assertEqual(self.game.player.balance, payroll_balance)
        passage_progress = self.game.get_return_passage_progress()

        # Leaving the Supply Shop records Triska but waits on the Route Map.
        self.game.handle_shop_click(self.game.shop_button.center)
        self.assertEqual(self.game.state, GameState.ROUTE_MAP)
        self.assertEqual(self.game.current_destination, get_destination(2))
        self.assertEqual(
            self.game.route.completed_destinations,
            (get_destination(1), get_destination(2)),
        )
        self.assertEqual(self.game.route.overall_performance["shifts_completed"], 2)
        self.assertEqual(self.game.route.overall_performance["patients_seen"], 8)
        self.assertEqual(self.game.route.overall_performance["correct_diagnoses"], 4)
        self.assertEqual(self.game.route.overall_performance["tests_run"], 8)
        self.assertEqual(self.game.route.shift_history[-1].net_pay, expected_net_pay)
        self.assertEqual(
            self.game.route.shift_history[-1].ending_balance,
            payroll_balance,
        )

        self.game.route.record_ticket_purchase("lumora_canopy")
        self.game.begin_ending_sequence("lumora_canopy")
        self.assertEqual(self.game.state, GameState.ENDING)
        self.assertEqual(self.game.current_destination, get_destination(3))
        self.game.finish_ending_sequence()
        self.assertEqual(self.game.state, GameState.ARRIVAL)
        self.assertEqual(self.game.current_destination, get_destination(3))
        self.game.draw()
        self.game.handle_arrival_click(self.game.arrival_begin_button.center)

        self.assertEqual(self.game.state, GameState.TITLE)
        self.assertEqual(self.game.day_number, 3)
        self.assertEqual(
            [entry["create"]().name for entry in self.game.waiting_room_queue],
            ["Velli Mosswhistle", "Gribble Sporekin", "Oola Dewdrop", "Krix Lanternback"],
        )
        self.assertEqual(self.game.player.balance, payroll_balance)
        self.assertEqual(
            self.game.player.machine_levels,
            {"TEMPERATURE": 2, "NEURAL SCAN": 2},
        )
        self.assertEqual(self.game.player.free_test_machines, {"OXYGEN SCAN"})
        self.assertEqual(self.game.player.test_discount, 3)
        self.assertEqual(self.game.purchased_shop_upgrades, permanent_upgrades)
        self.assertIn("recycler", self.game.purchased_shop_upgrades)
        self.assertFalse(self.game.recycler_used)
        self.assertEqual(self.game.get_return_passage_progress(), passage_progress)
        self.assertEqual(self.game.route.overall_performance["shifts_completed"], 2)

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
                    "Training shift complete. The Galactic Route Map handles every clinic departure.",
                ),
                ("YOU", "So I choose where the clinic goes next?"),
                (
                    "CLINIC SYSTEM",
                    "Select a destination and secure its ticket before departure.",
                ),
            ),
        )
        self.game.advance_route_briefing()
        self.assertEqual(self.game.route_briefing_index, 1)
        self.game.advance_route_briefing()
        self.assertEqual(self.game.route_briefing_index, 2)
        self.game.advance_route_briefing()

        self.assertTrue(self.game.route_briefing_seen)
        self.assertEqual(self.game.state, GameState.ROUTE_MAP)
        self.assertFalse(self.game.route.arrival_pending)
        self.assertEqual(self.game.current_destination, get_destination(1))
        self.assertEqual(
            self.game.route.selected_map_destination.key,
            "triska_station",
        )

    def test_route_map_blocks_roster_advancement_until_ticketed_travel(self):
        original_roster = tuple(
            entry["create"]().name for entry in self.game.waiting_room_queue
        )
        self.game.route_briefing_seen = True
        self.game.state = GameState.SHOP
        self.game.handle_shop_click(self.game.shop_button.center)

        self.assertEqual(self.game.state, GameState.ROUTE_MAP)
        self.assertEqual(self.game.current_destination, get_destination(1))
        self.assertFalse(self.game.route.arrival_pending)
        self.assertEqual(
            tuple(entry["create"]().name for entry in self.game.waiting_room_queue),
            original_roster,
        )
        with self.assertRaisesRegex(ValueError, "purchased destination ticket"):
            self.game.route.begin_travel("triska_station")
        self.assertEqual(self.game.current_destination, get_destination(1))

        triska = get_map_destination("triska_station")
        self.game.handle_route_map_click(
            self.game.get_route_map_node_center(triska)
        )
        self.assertEqual(
            self.game.route.selected_map_destination.key,
            "triska_station",
        )
        self.assertEqual(
            self.game.route.get_destination_state("triska_station", selected=True),
            DestinationState.TICKET_REQUIRED,
        )
        self.game.handle_route_map_click(
            self.game.route_map_purchase_button.center
        )
        self.assertEqual(self.game.player.balance, 0)
        self.assertIn(
            "triska_station",
            self.game.route.purchased_ticket_keys,
        )
        self.assertEqual(
            self.game.route.get_destination_state("triska_station", selected=True),
            DestinationState.READY_TO_TRAVEL,
        )
        self.game.handle_route_map_click(self.game.route_map_travel_button.center)
        self.assertEqual(self.game.state, GameState.ENDING)
        self.assertTrue(self.game.route.arrival_pending)
        self.assertEqual(self.game.current_destination, get_destination(2))
        # Roster loading remains deferred until the Arrival screen is accepted.
        self.assertEqual(
            tuple(entry["create"]().name for entry in self.game.waiting_room_queue),
            original_roster,
        )

    def test_basic_route_map_draws_every_node_and_support_controls(self):
        self.game.route_briefing_seen = True
        self.game.state = GameState.SHOP
        self.game.handle_shop_click(self.game.shop_button.center)
        self.game.draw()

        self.assertEqual(self.game.state, GameState.ROUTE_MAP)
        self.assertEqual(len(self.game.route_map_stars), 92)
        self.assertTrue(
            all(
                self.game.route_map_area.collidepoint(
                    self.game.get_route_map_node_center(destination)
                )
                for destination in MAP_DESTINATIONS
            )
        )
        self.assertEqual(
            self.game.get_help_context()[0],
            "GALACTIC ROUTE MAP",
        )
        self.assertEqual(
            self.game.get_tutorial_action_label(),
            "RETURN TO ROUTE MAP",
        )

    def test_blackglass_contract_shows_shortfall_and_opens_supervisor(self):
        """Accepting work starts the playable contract without spending money."""

        game = self.open_first_route_map_with_balance(80)
        game.finish_route_map_tutorial()
        blackglass = get_map_destination("blackglass_outpost")
        game.route.select_map_destination(blackglass.key)
        game.route_map_message = game.get_route_map_selection_message(blackglass)

        self.assertEqual(
            game.route.get_destination_state(blackglass.key, selected=True),
            DestinationState.EMERGENCY_CONTRACT,
        )
        self.assertEqual(game.get_blackglass_credit_shortfall(), 20)
        starting_balance = game.player.balance
        starting_travel_state = game.route.travel_state
        game.draw()
        game.handle_route_map_click(game.route_map_purchase_button.center)

        self.assertEqual(game.state, GameState.BLACKGLASS_BOSS)
        self.assertEqual(game.player.balance, starting_balance)
        self.assertEqual(game.route.travel_state, starting_travel_state)
        self.assertEqual(
            game.get_help_context()[0],
            "BLACKGLASS SUPERVISOR",
        )
        game.draw()
        self.assertEqual(game.blackglass_detour["target_key"], "triska_station")

    def test_blackglass_contract_is_not_needed_when_ticket_is_funded(self):
        game = self.open_first_route_map_with_balance(TRISKA_TICKET_COST)
        game.finish_route_map_tutorial()
        blackglass = get_map_destination("blackglass_outpost")
        game.route.select_map_destination(blackglass.key)
        game.handle_route_map_click(game.route_map_purchase_button.center)

        self.assertEqual(game.state, GameState.ROUTE_MAP)
        self.assertEqual(game.get_blackglass_credit_shortfall(), 0)
        self.assertIn("already fully funded", game.route_map_message)

    def test_route_map_exit_round_trip_preserves_navigation_state(self):
        """Returning to Shop must not reopen a shift or lose a paid ticket."""

        game = self.open_first_route_map_with_balance(140)
        game.finish_route_map_tutorial()
        game.handle_route_map_click(game.route_map_purchase_button.center)
        selected_key = game.route.selected_map_destination.key
        travel_state = game.route.travel_state
        balance = game.player.balance
        completed = game.route.completed_destinations

        game.open_exit_confirmation()
        game.handle_exit_confirmation_click(game.exit_reception_button.center)
        self.assertEqual(game.state, GameState.SHOP)
        self.assertEqual(game.route.travel_state, travel_state)
        self.assertEqual(game.player.balance, balance)
        self.assertEqual(game.route.completed_destinations, completed)

        game.handle_shop_click(game.shop_button.center)
        self.assertEqual(game.state, GameState.ROUTE_MAP)
        self.assertEqual(game.route.selected_map_destination.key, selected_key)
        self.assertEqual(game.route.travel_state, travel_state)
        self.assertIn("triska_station", game.route.purchased_ticket_keys)

    def test_first_map_tutorial_adapts_to_ticket_affordability(self):
        """Only a short player should be routed through the Blackglass lesson."""

        game = self.open_first_route_map_with_balance(80)
        self.assertTrue(game.route_map_tutorial_active)
        self.assertEqual(game.route_map_tutorial_step, "introduction")
        game.handle_route_map_tutorial_click((10, 10))
        self.assertEqual(game.route_map_tutorial_step, "next_destination")
        game.handle_route_map_tutorial_click(
            game.get_route_map_node_center(game.route.next_destination)
        )
        game.handle_route_map_tutorial_click((10, 10))
        game.handle_route_map_tutorial_click((10, 10))
        earth = get_map_destination("earth")
        game.handle_route_map_tutorial_click(
            game.get_route_map_node_center(earth)
        )
        game.handle_route_map_tutorial_click((10, 10))
        self.assertEqual(game.route_map_tutorial_step, "blackglass")

        blackglass = get_map_destination("blackglass_outpost")
        game.handle_route_map_tutorial_click(
            game.get_route_map_node_center(blackglass)
        )
        self.assertEqual(game.route_map_tutorial_step, "blackglass_contract")
        game.handle_route_map_tutorial_click((10, 10))
        game.handle_route_map_tutorial_click(
            game.get_route_map_node_center(game.route.current_location)
        )
        game.handle_route_map_tutorial_click((10, 10))
        self.assertFalse(game.route_map_tutorial_active)
        self.assertTrue(game.route_map_tutorial_seen)
        self.assertEqual(game.player.balance, 80)
        self.assertEqual(game.route.purchased_ticket_keys, set())
        self.assertEqual(
            game.route.selected_map_destination.key,
            "triska_station",
        )

        # A separate funded campaign follows the shorter branch.
        pygame.quit()
        self.game = CosmicClinicGUI(card_seed=151)
        self.game.finish_guided_tutorial()
        funded = self.open_first_route_map_with_balance(140)
        funded.handle_route_map_tutorial_click((10, 10))
        funded.handle_route_map_tutorial_click(
            funded.get_route_map_node_center(funded.route.next_destination)
        )
        funded.handle_route_map_tutorial_click((10, 10))
        funded.handle_route_map_tutorial_click((10, 10))
        funded.handle_route_map_tutorial_click(
            funded.get_route_map_node_center(earth)
        )
        funded.handle_route_map_tutorial_click((10, 10))
        self.assertEqual(funded.route_map_tutorial_step, "completed_planet")

    def test_destination_states_cover_the_route_map_contract(self):
        route = RouteController(starting_credits=100)
        self.assertEqual(
            route.get_destination_state("training_orbit"),
            DestinationState.CURRENT_LOCATION,
        )
        self.assertEqual(
            route.get_destination_state("triska_station"),
            DestinationState.LOCKED,
        )
        self.assertEqual(
            route.get_destination_state("blackglass_outpost"),
            DestinationState.UNKNOWN_DESTINATION,
        )

        route.complete_current_shift(
            ShiftPerformance(
                destination_key="training_orbit",
                day_number=1,
                patients_seen=4,
                correct_diagnoses=4,
                supported_diagnoses=4,
                wrong_diagnoses=0,
                patients_lost=0,
                tests_run=7,
                net_pay=100,
                ending_balance=200,
            )
        )
        self.assertEqual(
            route.get_destination_state("training_orbit"),
            DestinationState.SHIFT_COMPLETE,
        )
        self.assertEqual(
            route.get_destination_state("triska_station", selected=True),
            DestinationState.TICKET_REQUIRED,
        )
        route.record_ticket_purchase("triska_station")
        self.assertEqual(
            route.get_destination_state("triska_station"),
            DestinationState.TICKET_OWNED,
        )
        self.assertEqual(
            route.get_destination_state("triska_station", selected=True),
            DestinationState.READY_TO_TRAVEL,
        )
        route.begin_travel("triska_station")
        route.begin_current_shift()
        self.assertEqual(
            route.get_destination_state("training_orbit"),
            DestinationState.NO_NEW_PATIENTS,
        )
        self.assertEqual(
            route.get_destination_state("triska_station"),
            DestinationState.CURRENT_LOCATION,
        )

    def test_earth_return_passage_is_purchased_and_used_from_route_map(self):
        """Earth should be a gold map ticket, not a Supply Shop product."""

        self.travel_to_day_three()
        self.game.player.balance = RETURN_PASSAGE_COST
        self.game.begin_ending_sequence()

        self.assertEqual(self.game.state, GameState.ROUTE_MAP)
        self.assertTrue(self.game.route.route_is_complete)
        self.assertEqual(self.game.route.selected_map_destination.key, "earth")
        self.assertFalse(self.game.has_return_passage())
        self.assertEqual(self.game.get_return_passage_progress(), 1.0)

        self.game.handle_route_map_click(
            self.game.route_map_purchase_button.center
        )
        self.assertEqual(self.game.player.balance, 0)
        self.assertTrue(self.game.has_return_passage())
        self.assertIn("earth", self.game.route.purchased_ticket_keys)
        self.assertNotIn("return_passage", self.game.purchased_shop_upgrades)
        self.assertEqual(
            self.game.route.get_destination_state("earth", selected=True),
            DestinationState.READY_TO_TRAVEL,
        )
        self.game.draw()

        self.game.handle_route_map_click(self.game.route_map_travel_button.center)
        self.assertEqual(self.game.state, GameState.ENDING)
        self.assertTrue(self.game.homecoming_started)
        self.assertNotIn("earth", self.game.route.purchased_ticket_keys)
        self.assertIn("earth", self.game.route.used_ticket_keys)

    def test_route_briefing_does_not_repeat_after_the_training_destination(self):
        self.game.route_briefing_seen = True
        self.travel_to_day_two()
        self.game.state = GameState.SHOP

        self.game.handle_shop_click(self.game.shop_button.center)

        self.assertEqual(self.game.state, GameState.ROUTE_MAP)
        self.assertFalse(self.game.route.arrival_pending)
        self.assertEqual(self.game.current_destination, get_destination(2))
        self.assertEqual(self.game.route.next_destination, get_destination(3))
        self.assertFalse(self.game.route.route_is_complete)

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
        self.travel_to_day_three()
        day_three_names = tuple(
            entry["create"]().name for entry in self.game.waiting_room_queue
        )

        self.game.begin_ending_sequence()

        self.assertEqual(self.game.state, GameState.ROUTE_MAP)
        self.assertTrue(self.game.route.route_is_complete)
        self.assertIsNone(self.game.route.next_destination)
        self.assertEqual(self.game.day_number, 3)
        self.assertEqual(
            tuple(entry["create"]().name for entry in self.game.waiting_room_queue),
            day_three_names,
        )
        self.assertEqual(self.game.roster_for_day(4), [])

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
        self.game.select_developer_day(3)
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

    def test_f10_exposes_every_lumora_checkpoint_and_restores_live_campaign(self):
        """All Day 3 previews must remain an isolated developer sandbox."""

        self.game.state = GameState.PATIENT
        self.game.patients_called = 2
        self.game.player.balance = 287
        self.game.player.machine_levels["NEURAL SCAN"] = 2
        self.game.player.test_discount = 3
        self.game.purchased_shop_upgrades.update(
            {"neural", "smart_cards", "recycler"}
        )
        self.game.daily_correct_diagnoses = 1
        self.game.daily_wrong_diagnoses = 1
        live_fingerprint = self.game.get_campaign_state_fingerprint()

        self.game.toggle_developer_navigator()
        self.assertEqual(len(self.game.get_developer_day_rects()), 4)
        self.game.select_developer_day(3)
        entries = self.game.get_developer_screen_entries()
        scene_ids = {entry[1] for entry in entries}
        self.assertTrue(
            {
                "arrival",
                "reception",
                "patient_1",
                "patient_2",
                "patient_3",
                "patient_4",
                "shop",
                "route_map",
                "ending",
            }.issubset(scene_ids)
        )
        self.assertEqual(
            [
                self.game.get_developer_checkpoint_label(f"patient_{index}", f"PATIENT {index}")
                for index in range(1, 5)
            ],
            [
                "PATIENT 1  •  VELLI MOSSWHISTLE",
                "PATIENT 2  •  GRIBBLE SPOREKIN",
                "PATIENT 3  •  OOLA DEWDROP",
                "PATIENT 4  •  KRIX LANTERNBACK",
            ],
        )

        expected_states = {
            "arrival": GameState.ARRIVAL,
            "reception": GameState.TITLE,
            "patient_1": GameState.PATIENT,
            "patient_2": GameState.PATIENT,
            "patient_3": GameState.PATIENT,
            "patient_4": GameState.PATIENT,
            "shop": GameState.SHOP,
            "route_map": GameState.ROUTE_MAP,
            "ending": GameState.ENDING,
        }
        expected_patients = {
            "patient_1": "Velli Mosswhistle",
            "patient_2": "Gribble Sporekin",
            "patient_3": "Oola Dewdrop",
            "patient_4": "Krix Lanternback",
        }
        for scene_id, expected_state in expected_states.items():
            self.game.jump_to_developer_screen(
                self.game.get_developer_scene_index(scene_id)
            )
            self.assertEqual(self.game.state, expected_state)
            self.assertEqual(self.game.current_destination, get_destination(3))
            if scene_id in expected_patients:
                self.assertEqual(self.game.patient.name, expected_patients[scene_id])
            self.game.draw()

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
        self.game.select_developer_day(3)
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

    def test_f10_route_preview_preserves_owned_and_used_tickets(self):
        """Developer previews must restore every piece of paid travel state."""

        game = self.open_first_route_map_with_balance(140)
        game.finish_route_map_tutorial()
        game.handle_route_map_click(game.route_map_purchase_button.center)
        live_fingerprint = game.get_campaign_state_fingerprint()
        purchased = game.route.purchased_ticket_keys
        used = game.route.used_ticket_keys

        game.toggle_developer_navigator()
        game.select_developer_day(2)
        game.jump_to_developer_screen(
            game.get_developer_scene_index("route_map")
        )
        self.assertEqual(game.state, GameState.ROUTE_MAP)
        game.draw()

        game.toggle_developer_navigator()
        game.handle_developer_click(game.developer_return_button.center)

        self.assertEqual(game.get_campaign_state_fingerprint(), live_fingerprint)
        self.assertEqual(game.route.purchased_ticket_keys, purchased)
        self.assertEqual(game.route.used_ticket_keys, used)

    def test_every_planet_panel_fits_minimum_and_fullscreen_viewports(self):
        """Every map destination must remain contained at both display extremes."""

        game = self.open_first_route_map_with_balance(80)
        game.finish_route_map_tutorial()
        panel = game.route_map_ticket_panel
        logical_canvas = pygame.Rect((0, 0), WINDOW_SIZE)
        self.assertTrue(logical_canvas.contains(panel))
        self.assertTrue(panel.contains(game.route_map_purchase_button))
        self.assertTrue(panel.contains(game.route_map_travel_button))

        description_box = pygame.Rect(
            panel.x + 22,
            panel.y + 105,
            panel.width - 44,
            64,
        )
        message_width = panel.width - 42
        for destination in MAP_DESTINATIONS:
            game.route.select_map_destination(destination.key)
            game.route_map_message = game.get_route_map_selection_message(
                destination
            )
            game.draw()

            subtitle = destination.subtitle.upper()
            self.assertLessEqual(
                game.compact_ui_font.size(subtitle)[0],
                panel.width - 40,
                destination.key,
            )
            description_lines = game.wrap_text(
                destination.map_data.description,
                game.small_font,
                description_box.width,
            )
            description_height = sum(
                game.small_font.size(line)[1]
                for line in description_lines
            ) + max(0, len(description_lines) - 1) * 2
            self.assertLessEqual(
                description_height,
                description_box.height,
                destination.key,
            )
            self.assertLessEqual(
                game.compact_ui_font.size(game.route_map_message)[0],
                message_width,
                destination.key,
            )

        for display_size in (MIN_WINDOW_SIZE, (1920, 1080)):
            game.resize_display(display_size)
            game.draw()
            game.present_frame()
            top_left = game.game_to_window_position(panel.topleft)
            bottom_right = game.game_to_window_position(panel.bottomright)
            self.assertTrue(game.display_viewport.collidepoint(top_left))
            self.assertLessEqual(bottom_right[0], game.display_viewport.right)
            self.assertLessEqual(bottom_right[1], game.display_viewport.bottom)

        game.toggle_fullscreen()
        game.draw()
        game.present_frame()
        top_left = game.game_to_window_position(panel.topleft)
        bottom_right = game.game_to_window_position(panel.bottomright)
        self.assertTrue(game.display_viewport.collidepoint(top_left))
        self.assertLessEqual(bottom_right[0], game.display_viewport.right)
        self.assertLessEqual(bottom_right[1], game.display_viewport.bottom)


if __name__ == "__main__":
    unittest.main()
