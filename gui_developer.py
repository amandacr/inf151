"""Hidden checkpoint navigator used to preview the game during development."""

import copy

import pygame

from gui_state import GameState
from gui_theme import COLORS, WINDOW_SIZE
from Tests.catalog import create_test_catalog


DEVELOPER_SCREENS = (
    ("I", "intro", "OPENING STORY", GameState.INTRO),
    ("R", "reception", "RECEPTION", GameState.TITLE),
    ("1", "patient_1", "PATIENT 1", GameState.PATIENT),
    ("2", "patient_2", "PATIENT 2", GameState.PATIENT),
    ("3", "patient_3", "PATIENT 3", GameState.PATIENT),
    ("4", "patient_4", "PATIENT 4", GameState.PATIENT),
    ("C", "recap", "PAYROLL RECAP", GameState.DAY_COMPLETE),
    ("S", "shop", "SHOP", GameState.SHOP),
    ("B", "route_briefing", "ROUTE BRIEFING", GameState.ROUTE_BRIEFING),
    ("D", "ending", "DEPART PLANET", GameState.ENDING),
    ("A", "arrival", "PLANET ARRIVAL", GameState.ARRIVAL),
    ("F", "final", "ROUTE COMPLETE", GameState.FINAL),
    ("G", "homecoming", "GO HOME", GameState.ENDING),
)

DEVELOPER_KEY_MAP = {
    pygame.K_i: "intro",
    pygame.K_r: "reception",
    pygame.K_1: "patient_1",
    pygame.K_2: "patient_2",
    pygame.K_3: "patient_3",
    pygame.K_4: "patient_4",
    pygame.K_c: "recap",
    pygame.K_s: "shop",
    pygame.K_b: "route_briefing",
    pygame.K_d: "ending",
    pygame.K_a: "arrival",
    pygame.K_f: "final",
    pygame.K_g: "homecoming",
}


DEVELOPER_SNAPSHOT_FIELDS = (
    "state",
    "route",
    "player",
    "deck",
    "notebook",
    "patient",
    "patients_called",
    "patient_dialogue_index",
    "daily_correct_diagnoses",
    "daily_wrong_diagnoses",
    "daily_test_count",
    "daily_test_expenses",
    "daily_evidence_cases",
    "daily_payout_applied",
    "daily_card_shop_expenses",
    "daily_card_shop_purchases",
    "daily_patients_lost",
    "daily_draw_expenses",
    "money_deduction_animation",
    "recycler_used",
    "purchased_shop_upgrades",
    "selected_shop_upgrade",
    "shop_scroll_row",
    "shop_message",
    "route_briefing_seen",
    "route_briefing_index",
    "showing_health_id",
    "showing_diagnosis_hand",
    "hovered_card_index",
    "selected_card_index",
    "run_test_button",
    "discard_button",
    "play_diagnosis_button",
    "diagnosis_confirmation_open",
    "diagnosis_folder_animation_started_at",
    "discard_pile",
    "discard_animation",
    "pending_test_discard",
    "pending_diagnosis_discard",
    "note_transfer_animation",
    "notebook_attention_started_at",
    "notebook_columns",
    "notebook_spread",
    "notebook_preview_progress",
    "notebook_preview_last_tick",
    "last_test_name",
    "last_test_result",
    "last_test_cost",
    "last_diagnosis",
    "diagnosis_correct",
    "last_diagnosis_supported",
    "patient_left",
    "patient_leave_text",
    "patient_wrong_diagnoses",
    "advance_case_after_discard",
    "card_draw_notice",
    "card_draw_notice_started_at",
    "card_shop_open",
    "selected_card_shop_test",
    "card_shop_message",
    "card_shop_notice",
    "card_shop_notice_started_at",
    "card_shop_patient_purchases",
    "reception_transition_started_at",
    "queue_shift_started_at",
    "patient_fade_started_at",
    "end_day_shutdown_started_at",
    "test_result_started_at",
    "ending_started_at",
    "ending_duration",
    "homecoming_started",
    "arrival_started_at",
    "exit_confirmation_open",
    "exit_confirmation_opened_at",
    "guided_tutorial_active",
    "guided_tutorial_step",
    "guided_tutorial_step_started_at",
    "guided_tutorial_nudge",
    "guided_tutorial_nudge_started_at",
    "tutorial_open",
    "tutorial_opened_at",
    "help_attention_started_at",
    "help_attention_seen",
    "intro_dialogue_active",
    "intro_dialogue_index",
    "intro_dialogue_started_at",
    "intro_started_at",
    "intro_wake_active",
)


