"""Test-result and diagnosis-outcome screens for The Cosmic Clinic."""

import math

import pygame

from gui_theme import COLORS, TEST_SUBTITLES, WINDOW_SIZE
from Player import DIAGNOSIS_REWARD, WRONG_DIAGNOSIS_PENALTY


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
        pygame.draw.rect(self.screen, COLORS["accent"], icon, width=2, border_radius=7)
        self.draw_test_icon(test_name, icon, COLORS["accent"])

        heading = self.heading_font.render(test_name + " SCAN", True, COLORS["text"])
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
        mouse_position = pygame.mouse.get_pos()
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

        test_colors = {
            "TEMPERATURE": COLORS["accent"],
            "ULTRASOUND": (117, 190, 255),
            "X-RAY": (150, 238, 205),
            "ALLERGY": (219, 118, 239),
        }
        scan_color = test_colors.get(test_name, COLORS["accent"])
        icon = pygame.Rect(visual.centerx - 58, visual.y + 45, 116, 116)
        pygame.draw.rect(self.screen, (201, 218, 208), icon, border_radius=12)
        pygame.draw.rect(self.screen, scan_color, icon, width=3, border_radius=12)
        self.draw_test_icon(test_name, icon, scan_color)

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
            "CONTINUE TO DISPOSE OF THE USED TEST CARD",
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
        status_color = COLORS["accent"] if correct else (245, 130, 115)
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

        heading_text = "CASE RESOLVED" if correct else "CASE REQUIRES REVIEW"
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
            "CONFIRMED" if correct else "NOT CONFIRMED",
            True,
            status_color,
        )
        self.screen.blit(badge_text, badge_text.get_rect(center=badge.center))

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
            "TREATMENT PLAN" if correct else "NEXT STEP",
            True,
            COLORS["muted"],
        )
        self.screen.blit(detail_label, (report.x + 20, report.y + 91))
        if correct:
            detail_text = self.last_diagnosis.treatment
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
            "CASE FILE UPDATED" if correct else "CASE FILE REMAINS OPEN",
            True,
            status_color,
        )
        self.screen.blit(filing_note, (report.x + 20, report.bottom - 27))

        footer = pygame.Rect(panel.x + 24, panel.bottom - 91, panel.width - 48, 66)
        pygame.draw.rect(self.screen, (7, 22, 28), footer, border_radius=10)
        pygame.draw.rect(self.screen, (45, 72, 72), footer, width=1, border_radius=10)
        self.draw_outcome_reward(footer, correct, status_color)

        self.outcome_button = pygame.Rect(footer.right - 226, footer.y + 11, 208, 44)
        hovered = self.outcome_button.collidepoint(pygame.mouse.get_pos())
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
        if correct:
            button_label = (
                "VIEW SHIFT RECAP"
                if self.patients_waiting() == 0
                else "NEXT PATIENT"
            )
        else:
            button_label = "RETURN TO PATIENT"
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
            "PATIENT STABLE" if correct else "MORE TESTS NEEDED",
            True,
            status_color,
        )
        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 21)))
        platform = pygame.Rect(panel.centerx - 63, panel.bottom - 34, 126, 18)
        pygame.draw.ellipse(self.screen, (45, 80, 74), platform)
        pygame.draw.arc(self.screen, status_color, platform, 0, math.pi, width=2)
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
        reward_text = (
            f"PENDING CASE PAY  +${DIAGNOSIS_REWARD}"
            if correct
            else f"DIAGNOSIS FEE  -${WRONG_DIAGNOSIS_PENALTY}"
        )
        reward = self.card_font.render(reward_text, True, status_color)
        payment_note = self.card_font.render(
            "PAID AT END OF DAY" if correct else "DEDUCTED FROM SHIFT PAY",
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

