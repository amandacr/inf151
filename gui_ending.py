"""End-of-shift animation, final report, and exit confirmation."""

import math

import pygame

from gui_state import GameState
from gui_theme import COLORS, WINDOW_SIZE
from Player import STARTING_BALANCE


class EndingMixin:
    """Supply the closing sequence and safe exit controls to the main GUI."""

    def begin_ending_sequence(self):
        """Leave the Shop and begin the skippable clinic departure animation."""

        self.exit_confirmation_open = False
        self.ending_started_at = pygame.time.get_ticks()
        self.state = GameState.ENDING

    def finish_ending_sequence(self):
        """Skip or complete the departure animation and show the final report."""

        self.ending_started_at = None
        self.state = GameState.FINAL

    def update_ending_sequence(self):
        """Advance automatically to the final report when the animation completes."""

        if self.ending_started_at is None:
            self.ending_started_at = pygame.time.get_ticks()
            return
        elapsed = pygame.time.get_ticks() - self.ending_started_at
        if elapsed >= self.ending_duration:
            self.finish_ending_sequence()

    def get_ending_progress(self):
        """Return the closing animation's normalized zero-to-one progress."""

        if self.ending_started_at is None:
            return 1.0
        elapsed = pygame.time.get_ticks() - self.ending_started_at
        return max(0.0, min(1.0, elapsed / self.ending_duration))

    def draw_space_background(self, elapsed=0):
        """Draw the star field shared by the ending animation and final report."""

        self.screen.fill((6, 10, 27))

        # Low-contrast color clouds keep the empty space dimensional without
        # competing with the report panel or departing clinic.
        haze = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        pygame.draw.ellipse(haze, (51, 72, 130, 18), pygame.Rect(35, 80, 390, 185))
        pygame.draw.ellipse(haze, (112, 64, 132, 14), pygame.Rect(720, 210, 335, 180))
        self.screen.blit(haze, (0, 0))

        # The corner planet is deliberately small and muted so it frames the
        # summary rather than becoming the focal point.
        planet_layer = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        planet_center = (1038, 610)
        pygame.draw.circle(planet_layer, (92, 68, 139, 22), planet_center, 109)
        ring_rect = pygame.Rect(930, 576, 218, 57)
        pygame.draw.arc(
            planet_layer,
            (151, 115, 184, 105),
            ring_rect,
            math.pi,
            math.pi * 2,
            width=4,
        )
        pygame.draw.circle(planet_layer, (39, 34, 69, 210), planet_center, 94)
        pygame.draw.circle(planet_layer, (70, 56, 108, 215), (1013, 584), 57)
        pygame.draw.ellipse(
            planet_layer,
            (55, 44, 91, 150),
            pygame.Rect(955, 609, 168, 31),
        )
        for crater_x, crater_y, radius in ((1069, 575, 9), (1002, 622, 6), (1050, 640, 5)):
            pygame.draw.circle(
                planet_layer,
                (31, 27, 58, 115),
                (crater_x, crater_y),
                radius,
            )
        pygame.draw.arc(
            planet_layer,
            (151, 115, 184, 125),
            ring_rect,
            0,
            math.pi,
            width=4,
        )
        self.screen.blit(planet_layer, (0, 0))

        for index, (x, y, size) in enumerate(self.intro_stars):
            twinkle = (elapsed // 220 + index) % 6 == 0
            resting_colors = (
                (112, 140, 178),
                (133, 153, 194),
                (166, 143, 190),
                (116, 167, 178),
            )
            color = (221, 235, 255) if twinkle else resting_colors[index % 4]
            star_radius = size + int(twinkle and size == 1)
            pygame.draw.circle(
                self.screen,
                color,
                (x, y),
                star_radius,
            )
            if twinkle and size == 2:
                pygame.draw.line(self.screen, color, (x - 5, y), (x + 5, y), width=1)
                pygame.draw.line(self.screen, color, (x, y - 5), (x, y + 5), width=1)

    def draw_ending_screen(self):
        """Draw the clinic shrinking into space at the end of the shift."""

        elapsed = (
            0
            if self.ending_started_at is None
            else pygame.time.get_ticks() - self.ending_started_at
        )
        progress = self.get_ending_progress()
        eased = 1 - (1 - progress) ** 2
        self.draw_space_background(elapsed)

        clinic_layer = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        self.draw_intro_clinic(
            clinic_layer,
            beam_alpha=round(180 * max(0.0, 1.0 - progress * 2.4)),
        )
        self.draw_clinic_window_farewell(clinic_layer, elapsed)
        self.draw_clinic_shutdown_lights(clinic_layer, progress)

        scale = max(0.07, 0.76 * (1 - eased) + 0.07)
        scaled_size = (
            max(1, round(WINDOW_SIZE[0] * scale)),
            max(1, round(WINDOW_SIZE[1] * scale)),
        )
        clinic = pygame.transform.smoothscale(clinic_layer, scaled_size)
        center = (
            round(WINDOW_SIZE[0] / 2 + 125 * eased),
            round(330 - 125 * eased),
        )
        self.screen.blit(clinic, clinic.get_rect(center=center))

        self.draw_cinematic_skip_prompt()

    def draw_clinic_window_farewell(self, surface, elapsed):
        """Draw tiny colorful patients waving from the departing clinic dome."""

        wave = round(5 * math.sin(elapsed / 140))
        head_y = 166
        for x, color, direction in (
            (474, (151, 99, 211), -1),
            (550, (103, 173, 124), 1),
            (626, (64, 125, 166), -1),
        ):
            pygame.draw.circle(surface, color, (x, head_y), 13)
            pygame.draw.ellipse(
                surface,
                color,
                pygame.Rect(x - 10, head_y + 11, 20, 30),
            )
            arm_start = (x + direction * 8, head_y + 17)
            arm_end = (x + direction * (19 + wave), head_y + 3)
            pygame.draw.line(surface, color, arm_start, arm_end, width=5)
            pygame.draw.circle(surface, color, arm_end, 3)
            pygame.draw.circle(surface, (17, 27, 39), (x - 4, head_y - 1), 2)
            pygame.draw.circle(surface, (17, 27, 39), (x + 4, head_y - 1), 2)

        # A small cabin console masks their lower bodies and places them behind
        # the dome glass instead of making them appear to stand on the hull.
        console = pygame.Rect(436, 198, 228, 20)
        pygame.draw.rect(surface, (28, 48, 65), console, border_radius=9)
        pygame.draw.line(
            surface,
            (151, 219, 221),
            (console.x + 10, console.y + 2),
            (console.right - 10, console.y + 2),
            width=2,
        )

    def draw_clinic_shutdown_lights(self, surface, progress):
        """Switch the saucer's exterior lights off one at a time."""

        light_positions = (
            (292, 406),
            (375, 428),
            (462, 440),
            (550, 444),
            (638, 440),
            (725, 428),
            (808, 406),
        )
        for index, position in enumerate(light_positions):
            if progress >= 0.08 + index * 0.055:
                pygame.draw.circle(surface, (22, 35, 55), position, 10)
                pygame.draw.circle(surface, (56, 66, 82), position, 5)

    def draw_final_screen(self):
        """Draw an empty Day 2 reception that is ready for a future roster."""

        self.screen.fill(COLORS["background"])
        self.draw_game_logo((WINDOW_SIZE[0] // 2, 38), scale=0.86)
        subtitle = self.small_font.render("DAY 2  //  RECEPTION", True, COLORS["muted"])
        self.screen.blit(subtitle, subtitle.get_rect(center=(WINDOW_SIZE[0] // 2, 76)))

        self.draw_reception_room()
        self.draw_waiting_room_windows()
        self.draw_waiting_room_door()
        self.draw_waiting_room_chairs()
        self.draw_reception_desk()
        self.draw_next_day_status()

        has_roster = bool(self.next_shift_queue)
        action_label = "START DAY 2" if has_roster else "REPLAY DAY 1"
        self.draw_ending_button(self.final_replay_button, action_label, False)
        self.draw_ending_button(self.final_quit_button, "QUIT GAME", True)
        hint = self.card_font.render(
            (
                "New patient files received. Day 2 is ready to begin."
                if has_roster
                else "New patient files can be added to the Day 2 roster here."
            ),
            True,
            COLORS["muted"],
        )
        self.screen.blit(hint, hint.get_rect(center=(WINDOW_SIZE[0] // 2, 584)))

    def draw_next_day_status(self):
        """Draw the Day 2 monitor and roster-pending message over empty chairs."""

        status = pygame.Rect(30, 100, 1040, 49)
        pygame.draw.rect(self.screen, (54, 78, 78), status, border_radius=10)
        pygame.draw.rect(self.screen, COLORS["panel_border"], status, width=2, border_radius=10)
        display = status.inflate(-10, -10)
        pygame.draw.rect(self.screen, (5, 19, 24), display, border_radius=7)

        has_roster = bool(self.next_shift_queue)
        status_color = COLORS["accent"] if has_roster else (255, 198, 75)
        pygame.draw.circle(self.screen, status_color, (display.x + 15, display.centery), 5)
        day_label = self.body_font.render("DAY 2 RECEPTION", True, COLORS["text"])
        roster_label = self.small_font.render(
            "PATIENT ROSTER READY" if has_roster else "NO PATIENTS SCHEDULED YET",
            True,
            status_color,
        )
        money_label = self.body_font.render(
            f"MONEY: ${self.get_displayed_balance()}",
            True,
            COLORS["accent"],
        )
        self.screen.blit(day_label, day_label.get_rect(midleft=(display.x + 29, display.centery)))
        self.screen.blit(roster_label, roster_label.get_rect(center=display.center))
        self.screen.blit(
            money_label,
            money_label.get_rect(midright=(display.right - 13, display.centery)),
        )

        notice = pygame.Rect(342, 238, 416, 92)
        pygame.draw.rect(self.screen, (4, 12, 20), notice.move(5, 6), border_radius=13)
        pygame.draw.rect(self.screen, (19, 31, 45), notice, border_radius=13)
        pygame.draw.rect(self.screen, status_color, notice, width=2, border_radius=13)
        notice_heading = self.heading_font.render(
            "ROSTER READY" if has_roster else "ROSTER PENDING",
            True,
            status_color,
        )
        notice_body = self.small_font.render(
            (
                (
                    f"{len(self.next_shift_queue)} patient"
                    f"{'s are' if len(self.next_shift_queue) != 1 else ' is'} waiting for Day 2."
                )
                if has_roster
                else "The clinic is waiting for new patient files."
            ),
            True,
            COLORS["text"],
        )
        self.screen.blit(notice_heading, notice_heading.get_rect(center=(notice.centerx, notice.y + 31)))
        self.screen.blit(notice_body, notice_body.get_rect(center=(notice.centerx, notice.y + 63)))

    def draw_ending_button(self, rect, label, danger=False):
        """Draw a reusable final-screen or exit-dialog button."""

        hovered = rect.collidepoint(self.get_mouse_position())
        if danger:
            color = (225, 111, 100) if hovered else (157, 78, 79)
        else:
            color = COLORS["accent"] if hovered else COLORS["panel_border"]
        pygame.draw.rect(self.screen, color, rect, border_radius=9)
        pygame.draw.rect(
            self.screen,
            (236, 246, 240) if danger else (177, 229, 207),
            rect,
            width=2,
            border_radius=9,
        )
        text = self.small_font.render(label, True, COLORS["background"])
        self.screen.blit(text, text.get_rect(center=rect.center))

    def handle_final_screen_click(self, position):
        """Start an available Day 2 roster, replay Day 1, or close the game."""

        if self.final_replay_button.collidepoint(position):
            self.play_sfx("button")
            if self.next_shift_queue:
                next_roster = list(self.next_shift_queue)
                self.next_shift_queue = []
                self.start_next_shift(next_roster)
            else:
                self.restart_game()
        elif self.final_quit_button.collidepoint(position):
            self.play_sfx("button")
            self.running = False

    def open_exit_confirmation(self):
        """Pause interaction and open the three-option exit confirmation."""

        self.exit_confirmation_open = True
        self.exit_confirmation_opened_at = pygame.time.get_ticks()

    def close_exit_confirmation(self):
        """Close the exit confirmation and continue on the current screen."""

        if self.exit_confirmation_opened_at is not None:
            paused_for = pygame.time.get_ticks() - self.exit_confirmation_opened_at
            self.offset_animation_timers(paused_for)
        self.exit_confirmation_open = False
        self.exit_confirmation_opened_at = None

    def offset_animation_timers(self, paused_for):
        """Keep every active animation frozen while the exit modal is visible."""

        timer_names = (
            "intro_started_at",
            "test_result_started_at",
            "diagnosis_folder_animation_started_at",
            "notebook_attention_started_at",
            "reception_transition_started_at",
            "queue_shift_started_at",
            "patient_fade_started_at",
            "end_day_shutdown_started_at",
            "ending_started_at",
        )
        for timer_name in timer_names:
            started_at = getattr(self, timer_name, None)
            if started_at is not None:
                setattr(self, timer_name, started_at + paused_for)

        for animation_name in (
            "note_transfer_animation",
            "discard_animation",
            "money_deduction_animation",
        ):
            animation = getattr(self, animation_name, None)
            if animation is not None and "started_at" in animation:
                animation["started_at"] += paused_for

    def handle_exit_confirmation_click(self, position):
        """Continue, restart at reception, or quit from the exit confirmation."""

        if self.exit_continue_button.collidepoint(position):
            self.play_sfx("button")
            self.close_exit_confirmation()
        elif self.exit_reception_button.collidepoint(position):
            self.play_sfx("button")
            self.restart_game()
        elif self.exit_quit_button.collidepoint(position):
            self.play_sfx("button")
            self.running = False

    def start_next_shift(self, patient_queue):
        """Load a future shift roster while preserving clinic upgrades and money."""

        if not patient_queue:
            raise ValueError("A shift requires at least one patient.")
        self.waiting_room_queue = list(patient_queue)
        self.ending_started_at = None
        self.exit_confirmation_open = False
        self.exit_confirmation_opened_at = None
        self.reset_day()
        self.state = GameState.TITLE

    def restart_game(self):
        """Reset campaign progress and return to reception without the intro."""

        restart_training = self.guided_tutorial_active
        self.finish_guided_tutorial()
        self.intro_dialogue_active = False
        self.intro_dialogue_started_at = None
        self.player.balance = STARTING_BALANCE
        self.player.machine_levels.clear()
        self.player.test_discount = 0
        self.purchased_shop_upgrades.clear()
        self.ending_started_at = None
        self.exit_confirmation_open = False
        self.exit_confirmation_opened_at = None
        self.start_next_shift(self.waiting_room_queue)
        if restart_training:
            self.start_guided_tutorial()

    def draw_exit_confirmation(self):
        """Draw the styled modal used when Escape is pressed."""

        dim = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        dim.fill((2, 6, 12, 220))
        self.screen.blit(dim, (0, 0))
        panel = pygame.Rect(285, 145, 530, 365)
        pygame.draw.rect(self.screen, (3, 8, 13), panel.move(8, 9), border_radius=18)
        pygame.draw.rect(self.screen, (30, 37, 52), panel, border_radius=18)
        pygame.draw.rect(
            self.screen,
            (176, 126, 207),
            panel,
            width=3,
            border_radius=18,
        )

        heading = self.heading_font.render("LEAVE YOUR SHIFT?", True, COLORS["text"])
        self.screen.blit(heading, heading.get_rect(center=(panel.centerx, 190)))
        detail = self.small_font.render(
            "Return to reception restarts the current clinic shift.",
            True,
            COLORS["muted"],
        )
        self.screen.blit(detail, detail.get_rect(center=(panel.centerx, 232)))

        self.draw_ending_button(
            self.exit_continue_button,
            "CONTINUE PLAYING",
            False,
        )
        self.draw_ending_button(
            self.exit_reception_button,
            "RETURN TO RECEPTION",
            False,
        )
        self.draw_ending_button(self.exit_quit_button, "QUIT GAME", True)
