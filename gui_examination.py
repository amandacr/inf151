"""Patient examination workspace rendering for The Cosmic Clinic."""

import math

import pygame

from gui_theme import COLORS, WINDOW_SIZE


class ExaminationMixin:
    def draw_patient_screen(self):
        """Draw every panel that makes up the main patient workspace."""

        self.draw_med_bay_background()
        self.draw_status_bar()
        self.draw_draw_deck()
        self.draw_alien_patient()
        self.draw_id_card()
        self.draw_throwaway_deck()
        self.draw_notebook()
        self.draw_active_hand()
        self.draw_diagnosis_cards()
        self.draw_note_transfer_animation()
        self.draw_discard_animation()
        if self.diagnosis_confirmation_open:
            self.draw_diagnosis_confirmation()


    def draw_med_bay_background(self):
        """Draw a bright clinic wall, panoramic space window, and med-bay cabinetry."""

        room = pygame.Rect(18, 88, WINDOW_SIZE[0] - 36, 492)
        pygame.draw.rect(self.screen, (48, 59, 79), room, border_radius=14)
        pygame.draw.rect(
            self.screen,
            (112, 129, 145),
            room,
            width=3,
            border_radius=14,
        )

        ceiling = pygame.Rect(room.x + 2, room.y + 2, room.width - 4, 67)
        pygame.draw.rect(self.screen, (69, 80, 103), ceiling, border_radius=12)
        pygame.draw.line(
            self.screen,
            (128, 143, 158),
            (ceiling.x + 12, ceiling.bottom),
            (ceiling.right - 12, ceiling.bottom),
            width=2,
        )
        for light_x in (180, 550, 920):
            fixture = pygame.Rect(light_x - 52, room.y + 11, 104, 7)
            pygame.draw.rect(self.screen, (105, 120, 132), fixture, border_radius=4)
            pygame.draw.rect(
                self.screen,
                (164, 222, 211),
                fixture.inflate(-12, -3),
                border_radius=3,
            )

        window = pygame.Rect(room.x + 11, 157, room.width - 22, 210)
        pygame.draw.rect(self.screen, (18, 31, 62), window, border_radius=12)

        # Broad blue bands keep the view recognizably outer space without
        # turning the entire patient screen into a nearly black rectangle.
        pygame.draw.rect(
            self.screen,
            (24, 42, 80),
            pygame.Rect(window.x + 4, window.y + 45, window.width - 8, 62),
        )
        pygame.draw.rect(
            self.screen,
            (15, 26, 54),
            pygame.Rect(window.x + 4, window.y + 107, window.width - 8, 94),
        )

        nebula = pygame.Surface((255, 105), pygame.SRCALPHA)
        pygame.draw.ellipse(nebula, (107, 75, 157, 25), (0, 10, 255, 82))
        pygame.draw.ellipse(nebula, (89, 137, 178, 18), (55, 0, 185, 100))
        self.screen.blit(nebula, (window.x + 590, window.y + 45))
        pygame.draw.rect(
            self.screen,
            (119, 140, 161),
            window,
            width=4,
            border_radius=12,
        )
        star_data = (
            (55, 177, 1), (86, 211, 1), (121, 169, 2), (161, 322, 1),
            (207, 192, 1), (232, 343, 2), (286, 177, 1), (330, 316, 1),
            (384, 211, 2), (427, 350, 1), (471, 182, 1), (527, 332, 2),
            (576, 203, 1), (623, 347, 1), (670, 174, 2), (708, 302, 1),
            (756, 220, 1), (802, 345, 2), (846, 181, 1), (884, 314, 1),
            (928, 205, 2), (978, 339, 1), (1028, 176, 1), (1050, 267, 1),
        )
        for star_index, (star_x, star_y, star_size) in enumerate(star_data):
            pygame.draw.circle(
                self.screen,
                (190, 211, 239) if star_index % 4 else (193, 173, 233),
                (star_x, star_y),
                star_size,
            )

        distant_planets = (
            ((183, 175), 10, (225, 105, 126), (255, 169, 146), None),
            ((477, 342), 9, (61, 176, 185), (135, 231, 217), None),
            ((500, 181), 12, (218, 157, 69), (255, 212, 105), (240, 180, 99)),
            ((1042, 338), 8, (181, 99, 198), (237, 155, 224), None),
        )
        for center, radius, planet_color, highlight_color, ring_color in distant_planets:
            pygame.draw.circle(self.screen, planet_color, center, radius)
            pygame.draw.circle(
                self.screen,
                highlight_color,
                (center[0] - radius // 3, center[1] - radius // 3),
                max(2, radius // 3),
            )
            if ring_color is not None:
                ring = pygame.Rect(
                    center[0] - radius - 7,
                    center[1] - radius // 2,
                    radius * 2 + 14,
                    radius,
                )
                pygame.draw.arc(
                    self.screen,
                    ring_color,
                    ring,
                    0,
                    math.pi * 2,
                    width=2,
                )
        for frame_x in (window.x + 175, window.x + 462, window.x + 765):
            pygame.draw.line(
                self.screen,
                (80, 101, 124),
                (frame_x, window.y + 3),
                (frame_x, window.bottom - 3),
                width=3,
            )

        counter = pygame.Rect(room.x + 5, 365, room.width - 10, 207)
        pygame.draw.rect(self.screen, (68, 65, 89), counter)
        pygame.draw.rect(
            self.screen,
            (127, 119, 145),
            pygame.Rect(counter.x, counter.y, counter.width, 13),
            border_radius=5,
        )
        pygame.draw.line(
            self.screen,
            (166, 143, 181),
            (counter.x + 8, counter.y + 14),
            (counter.right - 8, counter.y + 14),
            width=2,
        )

        # One continuous workbench ties the notebook, cards, and diagnosis file together.
        workbench = pygame.Rect(30, 390, 1040, 174)
        pygame.draw.rect(
            self.screen,
            (25, 27, 40),
            workbench.move(0, 7),
            border_radius=13,
        )
        pygame.draw.rect(self.screen, (57, 62, 84), workbench, border_radius=13)
        pygame.draw.rect(
            self.screen,
            (107, 111, 138),
            workbench,
            width=2,
            border_radius=13,
        )
        pygame.draw.line(
            self.screen,
            (81, 83, 109),
            (workbench.x + 14, workbench.bottom - 14),
            (workbench.right - 14, workbench.bottom - 14),
            width=2,
        )
        for screw_position in (
            (workbench.x + 11, workbench.y + 11),
            (workbench.right - 11, workbench.y + 11),
            (workbench.x + 11, workbench.bottom - 11),
            (workbench.right - 11, workbench.bottom - 11),
        ):
            pygame.draw.circle(self.screen, (145, 148, 169), screw_position, 2)

        pipe_color = (95, 109, 119)
        pygame.draw.line(
            self.screen,
            pipe_color,
            (room.x + 9, 170),
            (room.x + 9, 345),
            width=5,
        )
        pygame.draw.circle(self.screen, (149, 158, 162), (room.x + 9, 250), 6)
        pygame.draw.line(
            self.screen,
            pipe_color,
            (room.right - 9, 168),
            (room.right - 9, 345),
            width=5,
        )
        pygame.draw.circle(self.screen, (149, 158, 162), (room.right - 9, 285), 6)


    def get_case_progress_step(self):
        """Return the currently active Inspect, Test, or Diagnose case stage."""

        if self.showing_diagnosis_hand or self.diagnosis_confirmation_open:
            return 2
        entries = self.notebook.get_entries(self.patient)
        if entries and "No tests" not in entries:
            return 1
        return 0


    def draw_case_progress(self, area):
        """Draw the compact Inspect-to-Diagnose tracker inside the status monitor."""

        stages = ("INSPECT", "TEST", "DIAGNOSE")
        active_step = self.get_case_progress_step()
        stage_width = 84
        stage_gap = 23
        total_width = stage_width * len(stages) + stage_gap * (len(stages) - 1)
        start_x = area.centerx - total_width // 2

        for index, stage in enumerate(stages):
            stage_rect = pygame.Rect(
                start_x + index * (stage_width + stage_gap),
                area.centery - 9,
                stage_width,
                18,
            )
            if index == active_step:
                fill_color = (38, 97, 78)
                border_color = COLORS["accent"]
                text_color = COLORS["text"]
            elif index < active_step:
                fill_color = (26, 61, 58)
                border_color = (85, 164, 139)
                text_color = (164, 208, 192)
            else:
                fill_color = (19, 33, 40)
                border_color = (66, 89, 91)
                text_color = COLORS["muted"]

            pygame.draw.rect(self.screen, fill_color, stage_rect, border_radius=6)
            pygame.draw.rect(
                self.screen,
                border_color,
                stage_rect,
                width=1,
                border_radius=6,
            )
            stage_text = self.pile_font.render(stage, True, text_color)
            self.screen.blit(stage_text, stage_text.get_rect(center=stage_rect.center))

            if index < len(stages) - 1:
                arrow = self.pile_font.render(">", True, COLORS["muted"])
                arrow_x = stage_rect.right + stage_gap // 2
                self.screen.blit(
                    arrow,
                    arrow.get_rect(center=(arrow_x, stage_rect.centery)),
                )


    def draw_status_bar(self):
        """Draw patient, case progress, and balance data on a clinic-monitor display."""

        panel = self.layout["status_bar"]
        pygame.draw.rect(self.screen, (54, 78, 78), panel, border_radius=10)
        pygame.draw.rect(
            self.screen,
            COLORS["panel_border"],
            panel,
            width=2,
            border_radius=10,
        )
        display = panel.inflate(-10, -10)
        pygame.draw.rect(self.screen, (5, 19, 24), display, border_radius=7)
        pygame.draw.rect(
            self.screen,
            (103, 135, 126),
            display,
            width=1,
            border_radius=7,
        )

        for grid_x in range(display.x + 40, display.right, 80):
            pygame.draw.line(
                self.screen,
                (12, 34, 39),
                (grid_x, display.y + 3),
                (grid_x, display.bottom - 3),
                width=1,
            )
        for screw_position in (
            (panel.x + 6, panel.y + 6),
            (panel.right - 6, panel.y + 6),
            (panel.x + 6, panel.bottom - 6),
            (panel.right - 6, panel.bottom - 6),
        ):
            pygame.draw.circle(self.screen, (151, 169, 163), screw_position, 2)

        pygame.draw.circle(
            self.screen,
            COLORS["accent"],
            (display.x + 15, display.centery),
            5,
        )
        pygame.draw.circle(
            self.screen,
            (215, 255, 232),
            (display.x + 14, display.centery - 1),
            2,
        )

        patient = self.body_font.render(
            "PATIENT: " + self.patient.name, True, COLORS["text"]
        )
        money = self.body_font.render(
            "MONEY: $" + str(self.player.balance), True, COLORS["accent"]
        )

        self.screen.blit(
            patient,
            patient.get_rect(midleft=(display.x + 28, display.centery)),
        )

        pygame.draw.line(
            self.screen,
            (72, 101, 91),
            (display.x + 300, display.y + 5),
            (display.x + 300, display.bottom - 5),
            width=1,
        )
        progress_left = display.x + 301
        progress_right = display.right - 236
        progress_area = pygame.Rect(
            progress_left,
            display.y + 3,
            progress_right - progress_left,
            display.height - 6,
        )
        self.draw_case_progress(progress_area)
        pygame.draw.line(
            self.screen,
            (72, 101, 91),
            (display.right - 235, display.y + 5),
            (display.right - 235, display.bottom - 5),
            width=1,
        )
        self.screen.blit(
            money,
            money.get_rect(midright=(display.right - 14, display.centery)),
        )


    def draw_draw_deck(self):
        """Draw the placeholder test-card stack resting in a counter tray."""

        panel = self.layout["draw_deck"]
        tray = pygame.Rect(panel.x + 14, panel.y + 28, panel.width - 28, panel.height - 34)
        pygame.draw.rect(
            self.screen,
            (5, 12, 18),
            tray.move(4, 5),
            border_radius=10,
        )
        pygame.draw.rect(self.screen, (38, 47, 60), tray, border_radius=10)
        pygame.draw.rect(
            self.screen,
            (88, 93, 111),
            tray,
            width=2,
            border_radius=10,
        )

        plaque = pygame.Rect(panel.x + 15, panel.y + 5, panel.width - 30, 25)
        pygame.draw.rect(self.screen, (43, 51, 64), plaque, border_radius=5)
        self.draw_centered_label("DRAW DECK", plaque, plaque.centery)

        card = pygame.Rect(panel.x + 31, panel.y + 54, 72, 96)
        for offset in (8, 4, 0):
            shifted = card.move(offset, -offset)
            pygame.draw.rect(self.screen, COLORS["card"], shifted, border_radius=5)
            pygame.draw.rect(
                self.screen, COLORS["card_text"], shifted, width=2, border_radius=5
            )


    def draw_alien_patient(self):
        """Draw Zorpa standing inside a softly lit examination bay."""

        panel = self.layout["alien"]
        pygame.draw.rect(
            self.screen,
            (5, 12, 18),
            panel.move(5, 5),
            border_radius=12,
        )
        pygame.draw.rect(self.screen, (35, 45, 56), panel, border_radius=12)
        pygame.draw.rect(
            self.screen,
            (82, 99, 105),
            panel,
            width=2,
            border_radius=12,
        )
        for screw_position in (
            (panel.x + 8, panel.y + 8),
            (panel.right - 8, panel.y + 8),
            (panel.x + 8, panel.bottom - 8),
            (panel.right - 8, panel.bottom - 8),
        ):
            pygame.draw.circle(self.screen, (114, 124, 126), screw_position, 2)
        self.draw_centered_label("EXAMINATION BAY", panel, panel.y + 18)

        bay = pygame.Rect(
            panel.x + 12,
            panel.y + 34,
            panel.width - 24,
            panel.height - 62,
        )
        pygame.draw.rect(self.screen, (8, 25, 32), bay, border_radius=10)
        pygame.draw.rect(
            self.screen,
            COLORS["muted"],
            bay,
            width=2,
            border_radius=10,
        )

        glow = pygame.Surface(bay.size, pygame.SRCALPHA)
        pygame.draw.polygon(
            glow,
            (112, 255, 181, 28),
            (
                (bay.width // 2 - 22, 6),
                (bay.width // 2 + 22, 6),
                (bay.width // 2 + 78, bay.height - 10),
                (bay.width // 2 - 78, bay.height - 10),
            ),
        )
        pygame.draw.ellipse(
            glow,
            (112, 255, 181, 22),
            pygame.Rect(30, 12, bay.width - 60, bay.height - 14),
        )
        self.screen.blit(glow, bay.topleft)

        ceiling_light = pygame.Rect(bay.centerx - 30, bay.y + 7, 60, 8)
        pygame.draw.rect(
            self.screen,
            COLORS["accent"],
            ceiling_light,
            border_radius=4,
        )
        pygame.draw.line(
            self.screen,
            (72, 101, 91),
            (bay.x + 18, bay.y + 18),
            (bay.x + 18, bay.bottom - 18),
            width=2,
        )
        pygame.draw.line(
            self.screen,
            (72, 101, 91),
            (bay.right - 18, bay.y + 18),
            (bay.right - 18, bay.bottom - 18),
            width=2,
        )

        idle_time = pygame.time.get_ticks()
        shake_x = round(math.sin(idle_time / 42) * 1.2 + math.sin(idle_time / 23) * 0.5)
        shake_y = round(math.sin(idle_time / 58) * 0.8)
        antenna_sway = round(math.sin(idle_time / 260) * 2)
        blinking = idle_time % 3600 >= 3480
        chest_pulse = (math.sin(idle_time / 310) + 1) / 2

        base_alien_center_x = bay.centerx - 38
        platform = pygame.Rect(base_alien_center_x - 67, bay.bottom - 20, 134, 17)
        pygame.draw.ellipse(self.screen, (56, 91, 83), platform)
        pygame.draw.arc(
            self.screen,
            COLORS["panel_border"],
            platform,
            0,
            math.pi,
            width=2,
        )

        alien_outline = (62, 36, 91)
        alien_shadow = (89, 54, 132)
        alien_color = (151, 99, 211)
        alien_highlight = (207, 166, 245)
        cheek_color = (239, 130, 190)
        alien_center_x = base_alien_center_x + shake_x
        head = pygame.Rect(alien_center_x - 29, bay.y + 25 + shake_y, 58, 52)
        body = pygame.Rect(alien_center_x - 23, head.bottom - 3, 46, 43)

        left_antenna_tip = (head.centerx - 22 + antenna_sway, head.y - 7)
        right_antenna_tip = (head.centerx + 22 + antenna_sway, head.y - 7)

        pygame.draw.line(
            self.screen,
            alien_outline,
            (head.centerx - 14, head.y + 7),
            (left_antenna_tip[0], left_antenna_tip[1] + 1),
            width=5,
        )
        pygame.draw.line(
            self.screen,
            alien_color,
            (head.centerx - 14, head.y + 7),
            (left_antenna_tip[0], left_antenna_tip[1] + 1),
            width=2,
        )
        pygame.draw.line(
            self.screen,
            alien_outline,
            (head.centerx + 14, head.y + 7),
            (right_antenna_tip[0], right_antenna_tip[1] + 1),
            width=5,
        )
        pygame.draw.line(
            self.screen,
            alien_color,
            (head.centerx + 14, head.y + 7),
            (right_antenna_tip[0], right_antenna_tip[1] + 1),
            width=2,
        )
        for antenna_x, antenna_y in (left_antenna_tip, right_antenna_tip):
            pygame.draw.circle(
                self.screen,
                alien_outline,
                (antenna_x, antenna_y),
                7,
            )
            pygame.draw.circle(
                self.screen,
                alien_color,
                (antenna_x, antenna_y),
                5,
            )
            pygame.draw.circle(
                self.screen,
                alien_highlight,
                (antenna_x - 1, antenna_y - 2),
                2,
            )

        for start, end in (
            (
                (body.x + 7, body.y + 12),
                (body.x - 11, body.bottom - 4),
            ),
            (
                (body.right - 7, body.y + 12),
                (body.right + 11, body.bottom - 4),
            ),
        ):
            pygame.draw.line(self.screen, alien_outline, start, end, width=11)
            pygame.draw.line(self.screen, alien_color, start, end, width=7)
            pygame.draw.circle(self.screen, alien_outline, end, 6)
            pygame.draw.circle(self.screen, alien_color, end, 4)

        for start, end in (
            (
                (body.centerx - 10, body.bottom - 4),
                (body.centerx - 18, platform.y + 5),
            ),
            (
                (body.centerx + 10, body.bottom - 4),
                (body.centerx + 18, platform.y + 5),
            ),
        ):
            pygame.draw.line(self.screen, alien_outline, start, end, width=12)
            pygame.draw.line(self.screen, alien_color, start, end, width=8)

        left_foot = pygame.Rect(body.centerx - 29, platform.y, 22, 9)
        right_foot = pygame.Rect(body.centerx + 7, platform.y, 22, 9)
        pygame.draw.ellipse(self.screen, alien_outline, left_foot.inflate(4, 3))
        pygame.draw.ellipse(self.screen, alien_outline, right_foot.inflate(4, 3))
        pygame.draw.ellipse(self.screen, alien_color, left_foot)
        pygame.draw.ellipse(self.screen, alien_color, right_foot)

        pygame.draw.rect(
            self.screen,
            alien_outline,
            body.inflate(5, 5),
            border_radius=20,
        )
        pygame.draw.rect(self.screen, alien_color, body, border_radius=18)
        belly = pygame.Rect(body.centerx - 13, body.y + 13, 26, 25)
        pygame.draw.ellipse(self.screen, (178, 124, 226), belly)
        pygame.draw.ellipse(
            self.screen,
            alien_highlight,
            pygame.Rect(belly.x + 5, belly.y + 4, 9, 7),
        )

        pygame.draw.ellipse(self.screen, alien_shadow, head.move(3, 4))
        pygame.draw.ellipse(self.screen, alien_outline, head.inflate(5, 5))
        pygame.draw.ellipse(self.screen, alien_color, head)
        pygame.draw.ellipse(
            self.screen,
            alien_highlight,
            pygame.Rect(head.x + 10, head.y + 7, 19, 12),
        )

        left_eye = pygame.Rect(head.x + 11, head.y + 18, 11, 16)
        right_eye = pygame.Rect(head.right - 22, head.y + 18, 11, 16)
        if blinking:
            for eye in (left_eye, right_eye):
                pygame.draw.arc(
                    self.screen,
                    alien_outline,
                    pygame.Rect(eye.x, eye.centery - 3, eye.width, 7),
                    math.pi,
                    math.pi * 2,
                    width=2,
                )
        else:
            pygame.draw.ellipse(self.screen, alien_outline, left_eye)
            pygame.draw.ellipse(self.screen, alien_outline, right_eye)
            pygame.draw.circle(
                self.screen,
                (245, 245, 255),
                (left_eye.x + 4, left_eye.y + 4),
                2,
            )
            pygame.draw.circle(
                self.screen,
                (245, 245, 255),
                (right_eye.x + 4, right_eye.y + 4),
                2,
            )

        pygame.draw.ellipse(
            self.screen,
            cheek_color,
            pygame.Rect(head.x + 5, head.y + 34, 10, 6),
        )
        pygame.draw.ellipse(
            self.screen,
            cheek_color,
            pygame.Rect(head.right - 15, head.y + 34, 10, 6),
        )
        pygame.draw.line(
            self.screen,
            alien_outline,
            (head.centerx - 7, head.y + 39),
            (head.centerx, head.y + 43),
            width=2,
        )
        pygame.draw.line(
            self.screen,
            alien_outline,
            (head.centerx, head.y + 43),
            (head.centerx + 7, head.y + 39),
            width=2,
        )

        chest_light_center = (body.centerx + 11, body.y + 13)
        chest_glow = pygame.Surface((22, 22), pygame.SRCALPHA)
        pygame.draw.circle(
            chest_glow,
            (255, 198, 75, round(35 + 45 * chest_pulse)),
            (11, 11),
            round(8 + 2 * chest_pulse),
        )
        self.screen.blit(
            chest_glow,
            (chest_light_center[0] - 11, chest_light_center[1] - 11),
        )
        pygame.draw.circle(
            self.screen,
            (
                255,
                round(185 + 45 * chest_pulse),
                round(68 + 45 * chest_pulse),
            ),
            chest_light_center,
            5 + round(chest_pulse),
        )
        pygame.draw.circle(
            self.screen,
            (255, 236, 164),
            (body.centerx + 10, body.y + 12),
            2,
        )

        self.draw_symptom_bubble(bay, head)

        name = self.small_font.render(self.patient.name, True, COLORS["muted"])
        self.screen.blit(name, name.get_rect(center=(panel.centerx, panel.bottom - 13)))


    def draw_symptom_bubble(self, bay, alien_head):
        """Draw Zorpa's current symptom in a speech bubble beside the alien."""

        bubble = pygame.Rect(bay.right - 100, bay.y + 15, 91, 55)
        bubble_fill = (246, 241, 220)
        bubble_outline = (62, 50, 74)
        tail = (
            (bubble.x + 5, bubble.y + 32),
            (alien_head.right - 2, alien_head.y + 27),
            (bubble.x + 7, bubble.y + 45),
        )
        pygame.draw.polygon(self.screen, bubble_fill, tail)
        pygame.draw.line(self.screen, bubble_outline, tail[0], tail[1], width=2)
        pygame.draw.line(self.screen, bubble_outline, tail[1], tail[2], width=2)
        pygame.draw.rect(self.screen, bubble_fill, bubble, border_radius=10)
        pygame.draw.rect(
            self.screen,
            bubble_outline,
            bubble,
            width=2,
            border_radius=10,
        )

        symptom_lines = ("I CAN'T STOP", "SHAKING!")
        for line_index, line_text in enumerate(symptom_lines):
            line = self.pile_font.render(line_text, True, bubble_outline)
            line_y = bubble.y + 17 + line_index * 17
            self.screen.blit(line, line.get_rect(center=(bubble.centerx, line_y)))


    def draw_id_card(self):
        """Draw either side of the patient's laminated license in a clipped holder."""

        panel = self.layout["id_card"]
        pygame.draw.rect(
            self.screen,
            (5, 12, 18),
            panel.move(4, 5),
            border_radius=10,
        )
        pygame.draw.rect(self.screen, (42, 48, 58), panel, border_radius=10)
        pygame.draw.rect(
            self.screen,
            (93, 101, 116),
            panel,
            width=2,
            border_radius=10,
        )
        border_color = (
            COLORS["accent"]
            if panel.collidepoint(pygame.mouse.get_pos())
            else COLORS["panel_border"]
        )

        card = pygame.Rect(panel.x + 8, panel.y + 10, panel.width - 16, panel.height - 18)
        pygame.draw.rect(self.screen, COLORS["card"], card, border_radius=9)
        pygame.draw.rect(
            self.screen,
            border_color,
            card,
            width=3,
            border_radius=9,
        )

        shine = pygame.Surface(card.size, pygame.SRCALPHA)
        pygame.draw.polygon(
            shine,
            (255, 255, 255, 24),
            (
                (card.width - 92, 0),
                (card.width - 43, 0),
                (card.width, 58),
                (card.width, 97),
            ),
        )
        self.screen.blit(shine, card.topleft)

        pygame.draw.line(
            self.screen,
            (177, 198, 190),
            (panel.centerx, panel.y),
            (panel.centerx, panel.y + 8),
            width=3,
        )
        clip = pygame.Rect(panel.centerx - 17, panel.y + 3, 34, 18)
        pygame.draw.rect(self.screen, (177, 198, 190), clip, border_radius=5)
        pygame.draw.rect(
            self.screen,
            COLORS["card_text"],
            clip,
            width=2,
            border_radius=5,
        )
        clip_slot = pygame.Rect(clip.centerx - 7, clip.y + 4, 14, 5)
        pygame.draw.rect(self.screen, COLORS["background"], clip_slot, border_radius=2)

        if self.showing_health_id:
            title_text = "HEALTH ID"
            details = list(self.patient.medical_info.items())
            next_side = "CLICK TO VIEW ID"
        else:
            title_text = "INTERGALACTIC ID"
            details = [("Name", self.patient.name)] + list(self.patient.profile.items())
            next_side = "CLICK TO VIEW HEALTH ID"

        title = self.body_font.render(title_text, True, COLORS["card_text"])
        self.screen.blit(title, title.get_rect(center=(card.centerx, card.y + 19)))

        pygame.draw.line(
            self.screen,
            (145, 169, 151),
            (card.x + 10, card.y + 34),
            (card.right - 10, card.y + 34),
            width=1,
        )

        portrait = pygame.Rect(card.x + 11, card.y + 43, 51, 63)
        self.draw_id_portrait(portrait, self.showing_health_id)

        detail_y = card.y + 43
        for label, value in details:
            detail_text = f"{label}: {value}"
            detail_font = self.card_font
            available_width = card.right - 10 - (card.x + 70)
            if detail_font.size(detail_text)[0] > available_width:
                detail_font = self.pile_font
            detail = detail_font.render(detail_text, True, (72, 101, 91))
            self.screen.blit(detail, (card.x + 70, detail_y))
            detail_y += 15

        serial = self.pile_font.render("BLP-004-ZV", True, (72, 101, 91))
        self.screen.blit(serial, serial.get_rect(center=(portrait.centerx, portrait.bottom + 9)))

        flip_hint = self.card_font.render(next_side, True, COLORS["card_text"])
        self.screen.blit(
            flip_hint,
            flip_hint.get_rect(center=(card.centerx + 31, card.bottom - 9)),
        )


    def draw_id_portrait(self, portrait, medical_side):
        """Draw a miniature version of Zorpa on either side of the ID."""

        portrait_background = (218, 199, 235)
        portrait_border = (91, 59, 125)
        portrait_alien = (126, 75, 174)
        portrait_highlight = (190, 143, 229)
        pygame.draw.rect(self.screen, portrait_background, portrait, border_radius=5)
        pygame.draw.rect(
            self.screen,
            portrait_border,
            portrait,
            width=2,
            border_radius=5,
        )

        head = pygame.Rect(portrait.centerx - 12, portrait.y + 11, 24, 22)
        body = pygame.Rect(portrait.centerx - 10, portrait.y + 31, 20, 23)

        for direction in (-1, 1):
            antenna_start = (head.centerx + direction * 6, head.y + 3)
            antenna_end = (head.centerx + direction * 10, portrait.y + 6)
            pygame.draw.line(
                self.screen,
                portrait_border,
                antenna_start,
                antenna_end,
                width=2,
            )
            pygame.draw.circle(self.screen, portrait_border, antenna_end, 3)
            pygame.draw.circle(self.screen, portrait_alien, antenna_end, 2)

        for start, end in (
            ((body.x + 3, body.y + 5), (body.x - 4, body.bottom - 3)),
            ((body.right - 3, body.y + 5), (body.right + 4, body.bottom - 3)),
            ((body.centerx - 5, body.bottom - 3), (body.centerx - 8, body.bottom + 5)),
            ((body.centerx + 5, body.bottom - 3), (body.centerx + 8, body.bottom + 5)),
        ):
            pygame.draw.line(self.screen, portrait_border, start, end, width=4)
            pygame.draw.line(self.screen, portrait_alien, start, end, width=2)

        pygame.draw.rect(
            self.screen,
            portrait_border,
            body.inflate(2, 2),
            border_radius=8,
        )
        pygame.draw.rect(self.screen, portrait_alien, body, border_radius=7)
        pygame.draw.ellipse(
            self.screen,
            portrait_highlight,
            pygame.Rect(body.centerx - 6, body.y + 7, 12, 12),
        )

        pygame.draw.ellipse(self.screen, portrait_border, head.inflate(2, 2))
        pygame.draw.ellipse(self.screen, portrait_alien, head)
        pygame.draw.ellipse(
            self.screen,
            portrait_highlight,
            pygame.Rect(head.x + 4, head.y + 3, 8, 5),
        )

        left_eye = pygame.Rect(head.x + 5, head.y + 8, 4, 6)
        right_eye = pygame.Rect(head.right - 9, head.y + 8, 4, 6)
        pygame.draw.ellipse(self.screen, COLORS["background"], left_eye)
        pygame.draw.ellipse(self.screen, COLORS["background"], right_eye)
        pygame.draw.circle(self.screen, (250, 250, 255), (left_eye.x + 1, left_eye.y + 1), 1)
        pygame.draw.circle(self.screen, (250, 250, 255), (right_eye.x + 1, right_eye.y + 1), 1)
        pygame.draw.circle(
            self.screen,
            (239, 130, 190),
            (head.x + 4, head.y + 16),
            2,
        )
        pygame.draw.circle(
            self.screen,
            (239, 130, 190),
            (head.right - 4, head.y + 16),
            2,
        )

        badge_color = COLORS["accent"] if medical_side else (255, 198, 75)
        pygame.draw.circle(
            self.screen,
            badge_color,
            (body.centerx + 5, body.y + 6),
            3,
        )
        if medical_side:
            pygame.draw.line(
                self.screen,
                portrait_border,
                (body.centerx + 5, body.y + 4),
                (body.centerx + 5, body.y + 8),
                width=1,
            )
            pygame.draw.line(
                self.screen,
                portrait_border,
                (body.centerx + 3, body.y + 6),
                (body.centerx + 7, body.y + 6),
                width=1,
            )

        mouth_y = head.y + 17
        pygame.draw.line(
            self.screen,
            portrait_border,
            (head.centerx - 3, mouth_y),
            (head.centerx, mouth_y + 2),
            width=1,
        )
        pygame.draw.line(
            self.screen,
            portrait_border,
            (head.centerx, mouth_y + 2),
            (head.centerx + 3, mouth_y),
            width=1,
        )

        for foot_x in (body.centerx - 8, body.centerx + 4):
            pygame.draw.ellipse(
                self.screen,
                portrait_alien,
                pygame.Rect(foot_x, body.bottom + 2, 7, 4),
            )


    def draw_throwaway_deck(self):
        """Draw used and discarded cards inside a medical-waste container."""

        panel = self.layout["throwaway"]
        label = self.card_font.render("MED-WASTE", True, (245, 130, 115))
        label_plate = pygame.Rect(panel.x + 4, panel.y + 3, panel.width - 8, 23)
        pygame.draw.rect(self.screen, (48, 38, 45), label_plate, border_radius=5)
        pygame.draw.rect(
            self.screen,
            (119, 70, 76),
            label_plate,
            width=1,
            border_radius=5,
        )
        self.screen.blit(label, label.get_rect(center=label_plate.center))

        if self.discard_pile:
            last_test = self.discard_pile[-1].value.name
            visible_card = pygame.Rect(panel.centerx - 22, panel.y + 25, 44, 29)
            pygame.draw.rect(
                self.screen,
                COLORS["card"],
                visible_card,
                border_radius=4,
            )
            pygame.draw.rect(
                self.screen,
                COLORS["card_text"],
                visible_card,
                width=2,
                border_radius=4,
            )
            waste_card_font = self.pile_font
            if waste_card_font.size(last_test)[0] > visible_card.width - 4:
                waste_card_font = self.tiny_font
            card_name = waste_card_font.render(
                last_test,
                True,
                COLORS["card_text"],
            )
            self.screen.blit(
                card_name,
                card_name.get_rect(center=(visible_card.centerx, visible_card.y + 10)),
            )

        lid = pygame.Rect(panel.x + 12, panel.y + 40, panel.width - 24, 10)
        pygame.draw.rect(self.screen, (245, 130, 115), lid, border_radius=5)
        pygame.draw.rect(
            self.screen,
            COLORS["background"],
            lid,
            width=2,
            border_radius=5,
        )
        slot = pygame.Rect(lid.centerx - 20, lid.y + 3, 40, 3)
        pygame.draw.rect(self.screen, COLORS["background"], slot, border_radius=2)

        container_points = (
            (panel.x + 18, lid.bottom - 1),
            (panel.right - 18, lid.bottom - 1),
            (panel.right - 23, panel.bottom - 7),
            (panel.x + 23, panel.bottom - 7),
        )
        pygame.draw.polygon(self.screen, (48, 72, 76), container_points)
        pygame.draw.polygon(
            self.screen,
            (245, 130, 115),
            container_points,
            width=2,
        )

        warning_center = (panel.centerx, panel.y + 68)
        warning_triangle = (
            (warning_center[0], warning_center[1] - 10),
            (warning_center[0] - 11, warning_center[1] + 8),
            (warning_center[0] + 11, warning_center[1] + 8),
        )
        pygame.draw.polygon(
            self.screen,
            (245, 130, 115),
            warning_triangle,
            width=2,
        )
        pygame.draw.line(
            self.screen,
            (245, 130, 115),
            (warning_center[0], warning_center[1] - 5),
            (warning_center[0], warning_center[1] + 3),
            width=2,
        )
        pygame.draw.circle(
            self.screen,
            (245, 130, 115),
            (warning_center[0], warning_center[1] + 7),
            1,
        )

        count_text = (
            "CARDS: " + str(len(self.discard_pile))
            if self.discard_pile
            else "EMPTY"
        )
        count = self.pile_font.render(count_text, True, COLORS["text"])
        self.screen.blit(
            count,
            count.get_rect(center=(panel.centerx, panel.bottom - 12)),
        )

