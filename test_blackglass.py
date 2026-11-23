"""Tests for the Blackglass Outpost debt detour."""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from PlanetData import (
    BLACKGLASS_DESTINATION,
    DESTINATIONS,
    get_any_destination,
    get_blackglass_destination,
    get_modifier,
    validate_blackglass_destination,
)
from Player import (
    BLACKGLASS_CONTRACT_PAYOUT,
    BLACKGLASS_DEBT_THRESHOLD,
    BLACKGLASS_MAX_DAYS,
    DEBT_LIMIT,
    DIAGNOSIS_REWARD,
    DRAW_COST,
    STARTING_BALANCE,
)
from gui_main import CosmicClinicGUI
from gui_state import GameState


class BlackglassDataTests(unittest.TestCase):
    def test_blackglass_is_a_fallback_outside_the_route(self):
        self.assertTrue(validate_blackglass_destination())
        self.assertNotIn(BLACKGLASS_DESTINATION, DESTINATIONS)
        self.assertIs(get_any_destination("blackglass_outpost"), BLACKGLASS_DESTINATION)
        self.assertEqual(BLACKGLASS_DESTINATION.theme.scene, "blackglass_outpost")

    def test_modifiers_match_the_design(self):
        self.assertEqual(get_modifier(BLACKGLASS_DESTINATION, "draw_cost"), 1.0)
        self.assertEqual(get_modifier(BLACKGLASS_DESTINATION, "test_cost_multiplier"), 0.25)
        self.assertEqual(get_modifier(BLACKGLASS_DESTINATION, "patient_leave_chance"), 0.0)
        self.assertLess(get_modifier(BLACKGLASS_DESTINATION, "reward_multiplier"), 1.0)
        self.assertEqual(get_modifier(DESTINATIONS[0], "draw_cost", 99), 99)

    def test_every_blackglass_day_has_four_patients(self):
        for day in range(1, BLACKGLASS_MAX_DAYS + 1):
            self.assertEqual(len(get_blackglass_destination(day).patient_roster), 4)


