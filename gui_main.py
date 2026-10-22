"""Pygame interface for The Cosmic Clinic vertical-slice prototype.

You can run this file independently from the older text-based version.
"""

import math
import random

import pygame

from gui_animations import AnimationMixin
from gui_cards import CardMixin
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


class AlienDoctorGUI(AnimationMixin, CardMixin, NotebookMixin, ReceptionMixin):

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
