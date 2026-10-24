"""Vertical-slice ending animation, final report, and exit confirmation."""

import math

import pygame

from gui_state import GameState
from gui_theme import COLORS, WINDOW_SIZE


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
        pygame.draw.circle(self.screen, (47, 38, 82), (1030, 595), 142)
        pygame.draw.circle(self.screen, (89, 67, 137), (997, 552), 88)
        pygame.draw.arc(
            self.screen,
            (155, 116, 190),
            pygame.Rect(865, 515, 320, 100),
            math.pi,
            math.pi * 2,
            width=4,
        )
        for index, (x, y, size) in enumerate(self.intro_stars):
            twinkle = (elapsed // 220 + index) % 6 == 0
            color = (221, 235, 255) if twinkle else (112, 140, 178)
            pygame.draw.circle(
                self.screen,
                color,
                (x, y),
                size + int(twinkle and size == 1),
            )

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

        message_progress = max(0.0, min(1.0, (progress - 0.42) / 0.2))
        if message_progress > 0:
            heading = self.title_font.render("SHIFT COMPLETE", True, COLORS["accent"])
            heading.set_alpha(round(255 * message_progress))
            self.screen.blit(heading, heading.get_rect(center=(550, 430)))
            message = self.body_font.render(
                "The Cosmic Clinic is closing for the night...",
                True,
                COLORS["text"],
            )
            message.set_alpha(round(255 * message_progress))
            self.screen.blit(message, message.get_rect(center=(550, 478)))

        skip = self.small_font.render(
            "Click anywhere or press Enter to skip",
            True,
            COLORS["muted"],
        )
        self.screen.blit(skip, skip.get_rect(center=(550, 620)))

    def draw_clinic_window_farewell(self, surface, elapsed):
        """Draw tiny colorful patients waving from the departing clinic dome."""

        wave = round(5 * math.sin(elapsed / 140))
        for x, color, direction in (
            (474, (151, 99, 211), -1),
            (550, (103, 173, 124), 1),
            (626, (64, 125, 166), -1),
        ):
            pygame.draw.circle(surface, color, (x, 260), 13)
            pygame.draw.ellipse(surface, color, pygame.Rect(x - 10, 271, 20, 25))
            arm_start = (x + direction * 8, 277)
            arm_end = (x + direction * (19 + wave), 263)
            pygame.draw.line(surface, color, arm_start, arm_end, width=5)
            pygame.draw.circle(surface, color, arm_end, 3)
            pygame.draw.circle(surface, (17, 27, 39), (x - 4, 259), 2)
            pygame.draw.circle(surface, (17, 27, 39), (x + 4, 259), 2)

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
        """Draw the completed vertical-slice report and replay/quit controls."""

        self.draw_space_background()
        self.draw_game_logo((550, 55), scale=0.72)
        panel = pygame.Rect(185, 105, 730, 465)
        pygame.draw.rect(self.screen, (4, 10, 17), panel.move(8, 9), border_radius=18)
        pygame.draw.rect(self.screen, COLORS["panel"], panel, border_radius=18)
        pygame.draw.rect(
            self.screen,
            COLORS["panel_border"],
            panel,
            width=3,
            border_radius=18,
        )

        heading = self.heading_font.render(
            "VERTICAL SLICE COMPLETE",
            True,
            COLORS["accent"],
        )
        self.screen.blit(heading, heading.get_rect(center=(panel.centerx, 148)))
        thanks = self.body_font.render(
            "Thanks for playing The Cosmic Clinic!",
            True,
            COLORS["text"],
        )
        self.screen.blit(thanks, thanks.get_rect(center=(panel.centerx, 186)))

        total_earned = self.get_daily_pay_breakdown()[3]
        summary = pygame.Rect(panel.x + 105, 220, panel.width - 210, 210)
        pygame.draw.rect(self.screen, (7, 22, 28), summary, border_radius=12)
        pygame.draw.rect(self.screen, (65, 101, 98), summary, width=2, border_radius=12)
        stats = (
            ("PATIENTS TREATED", str(self.daily_correct_diagnoses)),
            ("SHIFT EARNINGS", f"${total_earned}"),
            ("INCORRECT DIAGNOSES", str(self.daily_wrong_diagnoses)),
            ("UPGRADES PURCHASED", str(len(self.purchased_shop_upgrades))),
            ("FINAL BALANCE", f"${self.player.balance}"),
        )
        for index, (label_text, value_text) in enumerate(stats):
            y = summary.y + 20 + index * 36
            label = self.small_font.render(label_text, True, COLORS["muted"])
            value = self.small_font.render(value_text, True, COLORS["accent"])
            self.screen.blit(label, (summary.x + 24, y))
            self.screen.blit(value, value.get_rect(topright=(summary.right - 24, y)))

        self.draw_ending_button(self.final_replay_button, "REPLAY SHIFT", False)
        self.draw_ending_button(self.final_quit_button, "QUIT GAME", True)
        hint = self.card_font.render(
            "Replay begins again in reception with a fresh clinic balance.",
            True,
            COLORS["muted"],
        )
        self.screen.blit(hint, hint.get_rect(center=(panel.centerx, 466)))

    def draw_ending_button(self, rect, label, danger=False):
        """Draw a reusable final-screen or exit-dialog button."""

        hovered = rect.collidepoint(pygame.mouse.get_pos())
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
        """Replay the slice or close the game from the final report."""

        if self.final_replay_button.collidepoint(position):
            self.play_sfx("button")
            self.restart_vertical_slice()
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
            "ending_started_at",
        )
        for timer_name in timer_names:
            started_at = getattr(self, timer_name, None)
            if started_at is not None:
                setattr(self, timer_name, started_at + paused_for)

        for animation_name in ("note_transfer_animation", "discard_animation"):
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
            self.restart_vertical_slice()
        elif self.exit_quit_button.collidepoint(position):
            self.play_sfx("button")
            self.running = False

    def restart_vertical_slice(self):
        """Reset progress and return to reception without replaying the intro."""

        self.player.balance = 500
        self.purchased_shop_upgrades.clear()
        self.ending_started_at = None
        self.exit_confirmation_open = False
        self.exit_confirmation_opened_at = None
        self.reset_day()
        self.state = GameState.TITLE

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
            "Return to reception restarts the four-patient vertical slice.",
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
