"""Test-result and diagnosis-outcome screens for The Cosmic Clinic."""

import math

import pygame

from gui_theme import COLORS, TEST_SUBTITLES, WINDOW_SIZE
from Player import (
    DIAGNOSIS_REWARD,
    LIMITED_EVIDENCE_REWARD,
    WRONG_DIAGNOSIS_PENALTY,
)


class ResultsMixin:
    def draw_test_result_screen(self):
        """Draw an animated diagnostic terminal over the dimmed examination bay."""

        self.draw_patient_screen()
        dim = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        dim.fill((2, 8, 13, 205))
        self.screen.blit(dim, (0, 0))

        panel = pygame.Rect(105, 105, 890, 455)
        pygame.draw.rect(
            self.screen,
            (2, 8, 13),
            panel.move(8, 9),
            border_radius=16,
        )
        pygame.draw.rect(self.screen, (16, 35, 43), panel, border_radius=16)
        pygame.draw.rect(
            self.screen,
            (103, 135, 126),
            panel,
            width=3,
            border_radius=16,
        )
        pygame.draw.rect(
            self.screen,
            COLORS["accent"],
            panel.inflate(-10, -10),
            width=1,
            border_radius=12,
        )

        test_name = (self.last_test_name or "TEST").upper()
        progress = self.get_test_result_reveal_progress()
        revealed = progress >= 1.0
        status_color = COLORS["accent"]
        machine_color = self.get_test_scan_color(test_name)

        header = pygame.Rect(panel.x + 24, panel.y + 18, panel.width - 48, 68)
        pygame.draw.rect(self.screen, (7, 22, 28), header, border_radius=10)
        pygame.draw.rect(
            self.screen,
            (65, 101, 98),
            header,
            width=1,
            border_radius=10,
        )
        icon = pygame.Rect(header.x + 13, header.y + 10, 48, 48)
        pygame.draw.rect(self.screen, (202, 219, 208), icon, border_radius=7)
        pygame.draw.rect(self.screen, machine_color, icon, width=2, border_radius=7)
        self.draw_test_icon(test_name, icon, machine_color)

        heading_label = (
            test_name
            if test_name.endswith(("SCAN", "SCREEN"))
            else test_name + " SCAN"
        )
        heading = self.heading_font.render(heading_label, True, COLORS["text"])
        self.screen.blit(heading, heading.get_rect(midleft=(icon.right + 15, header.y + 25)))
        patient = self.card_font.render(
            "PATIENT: " + self.patient.name.upper(),
            True,
            COLORS["muted"],
        )
        self.screen.blit(patient, patient.get_rect(midleft=(icon.right + 16, header.y + 49)))

        badge = pygame.Rect(header.right - 128, header.y + 17, 112, 34)
        badge_color = status_color if revealed else (83, 128, 151)
        pygame.draw.rect(self.screen, (11, 28, 34), badge, border_radius=17)
        pygame.draw.rect(self.screen, badge_color, badge, width=2, border_radius=17)
        badge_text = self.card_font.render(
            "COMPLETE" if revealed else "SCANNING",
            True,
            badge_color,
        )
        self.screen.blit(badge_text, badge_text.get_rect(center=badge.center))
        self.draw_modal_balance(header, badge)

        visual = pygame.Rect(panel.x + 24, panel.y + 102, 252, 238)
        report = pygame.Rect(visual.right + 18, visual.y, panel.right - visual.right - 42, 238)
        self.draw_test_scan_visual(visual, test_name, progress)

        pygame.draw.rect(self.screen, (7, 22, 28), report, border_radius=10)
        pygame.draw.rect(
            self.screen,
            (65, 101, 98),
            report,
            width=2,
            border_radius=10,
        )
        report_title = self.card_font.render("DIAGNOSTIC RESULT", True, COLORS["muted"])
        self.screen.blit(report_title, (report.x + 20, report.y + 17))
        pygame.draw.line(
            self.screen,
            (45, 72, 72),
            (report.x + 20, report.y + 42),
            (report.right - 20, report.y + 42),
            width=1,
        )

        if revealed:
            result_heading = "OBSERVED RESULT"
            status = self.body_font.render(result_heading, True, status_color)
            self.screen.blit(status, (report.x + 20, report.y + 58))
            result_text = self.last_test_result or "No result recorded."
            result_box = pygame.Rect(
                report.x + 20,
                report.y + 98,
                report.width - 40,
                78,
            )
            result_y = result_box.y
            for paragraph in result_text.splitlines() or [result_text]:
                for line_text in self.wrap_text(
                    paragraph,
                    self.body_font,
                    result_box.width,
                ):
                    result_line = self.body_font.render(
                        line_text,
                        True,
                        COLORS["text"],
                    )
                    self.screen.blit(result_line, (result_box.x, result_y))
                    result_y += result_line.get_height() + 7

            note_y = report.bottom - 30
            note_icon = (report.x + 26, note_y + 1)
            pygame.draw.circle(self.screen, COLORS["accent"], note_icon, 7)
            pygame.draw.line(
                self.screen,
                COLORS["background"],
                (note_icon[0] - 3, note_icon[1]),
                (note_icon[0] - 1, note_icon[1] + 3),
                width=2,
            )
            pygame.draw.line(
                self.screen,
                COLORS["background"],
                (note_icon[0] - 1, note_icon[1] + 3),
                (note_icon[0] + 4, note_icon[1] - 3),
                width=2,
            )
            notebook_note = self.card_font.render(
                "RESULT READY FOR PATIENT NOTES",
                True,
                COLORS["accent"],
            )
            self.screen.blit(
                notebook_note,
                notebook_note.get_rect(midleft=(note_icon[0] + 13, note_icon[1])),
            )
        else:
            loading = self.body_font.render(
                "ANALYZING PATIENT DATA" + "." * (1 + int(progress * 9) % 3),
                True,
                (117, 190, 255),
            )
            self.screen.blit(loading, loading.get_rect(center=(report.centerx, report.centery - 5)))
            progress_back = pygame.Rect(report.x + 50, report.centery + 28, report.width - 100, 8)
            progress_fill = progress_back.copy()
            progress_fill.width = round(progress_back.width * progress)
            pygame.draw.rect(self.screen, (25, 50, 57), progress_back, border_radius=4)
            pygame.draw.rect(self.screen, (117, 190, 255), progress_fill, border_radius=4)

        footer = pygame.Rect(panel.x + 24, panel.bottom - 91, panel.width - 48, 66)
        pygame.draw.rect(self.screen, (7, 22, 28), footer, border_radius=10)
        pygame.draw.rect(self.screen, (45, 72, 72), footer, width=1, border_radius=10)
        self.draw_med_waste_notice(footer)

        self.continue_button = pygame.Rect(footer.right - 226, footer.y + 11, 208, 44)
        mouse_position = self.get_mouse_position()
        hovered = revealed and self.continue_button.collidepoint(mouse_position)
        button_color = (
            COLORS["accent"]
            if hovered
            else COLORS["panel_border"] if revealed else (52, 76, 78)
        )
        pygame.draw.rect(self.screen, button_color, self.continue_button, border_radius=8)
        pygame.draw.rect(
            self.screen,
            (168, 226, 204) if revealed else (79, 104, 105),
            self.continue_button,
            width=2,
            border_radius=8,
        )
        button_text = self.small_font.render(
            "RETURN TO PATIENT" if revealed else "ANALYZING...",
            True,
            COLORS["background"] if revealed else COLORS["muted"],
        )
        self.screen.blit(button_text, button_text.get_rect(center=self.continue_button.center))


    def get_test_result_reveal_progress(self):
        """Return the zero-to-one progress of the short diagnostic scan animation."""

        if self.test_result_started_at is None:
            return 1.0
        elapsed = pygame.time.get_ticks() - self.test_result_started_at
        return max(0.0, min(1.0, elapsed / self.test_result_reveal_duration))


    def draw_test_scan_visual(self, visual, test_name, progress):
        """Draw the reusable animated machine graphic for the selected test type."""

        pygame.draw.rect(self.screen, (5, 18, 26), visual, border_radius=10)
        pygame.draw.rect(
            self.screen,
            (66, 112, 126),
            visual,
            width=2,
            border_radius=10,
        )
        for grid_x in range(visual.x + 18, visual.right - 10, 28):
            pygame.draw.line(
                self.screen,
                (13, 39, 49),
                (grid_x, visual.y + 12),
                (grid_x, visual.bottom - 12),
            )
        for grid_y in range(visual.y + 18, visual.bottom - 10, 28):
            pygame.draw.line(
                self.screen,
                (13, 39, 49),
                (visual.x + 12, grid_y),
                (visual.right - 12, grid_y),
            )

        scan_color = self.get_test_scan_color(test_name)
        display = pygame.Rect(
            visual.x + 20,
            visual.y + 24,
            visual.width - 40,
            visual.height - 86,
        )
        pygame.draw.rect(self.screen, (8, 27, 36), display, border_radius=10)
        pygame.draw.rect(self.screen, scan_color, display, width=2, border_radius=10)
        self.draw_test_specific_readout(display, test_name, scan_color, progress)

        scan_range = visual.height - 42
        scan_phase = (pygame.time.get_ticks() % 3200) / 3200
        scan_travel = 1 - abs(2 * scan_phase - 1)
        scan_y = visual.y + 20 + round(scan_travel * scan_range)
        scan_glow = pygame.Surface((visual.width - 24, 8), pygame.SRCALPHA)
        scan_glow.fill((*scan_color, 48))
        self.screen.blit(scan_glow, (visual.x + 12, scan_y - 4))
        pygame.draw.line(
            self.screen,
            scan_color,
            (visual.x + 12, scan_y),
            (visual.right - 12, scan_y),
            width=2,
        )

        subtitle = TEST_SUBTITLES.get(test_name, "MEDICAL SCAN")
        machine_label = self.card_font.render(subtitle, True, scan_color)
        self.screen.blit(
            machine_label,
            machine_label.get_rect(center=(visual.centerx, visual.bottom - 30)),
        )
        percentage = self.card_font.render(
            f"SCAN {round(progress * 100):03d}%",
            True,
            COLORS["muted"],
        )
        self.screen.blit(percentage, percentage.get_rect(center=(visual.centerx, visual.bottom - 15)))


    def get_test_scan_color(self, test_name):
        """Return the distinct machine color assigned to one test type."""

        test_colors = {
            "TEMPERATURE": COLORS["accent"],
            "ULTRASOUND": (117, 190, 255),
            "X-RAY": (150, 238, 205),
            "ALLERGY": (219, 118, 239),
            "BLOOD CHEMISTRY": (245, 126, 112),
            "OXYGEN SCAN": (82, 209, 235),
            "TOXIN SCREEN": (202, 226, 91),
            "NEURAL SCAN": (195, 132, 245),
        }
        return test_colors.get(test_name, COLORS["accent"])


    def draw_test_specific_readout(self, display, test_name, scan_color, progress):
        """Draw the selected machine's own diagnostic visualization."""

        if test_name == "TEMPERATURE":
            self.draw_temperature_readout(display, scan_color, progress)
        elif test_name == "ULTRASOUND":
            self.draw_ultrasound_readout(display, scan_color, progress)
        elif test_name == "X-RAY":
            self.draw_xray_readout(display, scan_color, progress)
        elif test_name == "ALLERGY":
            self.draw_allergy_readout(display, scan_color, progress)
        elif test_name == "BLOOD CHEMISTRY":
            self.draw_blood_chemistry_readout(display, scan_color, progress)
        elif test_name == "OXYGEN SCAN":
            self.draw_oxygen_readout(display, scan_color, progress)
        elif test_name == "TOXIN SCREEN":
            self.draw_toxin_readout(display, scan_color, progress)
        elif test_name == "NEURAL SCAN":
            self.draw_neural_readout(display, scan_color, progress)
        else:
            icon = display.inflate(-54, -20)
            self.draw_test_icon(test_name, icon, scan_color)


    def draw_temperature_readout(self, display, scan_color, progress):
        """Draw a core-temperature gauge with the observed digital reading."""

        stem = pygame.Rect(display.x + 37, display.y + 25, 22, 77)
        bulb_center = (stem.centerx, stem.bottom + 8)
        pygame.draw.rect(self.screen, (14, 45, 48), stem, border_radius=11)
        pygame.draw.rect(self.screen, scan_color, stem, width=2, border_radius=11)
        pygame.draw.circle(self.screen, (14, 45, 48), bulb_center, 17)
        pygame.draw.circle(self.screen, scan_color, bulb_center, 17, width=2)

        fill_height = round(57 * max(0.08, progress))
        fill = pygame.Rect(
            stem.centerx - 4,
            stem.bottom - 10 - fill_height,
            8,
            fill_height + 18,
        )
        pygame.draw.rect(self.screen, scan_color, fill, border_radius=4)
        pygame.draw.circle(self.screen, scan_color, bulb_center, 11)
        pygame.draw.circle(
            self.screen,
            (224, 255, 238),
            (bulb_center[0] - 4, bulb_center[1] - 5),
            3,
        )
        for tick_index in range(5):
            tick_y = stem.y + 8 + tick_index * 15
            pygame.draw.line(
                self.screen,
                (104, 151, 149),
                (stem.right + 7, tick_y),
                (stem.right + 17 + (4 if tick_index % 2 == 0 else 0), tick_y),
                width=1,
            )

        reading = "CORE READING"
        if self.last_test_result and ":" in self.last_test_result:
            reading = self.last_test_result.rsplit(":", 1)[-1].strip()
        title = self.compact_ui_font.render("THERMAL CORE", True, COLORS["muted"])
        value = self.heading_font.render(reading, True, scan_color)
        status = self.card_font.render("LIVE PATIENT SAMPLE", True, COLORS["text"])
        self.screen.blit(title, (display.x + 91, display.y + 33))
        self.screen.blit(value, value.get_rect(center=(display.x + 142, display.y + 76)))
        self.screen.blit(status, status.get_rect(center=(display.x + 142, display.y + 111)))


    def draw_ultrasound_readout(self, display, scan_color, progress):
        """Draw a moving echo waveform and stylized sonic pulse source."""

        source_center = (display.x + 31, display.centery)
        pygame.draw.circle(self.screen, (18, 43, 54), source_center, 13)
        pygame.draw.circle(self.screen, scan_color, source_center, 13, width=2)
        pygame.draw.circle(self.screen, (210, 237, 246), source_center, 5)
        for radius in (20, 29, 38):
            pygame.draw.arc(
                self.screen,
                scan_color,
                pygame.Rect(
                    source_center[0] - radius,
                    source_center[1] - radius,
                    radius * 2,
                    radius * 2,
                ),
                -0.72,
                0.72,
                width=2,
            )

        phase = pygame.time.get_ticks() / 210
        wave_left = display.x + 65
        wave_right = display.right - 13
        visible_right = wave_left + round((wave_right - wave_left) * max(0.08, progress))
        wave_points = []
        for wave_x in range(wave_left, visible_right + 1, 3):
            distance = wave_x - wave_left
            amplitude = 24 * max(0.2, 1 - distance / 165)
            wave_y = display.centery + round(math.sin(distance / 8 - phase) * amplitude)
            wave_points.append((wave_x, wave_y))
        if len(wave_points) > 1:
            pygame.draw.lines(self.screen, (50, 89, 112), False, wave_points, width=6)
            pygame.draw.lines(self.screen, scan_color, False, wave_points, width=2)
        pygame.draw.line(
            self.screen,
            (73, 107, 123),
            (wave_left, display.bottom - 25),
            (wave_right, display.bottom - 25),
            width=1,
        )
        label = self.compact_ui_font.render("ECHO RETURN", True, COLORS["text"])
        self.screen.blit(label, label.get_rect(midright=(display.right - 12, display.y + 17)))


    def draw_xray_readout(self, display, scan_color, progress):
        """Draw a compact alien skeletal scan on a luminous X-ray plate."""

        plate = display.inflate(-30, -16)
        pygame.draw.rect(self.screen, (7, 34, 49), plate, border_radius=7)
        pygame.draw.rect(self.screen, (75, 130, 150), plate, width=1, border_radius=7)
        skeleton = pygame.Surface(plate.size, pygame.SRCALPHA)
        alpha = max(70, round(235 * progress))
        bone = (*scan_color, alpha)
        center_x = skeleton.get_width() // 2
        pygame.draw.circle(skeleton, bone, (center_x, 22), 13, width=3)
        pygame.draw.line(skeleton, bone, (center_x, 35), (center_x, 91), width=3)
        for rib_y, rib_width in ((44, 25), (53, 31), (62, 28), (71, 22)):
            pygame.draw.arc(
                skeleton,
                bone,
                pygame.Rect(center_x - rib_width, rib_y - 6, rib_width * 2, 16),
                0,
                math.pi,
                width=2,
            )
        pygame.draw.arc(
            skeleton,
            bone,
            pygame.Rect(center_x - 21, 79, 42, 24),
            0,
            math.pi,
            width=3,
        )
        for direction in (-1, 1):
            shoulder = (center_x + direction * 13, 42)
            elbow = (center_x + direction * 35, 66)
            hand = (center_x + direction * 42, 91)
            pygame.draw.line(skeleton, bone, shoulder, elbow, width=3)
            pygame.draw.line(skeleton, bone, elbow, hand, width=3)
            hip = (center_x + direction * 11, 91)
            knee = (center_x + direction * 20, 111)
            foot = (center_x + direction * 31, 128)
            pygame.draw.line(skeleton, bone, hip, knee, width=3)
            pygame.draw.line(skeleton, bone, knee, foot, width=3)
        self.screen.blit(skeleton, plate.topleft)
        label = self.compact_ui_font.render("STRUCTURAL PLATE", True, COLORS["text"])
        self.screen.blit(label, label.get_rect(center=(display.centerx, display.bottom - 10)))


    def draw_allergy_readout(self, display, scan_color, progress):
        """Draw a four-sample reaction tray with patient-specific activity."""

        reaction_detected = "no reaction" not in (self.last_test_result or "").lower()
        title = self.compact_ui_font.render("REACTION SAMPLE ARRAY", True, COLORS["text"])
        self.screen.blit(title, title.get_rect(center=(display.centerx, display.y + 17)))
        tray = pygame.Rect(display.x + 18, display.y + 41, display.width - 36, 84)
        pygame.draw.rect(self.screen, (20, 37, 48), tray, border_radius=9)
        pygame.draw.rect(self.screen, (93, 83, 119), tray, width=2, border_radius=9)
        for index in range(4):
            well_center = (tray.x + 25 + index * 41, tray.centery)
            active = reaction_detected and index == 2 and progress > 0.55
            well_color = (245, 137, 165) if active else scan_color
            pygame.draw.circle(self.screen, (6, 18, 27), well_center, 14)
            pygame.draw.circle(self.screen, well_color, well_center, 14, width=2)
            pygame.draw.circle(
                self.screen,
                well_color,
                (well_center[0], well_center[1] + 2),
                7 if active else 4,
            )
            pygame.draw.circle(
                self.screen,
                (251, 232, 248),
                (well_center[0] - 2, well_center[1]),
                2,
            )
            sample_label = self.legible_micro_font.render(
                chr(ord("A") + index),
                True,
                COLORS["muted"],
            )
            self.screen.blit(
                sample_label,
                sample_label.get_rect(center=(well_center[0], tray.bottom + 12)),
            )


    def draw_blood_chemistry_readout(self, display, scan_color, progress):
        """Draw an animated fluid vial beside its developing marker panel."""

        title = self.compact_ui_font.render("FLUID CHEMISTRY", True, COLORS["text"])
        self.screen.blit(title, title.get_rect(center=(display.centerx, display.y + 16)))

        vial = pygame.Rect(display.x + 20, display.y + 38, 48, 91)
        pygame.draw.rect(self.screen, (16, 38, 45), vial, border_radius=11)
        pygame.draw.rect(self.screen, (213, 232, 225), vial, width=2, border_radius=11)
        cap = pygame.Rect(vial.x + 8, vial.y - 5, vial.width - 16, 10)
        pygame.draw.rect(self.screen, (83, 105, 105), cap, border_radius=3)
        pygame.draw.rect(self.screen, scan_color, cap, width=2, border_radius=3)

        fluid_height = max(9, round(57 * progress))
        fluid = pygame.Rect(
            vial.x + 5,
            vial.bottom - 6 - fluid_height,
            vial.width - 10,
            fluid_height,
        )
        fluid_surface = pygame.Surface(fluid.size, pygame.SRCALPHA)
        fluid_surface.fill((*scan_color, 185))
        self.screen.blit(fluid_surface, fluid.topleft)
        pygame.draw.line(
            self.screen,
            (255, 208, 189),
            (fluid.x + 2, fluid.y),
            (fluid.right - 2, fluid.y),
            width=2,
        )

        phase = pygame.time.get_ticks() / 280
        particles = ((12, 13), (28, 23), (18, 38), (32, 49), (10, 56))
        for index, (offset_x, offset_y) in enumerate(particles):
            particle_y = fluid.bottom - 6 - (offset_y % max(7, fluid_height - 3))
            particle_y += round(math.sin(phase + index) * 2)
            if fluid.y + 3 <= particle_y <= fluid.bottom - 3:
                pygame.draw.circle(
                    self.screen,
                    (255, 230, 214),
                    (fluid.x + offset_x, particle_y),
                    2,
                )

        bar_x = display.x + 85
        labels = ("VISC", "CELL", "MIN")
        marker_levels = (0.82, 0.58, 0.70)
        for index, (label_text, marker_level) in enumerate(zip(labels, marker_levels)):
            y = display.y + 48 + index * 30
            label = self.legible_micro_font.render(label_text, True, COLORS["muted"])
            self.screen.blit(label, (bar_x, y))
            bar = pygame.Rect(bar_x + 36, y + 2, 79, 8)
            pygame.draw.rect(self.screen, (19, 48, 54), bar, border_radius=4)
            fill = bar.copy()
            fill.width = max(2, round(bar.width * marker_level * progress))
            pygame.draw.rect(self.screen, scan_color, fill, border_radius=4)
            pygame.draw.line(
                self.screen,
                (221, 238, 230),
                (bar.centerx, bar.y - 2),
                (bar.centerx, bar.bottom + 2),
                width=1,
            )

        status = self.compact_ui_font.render("SAMPLE ANALYSIS", True, scan_color)
        self.screen.blit(status, status.get_rect(center=(display.x + 140, display.bottom - 14)))


    def draw_oxygen_readout(self, display, scan_color, progress):
        """Draw breathing organs, rising gas bubbles, and an exchange waveform."""

        title = self.compact_ui_font.render("RESPIRATORY EXCHANGE", True, COLORS["text"])
        self.screen.blit(title, title.get_rect(center=(display.centerx, display.y + 16)))

        phase = pygame.time.get_ticks() / 330
        pulse = 1 + round((math.sin(phase) + 1) * 1.5)
        airway_x = display.x + 58
        pygame.draw.line(
            self.screen,
            (209, 237, 240),
            (airway_x, display.y + 36),
            (airway_x, display.y + 62),
            width=3,
        )
        for direction in (-1, 1):
            lung = pygame.Rect(0, 0, 31 + pulse, 50 + pulse)
            lung.midtop = (
                airway_x + direction * 18,
                display.y + 58,
            )
            lung_surface = pygame.Surface(lung.size, pygame.SRCALPHA)
            pygame.draw.ellipse(lung_surface, (*scan_color, 70 + round(100 * progress)), lung_surface.get_rect())
            pygame.draw.ellipse(lung_surface, scan_color, lung_surface.get_rect(), width=2)
            self.screen.blit(lung_surface, lung.topleft)
            pygame.draw.line(
                self.screen,
                (209, 237, 240),
                (airway_x, display.y + 55),
                (lung.centerx, lung.y + 15),
                width=2,
            )

        bubble_area = pygame.Rect(display.x + 102, display.y + 38, 91, 68)
        for index, (offset_x, speed, radius) in enumerate(((9, 0.9, 3), (31, 1.2, 4), (55, 0.7, 3), (76, 1.0, 2))):
            travel = (pygame.time.get_ticks() / (900 / speed) + index * 0.23) % 1
            bubble_y = bubble_area.bottom - round(travel * bubble_area.height)
            pygame.draw.circle(
                self.screen,
                scan_color,
                (bubble_area.x + offset_x, bubble_y),
                radius,
                width=1,
            )

        wave_points = []
        wave_left = display.x + 103
        wave_right = display.right - 12
        visible_right = wave_left + round((wave_right - wave_left) * max(0.08, progress))
        for wave_x in range(wave_left, visible_right + 1, 3):
            distance = wave_x - wave_left
            wave_y = display.bottom - 25 + round(math.sin(distance / 7 - phase) * 7)
            wave_points.append((wave_x, wave_y))
        if len(wave_points) > 1:
            pygame.draw.lines(self.screen, scan_color, False, wave_points, width=2)
        label = self.legible_micro_font.render("GAS FLOW", True, COLORS["muted"])
        self.screen.blit(label, label.get_rect(center=(display.x + 61, display.bottom - 18)))


    def draw_toxin_readout(self, display, scan_color, progress):
        """Draw a bubbling sample flask and three contaminant channels."""

        title = self.compact_ui_font.render("COMPOUND SCREEN", True, COLORS["text"])
        self.screen.blit(title, title.get_rect(center=(display.centerx, display.y + 16)))

        neck = pygame.Rect(display.x + 29, display.y + 37, 28, 28)
        pygame.draw.rect(self.screen, (16, 39, 43), neck, border_radius=4)
        pygame.draw.rect(self.screen, (218, 235, 220), neck, width=2, border_radius=4)
        flask_points = (
            (neck.x + 3, neck.bottom - 2),
            (neck.right - 3, neck.bottom - 2),
            (display.x + 73, display.y + 119),
            (display.x + 13, display.y + 119),
        )
        pygame.draw.polygon(self.screen, (13, 36, 42), flask_points)
        pygame.draw.polygon(self.screen, (218, 235, 220), flask_points, width=2)
        fluid_points = (
            (display.x + 21, display.y + 94),
            (display.x + 65, display.y + 94),
            (display.x + 72, display.y + 117),
            (display.x + 14, display.y + 117),
        )
        fluid_surface = pygame.Surface(display.size, pygame.SRCALPHA)
        local_fluid = tuple((x - display.x, y - display.y) for x, y in fluid_points)
        pygame.draw.polygon(fluid_surface, (*scan_color, 175), local_fluid)
        self.screen.blit(fluid_surface, display.topleft)

        phase = pygame.time.get_ticks() / 240
        for index, (x, y, radius) in enumerate(((31, 104, 3), (47, 110, 2), (57, 100, 3))):
            bubble_y = display.y + y - round((math.sin(phase + index) + 1) * 3)
            pygame.draw.circle(self.screen, (239, 250, 206), (display.x + x, bubble_y), radius)

        channel_x = display.x + 91
        for index, label_text in enumerate(("A", "B", "C")):
            channel = pygame.Rect(channel_x + index * 36, display.y + 48, 24, 63)
            pygame.draw.rect(self.screen, (17, 43, 47), channel, border_radius=6)
            pygame.draw.rect(self.screen, scan_color, channel, width=2, border_radius=6)
            fill = pygame.Rect(
                channel.x + 5,
                channel.bottom - 5 - round(43 * progress),
                channel.width - 10,
                round(43 * progress),
            )
            if fill.height > 0:
                pygame.draw.rect(self.screen, scan_color, fill, border_radius=3)
            marker = self.legible_micro_font.render(label_text, True, COLORS["text"])
            self.screen.blit(marker, marker.get_rect(center=(channel.centerx, channel.bottom + 12)))

        status = self.compact_ui_font.render("TOXIN FILTER", True, scan_color)
        self.screen.blit(status, status.get_rect(midbottom=(display.right - 12, display.bottom - 5)))


    def draw_neural_readout(self, display, scan_color, progress):
        """Draw a pulsing nervous-system map with a live signal trace."""

        title = self.compact_ui_font.render("NEURAL SIGNAL MAP", True, COLORS["text"])
        self.screen.blit(title, title.get_rect(center=(display.centerx, display.y + 16)))

        nodes = (
            (display.x + 42, display.y + 48),
            (display.x + 86, display.y + 39),
            (display.x + 129, display.y + 53),
            (display.x + 64, display.y + 82),
            (display.x + 111, display.y + 91),
            (display.x + 165, display.y + 75),
        )
        links = ((0, 1), (0, 3), (1, 2), (1, 3), (2, 4), (2, 5), (3, 4), (4, 5))
        revealed_links = max(1, round(len(links) * progress))
        for index, (start, end) in enumerate(links):
            color = scan_color if index < revealed_links else (45, 61, 72)
            pygame.draw.line(self.screen, color, nodes[start], nodes[end], width=2)

        active_node = int(pygame.time.get_ticks() / 190) % len(nodes)
        for index, node in enumerate(nodes):
            active = index == active_node and progress > index / len(nodes)
            pygame.draw.circle(self.screen, (11, 29, 39), node, 8 if active else 6)
            pygame.draw.circle(self.screen, scan_color, node, 8 if active else 6, width=2)
            if active:
                pygame.draw.circle(self.screen, (245, 226, 255), node, 3)

        phase = pygame.time.get_ticks() / 150
        wave_points = []
        wave_left = display.x + 20
        wave_right = display.right - 20
        visible_right = wave_left + round((wave_right - wave_left) * max(0.08, progress))
        for wave_x in range(wave_left, visible_right + 1, 3):
            distance = wave_x - wave_left
            spike = math.sin(distance / 6 - phase) * 4
            if distance % 43 < 7:
                spike -= 8 * math.sin((distance % 43) / 7 * math.pi)
            wave_points.append((wave_x, display.bottom - 18 + round(spike)))
        if len(wave_points) > 1:
            pygame.draw.lines(self.screen, scan_color, False, wave_points, width=2)


    def draw_med_waste_notice(self, footer):
        """Draw the compact used-card notice beside the result-screen button."""

        bin_rect = pygame.Rect(footer.x + 17, footer.y + 13, 31, 39)
        pygame.draw.rect(self.screen, (50, 81, 83), bin_rect, border_radius=4)
        pygame.draw.rect(self.screen, (245, 126, 112), bin_rect, width=2, border_radius=4)
        pygame.draw.line(
            self.screen,
            (245, 126, 112),
            (bin_rect.x - 3, bin_rect.y + 3),
            (bin_rect.right + 3, bin_rect.y + 3),
            width=3,
        )
        warning = self.card_font.render("!", True, (245, 126, 112))
        self.screen.blit(warning, warning.get_rect(center=bin_rect.center))
        waste_title = self.card_font.render("CARD READY FOR MED-WASTE", True, COLORS["text"])
        waste_detail = self.card_font.render(
            f"TEST COST ${self.last_test_cost} DEDUCTED  •  INCLUDED IN SHIFT RECAP",
            True,
            COLORS["muted"],
        )
        self.screen.blit(waste_title, (bin_rect.right + 12, footer.y + 18))
        self.screen.blit(waste_detail, (bin_rect.right + 12, footer.y + 38))


    def draw_diagnosis_outcome(self):
        """Draw a clinic case report for the submitted diagnosis."""

        self.draw_patient_screen()
        dim = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        dim.fill((2, 8, 13, 205))
        self.screen.blit(dim, (0, 0))

        correct = bool(self.diagnosis_correct)
        left = bool(self.patient_left)
        supported = correct and self.last_diagnosis_supported
        status_color = (
            COLORS["accent"]
            if supported
            else (232, 168, 92)
            if correct
            else (245, 130, 115)
        )
        diagnosis_name = self.last_diagnosis.name if self.last_diagnosis else "Unknown"
        panel = pygame.Rect(105, 105, 890, 455)
        pygame.draw.rect(self.screen, (2, 8, 13), panel.move(8, 9), border_radius=16)
        pygame.draw.rect(self.screen, (16, 35, 43), panel, border_radius=16)
        pygame.draw.rect(self.screen, (103, 135, 126), panel, width=3, border_radius=16)
        pygame.draw.rect(
            self.screen,
            status_color,
            panel.inflate(-10, -10),
            width=1,
            border_radius=12,
        )

        header = pygame.Rect(panel.x + 24, panel.y + 18, panel.width - 48, 68)
        pygame.draw.rect(self.screen, (7, 22, 28), header, border_radius=10)
        pygame.draw.rect(self.screen, (65, 101, 98), header, width=1, border_radius=10)
        seal = pygame.Rect(header.x + 13, header.y + 10, 48, 48)
        pygame.draw.rect(self.screen, (12, 34, 38), seal, border_radius=8)
        pygame.draw.rect(self.screen, status_color, seal, width=2, border_radius=8)
        self.draw_outcome_seal(seal, correct, status_color)

        heading_text = (
            "SUPPORTED DIAGNOSIS"
            if supported
            else "DIAGNOSIS CORRECT"
            if correct
            else "PATIENT LEFT"
            if left
            else "CASE REQUIRES REVIEW"
        )
        heading = self.heading_font.render(heading_text, True, COLORS["text"])
        self.screen.blit(heading, heading.get_rect(midleft=(seal.right + 15, header.y + 25)))
        patient = self.card_font.render(
            "PATIENT: " + self.patient.name.upper(),
            True,
            COLORS["muted"],
        )
        self.screen.blit(patient, patient.get_rect(midleft=(seal.right + 16, header.y + 49)))

        badge = pygame.Rect(header.right - 142, header.y + 17, 126, 34)
        pygame.draw.rect(self.screen, (11, 28, 34), badge, border_radius=17)
        pygame.draw.rect(self.screen, status_color, badge, width=2, border_radius=17)
        badge_text = self.card_font.render(
            "FULL EVIDENCE"
            if supported
            else "LIMITED EVIDENCE"
            if correct
            else "PATIENT LEFT"
            if left
            else "NOT CONFIRMED",
            True,
            status_color,
        )
        self.screen.blit(badge_text, badge_text.get_rect(center=badge.center))
        self.draw_modal_balance(header, badge)

        patient_panel = pygame.Rect(panel.x + 24, panel.y + 102, 252, 238)
        report = pygame.Rect(
            patient_panel.right + 18,
            patient_panel.y,
            panel.right - patient_panel.right - 42,
            238,
        )
        self.draw_outcome_patient_panel(patient_panel, correct, status_color)

        pygame.draw.rect(self.screen, (7, 22, 28), report, border_radius=10)
        pygame.draw.rect(self.screen, (65, 101, 98), report, width=2, border_radius=10)
        report_title = self.card_font.render("FINAL DIAGNOSIS", True, COLORS["muted"])
        self.screen.blit(report_title, (report.x + 20, report.y + 16))
        diagnosis = self.heading_font.render(diagnosis_name, True, status_color)
        self.screen.blit(diagnosis, (report.x + 20, report.y + 38))
        pygame.draw.line(
            self.screen,
            (45, 72, 72),
            (report.x + 20, report.y + 76),
            (report.right - 20, report.y + 76),
        )

        detail_label = self.card_font.render(
            "TREATMENT PLAN" if correct else "WHAT NOW" if left else "NEXT STEP",
            True,
            COLORS["muted"],
        )
        self.screen.blit(detail_label, (report.x + 20, report.y + 91))
        if correct:
            detail_text = self.last_diagnosis.treatment
        elif left:
            detail_text = (
                self.patient_leave_text
                + " The case is closed and cannot be recovered."
            )
        else:
            detail_text = (
                f"{diagnosis_name} does not match the available evidence. "
                "Return to the examination and collect more information."
            )
        detail_box = pygame.Rect(report.x + 20, report.y + 117, report.width - 40, 88)
        self.draw_wrapped_text(
            detail_text,
            self.body_font,
            COLORS["text"],
            detail_box,
            line_spacing=6,
        )
        filing_note = self.card_font.render(
            "CASE FILE UPDATED: FULL SUPPORT" if supported
            else "CASE FILE UPDATED: LIMITED SUPPORT" if correct
            else "CASE CLOSED: UNSUCCESSFUL" if left
            else "REJECTED CARD MARKED FOR MED-WASTE",
            True, status_color
        )
        self.screen.blit(filing_note, (report.x + 20, report.bottom - 27))

        footer = pygame.Rect(panel.x + 24, panel.bottom - 91, panel.width - 48, 66)
        pygame.draw.rect(self.screen, (7, 22, 28), footer, border_radius=10)
        pygame.draw.rect(self.screen, (45, 72, 72), footer, width=1, border_radius=10)
        self.draw_outcome_reward(footer, correct, status_color)

        self.outcome_button = pygame.Rect(footer.right - 226, footer.y + 11, 208, 44)
        hovered = self.outcome_button.collidepoint(self.get_mouse_position())
        button_color = status_color if hovered else (
            COLORS["panel_border"] if correct else (195, 95, 88)
        )
        pygame.draw.rect(self.screen, button_color, self.outcome_button, border_radius=8)
        pygame.draw.rect(
            self.screen,
            (177, 229, 207) if correct else (255, 174, 158),
            self.outcome_button,
            width=2,
            border_radius=8,
        )
        if correct or left:
            button_label = (
                "VIEW SHIFT RECAP"
                if self.patients_waiting() == 0
                else "NEXT PATIENT"
            )
        else:
            button_label = "DISCARD & RETURN"
        button_text = self.small_font.render(button_label, True, COLORS["background"])
        self.screen.blit(button_text, button_text.get_rect(center=self.outcome_button.center))


    def draw_outcome_seal(self, seal, correct, status_color):
        """Draw the confirmed or rejected symbol in the outcome header."""

        if correct:
            pygame.draw.line(
                self.screen,
                status_color,
                (seal.x + 12, seal.centery),
                (seal.x + 21, seal.bottom - 13),
                width=5,
            )
            pygame.draw.line(
                self.screen,
                status_color,
                (seal.x + 21, seal.bottom - 13),
                (seal.right - 10, seal.y + 12),
                width=5,
            )
        else:
            pygame.draw.line(
                self.screen,
                status_color,
                (seal.x + 13, seal.y + 13),
                (seal.right - 13, seal.bottom - 13),
                width=5,
            )
            pygame.draw.line(
                self.screen,
                status_color,
                (seal.right - 13, seal.y + 13),
                (seal.x + 13, seal.bottom - 13),
                width=5,
            )


    def draw_outcome_patient_panel(self, panel, correct, status_color):
        """Draw Zorpa reacting to the diagnosis inside a compact recovery bay."""

        pygame.draw.rect(self.screen, (5, 18, 26), panel, border_radius=10)
        pygame.draw.rect(self.screen, (66, 112, 126), panel, width=2, border_radius=10)
        glow = pygame.Surface(panel.size, pygame.SRCALPHA)
        pygame.draw.ellipse(
            glow,
            (*status_color, 32),
            pygame.Rect(28, 34, panel.width - 56, panel.height - 45),
        )
        self.screen.blit(glow, panel.topleft)

        title = self.card_font.render(
            "PATIENT STABLE" if correct else "PATIENT LEFT" if self.patient_left else "MORE TESTS NEEDED",
            True,
            status_color,
        )
        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 21)))
        platform = pygame.Rect(panel.centerx - 63, panel.bottom - 34, 126, 18)
        pygame.draw.ellipse(self.screen, (45, 80, 74), platform)
        pygame.draw.arc(self.screen, status_color, platform, 0, math.pi, width=2)
        if self.patient_left:
            empty = self.card_font.render("BAY EMPTY", True, COLORS["muted"])
            self.screen.blit(empty, empty.get_rect(center=panel.center))
            name = self.card_font.render(self.patient.name.upper(), True, COLORS["muted"])
            self.screen.blit(name, name.get_rect(center=(panel.centerx, panel.bottom - 11)))
            return
        entry = self.get_current_entry()
        if entry["exam"] is not None:
            self.draw_outcome_exam_sprite(panel, platform, entry, correct, status_color)
            name = self.card_font.render(self.patient.name.upper(), True, COLORS["muted"])
            self.screen.blit(name, name.get_rect(center=(panel.centerx, panel.bottom - 11)))
            return
        alien_color = (151, 99, 211)
        alien_outline = (62, 36, 91)
        body = pygame.Rect(panel.centerx - 24, panel.y + 126, 48, 64)
        head = pygame.Rect(panel.centerx - 35, panel.y + 67, 70, 64)
        for side in (-1, 1):
            tip = (head.centerx + side * 27, head.y - 9)
            pygame.draw.line(
                self.screen,
                alien_outline,
                (head.centerx + side * 17, head.y + 7),
                tip,
                width=5,
            )
            pygame.draw.line(
                self.screen,
                alien_color,
                (head.centerx + side * 17, head.y + 7),
                tip,
                width=2,
            )
            pygame.draw.circle(self.screen, alien_outline, tip, 7)
            pygame.draw.circle(self.screen, alien_color, tip, 5)

        for side in (-1, 1):
            arm_start = (
                body.centerx + side * 19,
                body.y + 20,
            )
            arm_end = (
                body.centerx + side * 38,
                body.y + 43,
            )
            pygame.draw.line(
                self.screen,
                alien_outline,
                arm_start,
                arm_end,
                width=11,
            )
            pygame.draw.line(
                self.screen,
                alien_color,
                arm_start,
                arm_end,
                width=7,
            )
            pygame.draw.circle(self.screen, alien_outline, arm_end, 6)
            pygame.draw.circle(self.screen, alien_color, arm_end, 4)

        for side in (-1, 1):
            leg_start = (
                body.centerx + side * 10,
                body.bottom - 7,
            )
            leg_end = (
                platform.centerx + side * 22,
                platform.y + 5,
            )
            pygame.draw.line(
                self.screen,
                alien_outline,
                leg_start,
                leg_end,
                width=12,
            )
            pygame.draw.line(
                self.screen,
                alien_color,
                leg_start,
                leg_end,
                width=8,
            )
            foot = pygame.Rect(0, 0, 24, 10)
            foot.center = (leg_end[0] + side * 4, platform.y + 5)
            pygame.draw.ellipse(self.screen, alien_outline, foot.inflate(4, 3))
            pygame.draw.ellipse(self.screen, alien_color, foot)

        pygame.draw.ellipse(self.screen, alien_outline, body.inflate(5, 5))
        pygame.draw.ellipse(self.screen, alien_color, body)
        pygame.draw.ellipse(
            self.screen,
            (181, 129, 224),
            pygame.Rect(body.x + 10, body.y + 20, 28, 31),
        )
        pygame.draw.ellipse(self.screen, alien_outline, head.inflate(5, 5))
        pygame.draw.ellipse(self.screen, alien_color, head)
        for eye_x in (head.centerx - 14, head.centerx + 14):
            pygame.draw.ellipse(
                self.screen,
                alien_outline,
                pygame.Rect(eye_x - 5, head.y + 23, 10, 15),
            )
            pygame.draw.circle(self.screen, (245, 245, 255), (eye_x - 1, head.y + 27), 2)

        mouth_y = head.y + 47
        if correct:
            pygame.draw.arc(
                self.screen,
                alien_outline,
                pygame.Rect(head.centerx - 11, mouth_y - 7, 22, 14),
                math.pi,
                math.pi * 2,
                width=2,
            )
            for sparkle_x, sparkle_y in (
                (panel.x + 42, panel.y + 64),
                (panel.right - 40, panel.y + 92),
                (panel.right - 58, panel.y + 49),
            ):
                pygame.draw.line(
                    self.screen,
                    status_color,
                    (sparkle_x - 5, sparkle_y),
                    (sparkle_x + 5, sparkle_y),
                    width=2,
                )
                pygame.draw.line(
                    self.screen,
                    status_color,
                    (sparkle_x, sparkle_y - 5),
                    (sparkle_x, sparkle_y + 5),
                    width=2,
                )
        else:
            pygame.draw.arc(
                self.screen,
                alien_outline,
                pygame.Rect(head.centerx - 10, mouth_y, 20, 12),
                0,
                math.pi,
                width=2,
            )

        name = self.card_font.render(self.patient.name.upper(), True, COLORS["muted"])
        self.screen.blit(name, name.get_rect(center=(panel.centerx, panel.bottom - 11)))


    def draw_outcome_reward(self, footer, correct, status_color):
        """Draw pending case pay or the fee added to the end-of-day calculation."""

        coin_center = (footer.x + 31, footer.centery)
        pygame.draw.circle(self.screen, (255, 198, 75), coin_center, 17)
        pygame.draw.circle(self.screen, (255, 230, 150), coin_center, 17, width=2)
        coin = self.small_font.render("$", True, (80, 61, 36))
        self.screen.blit(coin, coin.get_rect(center=coin_center))
        case_reward = (
            DIAGNOSIS_REWARD
            if self.last_diagnosis_supported
            else LIMITED_EVIDENCE_REWARD
        )
        reward_text = (
            f"PENDING CASE PAY  +${case_reward}"
            if correct
            else f"DIAGNOSIS FEE  -${WRONG_DIAGNOSIS_PENALTY}"
        )
        reward = self.card_font.render(reward_text, True, status_color)
        payment_note = self.card_font.render(
            (
                "FULL EVIDENCE RATE  •  PAID AT SHIFT END"
                if correct and self.last_diagnosis_supported
                else "LIMITED EVIDENCE RATE  •  PAID AT SHIFT END"
                if correct
                else "DEDUCTED FROM LIVE BALANCE"
            ),
            True,
            COLORS["muted"],
        )
        self.screen.blit(reward, (footer.x + 58, footer.y + 17))
        self.screen.blit(payment_note, (footer.x + 58, footer.y + 37))

    def draw_outcome_exam_sprite(self, panel, platform, entry, correct, status_color):
        """Draw the current patient's exam sprite, scaled up, standing on the recovery platform."""

        scale = 1.5
        layer_size = (166, 133)  # same height as the exam bay's inner area
        layer = pygame.Surface(layer_size, pygame.SRCALPHA)
        bay = layer.get_rect()
        layer_platform = pygame.Rect(bay.centerx - 67, bay.bottom - 20, 134, 17)
        blinking = pygame.time.get_ticks() % 3600 >= 3480

        real_screen = self.screen
        self.screen = layer
        try:
            head = entry["exam"](bay, bay.centerx, layer_platform, 0, 0, blinking)
        finally:
            self.screen = real_screen

        scaled_size = (round(layer_size[0] * scale), round(layer_size[1] * scale))
        scaled = pygame.transform.smoothscale(layer, scaled_size)
        # Line the sprite's platform up with the panel's platform
        position = (
            panel.centerx - scaled_size[0] // 2,
            platform.y - round(layer_platform.y * scale),
        )
        self.screen.blit(scaled, position)

        if correct:
            for sparkle_x, sparkle_y in (
                    (panel.x + 42, panel.y + 64),
                    (panel.right - 40, panel.y + 92),
                    (panel.right - 58, panel.y + 49),
            ):
                pygame.draw.line(self.screen, status_color,
                                 (sparkle_x - 5, sparkle_y), (sparkle_x + 5, sparkle_y), 2)
                pygame.draw.line(self.screen, status_color,
                                 (sparkle_x, sparkle_y - 5), (sparkle_x, sparkle_y + 5), 2)
        else:
            # A small sweat drop beside the head for "not quite right"
            drop_x = position[0] + round(head.right * scale) + 6
            drop_y = position[1] + round(head.y * scale) + 12
            pygame.draw.polygon(self.screen, (117, 190, 255),
                                ((drop_x, drop_y - 8), (drop_x - 5, drop_y + 1), (drop_x + 5, drop_y + 1)))
            pygame.draw.circle(self.screen, (117, 190, 255), (drop_x, drop_y + 3), 5)

