"""Pygame interface for The Cosmic Clinic vertical-slice prototype.

You can run this file independently from the older text-based version.
"""

import random

import pygame

from Tests.AllergyTest import AllergyTest
from Tests.TemperatureTest import TemperatureTest
from Tests.UltrasoundTest import UltrasoundTest
from Tests.XrayTest import XrayTest
from gui_animations import AnimationMixin
from gui_cards import CardMixin
from gui_examination import ExaminationMixin
from gui_notebook import NotebookMixin
from gui_reception import ReceptionMixin
from gui_results import ResultsMixin
from gui_shop import ShopMixin
from gui_state import GameState
from gui_theme import (
    COLORS,
    FPS,
    WINDOW_SIZE,
)
from PatientData import create_zorpa, create_zoogy, create_titus, create_conmann
from Player import Player
from Notebook import Notebook
from Deck import Deck


class AlienDoctorGUI(
    AnimationMixin,
    CardMixin,
    ExaminationMixin,
    NotebookMixin,
    ReceptionMixin,
    ResultsMixin,
    ShopMixin,
):

    def __init__(self):
        """Set up Pygame, shared game data, layout rectangles, and fonts."""

        pygame.init()
        pygame.display.set_caption("The Cosmic Clinic - GUI Prototype")

        self.start_music()
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

        self.waiting_room_queue = [
            {
                "chair_x": 782, "draw": self.draw_waiting_zorpa, "create": create_zorpa,
                "exam": None,
                "symptom": ("I CAN'T STOP", "SHAKING!"),
                "serial": "BLP-004-ZV",
                "portrait": ((218, 199, 235), (91, 59, 125), (126, 75, 174), (190, 143, 229)),
            },
            {
                "chair_x": 640, "draw": self.draw_waiting_zoogy, "create": create_zoogy,
                "exam": self.draw_exam_zoogy,
                "symptom": ("I FEEL...", "STRAINED?"),
                "serial": "GRN-017-ZG",
                "portrait": ((205, 228, 208), (49, 111, 82), (84, 151, 108), (151, 211, 155)),
            },
            {
                "chair_x": 498, "draw": self.draw_waiting_titus, "create": create_titus,
                "exam": self.draw_exam_titus,
                "symptom": ("I'M SO", "DISTRESSED!"),
                "serial": "BLU-203-TT",
                "portrait": ((200, 222, 236), (38, 83, 119), (64, 125, 166), (118, 190, 220)),
            },
            {
                "chair_x": 356, "draw": self.draw_waiting_conmann, "create": create_conmann,
                "exam": self.draw_exam_conmann,
                "symptom": ("MY TUMMY", "HURTS :("),
                "serial": "ORG-088-CM",
                "portrait": ((240, 212, 196), (159, 70, 66), (226, 127, 91), (249, 170, 119)),
            },
        ]
        self.patients_called = 0
        self.patient = self.waiting_room_queue[0]["create"]()
        self.player = Player("Dr GUI")
        self.notebook = Notebook()
        self.notebook.add_patient(self.patient)
        self.notebook_columns = []
        self.notebook_spread = 0
        self.notebook_preview_progress = 0.0
        self.notebook_preview_last_tick = pygame.time.get_ticks()
        self.notebook_preview_duration = 220
        self.deck = Deck()
        self.deck.populate([AllergyTest(), TemperatureTest(), UltrasoundTest(), XrayTest()])
        self.hovered_card_index = None
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
            "draw_deck": pygame.Rect(45, 180, 150, 175),
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
        if self.layout["draw_deck"].collidepoint(position):
            self.draw_card_from_pile()
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
                self.patients_called += 1
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
        next_slot = min(self.patients_called, len(self.waiting_room_queue) - 1)
        self.patient = self.waiting_room_queue[next_slot]["create"]()
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

    def start_music(self):
        """Start the looping background music."""

        try:
            pygame.mixer.music.load("assets/hyperdrive_boogie_bg_music.ogg")
            pygame.mixer.music.set_volume(0.4)
            pygame.mixer.music.play(loops=-1)
        except pygame.error as error:
            print(f"Could not begin background music: {error}")

def main():
    """Create and start the game."""

    AlienDoctorGUI().run()


if __name__ == "__main__":
    main()
