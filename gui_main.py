"""Pygame interface for The Cosmic Clinic vertical-slice prototype.

You can run this file independently from the older text-based version.
"""

import math
import random

import pygame

from gui_animations import AnimationMixin
from gui_cards import CardMixin
from gui_examination import ExaminationMixin
from gui_notebook import NotebookMixin
from gui_reception import ReceptionMixin
from gui_state import GameState
from gui_theme import (
    COLORS,
    FPS,
    TEST_SUBTITLES,
    WINDOW_SIZE,
)
from PatientData import create_zorpa
from Player import DIAGNOSIS_REWARD, Player
from Notebook import Notebook


class AlienDoctorGUI(AnimationMixin, CardMixin, ExaminationMixin, NotebookMixin, ReceptionMixin):

    def __init__(self):
        """Set up Pygame, shared game data, layout rectangles, and fonts."""

        pygame.init()
        pygame.display.set_caption("The Cosmic Clinic - GUI Prototype")

        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.INTRO
        self.intro_started_at = pygame.time.get_ticks()
        self.intro_duration = 5500
        intro_random = random.Random(151)
        self.intro_stars = [
            (
                intro_random.randrange(15, WINDOW_SIZE[0] - 15),
                intro_random.randrange(12, WINDOW_SIZE[1] - 12),
                intro_random.choice((1, 1, 1, 2)),
            )
            for _ in range(70)
        ]
        self.patient = create_zorpa()
        self.player = Player("Dr GUI")
        self.notebook = Notebook()
        self.notebook.add_patient(self.patient)
        self.notebook_columns = []
        self.notebook_spread = 0
        self.notebook_preview_progress = 0.0
        self.notebook_preview_last_tick = pygame.time.get_ticks()
        self.notebook_preview_duration = 220
        self.showing_health_id = False
        self.showing_diagnosis_hand = False
        self.selected_card_index = None
        self.run_test_button = None
        self.discard_button = None
        self.play_diagnosis_button = None
        self.diagnosis_confirmation_open = False
        self.diagnosis_folder_animation_started_at = None
        self.diagnosis_folder_animation_duration = 360
        self.discard_pile = []
        self.discard_animation = None
        self.discard_animation_duration = 350
        self.test_discard_animation_duration = 700
        self.pending_test_discard = None
        self.note_transfer_animation = None
        self.note_transfer_animation_duration = 650
        self.notebook_attention_started_at = None
        self.notebook_attention_duration = 420
        self.last_test_name = ""
        self.last_test_result = ""
        self.test_result_started_at = None
        self.test_result_reveal_duration = 1400
        self.last_diagnosis = None
        self.diagnosis_correct = None
        self.reception_transition_started_at = None
        self.reception_transition_duration = 3350
        self.reception_fade_duration = 650
        self.patient_fade_started_at = None
        self.patient_fade_duration = 650
        self.start_button = pygame.Rect(61, 505, 238, 43)
        self.continue_button = pygame.Rect(700, 472, 220, 44)
        self.outcome_button = pygame.Rect(410, 455, 280, 52)
        self.shop_button = pygame.Rect(400, 465, 300, 52)
        self.diagnosis_cancel_button = pygame.Rect(315, 410, 210, 48)
        self.diagnosis_confirm_button = pygame.Rect(575, 410, 210, 48)
        self.layout = {
            "status_bar": pygame.Rect(30, 100, 1040, 50),
            "draw_deck": pygame.Rect(45, 180, 125, 175),
            "alien": pygame.Rect(233, 165, 230, 195),
            "id_card": pygame.Rect(510, 180, 270, 155),
            "throwaway": pygame.Rect(923, 423, 100, 125),
            "notebook": pygame.Rect(35, 395, 180, 165),
            "active_hand": pygame.Rect(225, 390, 625, 170),
            "diagnosis": pygame.Rect(840, 175, 185, 180),
        }
        self.refresh_hand_layout()
        self.notebook_layout = self.build_notebook_rects()

        self.title_font = pygame.font.Font(None, 64)
        self.heading_font = pygame.font.Font(None, 38)
        self.body_font = pygame.font.Font(None, 26)
        self.small_font = pygame.font.Font(None, 20)
        self.card_font = pygame.font.Font(None, 17)
        self.pile_font = pygame.font.Font(None, 14)
        self.tiny_font = pygame.font.Font(None, 10)
        self.notebook_preview_font = pygame.font.Font(None, 15)
        self.diagnosis_name_font = pygame.font.SysFont("Arial", 21, bold=True)
        self.diagnosis_card_font = pygame.font.SysFont("Arial", 13, bold=True)
        self.notebook_title_font = pygame.font.Font(None, 28)
        self.notebook_body_font = pygame.font.Font(None, 22)
        self.logo_font = pygame.font.SysFont("Arial", 54, bold=True)
        self.logo_small_font = pygame.font.SysFont("Arial", 18, bold=True)
        self.game_logo = self.create_game_logo_surface()

    def run(self):
        """Run the GUI loop until the player closes the window."""

        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

    def handle_events(self):
        """Process window events and controls."""

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == GameState.INTRO:
                    self.finish_intro()
                elif self.state == GameState.TITLE and self.start_button.collidepoint(event.pos):
                    self.begin_reception_transition()
                elif self.state == GameState.PATIENT:
                    self.handle_patient_click(event.pos)
                elif self.state == GameState.TEST_RESULT:
                    self.handle_test_result_click(event.pos)
                elif self.state == GameState.NOTEBOOK:
                    self.handle_notebook_click(event.pos)
                elif self.state == GameState.OUTCOME:
                    self.handle_outcome_click(event.pos)
                elif self.state == GameState.SHOP:
                    self.handle_shop_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.PATIENT and self.diagnosis_confirmation_open:
                        self.diagnosis_confirmation_open = False
                    else:
                        self.running = False
                elif (
                    event.key == pygame.K_RETURN
                    and self.state == GameState.PATIENT
                    and self.diagnosis_confirmation_open
                ):
                    self.confirm_selected_diagnosis()
                elif event.key == pygame.K_RETURN and self.state == GameState.INTRO:
                    self.finish_intro()
                elif event.key == pygame.K_RETURN and self.state == GameState.TITLE:
                    self.begin_reception_transition()
                elif event.key == pygame.K_RETURN and self.state == GameState.TEST_RESULT:
                    self.handle_test_result_click(self.continue_button.center)
                elif event.key == pygame.K_RETURN and self.state == GameState.OUTCOME:
                    self.handle_outcome_click(self.outcome_button.center)
                elif event.key == pygame.K_RETURN and self.state == GameState.SHOP:
                    self.handle_shop_click(self.shop_button.center)
                elif event.key == pygame.K_LEFT and self.state == GameState.NOTEBOOK:
                    self.flip_notebook(-1)
                elif event.key == pygame.K_RIGHT and self.state == GameState.NOTEBOOK:
                    self.flip_notebook(1)

    def handle_patient_click(self, position):
        """Handle ID-card and test-card clicks on the patient screen."""

        note_sequence_active = (
            self.note_transfer_animation is not None
            or (
                self.notebook_attention_started_at is not None
                and self.pending_test_discard is not None
            )
        )
        if (
            note_sequence_active
            or (
                self.discard_animation
                and self.discard_animation.get("locks_input")
            )
        ):
            return
        if self.diagnosis_confirmation_open:
            self.handle_diagnosis_confirmation_click(position)
            return
        if self.layout["id_card"].collidepoint(position):
            self.showing_health_id = not self.showing_health_id
            return
        if self.layout["notebook"].collidepoint(position):
            self.open_notebook()
            return
        if self.layout["diagnosis"].collidepoint(position):
            self.switch_active_hand(not self.showing_diagnosis_hand)
            return

        self.handle_card_click(position)

    def handle_test_result_click(self, position):
        """Return to the workspace and begin logging the result in patient notes."""

        if (
            self.get_test_result_reveal_progress() >= 1.0
            and self.continue_button.collidepoint(position)
        ):
            self.state = GameState.PATIENT
            if self.pending_test_discard is not None:
                self.note_transfer_animation = {
                    "test_name": self.last_test_name,
                    "result": self.last_test_result,
                    "started_at": pygame.time.get_ticks(),
                }

    def handle_outcome_click(self, position):
        """Continue a correct diagnosis to the shop or an incorrect one to the patient."""

        if self.outcome_button.collidepoint(position):
            if self.diagnosis_correct:
                self.state = GameState.SHOP
            else:
                self.switch_active_hand(False)
                self.state = GameState.PATIENT

    def update(self):
        """Advance timed GUI transitions without pausing the event loop."""

        if self.state == GameState.INTRO:
            elapsed = pygame.time.get_ticks() - self.intro_started_at
            if elapsed >= self.intro_duration:
                self.finish_intro()
            return

        now = pygame.time.get_ticks()
        if self.note_transfer_animation is not None:
            elapsed = now - self.note_transfer_animation["started_at"]
            if elapsed >= self.note_transfer_animation_duration:
                self.note_transfer_animation = None
                self.notebook_attention_started_at = now

        if (
            self.notebook_attention_started_at is not None
            and self.pending_test_discard is not None
        ):
            attention_elapsed = now - self.notebook_attention_started_at
            if attention_elapsed >= self.notebook_attention_duration:
                self.notebook_attention_started_at = None
                self.start_pending_test_discard_animation()

        if self.discard_animation is not None:
            elapsed = now - self.discard_animation["started_at"]
            duration = self.discard_animation.get(
                "duration",
                self.discard_animation_duration,
            )
            if elapsed >= duration:
                if self.discard_animation.get("add_to_pile_on_complete"):
                    self.discard_pile.append(self.discard_animation["card"])
                self.discard_animation = None

        if self.state == GameState.TITLE and self.reception_transition_started_at is not None:
            elapsed = pygame.time.get_ticks() - self.reception_transition_started_at
            if elapsed >= self.reception_transition_duration:
                self.reception_transition_started_at = None
                self.patient_fade_started_at = pygame.time.get_ticks()
                self.state = GameState.PATIENT
            return

        if self.state == GameState.PATIENT and self.patient_fade_started_at is not None:
            elapsed = pygame.time.get_ticks() - self.patient_fade_started_at
            if elapsed >= self.patient_fade_duration:
                self.patient_fade_started_at = None

    def handle_shop_click(self, position):
        """Return to the main screen when the player continues from the shop."""

        if self.shop_button.collidepoint(position):
            self.reset_round()
            self.state = GameState.TITLE

    def reset_round(self):
        """Prepare a fresh patient encounter while preserving earned money."""

        current_balance = self.player.balance
        self.patient = create_zorpa()
        self.player = Player(self.player.name)
        self.player.balance = current_balance
        self.notebook = Notebook()
        self.notebook.add_patient(self.patient)
        self.notebook_columns = []
        self.notebook_spread = 0
        self.notebook_preview_progress = 0.0
        self.notebook_preview_last_tick = pygame.time.get_ticks()
        self.showing_health_id = False
        self.showing_diagnosis_hand = False
        self.selected_card_index = None
        self.run_test_button = None
        self.discard_button = None
        self.play_diagnosis_button = None
        self.diagnosis_confirmation_open = False
        self.diagnosis_folder_animation_started_at = None
        self.discard_pile = []
        self.discard_animation = None
        self.pending_test_discard = None
        self.note_transfer_animation = None
        self.notebook_attention_started_at = None
        self.last_test_name = ""
        self.last_test_result = ""
        self.test_result_started_at = None
        self.last_diagnosis = None
        self.diagnosis_correct = None
        self.reception_transition_started_at = None
        self.patient_fade_started_at = None
        self.refresh_hand_layout()

    def draw(self):
        """Draws shell + active screen."""

        if self.state == GameState.INTRO:
            self.draw_intro_screen()
            return

        self.screen.fill(COLORS["background"])
        self.draw_game_logo((WINDOW_SIZE[0] // 2, 38), scale=0.86)

        subtitle_text = (
            "RECEPTION"
            if self.state == GameState.TITLE
            else "INTERGALACTIC MEDICAL SERVICE"
        )
        subtitle = self.small_font.render(subtitle_text, True, COLORS["muted"])
        self.screen.blit(subtitle, subtitle.get_rect(center=(WINDOW_SIZE[0] // 2, 76)))

        if self.state == GameState.TITLE:
            self.draw_title_screen()
        elif self.state == GameState.PATIENT:
            self.draw_patient_screen()
        elif self.state == GameState.TEST_RESULT:
            self.draw_test_result_screen()
        elif self.state == GameState.NOTEBOOK:
            self.draw_patient_screen()
            self.draw_notebook_screen()
        elif self.state == GameState.OUTCOME:
            self.draw_diagnosis_outcome()
        elif self.state == GameState.SHOP:
            self.draw_shop_screen()

        footer_text = (
            "Press Esc to go back"
            if self.diagnosis_confirmation_open
            else "Press Esc to quit"
        )
        quit_hint = self.small_font.render(footer_text, True, COLORS["muted"])
        self.screen.blit(quit_hint, quit_hint.get_rect(center=(WINDOW_SIZE[0] // 2, 635)))
        self.draw_reception_transition_fade()

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
        button_label = "CONTINUE TO SHOP" if correct else "RETURN TO PATIENT"
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
        """Draw the diagnosis reward and updated balance in the outcome footer."""

        coin_center = (footer.x + 31, footer.centery)
        pygame.draw.circle(self.screen, (255, 198, 75), coin_center, 17)
        pygame.draw.circle(self.screen, (255, 230, 150), coin_center, 17, width=2)
        coin = self.small_font.render("$", True, (80, 61, 36))
        self.screen.blit(coin, coin.get_rect(center=coin_center))
        reward_text = (
            f"CASE REWARD  +${DIAGNOSIS_REWARD}" if correct else "NO CASE REWARD"
        )
        reward = self.card_font.render(reward_text, True, status_color)
        balance = self.card_font.render(
            "CURRENT BALANCE  $" + str(self.player.balance),
            True,
            COLORS["muted"],
        )
        self.screen.blit(reward, (footer.x + 58, footer.y + 17))
        self.screen.blit(balance, (footer.x + 58, footer.y + 37))

    def draw_shop_screen(self):
        """Draw the placeholder shop with the current balance and locked shelves."""

        panel = pygame.Rect(100, 115, 900, 435)
        self.draw_panel(panel)

        heading = self.heading_font.render(
            "INTERGALACTIC SUPPLY SHOP",
            True,
            COLORS["text"],
        )
        self.screen.blit(heading, heading.get_rect(center=(panel.centerx, 150)))

        balance_box = pygame.Rect(panel.right - 210, 130, 175, 42)
        pygame.draw.rect(
            self.screen,
            COLORS["background"],
            balance_box,
            border_radius=8,
        )
        pygame.draw.rect(
            self.screen,
            COLORS["panel_border"],
            balance_box,
            width=2,
            border_radius=8,
        )
        balance = self.small_font.render(
            "CURRENT MONEY: $" + str(self.player.balance),
            True,
            COLORS["accent"],
        )
        self.screen.blit(balance, balance.get_rect(center=balance_box.center))

        coming_soon = self.body_font.render(
            "UPGRADES COMING SOON",
            True,
            COLORS["accent"],
        )
        self.screen.blit(coming_soon, coming_soon.get_rect(center=(panel.centerx, 205)))

        shelf_labels = ("TEST MACHINES", "CARD STORAGE", "CLINIC DECOR")
        shelf_x_positions = (170, 445, 720)
        for label, shelf_x in zip(shelf_labels, shelf_x_positions):
            self.draw_shop_shelf(label, pygame.Rect(shelf_x, 240, 210, 150))

        hovered = self.shop_button.collidepoint(pygame.mouse.get_pos())
        button_color = COLORS["accent"] if hovered else COLORS["panel_border"]
        pygame.draw.rect(
            self.screen,
            button_color,
            self.shop_button,
            border_radius=8,
        )
        button_text = self.body_font.render(
            "CONTINUE / NEXT SHIFT",
            True,
            COLORS["background"],
        )
        self.screen.blit(
            button_text,
            button_text.get_rect(center=self.shop_button.center),
        )

    def draw_shop_shelf(self, label, shelf):
        """Draw one locked and currently empty upgrade shelf."""

        pygame.draw.rect(
            self.screen,
            COLORS["background"],
            shelf,
            border_radius=10,
        )
        pygame.draw.rect(
            self.screen,
            COLORS["muted"],
            shelf,
            width=2,
            border_radius=10,
        )

        shelf_label = self.small_font.render(label, True, COLORS["text"])
        self.screen.blit(
            shelf_label,
            shelf_label.get_rect(center=(shelf.centerx, shelf.y + 22)),
        )

        lock_body = pygame.Rect(shelf.centerx - 18, shelf.y + 65, 36, 32)
        pygame.draw.rect(self.screen, COLORS["muted"], lock_body, border_radius=5)
        pygame.draw.arc(
            self.screen,
            COLORS["muted"],
            pygame.Rect(shelf.centerx - 14, shelf.y + 48, 28, 30),
            0,
            3.14159,
            width=5,
        )
        keyhole = pygame.Rect(shelf.centerx - 3, shelf.y + 75, 6, 13)
        pygame.draw.rect(self.screen, COLORS["background"], keyhole, border_radius=3)

        empty = self.card_font.render("SHELF LOCKED", True, COLORS["muted"])
        self.screen.blit(
            empty,
            empty.get_rect(center=(shelf.centerx, shelf.bottom - 22)),
        )

        shelf_board = pygame.Rect(shelf.x - 8, shelf.bottom - 5, shelf.width + 16, 8)
        pygame.draw.rect(self.screen, (72, 101, 91), shelf_board, border_radius=3)

    def draw_centered_label(self, text, panel, y):
        """Draw a text label centered horizontally inside a panel."""

        label = self.small_font.render(text, True, COLORS["text"])
        self.screen.blit(label, label.get_rect(center=(panel.centerx, y)))

    def draw_panel(self, panel):
        """Draw a reusable dark panel with a rounded green border."""

        pygame.draw.rect(self.screen, COLORS["panel"], panel, border_radius=12)
        pygame.draw.rect(
            self.screen,
            COLORS["panel_border"],
            panel,
            width=2,
            border_radius=12,
        )

    def draw_wrapped_text(self, text, font, color, rect, line_spacing=2):
        """Wrap and draw text so it stays within the rectangle."""

        words = text.split()
        lines = []
        line = []

        for word in words:
            candidate = " ".join(line + [word])
            if font.size(candidate)[0] <= rect.width:
                line.append(word)
            else:
                lines.append(" ".join(line))
                line = [word]

        if line:
            lines.append(" ".join(line))

        y = rect.y
        for line_text in lines:
            surface = font.render(line_text, True, color)
            if y + surface.get_height() > rect.bottom:
                break
            self.screen.blit(surface, (rect.x, y))
            y += surface.get_height() + line_spacing

    def wrap_text(self, text, font, width):
        """Return a list of lines that fit within width pixels."""
        lines = []
        for paragraph in text.splitlines() or [""]:
            line = []
            for word in paragraph.split():
                if font.size(" ".join(line + [word]))[0] <= width:
                    line.append(word)
                else:
                    if line:
                        lines.append(" ".join(line))
                    line = [word]
            lines.append(" ".join(line))
        return lines

def main():
    """Create and start the game"""

    AlienDoctorGUI().run()


if __name__ == "__main__":
    main()