class BlackglassFlowTests(unittest.TestCase):
    def setUp(self):
        self.game = CosmicClinicGUI(card_seed=3)
        self.game.finish_intro()
        self.game.finish_intro_dialogue()
        self.game.finish_guided_tutorial()
        self.game.tutorial_open = False
        self.game.state = GameState.TITLE

    # -- helpers ---------------------------------------------------------
    def finish_shift(self, correct=0, evidence=0, wrong=0):
        """End the current shift with a chosen result and click the payroll button."""

        game = self.game
        game.daily_correct_diagnoses = correct
        game.daily_evidence_cases = evidence
        game.daily_wrong_diagnoses = wrong
        game.state = GameState.DAY_COMPLETE
        game.handle_day_complete_click(game.day_complete_button.center)

    def finish_dialogue(self):
        while self.game.state == GameState.BLACKGLASS_BOSS:
            self.game.advance_blackglass_boss_dialogue()

    def enter_blackglass(self):
        self.finish_shift(wrong=5)  # 100 - 175 - 50 = -125
        self.assertEqual(self.game.state, GameState.BLACKGLASS_BOSS)
        self.finish_dialogue()
        self.assertEqual(self.game.state, GameState.ARRIVAL)
        self.game.handle_arrival_click(self.game.arrival_begin_button.center)
        self.assertEqual(self.game.state, GameState.TITLE)

    # -- trigger ---------------------------------------------------------
    def test_shift_above_threshold_opens_the_shop_as_before(self):
        self.finish_shift(wrong=4)  # 100 - 140 - 50 = -90
        self.assertEqual(self.game.player.balance, -90)
        self.assertEqual(self.game.state, GameState.SHOP)
        self.assertIsNone(self.game.blackglass_detour)

    def test_shift_at_exact_threshold_triggers_the_detour(self):
        self.game.player.balance = 150
        self.finish_shift(wrong=7)  # 150 - 245 - 50 = -145 (below)
        self.assertEqual(self.game.state, GameState.BLACKGLASS_BOSS)

    def test_boss_reprimand_then_travel_to_blackglass(self):
        self.finish_shift(wrong=5)
        game = self.game
        self.assertEqual(game.state, GameState.BLACKGLASS_BOSS)
        self.assertLessEqual(game.player.balance, BLACKGLASS_DEBT_THRESHOLD)
        text = " ".join(line for _, line in game.blackglass_boss_lines)
        self.assertIn("unacceptable", text)
        self.assertIn("Blackglass", text)
        self.assertEqual(game.blackglass_detour["return_key"], DESTINATIONS[0].key)
        self.finish_dialogue()
        self.assertEqual(game.state, GameState.ARRIVAL)
        game.handle_arrival_click(game.arrival_begin_button.center)
        self.assertEqual(game.state, GameState.TITLE)
        self.assertEqual(game.current_destination.key, "blackglass_outpost")
        self.assertIn("DEBT SHIFT 1", game.get_location_subtitle())

    def test_planet_shift_is_filed_once_and_route_is_untouched(self):
        self.finish_shift(wrong=5)
        route = self.game.route
        self.assertEqual(len(route.shift_history), 1)
        self.finish_dialogue()
        self.game.handle_arrival_click(self.game.arrival_begin_button.center)
        self.assertEqual(route.current_destination.key, DESTINATIONS[0].key)
        self.assertEqual(len(route.shift_history), 1)
        self.assertFalse(route.arrival_pending)

    # -- Blackglass rules -------------------------------------------------
    def test_blackglass_rules_apply_during_the_detour(self):
        self.enter_blackglass()
        game = self.game
        self.assertEqual(game.get_random_draw_cost(), 1)
        self.assertEqual(game.player.test_cost_multiplier, 0.25)
        self.assertLess(game.get_debt_limit(), DEBT_LIMIT)
        self.assertEqual(game.get_operating_fee(), 0)
        self.assertEqual(game.scale_case_reward(DIAGNOSIS_REWARD), DIAGNOSIS_REWARD // 2)
        self.assertTrue(game.can_spend_clinic_funds(5))  # deep in debt, still allowed

    def test_tests_cost_a_quarter_price(self):
        self.enter_blackglass()
        normal = self.game.player.test_hand[0].value
        self.game.player.test_cost_multiplier = 1.0
        full = self.game.player.get_test_cost(normal)
        self.game.player.test_cost_multiplier = 0.25
        self.assertEqual(self.game.player.get_test_cost(normal), max(1, round(full * 0.25)))

    def test_patients_never_leave_at_blackglass(self):
        self.enter_blackglass()
        game = self.game
        self.assertEqual(game.get_destination_modifier("patient_leave_chance", 1.0), 0.0)

    def test_generic_rudeness_pass_skips_bespoke_voices(self):
        from PatientData import create_flersch, create_snelly

        self.enter_blackglass()
        # Generic patients are rewritten rudely at Blackglass...
        rude = self.game.apply_patient_rudeness(create_flersch())
        self.assertTrue(
            any(line.startswith(("Ugh.", "Tch.", "Hurry up")) for line in rude.dialogue)
        )
        # ...but characters with their own voice keep it.
        snelly = self.game.apply_patient_rudeness(create_snelly())
        self.assertEqual(snelly.dialogue, create_snelly().dialogue)

    def test_normal_planets_keep_normal_prices(self):
        game = self.game
        self.assertEqual(game.get_random_draw_cost(), DRAW_COST)
        self.assertEqual(game.player.test_cost_multiplier, 1.0)
        self.assertEqual(game.get_debt_limit(), DEBT_LIMIT)
        self.assertFalse(
            any(line.startswith(("Ugh.", "Tch.")) for line in game.patient.dialogue)
        )

    # -- outcomes ---------------------------------------------------------
    def test_clearing_debt_on_day_one_preserves_earned_balance(self):
        self.enter_blackglass()
        self.game.player.balance = -10
        self.finish_shift(correct=2, evidence=2)  # +50 -> $40, +$100 contract pay
        game = self.game
        self.assertEqual(game.state, GameState.BLACKGLASS_BOSS)
        self.assertEqual(game.blackglass_boss_action, "return")
        self.finish_dialogue()
        self.assertEqual(game.state, GameState.SHOP)
        self.assertIsNone(game.blackglass_detour)
        self.assertEqual(game.player.balance, 40 + BLACKGLASS_CONTRACT_PAYOUT)
        self.assertEqual(game.current_destination.key, DESTINATIONS[0].key)
        self.assertEqual(game.route.available_credits, 40 + BLACKGLASS_CONTRACT_PAYOUT)

    def test_still_in_debt_after_day_one_continues_to_day_two(self):
        self.enter_blackglass()
        self.finish_shift(correct=1, evidence=1)  # -125 + 25 = -100
        game = self.game
        self.assertLess(game.player.balance, 0)
        self.assertEqual(game.blackglass_boss_action, "next_day")
        self.finish_dialogue()
        self.assertEqual(game.state, GameState.TITLE)
        self.assertEqual(game.blackglass_detour["day"], 2)
        self.assertIn("DEBT SHIFT 2", game.get_location_subtitle())
        self.assertEqual(game.patients_called, 0)

    def test_debt_is_forgiven_after_day_two(self):
        self.enter_blackglass()
        self.finish_shift(correct=1, evidence=1)
        self.finish_dialogue()
        self.finish_shift(correct=1, evidence=1)  # still negative
        game = self.game
        self.assertLess(game.player.balance, 0)
        self.assertEqual(game.blackglass_boss_action, "return")
        text = " ".join(line for _, line in game.blackglass_boss_lines)
        self.assertIn("Consider it paid", text)
        self.assertEqual(game.blackglass_boss_lines[0][0], "OUTPOST BOSS")
        self.finish_dialogue()
        self.assertEqual(game.state, GameState.SHOP)
        self.assertIsNone(game.blackglass_detour)
        self.assertEqual(game.player.balance, BLACKGLASS_CONTRACT_PAYOUT)
        self.assertEqual(game.current_destination.key, DESTINATIONS[0].key)

    def test_clearing_debt_on_day_two_also_returns(self):
        self.enter_blackglass()
        self.finish_shift(correct=1, evidence=1)
        self.finish_dialogue()
        self.game.player.balance = -5
        self.finish_shift(correct=1, evidence=1)
        self.assertIn("Debt cleared", " ".join(l for _, l in self.game.blackglass_boss_lines))
        self.finish_dialogue()
        self.assertEqual(self.game.player.balance, 20 + BLACKGLASS_CONTRACT_PAYOUT)

    def test_debt_contract_always_affords_the_next_ticket(self):
        from PlanetData import TRISKA_TICKET_COST

        self.enter_blackglass()
        self.game.player.balance = -900  # a disastrous stint
        for _ in range(BLACKGLASS_MAX_DAYS):
            self.finish_shift()
            self.finish_dialogue()
        self.assertIsNone(self.game.blackglass_detour)
        self.assertGreaterEqual(self.game.player.balance, TRISKA_TICKET_COST)

    def test_wrong_diagnosis_is_free_at_blackglass(self):
        self.assertGreater(self.game.get_wrong_diagnosis_penalty(), 0)
        self.enter_blackglass()
        game = self.game
        self.assertEqual(game.get_wrong_diagnosis_penalty(), 0)
        before = game.get_live_balance()
        game.daily_wrong_diagnoses = 3
        self.assertEqual(game.get_live_balance(), before)
        self.assertEqual(game.get_daily_pay_breakdown()[1], 0)

    def test_recycling_a_test_card_refunds_one_draw(self):
        game = self.game
        self.assertEqual(game.get_recycle_refund(), 0)  # med-waste on planets
        self.enter_blackglass()
        game.state = GameState.PATIENT
        game.showing_diagnosis_hand = False
        game.selected_card_index = 0
        before = game.get_live_balance()
        self.assertTrue(game.discard_selected_test())
        self.assertEqual(game.get_live_balance(), before + game.get_random_draw_cost())
        self.assertEqual(game.daily_recycle_refunds, 1)

    def test_never_more_than_two_blackglass_shifts(self):
        self.enter_blackglass()
        shifts_played = 0
        while self.game.blackglass_detour is not None and shifts_played < 10:
            self.finish_shift()  # earns nothing, so debt never clears
            shifts_played += 1
            self.finish_dialogue()
        self.assertEqual(shifts_played, BLACKGLASS_MAX_DAYS)
        self.assertEqual(self.game.state, GameState.SHOP)

    def test_returning_resumes_the_route_map_normally(self):
        self.enter_blackglass()
        self.game.player.balance = -20
        self.finish_shift(correct=4, evidence=4)  # +112 with the perfect-day bonus
        self.finish_dialogue()
        self.assertEqual(self.game.state, GameState.SHOP)
        self.game.open_route_map()
        self.assertEqual(self.game.state, GameState.ROUTE_MAP)
        self.assertEqual(self.game.route.available_credits, self.game.player.balance)
        self.assertTrue(self.game.route.current_is_complete)

    # -- safety -----------------------------------------------------------
    def test_restarting_a_blackglass_shift_does_not_reopen_the_planet(self):
        self.enter_blackglass()
        route = self.game.route
        history = len(route.shift_history)
        self.game.restart_current_shift()
        self.assertEqual(len(route.shift_history), history)
        self.assertTrue(route.current_is_complete)
        self.assertEqual(self.game.current_destination.key, "blackglass_outpost")

    def test_skipping_the_dialogue_still_advances_the_flow(self):
        self.finish_shift(wrong=5)
        self.game.finish_blackglass_boss_dialogue()
        self.assertEqual(self.game.state, GameState.ARRIVAL)

    def test_restart_game_clears_the_detour(self):
        self.enter_blackglass()
        self.game.restart_game()
        self.assertIsNone(self.game.blackglass_detour)
        self.assertEqual(self.game.current_destination.key, DESTINATIONS[0].key)
        self.assertEqual(self.game.player.balance, STARTING_BALANCE)

    def test_ticket_contract_uses_shortfall_dialogue_and_returns_to_map(self):
        game = self.game
        game.player.balance = 80
        game.open_route_map()
        game.finish_route_map_tutorial()
        game.route.select_map_destination("blackglass_outpost")
        game.handle_route_map_click(game.route_map_purchase_button.center)
        self.assertEqual(game.state, GameState.BLACKGLASS_BOSS)
        self.assertEqual(game.blackglass_detour["mode"], "ticket")
        dialogue = " ".join(line for _, line in game.blackglass_boss_lines)
        self.assertIn("short", dialogue)
        self.assertNotIn("in debt", dialogue)
        self.finish_dialogue()
        game.handle_arrival_click(game.arrival_begin_button.center)
        game.player.balance = 160
        self.finish_shift()
        self.finish_dialogue()
        self.assertEqual(game.state, GameState.ROUTE_MAP)
        self.assertEqual(game.player.balance, 160)
        self.assertEqual(game.route.selected_map_destination.key, "triska_station")

    def test_ticket_contract_continues_until_the_ticket_is_funded(self):
        game = self.game
        game.player.balance = 10
        game.open_route_map()
        game.finish_route_map_tutorial()
        game.route.select_map_destination("blackglass_outpost")
        game.handle_route_map_click(game.route_map_purchase_button.center)
        self.finish_dialogue()
        game.handle_arrival_click(game.arrival_begin_button.center)
        self.finish_shift()
        self.assertEqual(game.blackglass_boss_action, "next_day")

    def test_every_detour_screen_renders(self):
        game = self.game
        game.player.balance = -125
        game.state = GameState.DAY_COMPLETE
        game.draw()
        self.finish_shift(wrong=5)
        for index in range(len(game.blackglass_boss_lines)):
            game.blackglass_boss_index = index
            game.draw()
        self.finish_dialogue()
        game.draw()  # arrival
        game.handle_arrival_click(game.arrival_begin_button.center)
        game.draw()  # reception
        game.state = GameState.DAY_COMPLETE
        game.draw()

    def test_f10_lists_blackglass_and_restores_the_live_campaign(self):
        game = self.game
        game.player.balance = 73
        game.toggle_developer_navigator()
        game.select_developer_day(0)
        scene_ids = {entry[1] for entry in game.get_developer_screen_entries()}
        self.assertEqual(
            scene_ids,
            {
                "blackglass_boss", "arrival", "reception", "patient_1",
                "patient_2", "patient_3", "patient_4", "recap",
            },
        )
        reception_index = game.get_developer_scene_index("reception")
        game.jump_to_developer_screen(reception_index)
        self.assertEqual(game.current_destination.key, "blackglass_outpost")
        self.assertEqual(game.state, GameState.TITLE)
        game.restore_developer_campaign_snapshot()
        self.assertEqual(game.player.balance, 73)
        self.assertIsNone(game.blackglass_detour)

    def test_blackglass_ambience_is_configured_and_selected(self):
        self.assertEqual(BLACKGLASS_DESTINATION.ambience, "blackglass_industrial")
        self.enter_blackglass()
        self.game.draw()
        if self.game.audio_available:
            self.assertIn("blackglass_industrial", self.game.destination_ambience)
            self.assertEqual(
                self.game.destination_ambience_key,
                "blackglass_industrial",
            )


if __name__ == "__main__":
    unittest.main()