class DeveloperMixin:
    """Provide an F10-only navigator without exposing debug controls to players."""

    def setup_developer_navigator(self):
        self.developer_navigator_open = False
        self.developer_button_rects = []
        self.developer_destination_button_rects = []
        self.developer_day_button_rects = self.developer_destination_button_rects
        self.developer_navigator_level = "destinations"
        self.developer_selected_day = 1
        self.developer_scene_id = None
        self.developer_back_button = pygame.Rect(82, 91, 118, 32)
        self.developer_return_button = pygame.Rect(390, 553, 320, 34)
        self.developer_campaign_snapshot = None
        self.developer_snapshot_started_at = None
        self.developer_preview_active = False

    def capture_developer_campaign_snapshot(self):
        """Preserve the live campaign before entering isolated preview screens."""

        if self.developer_campaign_snapshot is not None:
            return
        snapshot_values = {
            field: getattr(self, field)
            for field in DEVELOPER_SNAPSHOT_FIELDS
            if hasattr(self, field)
        }
        self.developer_campaign_snapshot = copy.deepcopy(snapshot_values)
        self.developer_snapshot_started_at = pygame.time.get_ticks()

    def restore_developer_campaign_snapshot(self):
        """Return from preview without changing route, money, cards, or progress."""

        if self.developer_campaign_snapshot is None:
            return False
        snapshot = self.developer_campaign_snapshot
        paused_for = max(
            0,
            pygame.time.get_ticks() - self.developer_snapshot_started_at,
        )
        for field, value in snapshot.items():
            setattr(self, field, value)
        self.waiting_room_queue = self.roster_for_destination(
            self.route.current_destination
        )
        self.developer_campaign_snapshot = None
        self.developer_snapshot_started_at = None
        self.developer_preview_active = False
        self.developer_navigator_open = False
        self.offset_animation_timers(paused_for)
        self.refresh_hand_layout()
        self.notebook_layout = self.build_notebook_rects()
        return True

    def get_campaign_state_fingerprint(self):
        """Return stable campaign data used by route and F10 regression tests."""

        def card_names(cards):
            return tuple(
                getattr(card.value, "name", str(card.value))
                for card in cards
            )

        notebook_entries = tuple(sorted(
            (
                patient.name,
                tuple(sorted(entries.items())),
                tuple(self.notebook.get_interview(patient)),
            )
            for patient, entries in self.notebook.contents.items()
        ))
        return (
            self.state,
            self.route.current_destination.key,
            tuple(item.key for item in self.route.completed_destinations),
            self.route.shift_history,
            self.route.arrival_pending,
            self.player.balance,
            tuple(sorted(self.player.machine_levels.items())),
            self.player.test_discount,
            tuple(sorted(self.player.free_test_machines)),
            tuple(sorted(self.player.free_tests_used)),
            self.recycler_used,
            tuple(sorted(self.purchased_shop_upgrades)),
            self.patients_called,
            self.patient.name,
            self.patient_dialogue_index,
            card_names(self.player.test_hand),
            card_names(self.player.diagnosis_hand),
            card_names(self.deck.contents),
            notebook_entries,
            self.daily_correct_diagnoses,
            self.daily_wrong_diagnoses,
            self.daily_test_count,
            self.daily_test_expenses,
            self.daily_card_shop_expenses,
            self.daily_draw_expenses,
            self.route_briefing_seen,
            self.route_briefing_index,
            self.ending_duration,
            self.homecoming_started,
            self.guided_tutorial_active,
            self.guided_tutorial_step,
        )

    def toggle_developer_navigator(self):
        """Open or close the hidden preview menu."""

        if not self.developer_navigator_open:
            self.capture_developer_campaign_snapshot()
            self.developer_navigator_open = True
            self.developer_selected_day = self.day_number
            self.developer_navigator_level = "destinations"
            self.developer_scene_id = self.infer_developer_scene_id()
        else:
            self.restore_developer_campaign_snapshot()
        self.play_sfx("button")

    def infer_developer_scene_id(self):
        """Identify the closest clean checkpoint for the visible scene."""

        if self.state == GameState.INTRO:
            return "intro"
        if self.intro_dialogue_active or self.guided_tutorial_active:
            return "intro"
        if self.state in (
            GameState.PATIENT,
            GameState.TEST_RESULT,
            GameState.NOTEBOOK,
            GameState.OUTCOME,
        ):
            patient_index = max(
                0,
                min(self.patients_called - 1, len(self.waiting_room_queue) - 1),
            )
            return f"patient_{patient_index + 1}"
        preferred_scenes = {
            GameState.TITLE: "reception",
            GameState.DAY_COMPLETE: "recap",
            GameState.SHOP: "shop",
            GameState.ROUTE_BRIEFING: "route_briefing",
            GameState.ENDING: "ending",
            GameState.ARRIVAL: "arrival",
            GameState.FINAL: "final",
        }
        return preferred_scenes.get(self.state, "intro")

    def get_developer_screen_rects(self):
        """Return the stable two-column checkpoint-directory layout."""

        screen_count = len(self.get_developer_screen_entries())
        return [
            pygame.Rect(
                92 + (index % 2) * 458,
                170 + (index // 2) * 64,
                432,
                50,
            )
            for index in range(screen_count)
        ]

    def get_developer_day_rects(self):
        """Return destination cards generated from the configured route."""

        return tuple(
            pygame.Rect(
                112 + (index % 2) * 448,
                175 + (index // 2) * 126,
                416,
                102,
            )
            for index in range(len(self.destinations))
        )

    def get_developer_screen_entries(self):
        """Return only checkpoints that belong to the selected destination."""

        destination_index = next(
            index
            for index, destination in enumerate(self.destinations)
            if destination.day_number == self.developer_selected_day
        )
        scene_ids = [
            "reception",
            "patient_1",
            "patient_2",
            "patient_3",
            "patient_4",
            "recap",
            "shop",
            "ending",
        ]
        if destination_index == 0:
            scene_ids.insert(0, "intro")
            scene_ids.insert(scene_ids.index("ending"), "route_briefing")
        else:
            scene_ids.insert(0, "arrival")
        if destination_index == len(self.destinations) - 1:
            scene_ids.append("final")
            scene_ids.append("homecoming")
        entries_by_id = {entry[1]: entry for entry in DEVELOPER_SCREENS}
        return tuple(entries_by_id[scene_id] for scene_id in scene_ids)

    def get_developer_roster(self, day_number=None):
        """Return the selected configured destination's stable preview roster."""

        selected_day = day_number or self.developer_selected_day
        return self.roster_for_day(selected_day)

    def select_developer_day(self, day_number):
        """Open the checkpoint directory for one configured destination."""

        configured_days = {destination.day_number for destination in self.destinations}
        if day_number not in configured_days:
            raise ValueError("The developer navigator requires a configured destination.")
        self.developer_selected_day = day_number
        self.developer_navigator_level = "screens"
        self.play_sfx("button")

    def return_to_developer_destinations(self):
        """Move up one level without closing the developer navigator."""

        self.developer_navigator_level = "destinations"
        self.play_sfx("button")

    def get_developer_scene_index(self, scene_id):
        """Return the directory position for a stable scene identifier."""

        return next(
            index
            for index, entry in enumerate(DEVELOPER_SCREENS)
            if entry[1] == scene_id
        )

    def handle_developer_key(self, key):
        """Choose a destination first, then navigate its checkpoints."""

        if self.developer_navigator_level == "destinations":
            number_keys = (
                pygame.K_1,
                pygame.K_2,
                pygame.K_3,
                pygame.K_4,
                pygame.K_5,
                pygame.K_6,
                pygame.K_7,
                pygame.K_8,
                pygame.K_9,
            )
            if key in number_keys:
                destination_index = number_keys.index(key)
                if destination_index < len(self.destinations):
                    self.select_developer_day(
                        self.destinations[destination_index].day_number
                    )
            elif key == pygame.K_RETURN:
                self.select_developer_day(self.developer_selected_day)
            return

        available_scene_ids = {
            entry[1] for entry in self.get_developer_screen_entries()
        }
        if key in DEVELOPER_KEY_MAP and DEVELOPER_KEY_MAP[key] in available_scene_ids:
            self.jump_to_developer_screen(
                self.get_developer_scene_index(DEVELOPER_KEY_MAP[key])
            )
            return
        if key in (pygame.K_LEFT, pygame.K_RIGHT):
            entries = self.get_developer_screen_entries()
            current_scene_id = self.infer_developer_scene_id()
            scene_ids = [entry[1] for entry in entries]
            current_index = (
                scene_ids.index(current_scene_id)
                if current_scene_id in scene_ids
                else 0
            )
            step = -1 if key == pygame.K_LEFT else 1
            self.jump_to_developer_screen(
                self.get_developer_scene_index(
                    entries[(current_index + step) % len(entries)][1]
                )
            )

    def get_current_developer_scene_index(self):
        """Choose the current special scene, falling back to its base state."""

        if self.developer_scene_id is not None:
            index = self.get_developer_scene_index(self.developer_scene_id)
            if DEVELOPER_SCREENS[index][3] == self.state:
                return index
        return self.get_developer_scene_index(self.infer_developer_scene_id())

    def handle_developer_click(self, position):
        """Jump to the clicked preview destination."""

        if (
            self.developer_preview_active
            and self.developer_return_button.collidepoint(position)
        ):
            self.restore_developer_campaign_snapshot()
            self.play_sfx("button")
            return
        if self.developer_navigator_level == "destinations":
            for destination, rect in zip(
                self.destinations,
                self.get_developer_day_rects(),
            ):
                if rect.collidepoint(position):
                    self.select_developer_day(destination.day_number)
                    return
            return

        if self.developer_back_button.collidepoint(position):
            self.return_to_developer_destinations()
            return
        for entry, rect in zip(
            self.get_developer_screen_entries(),
            self.get_developer_screen_rects(),
        ):
            if rect.collidepoint(position):
                self.jump_to_developer_screen(
                    self.get_developer_scene_index(entry[1])
                )
                return

    def jump_to_developer_screen(self, index):
        """Build and enter one clean development checkpoint."""

        _shortcut, scene_id, _label, target_state = DEVELOPER_SCREENS[index]
        self.developer_preview_active = self.developer_campaign_snapshot is not None
        # A developer jump intentionally leaves the opening story. Without
        # clearing it here, its dialogue overlay keeps intercepting input on
        # whichever preview screen was selected.
        self.intro_dialogue_active = False
        self.intro_dialogue_started_at = None
        self.developer_navigator_open = False
        self.exit_confirmation_open = False
        self.tutorial_open = False
        self.diagnosis_confirmation_open = False
        self.reception_transition_started_at = None
        self.queue_shift_started_at = None
        self.patient_fade_started_at = None
        self.end_day_shutdown_started_at = None
        self.test_result_started_at = None
        self.ending_started_at = None

        if scene_id == "intro":
            self.restart_game()
            self.state = GameState.INTRO
            self.intro_started_at = pygame.time.get_ticks()
            self.intro_wake_active = False
        elif scene_id == "reception":
            self.prepare_developer_campaign_day()
            self.state = GameState.TITLE
        elif scene_id.startswith("patient_"):
            patient_index = int(scene_id.rsplit("_", 1)[-1]) - 1
            self.prepare_developer_patient_checkpoint(patient_index)
        elif scene_id in ("recap", "shop", "route_briefing", "ending"):
            self.prepare_developer_shift_checkpoint()
        elif scene_id == "arrival":
            self.prepare_developer_arrival_checkpoint()
        elif scene_id == "final":
            self.prepare_developer_final_checkpoint()
        elif scene_id == "homecoming":
            self.prepare_developer_homecoming_checkpoint()

        if scene_id in ("shop", "route_briefing", "ending"):
            self.settle_daily_pay()
        if scene_id == "route_briefing":
            self.route_briefing_seen = False
            self.route_briefing_index = 0
        if scene_id == "ending":
            self.record_current_route_performance()
        if scene_id == "ending":
            self.ending_started_at = pygame.time.get_ticks()
        elif scene_id == "arrival":
            self.arrival_started_at = pygame.time.get_ticks()
        elif scene_id == "final":
            self.ending_started_at = None

        if scene_id != "intro":
            self.state = target_state
        self.developer_scene_id = scene_id
        self.play_sfx("button")

    def prepare_developer_patient_checkpoint(self, patient_index):
        """Start a fresh shift directly inside one selected patient encounter."""

        selected_roster = self.get_developer_roster()
        if not 0 <= patient_index < len(selected_roster):
            raise IndexError("Developer patient checkpoint is outside the roster.")

        # Rebuild the campaign and repopulate once more before selecting the
        # requested alien. This discards the temporary reception hand created
        # by restart_game, so the checkpoint always begins with one clean
        # five-card deal from a complete deck instead of draining live state.
        self.prepare_developer_campaign_day()
        self.deck.populate(create_test_catalog())
        self.patients_called = patient_index
        self.reset_round(recycle_unused_cards=False)
        self.patients_called = patient_index + 1
        self.state = GameState.PATIENT
        self.patient_left = False
        self.patient_leave_text = ""

    def prepare_developer_shift_checkpoint(self):
        """Build a consistent completed-shift state for late-game checkpoints."""

        self.prepare_developer_campaign_day()
        self.populate_developer_shift_metrics()

    def populate_developer_shift_metrics(self):
        """Fill the active preview shift with stable successful results."""

        self.patients_called = len(self.waiting_room_queue)
        self.daily_correct_diagnoses = len(self.waiting_room_queue)
        self.daily_test_count = len(self.waiting_room_queue) * 2
        self.daily_test_expenses = 100
        self.daily_evidence_cases = len(self.waiting_room_queue)
        self.daily_payout_applied = False

    def prepare_developer_arrival_checkpoint(self):
        """Complete every earlier stop and approach the selected destination."""

        selected_day = self.developer_selected_day
        destination_index = next(
            index
            for index, destination in enumerate(self.destinations)
            if destination.day_number == selected_day
        )
        if destination_index == 0:
            raise ValueError("The first destination uses the opening story, not arrival.")

        self.restart_game()
        reached_destination = None
        for completed_index in range(destination_index):
            if completed_index:
                self.route.begin_current_shift()
                self.load_current_destination()
            self.populate_developer_shift_metrics()
            self.settle_daily_pay()
            reached_destination = self.record_current_route_performance()

        self.developer_selected_day = selected_day
        if (
            reached_destination is None
            or reached_destination.day_number != selected_day
        ):
            raise ValueError("Developer arrival did not reach the selected destination.")

    def prepare_developer_final_checkpoint(self):
        """Complete the selected final destination without inventing another day."""

        selected_destination = next(
            destination
            for destination in self.destinations
            if destination.day_number == self.developer_selected_day
        )
        if selected_destination is not self.destinations[-1]:
            raise ValueError("Route Complete belongs to the final configured destination.")

        self.prepare_developer_arrival_checkpoint()
        self.route.begin_current_shift()
        self.load_current_destination()
        self.populate_developer_shift_metrics()
        self.settle_daily_pay()
        self.record_current_route_performance()

    def prepare_developer_homecoming_checkpoint(self):
        """Preview the real ticket-funded flight home from the final stop."""

        self.prepare_developer_final_checkpoint()
        self.purchased_shop_upgrades.add("return_passage")
        self.begin_homecoming_sequence()

    def prepare_developer_campaign_day(self):
        """Reset safely, then load the selected preview roster when needed."""

        self.restart_game()
        if self.developer_selected_day != self.destinations[0].day_number:
            self.route.select_day(self.developer_selected_day)
            self.load_current_destination()

    def get_developer_checkpoint_label(self, scene_id, label):
        """Add the current roster name to patient checkpoint buttons."""

        if not scene_id.startswith("patient_"):
            return label
        patient_index = int(scene_id.rsplit("_", 1)[-1]) - 1
        roster = self.get_developer_roster()
        if not 0 <= patient_index < len(roster):
            return label
        patient_name = roster[patient_index]["create"]().name
        return f"{label}  •  {patient_name.upper()}"

    def draw_developer_navigator(self):
        """Draw destination selection or that destination's checkpoint list."""

        dim = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        dim.fill((2, 6, 12, 224))
        self.screen.blit(dim, (0, 0))

        panel = pygame.Rect(65, 24, 970, 602)
        pygame.draw.rect(self.screen, (3, 8, 13), panel.move(8, 9), border_radius=18)
        pygame.draw.rect(self.screen, (27, 29, 45), panel, border_radius=18)
        pygame.draw.rect(self.screen, (187, 137, 211), panel, width=3, border_radius=18)

        tag = self.card_font.render("DEVELOPER TOOL", True, (216, 159, 238))
        self.screen.blit(tag, tag.get_rect(center=(panel.centerx, panel.y + 22)))
        heading_text = (
            "SELECT DESTINATION"
            if self.developer_navigator_level == "destinations"
            else "CHECKPOINT NAVIGATOR"
        )
        heading = self.heading_font.render(heading_text, True, COLORS["text"])
        self.screen.blit(heading, heading.get_rect(center=(panel.centerx, panel.y + 49)))

        mouse_position = self.get_mouse_position()
        if self.developer_navigator_level == "destinations":
            hint_text = "CHOOSE A ROUTE STOP  •  NUMBER KEYS SELECT  •  F10 CLOSES"
            self.draw_developer_destination_directory(panel, mouse_position)
        else:
            hint_text = "CHOOSE A PATIENT OR SCREEN  •  ESC RETURNS TO DESTINATIONS"
            self.draw_developer_checkpoint_directory(panel, mouse_position)
        hint = self.card_font.render(hint_text, True, COLORS["muted"])
        self.screen.blit(hint, hint.get_rect(center=(panel.centerx, panel.y + 76)))

        if self.developer_preview_active:
            hovered = self.developer_return_button.collidepoint(mouse_position)
            pygame.draw.rect(
                self.screen,
                (52, 103, 91) if hovered else (30, 66, 62),
                self.developer_return_button,
                border_radius=8,
            )
            pygame.draw.rect(
                self.screen,
                COLORS["accent"],
                self.developer_return_button,
                width=2,
                border_radius=8,
            )
            return_label = self.card_font.render(
                "RETURN TO LIVE CAMPAIGN",
                True,
                COLORS["text"],
            )
            self.screen.blit(
                return_label,
                return_label.get_rect(center=self.developer_return_button.center),
            )

        footer_text = (
            "PREVIEW SANDBOX ACTIVE  •  Live campaign progress is unchanged"
            if self.developer_preview_active
            else "Development shortcut only  •  Live campaign progress is protected"
        )
        footer = self.card_font.render(
            footer_text,
            True,
            COLORS["muted"],
        )
        self.screen.blit(footer, footer.get_rect(center=(panel.centerx, panel.bottom - 24)))

    def draw_developer_destination_directory(self, panel, mouse_position):
        """Draw one generated card for every route destination."""

        self.developer_destination_button_rects = list(self.get_developer_day_rects())
        self.developer_day_button_rects = self.developer_destination_button_rects
        for destination, rect in zip(
            self.destinations,
            self.developer_destination_button_rects,
        ):
            selected = destination.day_number == self.developer_selected_day
            hovered = rect.collidepoint(mouse_position)
            accent = destination.theme.accent_color
            fill = (
                tuple(max(0, component // 4) for component in accent)
                if selected
                else (50, 37, 68) if hovered else (21, 27, 39)
            )
            pygame.draw.rect(self.screen, (3, 8, 13), rect.move(3, 4), border_radius=12)
            pygame.draw.rect(self.screen, fill, rect, border_radius=12)
            pygame.draw.rect(self.screen, accent, rect, width=2, border_radius=12)

            planet_center = (rect.x + 48, rect.centery)
            pygame.draw.circle(self.screen, destination.theme.horizon_color, planet_center, 24)
            pygame.draw.arc(
                self.screen,
                accent,
                pygame.Rect(planet_center[0] - 31, planet_center[1] - 10, 62, 21),
                0,
                2 * 3.14159,
                width=2,
            )
            day = self.card_font.render(
                f"{destination.day_number}  •  DAY {destination.day_number}",
                True,
                accent,
            )
            name = self.small_font.render(
                destination.planet_name.upper(),
                True,
                COLORS["text"],
            )
            text_x = rect.x + 91
            self.screen.blit(day, (text_x, rect.y + 15))
            self.screen.blit(name, (text_x, rect.y + 38))
            detail_text = (
                f"{len(destination.patient_roster)} PATIENTS  //  "
                f"{destination.subtitle.upper()}"
            )
            detail_lines = self.wrap_text(
                detail_text,
                self.card_font,
                rect.right - text_x - 15,
            )[:2]
            for line_index, line in enumerate(detail_lines):
                details = self.card_font.render(line, True, COLORS["muted"])
                self.screen.blit(details, (text_x, rect.y + 66 + line_index * 14))

        future = pygame.Rect(panel.centerx - 230, panel.bottom - 151, 460, 72)
        pygame.draw.rect(self.screen, (18, 22, 34), future, border_radius=10)
        pygame.draw.rect(self.screen, (83, 77, 101), future, width=2, border_radius=10)
        future_title = self.small_font.render(
            "FUTURE DESTINATIONS",
            True,
            (151, 143, 169),
        )
        future_body = self.card_font.render(
            "New route data will appear here automatically.",
            True,
            COLORS["muted"],
        )
        self.screen.blit(
            future_title,
            future_title.get_rect(center=(future.centerx, future.y + 24)),
        )
        self.screen.blit(
            future_body,
            future_body.get_rect(center=(future.centerx, future.y + 50)),
        )

    def draw_developer_checkpoint_directory(self, panel, mouse_position):
        """Draw only the selected destination's patients and valid screens."""

        destination = next(
            item
            for item in self.destinations
            if item.day_number == self.developer_selected_day
        )
        back_hovered = self.developer_back_button.collidepoint(mouse_position)
        pygame.draw.rect(
            self.screen,
            (50, 37, 68) if back_hovered else (21, 27, 39),
            self.developer_back_button,
            border_radius=7,
        )
        pygame.draw.rect(
            self.screen,
            (187, 137, 211),
            self.developer_back_button,
            width=2,
            border_radius=7,
        )
        back = self.card_font.render("<  DESTINATIONS", True, COLORS["text"])
        self.screen.blit(back, back.get_rect(center=self.developer_back_button.center))

        destination_label = self.small_font.render(
            f"DAY {destination.day_number}  •  {destination.planet_name.upper()}",
            True,
            destination.theme.accent_color,
        )
        self.screen.blit(
            destination_label,
            destination_label.get_rect(center=(panel.centerx, 139)),
        )

        entries = self.get_developer_screen_entries()
        self.developer_button_rects = self.get_developer_screen_rects()
        current_scene_id = self.infer_developer_scene_id()
        for (shortcut, scene_id, label, _target_state), rect in zip(
            entries,
            self.developer_button_rects,
        ):
            selected = scene_id == current_scene_id
            hovered = rect.collidepoint(mouse_position)
            border = (
                COLORS["accent"]
                if selected
                else (216, 159, 238) if hovered else (126, 91, 153)
            )
            fill = (
                (19, 54, 49)
                if selected
                else (50, 37, 68) if hovered else (21, 27, 39)
            )
            pygame.draw.rect(self.screen, (3, 8, 13), rect.move(2, 3), border_radius=8)
            pygame.draw.rect(self.screen, fill, rect, border_radius=8)
            pygame.draw.rect(self.screen, border, rect, width=2, border_radius=8)
            shortcut_label = self.body_font.render(shortcut, True, border)
            checkpoint = self.get_developer_checkpoint_label(scene_id, label)
            screen_label = self.card_font.render(checkpoint, True, COLORS["text"])
            self.screen.blit(
                shortcut_label,
                shortcut_label.get_rect(midleft=(rect.x + 14, rect.centery)),
            )
            self.screen.blit(
                screen_label,
                screen_label.get_rect(midleft=(rect.x + 46, rect.centery)),
            )
