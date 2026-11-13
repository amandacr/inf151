"""End-of-shift animation, final report, and exit confirmation."""

import math

import pygame

from gui_state import GameState
from gui_theme import COLORS, WINDOW_SIZE
from Player import STARTING_BALANCE
from RouteController import ShiftPerformance


ROUTE_COMPLETE_HEADING = "CURRENT ROUTE COMPLETE"
ROUTE_COMPLETE_MESSAGE = "The next clinic destination is being prepared."
ROUTE_BRIEFING_DIALOGUE = (
    (
        "CLINIC SYSTEM",
        "Training shift complete. The Cosmic Clinic travels to a new destination after every shift.",
    ),
    ("YOU", "And when do I get to go home?"),
    (
        "CLINIC SYSTEM",
        "Earn enough credits to purchase return passage to Earth.",
    ),
)


class EndingMixin:
    """Supply the closing sequence and safe exit controls to the main GUI."""

    def begin_ending_sequence(self):
        """Leave the Shop and begin the clinic departure animation."""

        self.record_current_route_performance()
        if self.has_return_passage() and not self.route.arrival_pending:
            self.finish_ending_sequence()
            return
        self.exit_confirmation_open = False
        self.ending_duration = 4200
        self.ending_started_at = pygame.time.get_ticks()
        self.state = GameState.ENDING

    def should_show_route_briefing(self):
        """Return whether the first completed shift still needs its route lesson."""

        return (
            not self.route_briefing_seen
            and self.current_destination is self.destinations[0]
            and self.route.next_destination is not None
        )

    def start_route_briefing(self):
        """Open the one-time explanation of the clinic's traveling route."""

        self.route_briefing_index = 0
        self.state = GameState.ROUTE_BRIEFING

    def advance_route_briefing(self):
        """Advance the short route conversation, then depart for the next stop."""

        if self.route_briefing_index < len(ROUTE_BRIEFING_DIALOGUE) - 1:
            self.route_briefing_index += 1
            return
        self.route_briefing_seen = True
        self.begin_ending_sequence()

    def draw_route_briefing_screen(self):
        """Draw the Supply Shop behind a compact post-training conversation."""

        self.screen.fill(COLORS["background"])
        self.draw_game_logo((WINDOW_SIZE[0] // 2, 38), scale=0.86)
        subtitle = self.small_font.render(
            "TRAINING ROUTE BRIEFING",
            True,
            COLORS["muted"],
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(WINDOW_SIZE[0] // 2, 76)))
        self.draw_shop_screen()

        dim = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        dim.fill((2, 6, 12, 190))
        self.screen.blit(dim, (0, 0))

        speaker, line = ROUTE_BRIEFING_DIALOGUE[self.route_briefing_index]
        system_speaking = speaker == "CLINIC SYSTEM"
        accent = (100, 238, 193) if system_speaking else (136, 190, 255)
        panel = pygame.Rect(145, 215, 810, 205)
        pygame.draw.rect(self.screen, (1, 5, 10), panel.move(8, 9), border_radius=18)
        pygame.draw.rect(self.screen, (9, 22, 31), panel, border_radius=18)
        pygame.draw.rect(self.screen, accent, panel, width=3, border_radius=18)

        badge = pygame.Rect(panel.x + 26, panel.y + 20, 190, 34)
        badge_fill = (15, 57, 54) if system_speaking else (23, 43, 71)
        pygame.draw.rect(self.screen, badge_fill, badge, border_radius=7)
        pygame.draw.rect(self.screen, accent, badge, width=1, border_radius=7)
        speaker_label = self.dialogue_speaker_font.render(speaker, True, accent)
        self.screen.blit(speaker_label, speaker_label.get_rect(center=badge.center))

        line_box = pygame.Rect(panel.x + 28, panel.y + 74, panel.width - 56, 70)
        self.draw_wrapped_text(
            line,
            self.dialogue_body_font,
            COLORS["text"],
            line_box,
            line_spacing=4,
        )

        for dot_index in range(len(ROUTE_BRIEFING_DIALOGUE)):
            dot_color = accent if dot_index <= self.route_briefing_index else (55, 76, 84)
            pygame.draw.circle(
                self.screen,
                dot_color,
                (panel.x + 32 + dot_index * 18, panel.bottom - 25),
                4 if dot_index == self.route_briefing_index else 3,
            )

        final_line = self.route_briefing_index == len(ROUTE_BRIEFING_DIALOGUE) - 1
        next_destination = self.route.next_destination
        prompt_text = (
            f"DEPART FOR {next_destination.planet_name.upper()}"
            if final_line and next_destination is not None
            else "CLICK OR PRESS ENTER TO CONTINUE"
        )
        prompt = self.tutorial_label_font.render(prompt_text, True, accent)
        prompt_panel = prompt.get_rect(center=(panel.centerx + 95, panel.bottom - 25)).inflate(24, 12)
        pygame.draw.rect(self.screen, (12, 30, 40), prompt_panel, border_radius=10)
        pygame.draw.rect(self.screen, accent, prompt_panel, width=2, border_radius=10)
        self.screen.blit(prompt, prompt.get_rect(center=prompt_panel.center))

    def record_current_route_performance(self):
        """Preserve this shift's results before daily counters are reset."""

        performance = ShiftPerformance(
            destination_key=self.current_destination.key,
            day_number=self.day_number,
            patients_seen=len(self.waiting_room_queue),
            correct_diagnoses=self.daily_correct_diagnoses,
            supported_diagnoses=self.daily_evidence_cases,
            wrong_diagnoses=self.daily_wrong_diagnoses,
            patients_lost=self.daily_patients_lost,
            tests_run=self.daily_test_count,
            net_pay=self.get_daily_pay_breakdown()[3],
            ending_balance=self.player.balance,
        )
        return self.route.complete_current_shift(performance)

    def begin_homecoming_sequence(self):
        """Start the final flight after the player chooses to go home."""
        self.homecoming_started = True
        self.exit_confirmation_open = False
        self.ending_duration = 14000
        self.ending_started_at = pygame.time.get_ticks()
        self.state = GameState.ENDING

    def can_skip_ending(self):
        return not self.homecoming_started

    def finish_ending_sequence(self):
        """Finish departure at an arrival screen or the completed-route report."""

        self.ending_started_at = None
        if self.route.arrival_pending:
            self.arrival_started_at = pygame.time.get_ticks()
            self.state = GameState.ARRIVAL
        else:
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
        """Draw route travel between stops or the final clinic departure."""

        if self.route.arrival_pending:
            self.draw_interplanetary_travel_screen()
        else:
            self.draw_final_departure_screen()

    def draw_interplanetary_travel_screen(self):
        """Draw a clean, readable flight between two configured destinations."""

        elapsed = (
            0
            if self.ending_started_at is None
            else pygame.time.get_ticks() - self.ending_started_at
        )
        progress = self.get_ending_progress()
        eased = self._intro_smooth(progress)
        departing = self.route.completed_destinations[-1]
        arriving = self.current_destination

        self.screen.fill((5, 9, 25))
        atmosphere = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        pygame.draw.circle(
            atmosphere,
            (*departing.theme.accent_color, 12),
            (72, 405),
            116,
        )
        pygame.draw.circle(
            atmosphere,
            (*arriving.theme.accent_color, 16),
            (930, 285),
            158,
        )
        self.screen.blit(atmosphere, (0, 0))

        # Moving points provide parallax without turning the sky into a field
        # of disconnected white dashes.
        for index, (star_x, star_y, star_size) in enumerate(self.intro_stars):
            shifted_x = (star_x - round(eased * (75 + index % 4 * 24))) % WINDOW_SIZE[0]
            twinkle = (elapsed // 210 + index) % 9 == 0
            color = (199, 222, 242) if twinkle else (99, 132, 170)
            pygame.draw.circle(
                self.screen,
                color,
                (shifted_x, star_y),
                star_size + int(twinkle and star_size == 1),
            )

        self.draw_travel_planet(
            departing,
            (72 - round(eased * 28), 405 + round(eased * 8)),
            64 - round(eased * 8),
            foreground=False,
        )

        self.draw_travel_moons(arriving, elapsed)
        self.draw_travel_planet(
            arriving,
            (930, 285),
            94 + round(eased * 10),
            foreground=True,
        )

        # Follow a gentle arc and stop well before Triska's ring. The arrival
        # screen handles the final approach, so the two scenes no longer collide.
        start = (230, 430)
        control = (475, 342)
        end = (710, 292)
        inverse = 1.0 - eased
        ship_center = (
            round(inverse * inverse * start[0] + 2 * inverse * eased * control[0] + eased * eased * end[0]),
            round(
                inverse * inverse * start[1]
                + 2 * inverse * eased * control[1]
                + eased * eased * end[1]
                + math.sin(progress * math.pi * 4) * 3
            ),
        )
        trail = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        trail_length = 82 + round(28 * math.sin(progress * math.pi))
        pygame.draw.polygon(
            trail,
            (*arriving.theme.secondary_color, 48),
            (
                (ship_center[0] - 25, ship_center[1] - 4),
                (ship_center[0] - trail_length, ship_center[1] + 11),
                (ship_center[0] - 25, ship_center[1] + 9),
            ),
        )
        pygame.draw.polygon(
            trail,
            (207, 244, 255, 125),
            (
                (ship_center[0] - 24, ship_center[1] + 1),
                (ship_center[0] - round(trail_length * 0.72), ship_center[1] + 8),
                (ship_center[0] - 24, ship_center[1] + 6),
            ),
        )
        self.screen.blit(trail, (0, 0))
        self.draw_approaching_ufo(ship_center, 0.14, elapsed, rotation=-4)

        # A few fading navigation pips reinforce direction without drawing a
        # hard line through the UFO and destination planet.
        for pip_index in range(3):
            pip_x = ship_center[0] - 102 - pip_index * 42
            pip_y = ship_center[1] + 9 + pip_index * 8
            pip_alpha = 105 - pip_index * 25
            pip = pygame.Surface((12, 12), pygame.SRCALPHA)
            pygame.draw.circle(
                pip,
                (*arriving.theme.secondary_color, pip_alpha),
                (6, 6),
                3,
            )
            self.screen.blit(pip, (pip_x - 6, pip_y - 6))

        title = self.heading_font.render("EN ROUTE", True, COLORS["accent"])
        self.screen.blit(title, title.get_rect(center=(WINDOW_SIZE[0] // 2, 72)))
        route_name = self.small_font.render(
            f"{departing.planet_name.upper()}  TO  {arriving.planet_name.upper()}",
            True,
            COLORS["text"],
        )
        route_panel = route_name.get_rect(center=(WINDOW_SIZE[0] // 2, 112)).inflate(28, 16)
        pygame.draw.rect(self.screen, (12, 25, 37), route_panel, border_radius=10)
        pygame.draw.rect(self.screen, arriving.theme.accent_color, route_panel, width=2, border_radius=10)
        self.screen.blit(route_name, route_name.get_rect(center=route_panel.center))

        status = self.small_font.render(
            f"PATIENT FILES RECEIVED  •  APPROACHING {arriving.planet_name.upper()}",
            True,
            arriving.theme.accent_color,
        )
        status_rect = status.get_rect(center=(WINDOW_SIZE[0] // 2, 548)).inflate(28, 14)
        pygame.draw.rect(self.screen, (10, 20, 34), status_rect, border_radius=9)
        pygame.draw.rect(
            self.screen,
            (*arriving.theme.accent_color,),
            status_rect,
            width=1,
            border_radius=9,
        )
        self.screen.blit(status, status.get_rect(center=status_rect.center))
        self.draw_cinematic_skip_prompt()

    def draw_travel_moons(self, destination, elapsed):
        """Frame the next route marker with destination-specific moons."""

        moon_shift = round(math.sin(elapsed / 650) * 3)
        if destination.theme.scene == "lumora_orbit":
            pygame.draw.circle(self.screen, (238, 139, 126), (817 + moon_shift, 172), 15)
            pygame.draw.circle(self.screen, (255, 194, 156), (812 + moon_shift, 167), 5)
            pygame.draw.circle(self.screen, (99, 210, 218), (1031 - moon_shift, 228), 11)
            pygame.draw.circle(self.screen, (204, 133, 232), (1027 - moon_shift, 401), 13)
            return

        pygame.draw.circle(
            self.screen,
            destination.theme.secondary_color,
            (824 + moon_shift, 184),
            14,
        )
        pygame.draw.circle(
            self.screen,
            (191, 203, 221),
            (1034 - moon_shift, 382),
            10,
        )

    def draw_travel_planet(self, destination, center, radius, foreground=False):
        """Draw a compact route marker planet without exposing clipped layers."""

        theme = destination.theme
        def blend(first, second, amount):
            return tuple(
                round(a + (b - a) * amount)
                for a, b in zip(first, second)
            )

        radius = max(20, radius)
        glow = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        pygame.draw.circle(glow, (*theme.accent_color, 26), center, radius + 16)
        self.screen.blit(glow, (0, 0))

        ring = pygame.Rect(
            center[0] - round(radius * 1.42),
            center[1] - round(radius * 0.38),
            round(radius * 2.84),
            round(radius * 0.76),
        )
        if foreground:
            pygame.draw.arc(
                self.screen,
                theme.secondary_color,
                ring,
                0,
                math.pi * 2,
                width=3,
            )

        diameter = radius * 2
        globe = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.circle(globe, theme.accent_color, (radius, radius), radius)
        if theme.scene == "lumora_orbit":
            pygame.draw.ellipse(
                globe,
                (39, 124, 91),
                pygame.Rect(-radius // 4, round(radius * 0.98), round(radius * 2.4), round(radius * 0.72)),
            )
            pygame.draw.ellipse(
                globe,
                (80, 187, 119),
                pygame.Rect(round(radius * 0.1), round(radius * 0.42), round(radius * 1.18), round(radius * 0.5)),
            )
            pygame.draw.ellipse(
                globe,
                (168, 232, 209, 125),
                pygame.Rect(-radius // 5, round(radius * 0.62), round(radius * 1.8), round(radius * 0.18)),
            )
            for light_x, light_y in ((0.44, 0.72), (0.66, 1.18), (1.16, 0.88), (1.3, 1.3)):
                pygame.draw.circle(
                    globe,
                    (196, 255, 163),
                    (round(radius * light_x), round(radius * light_y)),
                    max(2, radius // 18),
                )
        else:
            pygame.draw.ellipse(
                globe,
                blend(theme.accent_color, theme.horizon_color, 0.48),
                pygame.Rect(-radius // 3, round(radius * 1.15), round(radius * 2.6), round(radius * 0.55)),
            )
            pygame.draw.ellipse(
                globe,
                blend(theme.accent_color, theme.secondary_color, 0.2),
                pygame.Rect(round(radius * 0.2), round(radius * 0.42), round(radius * 1.35), round(radius * 0.34)),
            )
        shadow = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.ellipse(
            shadow,
            (4, 8, 22, 105 if foreground else 130),
            pygame.Rect(round(radius * 1.12), -radius // 8, radius, round(radius * 2.25)),
        )
        globe.blit(shadow, (0, 0))
        mask = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255, 255), (radius, radius), radius)
        globe.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.screen.blit(globe, (center[0] - radius, center[1] - radius))
        pygame.draw.circle(self.screen, theme.secondary_color, center, radius, width=3)

    def draw_final_departure_screen(self):
        """Draw the farewell-style departure after the final configured stop."""

        if self.homecoming_started:
            self.draw_homecoming_ending()
            return
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

    def draw_homecoming_ending(self, finished=False):
        """Fly toward a living planet, then settle outside a weathered home."""
        progress = 1.0 if finished else self.get_ending_progress()
        elapsed = 0 if self.ending_started_at is None else pygame.time.get_ticks() - self.ending_started_at
        if progress < 0.32:
            self.draw_space_background(elapsed)
            planet = pygame.Surface((440, 440), pygame.SRCALPHA)
            pygame.draw.circle(planet, (65, 132, 169), (220, 220), 207)
            for points in (((165, 40), (264, 64), (293, 127), (244, 155), (256, 206), (190, 228), (149, 157), (99, 125)),
                           ((300, 246), (379, 227), (411, 289), (370, 359), (289, 386), (258, 325)),
                           ((57, 255), (118, 237), (164, 288), (120, 346), (72, 331))):
                pygame.draw.polygon(planet, (94, 151, 112), points)
            for rect in ((100, 93, 182, 18), (220, 190, 160, 14), (66, 330, 159, 12)):
                pygame.draw.ellipse(planet, (208, 220, 208, 170), rect)
            pygame.draw.circle(planet, (156, 193, 198), (220, 220), 210, width=4)
            self.screen.blit(planet, (570, 100))
            t = progress / 0.32
            self.draw_approaching_ufo((round(120 + 520 * t), round(250 + 30 * t)), 0.28 - 0.17 * t, elapsed)
            label = self.small_font.render("One last flight.", True, (208, 216, 225))
            self.screen.blit(label, label.get_rect(center=(550, 600)))
            return

        # Dusk on the home planet. Broad, quiet shapes match the clinic artwork.
        self.screen.fill((39, 47, 67))
        pygame.draw.rect(self.screen, (78, 77, 86), (0, 240, 1100, 200))
        pygame.draw.circle(self.screen, (194, 190, 164), (949, 125), 32)
        for x, y in ((97, 88), (245, 132), (480, 63), (772, 79), (1030, 199)):
            pygame.draw.circle(self.screen, (168, 176, 188), (x, y), 1)
        for x, y, w in ((0, 337, 150), (140, 315, 125), (930, 325, 180)):
            pygame.draw.rect(self.screen, (49, 58, 64), (x, y, w, 128))
            pygame.draw.polygon(self.screen, (37, 46, 54), ((x - 10, y), (x + w // 2, y - 65), (x + w + 10, y)))
        pygame.draw.rect(self.screen, (54, 64, 57), (0, 429, 1100, 221))
        pygame.draw.ellipse(self.screen, (44, 53, 49), (480, 482, 535, 90))
        # The house: sagging roof, peeling boards, boarded window and dim porch.
        house = pygame.Rect(602, 303, 331, 203)
        pygame.draw.rect(self.screen, (110, 107, 94), house)
        for y in range(316, 506, 17):
            pygame.draw.line(self.screen, (79, 83, 77), (602, y), (933, y + 2), 2)
        for x, y in ((620, 347), (886, 467), (788, 408), (652, 486), (906, 326)):
            pygame.draw.polygon(self.screen, (151, 145, 121), ((x, y), (x + 19, y - 3), (x + 12, y + 10), (x + 3, y + 6)))
        pygame.draw.polygon(self.screen, (49, 53, 57), ((570, 312), (674, 229), (765, 242), (827, 232), (960, 319)))
        pygame.draw.lines(self.screen, (94, 93, 83), False, ((570, 312), (674, 229), (765, 242), (827, 232), (960, 319)), 5)
        pygame.draw.rect(self.screen, (91, 87, 80), (860, 231, 25, 47))
        pygame.draw.rect(self.screen, (35, 45, 48), (625, 350, 66, 68))
        pygame.draw.rect(self.screen, (66, 71, 66), (625, 350, 66, 68), 5)
        pygame.draw.line(self.screen, (127, 113, 86), (621, 363), (696, 392), 10)
        pygame.draw.line(self.screen, (96, 88, 70), (622, 408), (695, 380), 9)
        pygame.draw.rect(self.screen, (52, 58, 54), (830, 351, 67, 67))
        pygame.draw.line(self.screen, (99, 102, 83), (863, 352), (863, 416), 3)
        pygame.draw.line(self.screen, (99, 102, 83), (831, 385), (896, 385), 3)
        pygame.draw.rect(self.screen, (69, 67, 59), (732, 374, 55, 128))
        pygame.draw.circle(self.screen, (156, 144, 105), (775, 443), 3)
        pygame.draw.rect(self.screen, (87, 87, 74), (718, 501, 87, 10))
        pygame.draw.rect(self.screen, (75, 79, 67), (709, 511, 105, 9))
        glow = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        pygame.draw.circle(glow, (229, 190, 111, 12), (806, 372), 47)
        pygame.draw.circle(glow, (229, 190, 111, 20), (806, 372), 24)
        self.screen.blit(glow, (0, 0))
        pygame.draw.rect(self.screen, (173, 151, 100), (802, 365, 8, 13), border_radius=2)
        # Overgrowth, a cracked walk, and a fence whose boards lean unevenly.
        pygame.draw.polygon(self.screen, (87, 89, 77), ((725, 521), (799, 521), (850, 650), (668, 650)))
        pygame.draw.lines(self.screen, (51, 60, 53), False, ((758, 535), (748, 556), (773, 573), (754, 600)), 3)
        for i in range(55):
            x = 559 + (i * 73) % 448
            y = 503 + (i * 29) % 87
            if 712 < x < 820:
                continue
            pygame.draw.lines(self.screen, (72 + i % 3 * 6, 88, 62), False,
                              ((x - 6, y - 11), (x, y + 3), (x + 5, y - 16)), 2)
        for x in range(880, 1090, 24):
            tilt = (x % 7) - 3
            pygame.draw.line(self.screen, (105, 101, 83), (x, 552), (x + tilt * 3, 508 + x % 11), 7)
        pygame.draw.lines(self.screen, (94, 92, 78), False, ((875, 527), (971, 538), (1090, 529)), 5)
        # The UFO eases to a stop in front of the house, then holds in silence.
        t = min(1.0, max(0.0, (progress - 0.32) / 0.43))
        eased = 1 - (1 - t) ** 3
        x = round(-190 + 570 * eased)
        y = round(140 + 302 * eased)
        pygame.draw.ellipse(self.screen, (39, 49, 45), (x - 130, 521, 260, 29))
        self.draw_approaching_ufo((x, y), 0.32, elapsed if t < 1 else 0)
        if progress > 0.82 and not finished:
            label = self.small_font.render("Home.", True, (220, 211, 186))
            self.screen.blit(label, label.get_rect(center=(550, 605)))

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

    def get_arrival_progress(self):
        """Return the destination approach animation's zero-to-one progress."""

        if self.arrival_started_at is None:
            return 1.0
        elapsed = pygame.time.get_ticks() - self.arrival_started_at
        return max(0.0, min(1.0, elapsed / self.arrival_animation_duration))

    def draw_planet_arrival_screen(self):
        """Draw the clinic approaching the route controller's new destination."""

        destination = self.current_destination
        theme = destination.theme
        elapsed = (
            0
            if self.arrival_started_at is None
            else pygame.time.get_ticks() - self.arrival_started_at
        )
        progress = self._intro_smooth(self.get_arrival_progress())
        self.screen.fill(theme.space_color)

        haze = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        pygame.draw.ellipse(
            haze,
            (*theme.horizon_color, 34),
            pygame.Rect(560, 58, 570, 465),
        )
        pygame.draw.ellipse(
            haze,
            (*theme.secondary_color, 17),
            pygame.Rect(-110, 290, 710, 310),
        )
        self.screen.blit(haze, (0, 0))

        for index, (star_x, star_y, star_size) in enumerate(self.intro_stars):
            twinkle = (elapsed // 180 + index) % 7 == 0
            star_color = (230, 242, 255) if twinkle else (106, 139, 177)
            pygame.draw.circle(
                self.screen,
                star_color,
                (star_x, star_y),
                star_size + int(twinkle and star_size == 1),
            )

        self.draw_destination_planet(destination, elapsed)
        self.draw_arrival_ufo(progress, elapsed)
        self.draw_arrival_information(destination)
        self.draw_arrival_begin_button(destination)

    def draw_destination_planet(self, destination, elapsed):
        """Draw clean, layered planet art derived from destination metadata."""

        if destination.theme.scene == "lumora_orbit":
            self.draw_lumora_destination_planet(destination, elapsed)
            return

        theme = destination.theme
        def blend(first, second, amount):
            return tuple(
                round(a + (b - a) * amount)
                for a, b in zip(first, second)
            )

        center = (835, 300)
        radius = 145
        layer = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)

        for glow_radius, glow_alpha in ((181, 14), (166, 22), (154, 30)):
            pygame.draw.circle(
                layer,
                (*theme.accent_color, glow_alpha),
                center,
                glow_radius,
            )

        if "paired_moons" in theme.window_details:
            moon_shift = round(math.sin(elapsed / 780) * 4)
            pygame.draw.circle(
                layer,
                (*theme.secondary_color, 220),
                (705 + moon_shift, 151),
                25,
            )
            pygame.draw.circle(
                layer,
                (24, 38, 65, 100),
                (696 + moon_shift, 145),
                9,
            )
            pygame.draw.circle(
                layer,
                (211, 219, 229, 210),
                (1016 - moon_shift, 424),
                17,
            )
            pygame.draw.circle(
                layer,
                (146, 158, 182, 120),
                (1011 - moon_shift, 419),
                5,
            )

        # Draw the full ring behind the globe so it remains visible on the
        # outer edges without ever appearing to pass through the planet.
        orbit = pygame.Rect(center[0] - 205, center[1] - 58, 410, 116)
        pygame.draw.arc(
            layer,
            (*theme.secondary_color, 125),
            orbit,
            0,
            math.pi * 2,
            width=4,
        )

        diameter = radius * 2
        globe = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        globe_center = (radius, radius)
        pygame.draw.circle(globe, (*theme.accent_color, 255), globe_center, radius)

        # Soft atmospheric bands stay clipped to the circular globe instead
        # of becoming the large rectangular-looking patches seen previously.
        pygame.draw.ellipse(
            globe,
            blend(theme.accent_color, theme.horizon_color, 0.48),
            pygame.Rect(-20, 183, 330, 57),
        )
        pygame.draw.ellipse(
            globe,
            blend(theme.accent_color, theme.secondary_color, 0.18),
            pygame.Rect(34, 69, 164, 28),
        )
        pygame.draw.ellipse(
            globe,
            blend(theme.accent_color, (255, 229, 180), 0.3),
            pygame.Rect(36, 28, 158, 58),
        )
        for offset_x, offset_y, crater_radius in (
            (-61, 18, 13),
            (43, -44, 9),
            (62, 46, 16),
            (-5, 75, 7),
        ):
            pygame.draw.circle(
                globe,
                blend(theme.accent_color, theme.horizon_color, 0.58),
                (radius + offset_x, radius + offset_y),
                crater_radius,
            )

        terminator = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.ellipse(
            terminator,
            (8, 12, 35, 92),
            pygame.Rect(radius + 35, -18, radius, diameter + 36),
        )
        globe.blit(terminator, (0, 0))

        mask = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255, 255), globe_center, radius)
        globe.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        layer.blit(globe, (center[0] - radius, center[1] - radius))
        pygame.draw.circle(
            layer,
            (*theme.secondary_color, 205),
            center,
            radius,
            width=3,
        )

        if "orbital_traffic" in theme.window_details:
            station_angle = elapsed / 900
            station = (
                round(center[0] + math.cos(station_angle) * 188),
                round(center[1] + math.sin(station_angle) * 51),
            )
            pygame.draw.line(
                layer,
                (215, 230, 235, 220),
                (station[0] - 10, station[1]),
                (station[0] + 10, station[1]),
                width=3,
            )
            pygame.draw.rect(
                layer,
                (*theme.accent_color, 230),
                pygame.Rect(station[0] - 4, station[1] - 5, 8, 10),
                border_radius=2,
            )

        self.screen.blit(layer, (0, 0))

    def draw_lumora_destination_planet(self, destination, elapsed):
        """Draw Lumora as a living bioluminescent jungle world."""

        theme = destination.theme
        center = (835, 300)
        radius = 148
        pulse = (math.sin(elapsed / 430) + 1) / 2
        layer = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)

        for glow_radius, glow_alpha in (
            (205, 10),
            (184, 18),
            (164, 28 + round(pulse * 8)),
        ):
            pygame.draw.circle(
                layer,
                (*theme.accent_color, glow_alpha),
                center,
                glow_radius,
            )

        # Three differently colored moons establish Lumora as a new system at
        # a glance and remain outside the information panel and flight path.
        moon_drift = round(math.sin(elapsed / 820) * 4)
        moon_specs = (
            ((690 + moon_drift, 150), 26, (236, 139, 126), (255, 194, 156)),
            ((1010 - moon_drift, 174), 18, (91, 198, 216), (161, 236, 229)),
            ((1022 + moon_drift, 430), 22, (188, 121, 222), (230, 181, 241)),
        )
        for moon_center, moon_radius, moon_color, moon_highlight in moon_specs:
            pygame.draw.circle(layer, moon_color, moon_center, moon_radius)
            pygame.draw.circle(
                layer,
                moon_highlight,
                (moon_center[0] - moon_radius // 3, moon_center[1] - moon_radius // 3),
                max(4, moon_radius // 3),
            )
            pygame.draw.circle(
                layer,
                (16, 35, 51, 72),
                (moon_center[0] + moon_radius // 3, moon_center[1] + moon_radius // 4),
                max(3, moon_radius // 4),
            )

        # Thin orbital glows sit behind the globe and disappear naturally when
        # the planet is composited over them.
        orbit = pygame.Rect(center[0] - 205, center[1] - 55, 410, 110)
        pygame.draw.arc(layer, (*theme.secondary_color, 82), orbit, 0, math.pi * 2, width=3)
        inner_orbit = pygame.Rect(center[0] - 178, center[1] - 78, 356, 156)
        pygame.draw.arc(layer, (100, 223, 218, 65), inner_orbit, 0, math.pi * 2, width=2)

        diameter = radius * 2
        globe = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        globe_center = (radius, radius)
        pygame.draw.circle(globe, (20, 82, 82, 255), globe_center, radius)

        # Layered jungle landmasses create depth without resembling the flat
        # rectangular bands from the early placeholder planet.
        pygame.draw.ellipse(globe, (43, 128, 91), pygame.Rect(-35, 150, 235, 118))
        pygame.draw.ellipse(globe, (67, 166, 102), pygame.Rect(78, 42, 184, 118))
        pygame.draw.ellipse(globe, (93, 191, 111), pygame.Rect(24, 28, 118, 82))
        pygame.draw.ellipse(globe, (35, 116, 91), pygame.Rect(174, 176, 150, 92))
        pygame.draw.polygon(
            globe,
            (56, 154, 102),
            ((10, 128), (70, 102), (129, 127), (170, 111), (218, 151),
             (183, 188), (112, 177), (52, 198)),
        )

        # Bioluminescent canopy clusters pulse gently across the night side.
        light_points = (
            (53, 180, 5), (78, 147, 4), (104, 195, 6), (135, 154, 4),
            (166, 211, 5), (196, 172, 4), (220, 224, 6), (245, 136, 4),
            (258, 195, 5), (91, 82, 4), (137, 69, 5), (187, 91, 4),
        )
        canopy_glow = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        for light_x, light_y, light_radius in light_points:
            glow_radius = light_radius + 4 + round(pulse * 2)
            pygame.draw.circle(
                canopy_glow,
                (178, 255, 145, 38 + round(pulse * 22)),
                (light_x, light_y),
                glow_radius,
            )
            pygame.draw.circle(
                canopy_glow,
                (203, 255, 166, 225),
                (light_x, light_y),
                light_radius,
            )
        globe.blit(canopy_glow, (0, 0))

        # Mint, aqua, and lavender cloud banks curve around the world. Their
        # translucent overlap makes the atmosphere feel colorful and alive.
        clouds = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        cloud_shift = round(math.sin(elapsed / 1200) * 4)
        cloud_data = (
            (pygame.Rect(-34 + cloud_shift, 72, 190, 34), (205, 249, 213, 138)),
            (pygame.Rect(98 - cloud_shift, 111, 218, 39), (161, 231, 229, 122)),
            (pygame.Rect(18 + cloud_shift, 222, 196, 35), (221, 190, 240, 105)),
            (pygame.Rect(164 - cloud_shift, 47, 145, 27), (218, 248, 224, 118)),
        )
        for cloud_rect, cloud_color in cloud_data:
            pygame.draw.ellipse(clouds, cloud_color, cloud_rect)
            pygame.draw.ellipse(
                clouds,
                (*cloud_color[:3], max(28, cloud_color[3] // 2)),
                cloud_rect.inflate(-22, 10),
            )
        globe.blit(clouds, (0, 0))

        terminator = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.ellipse(
            terminator,
            (5, 14, 31, 100),
            pygame.Rect(radius + 35, -18, radius, diameter + 36),
        )
        globe.blit(terminator, (0, 0))

        mask = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255, 255), globe_center, radius)
        globe.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        layer.blit(globe, (center[0] - radius, center[1] - radius))
        pygame.draw.circle(layer, (105, 226, 176, 230), center, radius, width=4)
        pygame.draw.circle(layer, (*theme.secondary_color, 130), center, radius + 5, width=2)

        self.screen.blit(layer, (0, 0))

    def draw_arrival_ufo(self, progress, elapsed):
        """Fly the clinic from the foreground toward the destination planet."""

        start = (175, 500)
        end = (661, 360)
        center = (
            round(start[0] + (end[0] - start[0]) * progress),
            round(start[1] + (end[1] - start[1]) * progress),
        )
        scale = 0.25 - 0.15 * progress
        trail = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        trail_alpha = round(120 * (1 - progress))
        pygame.draw.line(
            trail,
            (*self.current_destination.theme.secondary_color, trail_alpha),
            (45, 545),
            (center[0] - 35, center[1] + 18),
            width=4,
        )
        pygame.draw.line(
            trail,
            (215, 247, 255, min(190, trail_alpha + 45)),
            (82, 528),
            (center[0] - 31, center[1] + 10),
            width=2,
        )
        self.screen.blit(trail, (0, 0))
        self.draw_approaching_ufo(center, scale, elapsed, rotation=-6)

    def draw_arrival_information(self, destination):
        """Draw destination, roster, and location details in a compact panel."""

        theme = destination.theme
        panel = pygame.Rect(48, 82, 555, 350)
        pygame.draw.rect(self.screen, (2, 7, 15), panel.move(7, 8), border_radius=18)
        pygame.draw.rect(self.screen, (17, 30, 43), panel, border_radius=18)
        pygame.draw.rect(
            self.screen,
            theme.accent_color,
            panel,
            width=3,
            border_radius=18,
        )

        tag = self.small_font.render("NEXT STOP", True, theme.accent_color)
        self.screen.blit(tag, (panel.x + 28, panel.y + 24))
        name_box = pygame.Rect(panel.x + 28, panel.y + 58, panel.width - 56, 72)
        self.draw_wrapped_text(
            destination.planet_name.upper(),
            self.heading_font,
            COLORS["text"],
            name_box,
            line_spacing=0,
        )
        subtitle = self.small_font.render(
            destination.subtitle.upper(),
            True,
            theme.secondary_color,
        )
        self.screen.blit(subtitle, (panel.x + 28, panel.y + 137))
        pygame.draw.line(
            self.screen,
            (*theme.secondary_color,),
            (panel.x + 28, panel.y + 171),
            (panel.right - 28, panel.y + 171),
            width=2,
        )

        roster_text = (
            f"DAY {destination.day_number}  •  "
            f"{len(destination.patient_roster)} PATIENTS WAITING"
        )
        roster = self.body_font.render(roster_text, True, theme.accent_color)
        self.screen.blit(roster, (panel.x + 28, panel.y + 193))
        message_box = pygame.Rect(
            panel.x + 28,
            panel.y + 235,
            panel.width - 56,
            76,
        )
        self.draw_wrapped_text(
            destination.arrival_message,
            self.body_font,
            COLORS["text"],
            message_box,
            line_spacing=4,
        )

    def draw_arrival_begin_button(self, destination):
        """Draw the action that opens the arrived destination's reception."""

        hovered = self.arrival_begin_button.collidepoint(self.get_mouse_position())
        fill = (116, 255, 191) if hovered else destination.theme.accent_color
        pygame.draw.rect(
            self.screen,
            (2, 7, 13),
            self.arrival_begin_button.move(4, 6),
            border_radius=10,
        )
        pygame.draw.rect(
            self.screen,
            fill,
            self.arrival_begin_button,
            border_radius=10,
        )
        pygame.draw.rect(
            self.screen,
            (225, 244, 239),
            self.arrival_begin_button,
            width=2,
            border_radius=10,
        )
        label = self.body_font.render(
            f"BEGIN DAY {destination.day_number}",
            True,
            (5, 16, 22),
        )
        self.screen.blit(label, label.get_rect(center=self.arrival_begin_button.center))
        hint = self.card_font.render(
            "Press Enter to begin the next clinic shift",
            True,
            COLORS["muted"],
        )
        self.screen.blit(
            hint,
            hint.get_rect(center=(WINDOW_SIZE[0] // 2, 632)),
        )

    def handle_arrival_click(self, position):
        """Begin the arrived destination when its action is selected."""

        if self.arrival_begin_button.collidepoint(position):
            self.play_sfx("button")
            self.start_next_shift()

    def draw_final_screen(self):
        """Draw an empty clinic after every configured route stop is complete."""

        if self.homecoming_started:
            self.draw_homecoming_ending(finished=True)
            for text, y, font in (("HOME, AT LAST.", 63, self.heading_font),
                                  (f"You made it home after {self.day_number} shifts.", 96, self.small_font)):
                label = font.render(text, True, (230, 220, 191))
                self.screen.blit(label, label.get_rect(center=(550, y)))
            self.draw_ending_button(self.final_replay_button, "PLAY AGAIN", False)
            self.draw_ending_button(self.final_quit_button, "QUIT GAME", True)
            return
        self.screen.fill(COLORS["background"])
        self.draw_game_logo((WINDOW_SIZE[0] // 2, 38), scale=0.86)
        subtitle = self.small_font.render(
            f"ROUTE STATUS  //  {self.current_destination.planet_name.upper()}",
            True,
            COLORS["muted"],
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(WINDOW_SIZE[0] // 2, 76)))

        self.draw_reception_room()
        self.draw_waiting_room_windows()
        self.draw_waiting_room_door()
        self.draw_waiting_room_chairs()
        self.draw_reception_desk(force_empty=True)
        self.draw_next_day_status()

        ticket_secured = self.has_return_passage()
        self.draw_ending_button(self.final_replay_button, "KEEP GOING" if ticket_secured else "RESTART ROUTE", False)
        self.draw_ending_button(self.final_quit_button, "GO HOME" if ticket_secured else "QUIT GAME", not ticket_secured)
        hint_text = (
            "Replay this stop with your money, upgrades, and ticket."
            if ticket_secured else "The route is complete. Return Passage was not purchased."
        )
        hint = self.card_font.render(
            hint_text,
            True,
            COLORS["muted"],
        )
        self.screen.blit(hint, hint.get_rect(center=(WINDOW_SIZE[0] // 2, 584)))

    def draw_next_day_status(self):
        """Draw route-completion status without inventing another clinic day."""

        status = pygame.Rect(30, 100, 1040, 49)
        pygame.draw.rect(self.screen, (54, 78, 78), status, border_radius=10)
        pygame.draw.rect(self.screen, COLORS["panel_border"], status, width=2, border_radius=10)
        display = status.inflate(-10, -10)
        pygame.draw.rect(self.screen, (5, 19, 24), display, border_radius=7)

        status_color = (255, 198, 75)
        pygame.draw.circle(self.screen, status_color, (display.x + 15, display.centery), 5)
        day_label = self.body_font.render("ROUTE STATUS", True, COLORS["text"])
        roster_label = self.small_font.render(
            "ALL SCHEDULED STOPS COMPLETE",
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
            "RETURN PASSAGE SECURED" if self.has_return_passage() else ROUTE_COMPLETE_HEADING,
            True,
            status_color,
        )
        notice_body = self.compact_ui_font.render(
            "Keep working or take the UFO home." if self.has_return_passage() else ROUTE_COMPLETE_MESSAGE,
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
        """Handle the route-complete choice or the post-homecoming buttons."""

        choosing = self.has_return_passage() and not self.homecoming_started
        if self.final_replay_button.collidepoint(position):
            self.play_sfx("button")
            if choosing:
                self.restart_current_shift()
            else:
                self.restart_game()
        elif self.final_quit_button.collidepoint(position):
            self.play_sfx("button")
            if choosing:
                self.begin_homecoming_sequence()
            else:
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
            "intro_dialogue_started_at",
            "test_result_started_at",
            "diagnosis_folder_animation_started_at",
            "notebook_attention_started_at",
            "notebook_preview_last_tick",
            "reception_transition_started_at",
            "queue_shift_started_at",
            "patient_fade_started_at",
            "end_day_shutdown_started_at",
            "ending_started_at",
            "arrival_started_at",
            "card_draw_notice_started_at",
            "card_shop_notice_started_at",
            "guided_tutorial_step_started_at",
            "guided_tutorial_nudge_started_at",
            "tutorial_opened_at",
            "help_attention_started_at",
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
            self.restart_current_shift()
        elif self.exit_quit_button.collidepoint(position):
            self.play_sfx("button")
            self.running = False

    def load_current_destination(self):
        """Load the route controller's current roster into the playable GUI."""

        destination = self.route.current_destination
        if destination.key != self.destinations[0].key:
            self.finish_guided_tutorial()
        patient_queue = self.roster_for_destination(destination)
        if not patient_queue:
            raise ValueError("A destination requires at least one patient.")
        self.waiting_room_queue = patient_queue
        self.ending_started_at = None
        self.arrival_started_at = None
        self.exit_confirmation_open = False
        self.exit_confirmation_opened_at = None
        self.reset_day()
        self.state = GameState.TITLE

    def start_next_shift(self):
        """Start the shift at the destination reached after Shop departure."""

        self.route.begin_current_shift()
        self.load_current_destination()

    def restart_current_shift(self):
        """Return to the active destination without erasing campaign progress."""

        self.homecoming_started = False
        restart_training = self.guided_tutorial_active and self.is_training_destination()
        # If payroll has already been collected for this exact destination,
        # remember that fact so replaying it cannot award the same pay twice.
        # A pending arrival belongs to the *next* destination, so that shift
        # must still begin with a fresh unpaid ledger.
        preserve_paid_status = (
            self.daily_payout_applied and not self.route.arrival_pending
        )
        self.finish_guided_tutorial()
        self.intro_dialogue_active = False
        self.intro_dialogue_started_at = None
        if self.route.arrival_pending:
            self.route.begin_current_shift()
        elif self.route.current_is_complete:
            self.route.reopen_current_shift()
        self.load_current_destination()
        if preserve_paid_status:
            self.daily_payout_applied = True
        if restart_training:
            self.start_guided_tutorial()

    def restart_game(self):
        """Reset campaign progress and return to reception without the intro."""

        restart_training = self.guided_tutorial_active
        self.finish_guided_tutorial()
        self.intro_dialogue_active = False
        self.intro_dialogue_started_at = None
        self.player.balance = STARTING_BALANCE
        self.player.machine_levels.clear()
        self.player.free_test_machines.clear()
        self.player.free_tests_used.clear()
        self.player.test_discount = 0
        self.purchased_shop_upgrades.clear()
        self.homecoming_started = False
        self.route_briefing_seen = False
        self.route_briefing_index = 0
        self.ending_started_at = None
        self.exit_confirmation_open = False
        self.exit_confirmation_opened_at = None
        self.route.reset()
        self.load_current_destination()
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
