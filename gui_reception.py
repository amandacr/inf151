"""Opening animation and reception-room presentation for The Cosmic Clinic."""

import math

import pygame

from gui_state import GameState
from gui_theme import COLORS, WINDOW_SIZE


class ReceptionMixin:
    def finish_intro(self):
        """Skip or finish the one-time opening animation and show the welcome screen."""

        self.reception_transition_started_at = None
        self.patient_fade_started_at = None
        self.state = GameState.TITLE

    def begin_reception_transition(self):
        """Call the next patient, or end the day if the room is empty."""

        if self.queue_shift_started_at is not None:
            return
        if self.patients_waiting() == 0:
            self.end_day()
            return
        if self.reception_transition_started_at is None:
            self.patient_fade_started_at = None
            self.reception_transition_started_at = pygame.time.get_ticks()

    def get_reception_transition_progress(self):
        """Return a zero-to-one value for the active reception-room transition."""

        if self.reception_transition_started_at is None:
            return 0.0
        elapsed = pygame.time.get_ticks() - self.reception_transition_started_at
        return max(0.0, min(1.0, elapsed / self.reception_transition_duration))

    def begin_queue_shift(self):
        """Begin sliding every remaining patient one chair toward the exam door."""

        if self.patients_waiting() > 0:
            self.queue_shift_started_at = pygame.time.get_ticks()

    def get_queue_shift_progress(self):
        """Return zero-to-one progress for the active waiting-room queue movement."""

        if self.queue_shift_started_at is None:
            return 1.0
        elapsed = pygame.time.get_ticks() - self.queue_shift_started_at
        progress = max(0.0, min(1.0, elapsed / self.queue_shift_duration))
        return progress * progress * (3 - 2 * progress)

    def get_waiting_patient_x(self, slot):
        """Return a remaining patient's animated chair position."""

        chair_positions = [entry["chair_x"] for entry in self.waiting_room_queue]
        remaining_index = slot - self.patients_called
        target_x = chair_positions[remaining_index]
        if self.queue_shift_started_at is None:
            return target_x

        start_index = min(remaining_index + 1, len(chair_positions) - 1)
        start_x = chair_positions[start_index]
        progress = self.get_queue_shift_progress()
        return round(start_x + (target_x - start_x) * progress)


    def create_game_logo_surface(self):
        """Build the two-tone clinic logo and its heartbeat divider once for reuse."""

        logo = pygame.Surface((720, 82), pygame.SRCALPHA)
        the_text = self.logo_small_font.render("THE", True, (200, 216, 224))
        cosmic_text = self.logo_font.render("COSMIC", True, (117, 190, 255))
        clinic_text = self.logo_font.render("CLINIC", True, COLORS["accent"])
        pulse_width = 78
        gap = 13
        total_width = (
            the_text.get_width()
            + cosmic_text.get_width()
            + clinic_text.get_width()
            + pulse_width
            + gap * 3
        )
        start_x = (logo.get_width() - total_width) // 2
        center_y = 39

        placements = (
            (the_text, start_x, center_y + 4),
            (cosmic_text, start_x + the_text.get_width() + gap, center_y),
        )
        for text_surface, text_x, text_y in placements:
            shadow = text_surface.copy()
            shadow.set_alpha(120)
            logo.blit(
                shadow,
                shadow.get_rect(midleft=(text_x + 3, text_y + 4)),
            )
            logo.blit(text_surface, text_surface.get_rect(midleft=(text_x, text_y)))

        pulse_x = start_x + the_text.get_width() + gap + cosmic_text.get_width() + gap
        pulse_y = center_y + 3
        pulse_points = (
            (pulse_x, pulse_y),
            (pulse_x + 13, pulse_y),
            (pulse_x + 20, pulse_y - 7),
            (pulse_x + 28, pulse_y + 11),
            (pulse_x + 38, pulse_y - 16),
            (pulse_x + 49, pulse_y + 3),
            (pulse_x + pulse_width, pulse_y + 3),
        )
        shadow_points = tuple((x + 3, y + 4) for x, y in pulse_points)
        pygame.draw.lines(logo, (13, 47, 61, 180), False, shadow_points, width=5)
        pygame.draw.lines(logo, (96, 224, 222), False, pulse_points, width=3)

        clinic_x = pulse_x + pulse_width + gap
        clinic_shadow = clinic_text.copy()
        clinic_shadow.set_alpha(120)
        logo.blit(
            clinic_shadow,
            clinic_shadow.get_rect(midleft=(clinic_x + 3, center_y + 4)),
        )
        logo.blit(
            clinic_text,
            clinic_text.get_rect(midleft=(clinic_x, center_y)),
        )

        pygame.draw.line(
            logo,
            (68, 98, 117),
            (start_x + the_text.get_width() + gap, 72),
            (clinic_x + clinic_text.get_width(), 72),
            width=1,
        )
        return logo


    def draw_game_logo(self, center, scale=1.0, alpha=255):
        """Draw the cached game logo at the requested size and opacity."""

        logo_size = (
            max(1, round(self.game_logo.get_width() * scale)),
            max(1, round(self.game_logo.get_height() * scale)),
        )
        logo = pygame.transform.smoothscale(self.game_logo, logo_size)
        logo.set_alpha(alpha)
        self.screen.blit(logo, logo.get_rect(center=center))


    def draw_reception_transition_fade(self):
        """Fade from the waiting room to black and then into the examination room."""

        alpha = 0
        if self.state == GameState.TITLE and self.reception_transition_started_at is not None:
            elapsed = pygame.time.get_ticks() - self.reception_transition_started_at
            fade_start = self.reception_transition_duration - self.reception_fade_duration
            fade_progress = max(
                0.0,
                min(1.0, (elapsed - fade_start) / self.reception_fade_duration),
            )
            alpha = round(255 * fade_progress)
        elif self.state == GameState.PATIENT and self.patient_fade_started_at is not None:
            elapsed = pygame.time.get_ticks() - self.patient_fade_started_at
            fade_progress = max(0.0, min(1.0, elapsed / self.patient_fade_duration))
            alpha = round(255 * (1 - fade_progress))

        if alpha > 0:
            fade = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
            fade.fill((4, 7, 16, alpha))
            self.screen.blit(fade, (0, 0))


    def draw_intro_screen(self):
        """Animate the clinic arriving in space before the welcome screen appears."""

        elapsed = pygame.time.get_ticks() - self.intro_started_at
        self.screen.fill((6, 10, 27))

        pygame.draw.circle(self.screen, (55, 45, 92), (1035, 575), 155)
        pygame.draw.circle(self.screen, (82, 64, 126), (1000, 535), 98)
        pygame.draw.arc(
            self.screen,
            (150, 113, 185),
            pygame.Rect(850, 490, 350, 115),
            math.pi,
            math.pi * 2,
            width=5,
        )

        for star_index, (star_x, star_y, star_size) in enumerate(self.intro_stars):
            twinkle = (elapsed // 180 + star_index) % 5 == 0
            star_color = (220, 232, 255) if twinkle else (125, 151, 185)
            pygame.draw.circle(
                self.screen,
                star_color,
                (star_x, star_y),
                star_size + int(twinkle and star_size == 1),
            )

        approach_progress = max(0.0, min(1.0, elapsed / 2800))
        approach_eased = approach_progress ** 1.65
        clinic_scale = 0.04 + 0.96 * approach_eased
        beam_progress = max(0.0, min(1.0, (elapsed - 2450) / 350))
        clinic_layer = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        self.draw_intro_clinic(clinic_layer, round(255 * beam_progress))

        scaled_size = (
            max(1, round(WINDOW_SIZE[0] * clinic_scale)),
            max(1, round(WINDOW_SIZE[1] * clinic_scale)),
        )
        scaled_clinic = pygame.transform.smoothscale(clinic_layer, scaled_size)
        arrival_alpha = max(0.0, min(1.0, elapsed / 450))
        scaled_clinic.set_alpha(round(255 * arrival_alpha))
        clinic_center_y = round(250 + 75 * approach_eased)
        clinic_position = (
            (WINDOW_SIZE[0] - scaled_size[0]) // 2,
            clinic_center_y - scaled_size[1] // 2,
        )
        self.screen.blit(scaled_clinic, clinic_position)

        title_progress = max(0.0, min(1.0, (elapsed - 2850) / 650))
        if title_progress > 0:
            self.draw_intro_title(title_progress)

        message_progress = max(0.0, min(1.0, (elapsed - 3650) / 650))
        message = self.body_font.render(
            "Your shift is beginning...",
            True,
            COLORS["text"],
        )
        message.set_alpha(round(255 * message_progress))
        self.screen.blit(
            message,
            message.get_rect(center=(WINDOW_SIZE[0] // 2, 545)),
        )

        skip = self.small_font.render(
            "Click anywhere or press Enter to skip",
            True,
            (139, 169, 180),
        )
        self.screen.blit(skip, skip.get_rect(center=(WINDOW_SIZE[0] // 2, 620)))

        fade_progress = max(0.0, min(1.0, (elapsed - 4850) / 650))
        if fade_progress > 0:
            fade = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
            fade.fill((6, 10, 27, round(255 * fade_progress)))
            self.screen.blit(fade, (0, 0))


    def draw_intro_clinic(self, surface, beam_alpha=255):
        """Draw the Cosmic Clinic as a classic flying saucer on a scalable layer."""

        # A faint beam under the ship gives the saucer a familiar hovering silhouette.
        beam = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        pygame.draw.polygon(
            beam,
            (103, 230, 221, 28),
            ((430, 405), (670, 405), (735, 535), (365, 535)),
        )
        pygame.draw.ellipse(beam, (135, 246, 231, 38), pygame.Rect(365, 515, 370, 34))
        beam.set_alpha(beam_alpha)
        surface.blit(beam, (0, 0))

        dome_shadow = pygame.Rect(313, 115, 474, 245)
        dome = pygame.Rect(323, 105, 454, 242)
        pygame.draw.ellipse(surface, (25, 35, 57), dome_shadow)
        pygame.draw.ellipse(surface, (65, 121, 153), dome)
        pygame.draw.ellipse(
            surface,
            (112, 190, 207),
            pygame.Rect(dome.x + 24, dome.y + 14, dome.width - 48, 150),
        )
        pygame.draw.ellipse(
            surface,
            (188, 231, 230),
            pygame.Rect(dome.x + 67, dome.y + 20, 122, 31),
        )
        pygame.draw.arc(surface, (174, 218, 222), dome, math.pi, math.pi * 2, width=5)

        saucer_shadow = pygame.Rect(65, 230, 980, 245)
        saucer = pygame.Rect(55, 216, 990, 242)
        pygame.draw.ellipse(surface, (22, 29, 49), saucer_shadow)
        pygame.draw.ellipse(surface, (82, 91, 113), saucer)
        pygame.draw.ellipse(surface, (158, 171, 183), saucer, width=5)

        upper_rim = pygame.Rect(83, 228, 934, 150)
        pygame.draw.ellipse(surface, (130, 143, 159), upper_rim)
        pygame.draw.arc(
            surface,
            (207, 218, 221),
            upper_rim,
            math.pi,
            math.pi * 2,
            width=5,
        )
        pygame.draw.arc(surface, (72, 81, 105), saucer, 0, math.pi, width=7)

        underside = pygame.Rect(208, 344, 684, 144)
        pygame.draw.ellipse(surface, (37, 45, 68), underside)
        pygame.draw.arc(
            surface,
            (122, 138, 156),
            underside,
            0,
            math.pi,
            width=4,
        )

        bolt_positions = (
            (155, 276),
            (242, 251),
            (330, 237),
            (770, 237),
            (858, 251),
            (945, 276),
        )
        for bolt_x, bolt_y in bolt_positions:
            pygame.draw.circle(surface, (66, 74, 91), (bolt_x, bolt_y), 4)
            pygame.draw.circle(surface, (204, 213, 214), (bolt_x - 1, bolt_y - 1), 1)

        light_positions = (
            (292, 406),
            (375, 428),
            (462, 440),
            (550, 444),
            (638, 440),
            (725, 428),
            (808, 406),
        )
        for light_x, light_y in light_positions:
            pygame.draw.circle(surface, (22, 35, 55), (light_x, light_y), 13)
            pygame.draw.circle(surface, (87, 211, 230), (light_x, light_y), 8)
            pygame.draw.circle(surface, (192, 247, 239), (light_x - 2, light_y - 2), 3)

        emitter = pygame.Rect(466, 366, 168, 66)
        emitter_glow = pygame.Rect(493, 381, 114, 37)
        pygame.draw.ellipse(surface, (23, 33, 53), emitter)
        pygame.draw.ellipse(surface, (108, 133, 153), emitter, width=3)
        pygame.draw.ellipse(surface, (34, 105, 119), emitter_glow)
        pygame.draw.ellipse(surface, (116, 231, 221), emitter_glow, width=3)
        pygame.draw.ellipse(
            surface,
            (191, 246, 237),
            pygame.Rect(emitter_glow.x + 30, emitter_glow.y + 8, 54, 14),
        )


    def draw_intro_title(self, progress):
        """Pop the glowing game title into place above the arrived clinic ship."""

        if progress < 0.72:
            title_scale = 0.68 + 0.47 * (progress / 0.72)
        else:
            title_scale = 1.15 - 0.15 * ((progress - 0.72) / 0.28)
        self.draw_game_logo(
            (WINDOW_SIZE[0] // 2, 64),
            scale=title_scale,
            alpha=round(255 * progress),
        )


    def draw_title_screen(self):
        """Draw the reusable reception room and its next-patient controls."""

        self.draw_reception_room()
        self.draw_reception_status()
        self.draw_waiting_room_windows()
        self.draw_waiting_room_door()
        self.draw_waiting_room_chairs()
        self.draw_waiting_room_aliens()
        self.draw_reception_desk()
        self.draw_reception_button()


    def draw_reception_room(self):
        """Draw the reception walls, flooring, and structural framing."""

        room = pygame.Rect(18, 90, WINDOW_SIZE[0] - 36, 490)
        pygame.draw.rect(self.screen, (48, 59, 79), room, border_radius=15)
        pygame.draw.rect(self.screen, (112, 129, 145), room, width=3, border_radius=15)

        upper_wall = pygame.Rect(room.x + 3, room.y + 3, room.width - 6, 320)
        pygame.draw.rect(self.screen, (55, 68, 91), upper_wall, border_radius=12)
        for panel_x in (365, 742):
            pygame.draw.line(
                self.screen,
                (92, 108, 128),
                (panel_x, 155),
                (panel_x, 408),
                width=2,
            )

        floor = pygame.Rect(room.x + 3, 405, room.width - 6, 172)
        pygame.draw.rect(self.screen, (68, 64, 87), floor)
        pygame.draw.line(
            self.screen,
            (155, 137, 171),
            (floor.x, floor.y),
            (floor.right, floor.y),
            width=3,
        )
        for floor_x in range(70, WINDOW_SIZE[0], 145):
            pygame.draw.line(
                self.screen,
                (80, 75, 102),
                (floor_x, floor.y + 5),
                (floor_x - 45, floor.bottom),
                width=1,
            )


    def draw_reception_status(self):
        """Draw reception, waiting status, shift, and money on a clinic monitor."""

        panel = pygame.Rect(30, 100, 1040, 49)
        pygame.draw.rect(self.screen, (54, 78, 78), panel, border_radius=10)
        pygame.draw.rect(self.screen, COLORS["panel_border"], panel, width=2, border_radius=10)
        display = panel.inflate(-10, -10)
        pygame.draw.rect(self.screen, (5, 19, 24), display, border_radius=7)

        progress = self.get_reception_transition_progress()
        queue_moving = self.queue_shift_started_at is not None
        waiting_color = (
            (117, 190, 255)
            if queue_moving
            else COLORS["accent"] if progress > 0 else (255, 198, 75)
        )
        pulse = 2 if (pygame.time.get_ticks() // 450) % 2 == 0 else 0
        pygame.draw.circle(
            self.screen,
            waiting_color,
            (display.x + 15, display.centery),
            5 + pulse,
        )

        left = self.body_font.render("RECEPTION", True, COLORS["text"])
        waiting = self.patients_waiting()
        if queue_moving:
            middle_text = f"PATIENTS WAITING: {waiting} • MOVING FORWARD"
        elif progress > 0:
            middle_text = "CALLING NEXT PATIENT"
        elif waiting == 0:
            middle_text = "ALL PATIENTS SEEN"
        else:
            middle_text = f"PATIENTS WAITING: {waiting}"
        middle = self.small_font.render(middle_text, True, waiting_color)
        right = self.body_font.render(
            "MONEY: $" + str(self.player.balance),
            True,
            COLORS["accent"],
        )
        self.screen.blit(left, left.get_rect(midleft=(display.x + 29, display.centery)))
        self.screen.blit(middle, middle.get_rect(center=display.center))
        self.screen.blit(right, right.get_rect(midright=(display.right - 13, display.centery)))


    def draw_waiting_room_windows(self):
        """Draw the panoramic space windows across the waiting-room wall."""

        window = pygame.Rect(37, 164, 792, 239)
        pygame.draw.rect(self.screen, (17, 31, 62), window, border_radius=13)
        pygame.draw.rect(self.screen, (122, 142, 163), window, width=4, border_radius=13)
        for star_x, star_y, radius in (
            (50, 183, 1), (65, 218, 1), (83, 298, 2), (105, 238, 2),
            (126, 335, 1), (151, 181, 1), (174, 230, 1), (196, 275, 1),
            (218, 362, 1), (236, 205, 2), (262, 321, 1), (285, 257, 1),
            (306, 220, 1), (326, 188, 1), (348, 286, 2), (384, 337, 1),
            (405, 239, 1), (427, 181, 1), (441, 205, 1), (466, 353, 1),
            (486, 224, 1), (507, 274, 2), (530, 326, 1), (548, 237, 1),
            (565, 185, 1), (588, 294, 2), (610, 216, 1), (623, 344, 1),
            (649, 183, 1), (670, 302, 1), (688, 226, 2), (707, 365, 1),
            (730, 188, 1), (746, 316, 1), (768, 271, 1), (787, 344, 2),
            (801, 193, 1), (816, 245, 1),
        ):
            pygame.draw.circle(self.screen, (192, 215, 239), (star_x, star_y), radius)
        pygame.draw.circle(self.screen, (91, 72, 141), (730, 232), 61)
        pygame.draw.circle(self.screen, (119, 94, 164), (710, 212), 27)
        pygame.draw.arc(
            self.screen,
            (175, 132, 208),
            pygame.Rect(662, 211, 136, 61),
            math.pi,
            math.pi * 2,
            width=4,
        )
        for divider_x in (235, 433, 631):
            pygame.draw.line(
                self.screen,
                (84, 104, 129),
                (divider_x, window.y + 4),
                (divider_x, window.bottom - 4),
                width=3,
            )

        poster = pygame.Rect(58, 184, 130, 73)
        pygame.draw.rect(self.screen, (46, 53, 79), poster, border_radius=7)
        pygame.draw.rect(self.screen, (139, 128, 159), poster, width=2, border_radius=7)
        poster_title = self.pile_font.render("CLINIC REMINDER", True, (222, 208, 229))
        poster_line = self.pile_font.render("KEEP ALL ORGANS", True, COLORS["accent"])
        poster_line_two = self.pile_font.render("INSIDE YOUR BODY", True, COLORS["accent"])
        self.screen.blit(poster_title, poster_title.get_rect(center=(poster.centerx, poster.y + 17)))
        self.screen.blit(poster_line, poster_line.get_rect(center=(poster.centerx, poster.y + 40)))
        self.screen.blit(poster_line_two, poster_line_two.get_rect(center=(poster.centerx, poster.y + 55)))


    def draw_waiting_room_door(self):
        """Draw the side examination door opening as the next patient approaches."""

        frame = pygame.Rect(850, 163, 211, 398)
        pygame.draw.rect(self.screen, (35, 44, 59), frame, border_radius=15)
        pygame.draw.rect(self.screen, (117, 134, 148), frame, width=4, border_radius=15)
        plaque = pygame.Rect(871, 173, 169, 31)
        pygame.draw.rect(self.screen, (23, 32, 46), plaque, border_radius=6)

        progress = self.get_reception_transition_progress()
        light_color = COLORS["accent"] if progress > 0 else (255, 198, 75)
        plaque_text = "EXAM BAY 01"
        plaque_label = self.small_font.render(plaque_text, True, light_color)
        self.screen.blit(plaque_label, plaque_label.get_rect(center=plaque.center))

        doorway = pygame.Rect(869, 215, 173, 320)
        pygame.draw.rect(self.screen, (8, 18, 28), doorway, border_radius=8)
        pygame.draw.rect(self.screen, (74, 95, 111), doorway, width=2, border_radius=8)
        door_progress = max(0.0, min(1.0, (progress - 0.38) / 0.42))
        panel_width = doorway.width // 2
        offset = round(panel_width * door_progress)
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(doorway)
        left_panel = pygame.Rect(
            doorway.x - offset,
            doorway.y,
            panel_width,
            doorway.height,
        )
        right_panel = pygame.Rect(
            doorway.centerx + offset,
            doorway.y,
            doorway.width - panel_width,
            doorway.height,
        )
        for panel in (left_panel, right_panel):
            pygame.draw.rect(self.screen, (80, 108, 122), panel)
            pygame.draw.rect(self.screen, (139, 170, 176), panel, width=2)
            pygame.draw.line(
                self.screen,
                (164, 191, 190),
                (panel.x + 9, panel.y + 18),
                (panel.x + 9, panel.bottom - 18),
                width=2,
            )
        self.screen.set_clip(previous_clip)
        pygame.draw.rect(
            self.screen,
            (125, 137, 152),
            pygame.Rect(frame.x + 15, frame.bottom - 17, frame.width - 30, 10),
            border_radius=4,
        )


    def draw_waiting_room_chairs(self):
        """Draw a row of futuristic chairs for the waiting patients."""

        for chair_center_x in (356, 498, 640, 782):
            back = pygame.Rect(chair_center_x - 48, 331, 96, 91)
            seat = pygame.Rect(chair_center_x - 52, 404, 104, 30)
            pygame.draw.rect(self.screen, (50, 48, 73), back, border_radius=18)
            pygame.draw.rect(self.screen, (119, 91, 132), back, width=3, border_radius=18)
            pygame.draw.rect(self.screen, (69, 63, 91), seat, border_radius=10)
            pygame.draw.rect(self.screen, (145, 113, 149), seat, width=2, border_radius=10)
            pygame.draw.line(
                self.screen,
                (91, 96, 116),
                (chair_center_x - 33, seat.bottom),
                (chair_center_x - 39, 470),
                width=6,
            )
            pygame.draw.line(
                self.screen,
                (91, 96, 116),
                (chair_center_x + 33, seat.bottom),
                (chair_center_x + 39, 470),
                width=6,
            )

    def draw_waiting_room_aliens(self):
        """Draw patients still waiting; walk the called one to the exam door."""

        progress = self.get_reception_transition_progress()
        shift_progress = self.get_queue_shift_progress()
        for slot, entry in enumerate(self.waiting_room_queue):
            if slot < self.patients_called:
                continue  # already seen, so the chair stays empty

            waiting_x = self.get_waiting_patient_x(slot)
            if slot == self.patients_called and progress > 0:
                walk = min(1.0, progress / 0.92)
                eased = walk * walk * (3 - 2 * walk)
                current_x = round(waiting_x + (930 - waiting_x) * eased)
                dx = current_x - entry["chair_x"]
                dy = round(-5 * math.sin(walk * math.pi * 5))
                self.draw_with_offset(entry["draw"], dx, dy)
            else:
                dx = waiting_x - entry["chair_x"]
                dy = (
                    -round(5 * math.sin(shift_progress * math.pi))
                    if self.queue_shift_started_at is not None
                    else 0
                )
                self.draw_with_offset(entry["draw"], dx, dy)

    def draw_with_offset(self, draw_method, dx, dy):
        """Run a draw method onto a temporary layer, then blit it shifted."""

        layer = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        real_screen = self.screen
        self.screen = layer
        try:
            draw_method()
        finally:
            self.screen = real_screen
        self.screen.blit(layer, (dx, dy))

    def draw_waiting_zorpa(self):
        # Zorpa walks from the chair nearest the exam door after being called.
        zorpa_x, zorpa_y = 782, 360
        alien_outline = (62, 36, 91)
        alien_color = (151, 99, 211)
        pygame.draw.ellipse(
            self.screen,
            alien_outline,
            pygame.Rect(zorpa_x - 31, zorpa_y - 4, 62, 57),
        )
        pygame.draw.ellipse(
            self.screen,
            alien_color,
            pygame.Rect(zorpa_x - 28, zorpa_y - 1, 56, 51),
        )
        pygame.draw.ellipse(
            self.screen,
            (207, 166, 245),
            pygame.Rect(zorpa_x - 18, zorpa_y + 5, 19, 11),
        )
        for antenna_x in (zorpa_x - 18, zorpa_x + 18):
            pygame.draw.line(
                self.screen,
                alien_outline,
                (antenna_x, zorpa_y + 2),
                (antenna_x - (4 if antenna_x < zorpa_x else -4), zorpa_y - 17),
                width=4,
            )
            pygame.draw.circle(
                self.screen,
                alien_color,
                (antenna_x - (4 if antenna_x < zorpa_x else -4), zorpa_y - 18),
                6,
            )
            pygame.draw.circle(
                self.screen,
                (207, 166, 245),
                (antenna_x - (5 if antenna_x < zorpa_x else -3), zorpa_y - 20),
                2,
            )
        pygame.draw.circle(self.screen, (42, 31, 63), (zorpa_x - 10, zorpa_y + 18), 5)
        pygame.draw.circle(self.screen, (42, 31, 63), (zorpa_x + 10, zorpa_y + 18), 5)
        pygame.draw.circle(self.screen, (245, 245, 255), (zorpa_x - 12, zorpa_y + 16), 1)
        pygame.draw.circle(self.screen, (245, 245, 255), (zorpa_x + 8, zorpa_y + 16), 1)
        pygame.draw.ellipse(
            self.screen,
            (239, 130, 190),
            pygame.Rect(zorpa_x - 23, zorpa_y + 29, 9, 5),
        )
        pygame.draw.ellipse(
            self.screen,
            (239, 130, 190),
            pygame.Rect(zorpa_x + 14, zorpa_y + 29, 9, 5),
        )
        pygame.draw.line(self.screen, alien_outline, (zorpa_x - 7, zorpa_y + 31), (zorpa_x, zorpa_y + 35), width=2)
        pygame.draw.line(self.screen, alien_outline, (zorpa_x, zorpa_y + 35), (zorpa_x + 7, zorpa_y + 31), width=2)
        for arm_start, arm_end in (
                ((zorpa_x - 17, zorpa_y + 57), (zorpa_x - 31, zorpa_y + 78)),
                ((zorpa_x + 17, zorpa_y + 57), (zorpa_x + 31, zorpa_y + 78)),
        ):
            pygame.draw.line(self.screen, alien_outline, arm_start, arm_end, width=9)
            pygame.draw.line(self.screen, alien_color, arm_start, arm_end, width=6)
            pygame.draw.circle(self.screen, alien_color, arm_end, 4)
        pygame.draw.ellipse(
            self.screen,
            alien_outline,
            pygame.Rect(zorpa_x - 24, zorpa_y + 43, 48, 52),
        )
        pygame.draw.ellipse(
            self.screen,
            alien_color,
            pygame.Rect(zorpa_x - 21, zorpa_y + 46, 42, 46),
        )
        pygame.draw.ellipse(
            self.screen,
            (178, 124, 226),
            pygame.Rect(zorpa_x - 12, zorpa_y + 60, 24, 23),
        )
        pygame.draw.ellipse(
            self.screen,
            (207, 166, 245),
            pygame.Rect(zorpa_x - 7, zorpa_y + 64, 8, 6),
        )
        pygame.draw.circle(self.screen, (255, 198, 75), (zorpa_x + 11, zorpa_y + 57), 5)
        pygame.draw.circle(self.screen, (255, 236, 164), (zorpa_x + 10, zorpa_y + 56), 2)
        for leg_x in (zorpa_x - 12, zorpa_x + 12):
            pygame.draw.line(
                self.screen,
                alien_outline,
                (leg_x, zorpa_y + 84),
                (leg_x, zorpa_y + 104),
                width=9,
            )
        pygame.draw.ellipse(self.screen, alien_outline, pygame.Rect(zorpa_x - 24, zorpa_y + 99, 22, 10))
        pygame.draw.ellipse(self.screen, alien_outline, pygame.Rect(zorpa_x + 2, zorpa_y + 99, 22, 10))
        pygame.draw.ellipse(self.screen, alien_color, pygame.Rect(zorpa_x - 21, zorpa_y + 100, 18, 7))
        pygame.draw.ellipse(self.screen, alien_color, pygame.Rect(zorpa_x + 3, zorpa_y + 100, 18, 7))

    def draw_waiting_zoogy(self):
        # draws zoogy
        pygame.draw.circle(self.screen, (49, 111, 82), (640, 371), 34)
        pygame.draw.circle(self.screen, (103, 173, 124), (640, 371), 31)
        pygame.draw.ellipse(self.screen, (68, 130, 92), pygame.Rect(614, 393, 52, 58))
        pygame.draw.ellipse(self.screen, (84, 151, 108), pygame.Rect(617, 396, 46, 52))
        pygame.draw.ellipse(self.screen, (151, 211, 155), pygame.Rect(623, 347, 20, 14))
        pygame.draw.circle(self.screen, (31, 51, 47), (629, 367), 4)
        pygame.draw.circle(self.screen, (31, 51, 47), (650, 367), 4)
        pygame.draw.circle(self.screen, (235, 249, 232), (628, 366), 1)
        pygame.draw.circle(self.screen, (235, 249, 232), (649, 366), 1)
        pygame.draw.circle(self.screen, (72, 137, 98), (618, 380), 3)
        pygame.draw.circle(self.screen, (72, 137, 98), (661, 380), 3)
        pygame.draw.arc(self.screen, (38, 81, 64), pygame.Rect(631, 377, 18, 11), 0, math.pi, width=2)
        for arm_y, direction in ((407, -1), (420, -1), (407, 1), (420, 1)):
            start_x = 623 if direction < 0 else 657
            end_x = start_x + 24 * direction
            pygame.draw.line(
                self.screen,
                (84, 151, 108),
                (start_x, arm_y),
                (end_x, arm_y - 6),
                width=7,
            )
            pygame.draw.circle(self.screen, (103, 173, 124), (end_x, arm_y - 6), 4)
        pygame.draw.line(self.screen, (143, 207, 151), (622, 404), (658, 404), width=3)
        pygame.draw.polygon(
            self.screen,
            (232, 194, 93),
            ((640, 411), (645, 417), (640, 423), (635, 417)),
        )
        pygame.draw.ellipse(self.screen, (111, 184, 126), pygame.Rect(625, 425, 30, 16))
        pygame.draw.line(self.screen, (65, 124, 92), (628, 442), (623, 466), width=8)
        pygame.draw.line(self.screen, (65, 124, 92), (652, 442), (657, 466), width=8)
        pygame.draw.ellipse(self.screen, (50, 103, 75), pygame.Rect(614, 461, 20, 8))
        pygame.draw.ellipse(self.screen, (50, 103, 75), pygame.Rect(647, 461, 20, 8))

    def draw_waiting_titus(self):
        # draws titus
        pygame.draw.ellipse(self.screen, (64, 125, 166), pygame.Rect(468, 338, 61, 74))
        pygame.draw.ellipse(self.screen, (118, 190, 220), pygame.Rect(477, 344, 20, 29))
        pygame.draw.ellipse(self.screen, (45, 95, 132), pygame.Rect(471, 390, 55, 64))
        pygame.draw.ellipse(self.screen, (77, 148, 188), pygame.Rect(474, 393, 49, 58))
        for eye_x, eye_y in ((484, 365), (499, 358), (514, 365)):
            pygame.draw.circle(self.screen, (233, 246, 242), (eye_x, eye_y), 6)
            pygame.draw.circle(self.screen, (31, 50, 70), (eye_x, eye_y), 2)
            pygame.draw.circle(self.screen, (255, 255, 255), (eye_x - 1, eye_y - 2), 1)
        pygame.draw.circle(self.screen, (38, 91, 132), (480, 382), 2)
        pygame.draw.circle(self.screen, (38, 91, 132), (518, 382), 2)
        pygame.draw.arc(self.screen, (31, 70, 104), pygame.Rect(489, 377, 20, 13), 0, math.pi, width=2)
        pygame.draw.line(self.screen, (175, 220, 225), (477, 402), (520, 402), width=3)
        pygame.draw.circle(self.screen, (245, 187, 87), (499, 407), 4)
        pygame.draw.line(self.screen, (45, 95, 132), (476, 410), (460, 429), width=7)
        pygame.draw.line(self.screen, (45, 95, 132), (521, 410), (537, 429), width=7)
        pygame.draw.circle(self.screen, (77, 148, 188), (459, 430), 5)
        pygame.draw.circle(self.screen, (77, 148, 188), (538, 430), 5)
        pygame.draw.arc(self.screen, (132, 197, 219), pygame.Rect(485, 418, 28, 22), 0, math.pi * 2, width=2)
        pygame.draw.line(self.screen, (45, 95, 132), (482, 442), (474, 466), width=8)
        pygame.draw.line(self.screen, (45, 95, 132), (515, 442), (523, 466), width=8)
        pygame.draw.ellipse(self.screen, (38, 83, 119), pygame.Rect(465, 461, 20, 8))
        pygame.draw.ellipse(self.screen, (38, 83, 119), pygame.Rect(514, 461, 20, 8))

    def draw_waiting_conmann(self):

        # draws conmann
        pygame.draw.ellipse(self.screen, (191, 91, 72), pygame.Rect(323, 355, 67, 62))
        pygame.draw.ellipse(self.screen, (226, 127, 91), pygame.Rect(329, 350, 55, 48))
        pygame.draw.ellipse(self.screen, (249, 170, 119), pygame.Rect(337, 355, 19, 12))
        pygame.draw.circle(self.screen, (177, 75, 68), (378, 385), 5)
        pygame.draw.circle(self.screen, (197, 88, 70), (335, 392), 3)
        pygame.draw.circle(self.screen, (50, 39, 57), (346, 371), 4)
        pygame.draw.circle(self.screen, (50, 39, 57), (367, 371), 4)
        pygame.draw.circle(self.screen, (249, 235, 220), (345, 370), 1)
        pygame.draw.circle(self.screen, (249, 235, 220), (366, 370), 1)
        pygame.draw.arc(
            self.screen,
            (82, 50, 62),
            pygame.Rect(348, 376, 18, 12),
            0,
            math.pi,
            width=2,
        )
        pygame.draw.arc(
            self.screen,
            (255, 190, 125),
            pygame.Rect(339, 393, 36, 13),
            math.pi,
            math.pi * 2,
            width=3,
        )
        pygame.draw.circle(self.screen, (255, 211, 105), (357, 401), 3)
        for foot_x in (334, 354, 374):
            pygame.draw.ellipse(self.screen, (159, 70, 66), pygame.Rect(foot_x, 407, 19, 12))
            pygame.draw.line(
                self.screen,
                (224, 125, 94),
                (foot_x + 8, 410),
                (foot_x + 8, 416),
                width=1,
            )

    def draw_reception_desk(self):
        """Draw the small reception desk, queue display, and decorative plant."""

        desk = pygame.Rect(35, 450, 280, 108)
        pygame.draw.rect(self.screen, (55, 56, 78), desk, border_radius=9)
        pygame.draw.rect(self.screen, (112, 107, 133), desk, width=2, border_radius=9)
        pygame.draw.rect(
            self.screen,
            (144, 129, 157),
            pygame.Rect(desk.x - 4, desk.y, desk.width + 8, 13),
            border_radius=5,
        )
        queue = pygame.Rect(61, 464, 238, 31)
        pygame.draw.rect(self.screen, (12, 27, 34), queue, border_radius=5)
        pygame.draw.rect(self.screen, (91, 132, 132), queue, width=1, border_radius=5)
        if self.queue_shift_started_at is not None:
            queue_text = f"{self.patients_waiting()} WAITING • MOVING UP"
        elif self.get_reception_transition_progress() > 0:
            queue_text = "CALLING PATIENT..."
        elif self.patients_waiting() == 0:
            queue_text = "NO PATIENTS WAITING"
        else:
            queue_text = f"PATIENTS WAITING: {self.patients_waiting()}"
        queue_label = self.card_font.render(queue_text, True, COLORS["accent"])
        self.screen.blit(queue_label, queue_label.get_rect(center=queue.center))

        pygame.draw.ellipse(self.screen, (38, 35, 55), pygame.Rect(244, 447, 52, 10))
        stem_color = (73, 145, 113)
        for stem_end in ((258, 405), (271, 395), (285, 407), (267, 411)):
            pygame.draw.line(self.screen, stem_color, (270, 435), stem_end, width=3)

        leaf_data = (
            (pygame.Rect(247, 399, 21, 34), (81, 169, 130)),
            (pygame.Rect(260, 391, 23, 42), (105, 194, 149)),
            (pygame.Rect(276, 402, 20, 31), (74, 158, 126)),
            (pygame.Rect(259, 407, 20, 27), (118, 203, 153)),
        )
        for leaf_rect, leaf_color in leaf_data:
            pygame.draw.ellipse(self.screen, (48, 104, 87), leaf_rect.inflate(3, 3))
            pygame.draw.ellipse(self.screen, leaf_color, leaf_rect)
            pygame.draw.line(
                self.screen,
                (170, 224, 181),
                leaf_rect.center,
                (leaf_rect.centerx, leaf_rect.y + 5),
                width=1,
            )

        pygame.draw.circle(self.screen, (208, 143, 226), (289, 406), 4)
        pygame.draw.circle(self.screen, (245, 202, 255), (288, 405), 1)

        pot = pygame.Rect(249, 427, 40, 28)
        pygame.draw.rect(self.screen, (88, 54, 91), pot.move(2, 2), border_radius=7)
        pygame.draw.rect(self.screen, (128, 82, 112), pot, border_radius=7)
        pygame.draw.rect(self.screen, (157, 101, 137), pygame.Rect(249, 427, 40, 8), border_radius=4)
        pygame.draw.rect(self.screen, (72, 45, 68), pygame.Rect(254, 428, 30, 4), border_radius=2)
        pygame.draw.line(self.screen, (181, 125, 157), (255, 438), (255, 448), width=2)
        pygame.draw.arc(
            self.screen,
            (95, 57, 91),
            pygame.Rect(253, 439, 32, 14),
            0,
            math.pi,
            width=2,
        )

    def patients_waiting(self):
        """Return how many patients are still in the waiting room."""

        return len(self.waiting_room_queue) - self.patients_called

    def draw_reception_button(self):
        """Draw the physical control that calls the patient into the exam bay."""

        progress = self.get_reception_transition_progress()
        queue_moving = self.queue_shift_started_at is not None
        hovered = (
            self.start_button.collidepoint(pygame.mouse.get_pos())
            and progress == 0
            and not queue_moving
        )
        shadow = self.start_button.move(0, 5)
        pygame.draw.rect(self.screen, (26, 31, 45), shadow, border_radius=10)
        if queue_moving:
            button_color = (74, 96, 110)
            label_text = "MOVING QUEUE..."
        elif progress > 0:
            button_color = (96, 119, 123)
            label_text = "PATIENT CALLED"
        else:
            pulse = (math.sin(pygame.time.get_ticks() / 420) + 1) / 2
            resting_green = (62, 205, 139)
            button_color = (
                COLORS["accent"]
                if hovered
                else tuple(
                    round(
                        resting_green[channel]
                        + (COLORS["accent"][channel] - resting_green[channel])
                        * pulse
                    )
                    for channel in range(3)
                )
            )
            label_text = "CALL NEXT PATIENT" if self.patients_waiting() else "END DAY"
        pygame.draw.rect(self.screen, button_color, self.start_button, border_radius=10)
        pygame.draw.rect(
            self.screen,
            (180, 221, 205),
            self.start_button,
            width=2,
            border_radius=10,
        )
        pygame.draw.circle(
            self.screen,
            (255, 198, 75) if progress == 0 else COLORS["accent"],
            (self.start_button.x + 21, self.start_button.centery),
            6,
        )
        button_text = self.small_font.render(label_text, True, COLORS["background"])
        self.screen.blit(button_text, button_text.get_rect(center=self.start_button.center))

