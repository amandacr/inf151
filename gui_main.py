"""Pygame interface for The Cosmic Clinic vertical-slice prototype.

You can run this file independently from the older text-based version.
"""

from enum import Enum, auto
import math
import random

import pygame

from PatientData import create_zorpa
from Player import DIAGNOSIS_REWARD, Player
from Notebook import Notebook


WINDOW_SIZE = (1100, 650)
FPS = 60

COLORS = {
    "background": (10, 18, 23),
    "panel": (18, 34, 40),
    "card": (225, 235, 210),
    "card_text": (22, 38, 35),
    "panel_border": (63, 219, 144),
    "accent": (112, 255, 181),
    "text": (226, 244, 235),
    "muted": (139, 169, 158),
}

RARITY_COLORS = {
    "Common": (64, 190, 125),
    "Uncommon": (85, 145, 230),
    "Rare": (205, 100, 235),
}

RARITY_CARD_COLORS = {
    "Common": (225, 235, 214),
    "Uncommon": (218, 230, 239),
    "Rare": (235, 220, 239),
}

TEST_SUBTITLES = {
    "TEMPERATURE": "VITAL SCAN",
    "ULTRASOUND": "SONIC IMAGING",
    "X-RAY": "BONE IMAGING",
    "ALLERGY": "REACTION SCAN",
}


class GameState(Enum):
    """Screens used by the GUI version of the prototype."""

    INTRO = auto()
    TITLE = auto()
    PATIENT = auto()
    TEST_RESULT = auto()
    OUTCOME = auto()
    NOTEBOOK = auto()
    SHOP = auto()


class AlienDoctorGUI:

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
            "throwaway": pygame.Rect(910, 410, 125, 145),
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

        if self.discard_animation and self.discard_animation.get("locks_input"):
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

    def get_active_hand(self):
        """Return whichever card hand is currently displayed in the center panel."""

        if self.showing_diagnosis_hand:
            return self.player.diagnosis_hand
        return self.player.test_hand

    def switch_active_hand(self, show_diagnoses):
        """Switch between test and diagnosis cards and clear the previous selection."""

        self.showing_diagnosis_hand = show_diagnoses
        self.selected_card_index = None
        self.run_test_button = None
        self.discard_button = None
        self.play_diagnosis_button = None
        self.diagnosis_confirmation_open = False
        self.diagnosis_folder_animation_started_at = (
            pygame.time.get_ticks() if show_diagnoses else None
        )
        self.refresh_hand_layout()

    def calculate_hand_layout(self, card_count):
        """Calculate a centered fan for any number of cards without changing game data."""

        panel = self.layout["active_hand"]
        card_width = 96
        card_height = 118

        if card_count == 0:
            return []

        usable_width = panel.width - 28
        if card_count == 1:
            card_step = 0
            total_width = card_width
        else:
            available_step = (usable_width - card_width) / (card_count - 1)
            card_step = min(card_width - 4, available_step)
            total_width = card_width + card_step * (card_count - 1)
        start_x = panel.centerx - total_width // 2
        hand_center = (card_count - 1) / 2

        return [
            pygame.Rect(
                round(start_x + index * card_step),
                panel.y + 43 + min(9, round(abs(index - hand_center) * 3)),
                card_width,
                card_height,
            )
            for index in range(card_count)
        ]

    def refresh_hand_layout(self):
        """Recalculate positions after player.draw, play, discard, or a hand switch."""

        self.card_rects = self.calculate_hand_layout(len(self.get_active_hand()))
        if (
            self.selected_card_index is not None
            and self.selected_card_index >= len(self.card_rects)
        ):
            self.selected_card_index = None

    def build_card_rects(self):
        """Return the current hand layout for compatibility with earlier GUI code."""

        return self.calculate_hand_layout(len(self.get_active_hand()))

    def handle_card_click(self, position):
        """Select or dismiss a card and run it when it belongs to the test hand."""

        if self.selected_card_index is not None:
            selected_rect = self.get_selected_card_rect(self.selected_card_index)
            if self.showing_diagnosis_hand:
                action_button = self.get_card_action_button(selected_rect)
                if action_button.collidepoint(position):
                    self.open_diagnosis_confirmation()
                    return
            else:
                if self.get_run_test_button(selected_rect).collidepoint(position):
                    self.run_selected_test()
                    return
                if self.get_discard_button(selected_rect).collidepoint(position):
                    self.discard_selected_test()
                    return

            if selected_rect.collidepoint(position):
                self.selected_card_index = None
                return

        for index in reversed(range(len(self.card_rects))):
            if self.card_rects[index].collidepoint(position):
                self.selected_card_index = index
                return

        if self.selected_card_index is not None:
            self.selected_card_index = None

    def run_selected_test(self):
        """Play the selected test card and open its patient-specific result screen."""

        if self.selected_card_index is None:
            return
        if self.showing_diagnosis_hand:
            return

        card = self.player.test_hand[self.selected_card_index]
        self.last_test_name = card.value.name
        result = self.patient.perform_test(self.last_test_name)
        self.last_test_result = result.replace("RESULTS: ", "", 1)

        self.player.play(card)
        self.pending_test_discard = card
        self.selected_card_index = None
        self.run_test_button = None
        self.refresh_hand_layout()
        self.test_result_started_at = pygame.time.get_ticks()
        self.state = GameState.TEST_RESULT
        self.notebook.add_test(self.patient, self.last_test_name, self.last_test_result)

    def discard_selected_test(self):
        """Move the selected test card to the throwaway pile without running it."""

        if self.showing_diagnosis_hand or self.selected_card_index is None:
            return

        selected_rect = self.get_selected_card_rect(self.selected_card_index)
        card = self.player.test_hand.pop(self.selected_card_index)
        self.discard_pile.append(card)
        self.discard_animation = {
            "card": card,
            "start": selected_rect.center,
            "started_at": pygame.time.get_ticks(),
        }
        self.selected_card_index = None
        self.run_test_button = None
        self.discard_button = None
        self.refresh_hand_layout()

    def handle_test_result_click(self, position):
        """Return to the workspace and visibly send the used card to med-waste."""

        if (
            self.get_test_result_reveal_progress() >= 1.0
            and self.continue_button.collidepoint(position)
        ):
            self.state = GameState.PATIENT
            if self.pending_test_discard is not None:
                self.discard_animation = {
                    "card": self.pending_test_discard,
                    "start": self.layout["active_hand"].center,
                    "started_at": pygame.time.get_ticks(),
                    "duration": self.test_discard_animation_duration,
                    "add_to_pile_on_complete": True,
                    "locks_input": True,
                    "arc_height": 105,
                }
                self.pending_test_discard = None

    def get_selected_card_rect(self, index):
        """Return the larger rectangle used to display a selected test card."""

        preview = pygame.Rect(0, 0, 220, 218)
        preview.midbottom = (
            self.card_rects[index].centerx,
            self.layout["active_hand"].bottom - 5,
        )
        return preview

    def get_run_test_button(self, selected_rect):
        """Return the Run Test button rectangle for an enlarged card."""

        return pygame.Rect(
            selected_rect.x + 16,
            selected_rect.bottom - 38,
            90,
            28,
        )

    def get_discard_button(self, selected_rect):
        """Return the Discard button rectangle for an enlarged test card."""

        return pygame.Rect(
            selected_rect.right - 106,
            selected_rect.bottom - 38,
            90,
            28,
        )

    def get_card_action_button(self, selected_rect):
        """Return the action-button rectangle used by an enlarged card."""

        return pygame.Rect(
            selected_rect.x + 24,
            selected_rect.bottom - 38,
            selected_rect.width - 48,
            28,
        )

    def play_selected_diagnosis(self):
        """Play the selected diagnosis and open its correct-or-incorrect result."""

        if not self.showing_diagnosis_hand or self.selected_card_index is None:
            return

        card = self.player.diagnosis_hand[self.selected_card_index]
        self.diagnosis_confirmation_open = False
        self.last_diagnosis = card.value
        self.player.play(card)
        self.diagnosis_correct = self.patient.receive_diagnosis(card.value)
        if self.diagnosis_correct:
            self.player.earn(DIAGNOSIS_REWARD)
        self.selected_card_index = None
        self.play_diagnosis_button = None
        self.state = GameState.OUTCOME

    def open_diagnosis_confirmation(self):
        """Open a confirmation dialog for the currently selected diagnosis card."""

        if self.showing_diagnosis_hand and self.selected_card_index is not None:
            self.diagnosis_confirmation_open = True

    def confirm_selected_diagnosis(self):
        """Confirm and play the diagnosis currently shown in the dialog."""

        if not self.diagnosis_confirmation_open:
            return
        self.diagnosis_confirmation_open = False
        self.play_selected_diagnosis()

    def handle_diagnosis_confirmation_click(self, position):
        """Handle the submit and return buttons in the diagnosis confirmation dialog."""

        if self.diagnosis_confirm_button.collidepoint(position):
            self.confirm_selected_diagnosis()
        elif self.diagnosis_cancel_button.collidepoint(position):
            self.diagnosis_confirmation_open = False

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

        if self.discard_animation is not None:
            elapsed = pygame.time.get_ticks() - self.discard_animation["started_at"]
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
        self.last_test_name = ""
        self.last_test_result = ""
        self.test_result_started_at = None
        self.last_diagnosis = None
        self.diagnosis_correct = None
        self.reception_transition_started_at = None
        self.patient_fade_started_at = None
        self.refresh_hand_layout()

    def finish_intro(self):
        """Skip or finish the one-time opening animation and show the welcome screen."""

        self.reception_transition_started_at = None
        self.patient_fade_started_at = None
        self.state = GameState.TITLE

    def begin_reception_transition(self):
        """Call the waiting patient and begin the examination-door animation."""

        if self.reception_transition_started_at is None:
            self.patient_fade_started_at = None
            self.reception_transition_started_at = pygame.time.get_ticks()

    def get_reception_transition_progress(self):
        """Return a zero-to-one value for the active reception-room transition."""

        if self.reception_transition_started_at is None:
            return 0.0
        elapsed = pygame.time.get_ticks() - self.reception_transition_started_at
        return max(0.0, min(1.0, elapsed / self.reception_transition_duration))

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
        waiting_color = COLORS["accent"] if progress > 0 else (255, 198, 75)
        pulse = 2 if (pygame.time.get_ticks() // 450) % 2 == 0 else 0
        pygame.draw.circle(
            self.screen,
            waiting_color,
            (display.x + 15, display.centery),
            5 + pulse,
        )

        left = self.body_font.render("RECEPTION", True, COLORS["text"])
        middle_text = "CALLING NEXT PATIENT" if progress > 0 else "PATIENTS WAITING: 4"
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
        """Draw four distinct patients and move Zorpa toward the exam door when called."""

        # A sleepy orange blob occupies the first chair.
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

        # Zorpa walks from the chair nearest the exam door after being called.
        progress = self.get_reception_transition_progress()
        walking_progress = min(1.0, progress / 0.92)
        walking_eased = walking_progress * walking_progress * (3 - 2 * walking_progress)
        zorpa_x = round(782 + (930 - 782) * walking_eased)
        zorpa_y = round(360 - 5 * math.sin(walking_progress * math.pi * 5))
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

        # A tall blue patient watches the queue display with all three eyes.
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

        # A small green four-armed patient fills the final chair.
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
        queue_text = "CALLING PATIENT..." if self.get_reception_transition_progress() > 0 else "PATIENTS WAITING: 4"
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

    def draw_reception_button(self):
        """Draw the physical control that calls the patient into the exam bay."""

        progress = self.get_reception_transition_progress()
        hovered = self.start_button.collidepoint(pygame.mouse.get_pos()) and progress == 0
        shadow = self.start_button.move(0, 5)
        pygame.draw.rect(self.screen, (26, 31, 45), shadow, border_radius=10)
        if progress > 0:
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
            label_text = "CALL NEXT PATIENT"
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
                "RESULT ADDED TO PATIENT NOTES",
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

    def build_notebook_rects(self):
        """Builds the rectangles that position the notebook's pages and buttons."""

        book = pygame.Rect(130, 100, 840, 490)
        page_width = book.width // 2 - 60
        page_height = book.height - 90
        button_y = book.bottom - 48

        return {
            "book": book,
            "left": pygame.Rect(book.x + 30, book.y + 30, page_width, page_height),
            "right": pygame.Rect(book.centerx + 30, book.y + 30, page_width, page_height),
            "prev": pygame.Rect(book.x + 30, button_y, 100, 30),
            "next": pygame.Rect(book.right - 130, button_y, 100, 30),
            "close": pygame.Rect(book.centerx - 50, button_y, 100, 30),
        }

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
        label = self.small_font.render("MED-WASTE", True, (245, 130, 115))
        label_plate = pygame.Rect(panel.x + 15, panel.y + 2, panel.width - 30, 27)
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
            visible_card = pygame.Rect(panel.centerx - 27, panel.y + 30, 54, 34)
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
                card_name.get_rect(center=(visible_card.centerx, visible_card.y + 11)),
            )

        lid = pygame.Rect(panel.x + 16, panel.y + 45, panel.width - 32, 12)
        pygame.draw.rect(self.screen, (245, 130, 115), lid, border_radius=5)
        pygame.draw.rect(
            self.screen,
            COLORS["background"],
            lid,
            width=2,
            border_radius=5,
        )
        slot = pygame.Rect(lid.centerx - 25, lid.y + 3, 50, 4)
        pygame.draw.rect(self.screen, COLORS["background"], slot, border_radius=2)

        container_points = (
            (panel.x + 23, lid.bottom - 2),
            (panel.right - 23, lid.bottom - 2),
            (panel.right - 29, panel.bottom - 8),
            (panel.x + 29, panel.bottom - 8),
        )
        pygame.draw.polygon(self.screen, (48, 72, 76), container_points)
        pygame.draw.polygon(
            self.screen,
            (245, 130, 115),
            container_points,
            width=2,
        )

        warning_center = (panel.centerx, panel.y + 78)
        warning_triangle = (
            (warning_center[0], warning_center[1] - 12),
            (warning_center[0] - 13, warning_center[1] + 10),
            (warning_center[0] + 13, warning_center[1] + 10),
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
            count.get_rect(center=(panel.centerx, panel.bottom - 14)),
        )

    def draw_discard_animation(self):
        """Arc a visible test card into the med-waste slot after use or discard."""

        if self.discard_animation is None:
            return

        elapsed = pygame.time.get_ticks() - self.discard_animation["started_at"]
        duration = self.discard_animation.get(
            "duration",
            self.discard_animation_duration,
        )
        progress = min(1.0, elapsed / duration)
        eased_progress = progress * progress * (3 - 2 * progress)
        start_x, start_y = self.discard_animation["start"]
        target = (
            self.layout["throwaway"].centerx,
            self.layout["throwaway"].y + 51,
        )
        control = (
            (start_x + target[0]) / 2,
            min(start_y, target[1]) - self.discard_animation.get("arc_height", 55),
        )
        center_x, center_y = self.get_quadratic_curve_point(
            (start_x, start_y),
            control,
            target,
            eased_progress,
        )

        for lag, radius, trail_color in (
            (0.12, 5, (74, 120, 142)),
            (0.07, 4, (91, 162, 166)),
            (0.03, 3, (147, 208, 190)),
        ):
            trail_progress = max(0.0, eased_progress - lag)
            trail_x, trail_y = self.get_quadratic_curve_point(
                (start_x, start_y),
                control,
                target,
                trail_progress,
            )
            pygame.draw.circle(
                self.screen,
                trail_color,
                (round(trail_x), round(trail_y)),
                radius,
            )

        card_surface = self.create_discard_card_surface(
            self.discard_animation["card"],
        )
        scale = 1.0 - 0.57 * eased_progress
        scaled_size = (
            max(38, round(card_surface.get_width() * scale)),
            max(48, round(card_surface.get_height() * scale)),
        )
        card_surface = pygame.transform.smoothscale(card_surface, scaled_size)
        card_surface = pygame.transform.rotate(
            card_surface,
            -8 + 30 * math.sin(progress * math.pi),
        )
        if progress > 0.82:
            card_surface.set_alpha(round(255 * (1 - (progress - 0.82) / 0.18)))
        card_rect = card_surface.get_rect(center=(round(center_x), round(center_y)))
        self.screen.blit(card_surface, card_rect)

        if progress > 0.72:
            self.draw_med_waste_slot_lip()

    def get_quadratic_curve_point(self, start, control, target, progress):
        """Return a point along the arcing path used by the disposal animation."""

        inverse = 1 - progress
        return (
            inverse * inverse * start[0]
            + 2 * inverse * progress * control[0]
            + progress * progress * target[0],
            inverse * inverse * start[1]
            + 2 * inverse * progress * control[1]
            + progress * progress * target[1],
        )

    def create_discard_card_surface(self, card):
        """Create a compact snapshot so the flying object is recognizably the used card."""

        test = card.value
        rarity_color = RARITY_COLORS.get(test.rarity, COLORS["panel_border"])
        fill_color = RARITY_CARD_COLORS.get(test.rarity, COLORS["card"])
        card_surface = pygame.Surface((96, 118), pygame.SRCALPHA)
        shape = self.get_card_shape_points(card_surface.get_rect(), 7)
        pygame.draw.polygon(card_surface, fill_color, shape)
        pygame.draw.polygon(card_surface, rarity_color, shape, width=3)

        header = pygame.Rect(7, 7, 82, 25)
        header_color = tuple(max(0, channel - 18) for channel in fill_color)
        pygame.draw.rect(card_surface, header_color, header, border_radius=5)
        title_font = self.card_font
        if title_font.size(test.name)[0] > header.width - 6:
            title_font = self.pile_font
        title = title_font.render(test.name, True, COLORS["card_text"])
        card_surface.blit(title, title.get_rect(center=header.center))

        icon = pygame.Rect(28, 40, 40, 40)
        pygame.draw.rect(card_surface, (201, 214, 205), icon, border_radius=6)
        pygame.draw.rect(card_surface, rarity_color, icon, width=2, border_radius=6)
        initial = self.body_font.render(test.name[0], True, COLORS["card_text"])
        card_surface.blit(initial, initial.get_rect(center=icon.center))

        rarity = self.pile_font.render(test.rarity.upper(), True, rarity_color)
        card_surface.blit(rarity, rarity.get_rect(center=(48, 101)))
        return card_surface

    def draw_med_waste_slot_lip(self):
        """Redraw the bin opening over the final frames so the card appears to enter it."""

        panel = self.layout["throwaway"]
        lid = pygame.Rect(panel.x + 16, panel.y + 45, panel.width - 32, 12)
        pygame.draw.rect(self.screen, (245, 130, 115), lid, border_radius=5)
        pygame.draw.rect(
            self.screen,
            COLORS["background"],
            lid,
            width=2,
            border_radius=5,
        )
        slot = pygame.Rect(lid.centerx - 25, lid.y + 3, 50, 4)
        pygame.draw.rect(self.screen, COLORS["background"], slot, border_radius=2)

    def update_notebook_preview_animation(self, hovered):
        """Open or close the miniature notebook smoothly based on the mouse position."""

        now = pygame.time.get_ticks()
        elapsed = max(0, min(50, now - self.notebook_preview_last_tick))
        self.notebook_preview_last_tick = now
        direction = 1 if hovered else -1
        step = elapsed / self.notebook_preview_duration
        self.notebook_preview_progress = max(
            0.0,
            min(1.0, self.notebook_preview_progress + direction * step),
        )
        progress = self.notebook_preview_progress
        return 1 - (1 - progress) ** 3

    def get_notebook_test_count_label(self):
        """Return a compact test count that fits on the miniature notebook page."""

        entries = self.notebook.get_entries(self.patient)
        test_count = sum(test_name != "No tests" for test_name in entries)
        if test_count == 0:
            return "NO TESTS"
        if test_count == 1:
            return "1 TEST"
        return f"{test_count} TESTS"

    def draw_notebook(self):
        """Draw a portrait notebook whose front cover swings open on hover."""

        panel = self.layout["notebook"]
        hovered = panel.collidepoint(pygame.mouse.get_pos())
        progress = self.update_notebook_preview_animation(hovered)
        lift = round(7 * progress)

        page_width = 70
        book_height = round(110 - 6 * progress)
        closed_spine_x = panel.centerx - page_width // 2
        spine_x = round(closed_spine_x + (panel.centerx - closed_spine_x) * progress)
        book_y = panel.y + 13 - lift
        book_bottom = book_y + book_height
        left_extent = round(page_width * progress)

        cover_color = (82, 58, 112)
        cover_dark = (54, 39, 78)
        cover_highlight = (171, 123, 203)
        page_color = (240, 237, 211)
        page_edge = (174, 160, 176)
        rule_color = (188, 196, 174)

        glow = pygame.Surface(panel.size, pygame.SRCALPHA)
        pulse = (math.sin(pygame.time.get_ticks() / 650) + 1) / 2
        glow_alpha = round(18 + 12 * pulse + 16 * progress)
        pygame.draw.ellipse(
            glow,
            (173, 118, 208, glow_alpha),
            pygame.Rect(8, 5, panel.width - 16, panel.height - 27),
        )
        self.screen.blit(glow, panel.topleft)

        full_book = pygame.Rect(
            spine_x - left_extent - 2,
            book_y - 2,
            page_width + left_extent + 4,
            book_height + 4,
        )
        pygame.draw.rect(
            self.screen,
            (4, 9, 16),
            full_book.move(5, 7),
            border_radius=7,
        )
        pygame.draw.rect(self.screen, cover_color, full_book, border_radius=6)
        pygame.draw.rect(
            self.screen,
            cover_highlight,
            full_book,
            width=2,
            border_radius=6,
        )

        right_page = pygame.Rect(spine_x, book_y, page_width, book_height)
        pygame.draw.rect(
            self.screen,
            page_color,
            right_page,
            border_top_right_radius=5,
            border_bottom_right_radius=5,
        )
        pygame.draw.rect(
            self.screen,
            page_edge,
            right_page,
            width=1,
            border_top_right_radius=5,
            border_bottom_right_radius=5,
        )

        # Past the halfway point, the underside of the cover becomes the left page.
        flipped_progress = max(0.0, (progress - 0.5) / 0.5)
        flipped_width = round(page_width * flipped_progress)
        left_page = pygame.Rect(
            spine_x - flipped_width,
            book_y,
            flipped_width,
            book_height,
        )
        if flipped_width > 0:
            pygame.draw.rect(
                self.screen,
                page_color,
                left_page,
                border_top_left_radius=5,
                border_bottom_left_radius=5,
            )
            pygame.draw.rect(
                self.screen,
                page_edge,
                left_page,
                width=1,
                border_top_left_radius=5,
                border_bottom_left_radius=5,
            )

        # Ruled paper appears gradually as the purple cover moves out of the way.
        if progress > 0.18:
            for line_y in range(book_y + 18, book_bottom - 8, 12):
                if flipped_width > 13:
                    pygame.draw.line(
                        self.screen,
                        rule_color,
                        (left_page.x + 7, line_y),
                        (spine_x - 6, line_y),
                    )
                pygame.draw.line(
                    self.screen,
                    rule_color,
                    (spine_x + 6, line_y),
                    (right_page.right - 7, line_y),
                )

        # During the first half, the purple front cover narrows toward its spine.
        if progress < 0.5:
            cover_width = max(2, round(page_width * (1 - progress / 0.5)))
            perspective = round(4 * (progress / 0.5))
            front_cover = (
                (spine_x, book_y),
                (spine_x + cover_width, book_y + perspective),
                (spine_x + cover_width, book_bottom - perspective),
                (spine_x, book_bottom),
            )
            pygame.draw.polygon(self.screen, cover_color, front_cover)
            pygame.draw.polygon(self.screen, cover_highlight, front_cover, width=2)

            title_alpha = max(0, min(255, round(255 * (1 - progress / 0.32))))
            if title_alpha > 0:
                cover_surface = pygame.Surface(
                    (page_width, book_height),
                    pygame.SRCALPHA,
                )
                title = self.card_font.render("PATIENT", True, (245, 225, 255))
                subtitle = self.card_font.render("NOTES", True, (245, 225, 255))
                title.set_alpha(title_alpha)
                subtitle.set_alpha(title_alpha)
                cover_surface.blit(
                    title,
                    title.get_rect(center=(page_width // 2, 30)),
                )
                cover_surface.blit(
                    subtitle,
                    subtitle.get_rect(center=(page_width // 2, 46)),
                )
                self.screen.blit(cover_surface, (spine_x, book_y))

        pygame.draw.line(
            self.screen,
            cover_dark,
            (spine_x, book_y + 4),
            (spine_x, book_bottom - 4),
            width=2,
        )

        fold_size = 9
        pygame.draw.polygon(
            self.screen,
            (206, 198, 184),
            [
                (right_page.right - fold_size, right_page.y),
                (right_page.right, right_page.y),
                (right_page.right, right_page.y + fold_size),
            ],
        )
        pygame.draw.line(
            self.screen,
            page_edge,
            (right_page.right - fold_size, right_page.y),
            (right_page.right, right_page.y + fold_size),
        )

        bookmark_x = spine_x + round(page_width * 0.48)
        pygame.draw.polygon(
            self.screen,
            (228, 90, 113),
            [
                (bookmark_x - 4, book_bottom - 3),
                (bookmark_x + 4, book_bottom - 3),
                (bookmark_x + 4, book_bottom + 10),
                (bookmark_x, book_bottom + 6),
                (bookmark_x - 4, book_bottom + 10),
            ],
        )

        if progress > 0.62:
            note_alpha = max(0, min(255, round(255 * (progress - 0.62) / 0.38)))
            count_label = self.get_notebook_test_count_label()
            note_surface = self.notebook_preview_font.render(
                count_label,
                True,
                COLORS["card_text"],
            )
            note_surface.set_alpha(note_alpha)
            note_rect = note_surface.get_rect(
                center=(right_page.centerx, book_y + 24)
            )
            self.screen.blit(note_surface, note_rect)

            pencil_surface = pygame.Surface((24, 67), pygame.SRCALPHA)
            pygame.draw.polygon(
                pencil_surface,
                (247, 183, 69, note_alpha),
                [(8, 7), (14, 7), (14, 57), (8, 57)],
            )
            pygame.draw.rect(
                pencil_surface,
                (235, 105, 127, note_alpha),
                pygame.Rect(8, 4, 6, 7),
                border_radius=2,
            )
            pygame.draw.polygon(
                pencil_surface,
                (222, 203, 164, note_alpha),
                [(8, 57), (14, 57), (11, 65)],
            )
            pygame.draw.polygon(
                pencil_surface,
                (50, 45, 54, note_alpha),
                [(10, 62), (12, 62), (11, 66)],
            )
            rotated_pencil = pygame.transform.rotate(pencil_surface, -13)
            self.screen.blit(
                rotated_pencil,
                (right_page.right - 18, book_y + 18),
            )

        if hovered:
            hover_label = self.card_font.render(
                "OPEN NOTEBOOK",
                True,
                COLORS["accent"],
            )
            self.screen.blit(
                hover_label,
                hover_label.get_rect(center=(panel.centerx, panel.bottom - 5)),
            )

    def draw_active_hand(self):
        """Draw the currently active test or diagnosis hand and its selection state."""

        panel = self.layout["active_hand"]
        tray = panel.inflate(-8, -8)
        tray.y += 3
        pygame.draw.rect(
            self.screen,
            (8, 12, 20),
            tray.move(5, 6),
            border_radius=13,
        )
        pygame.draw.rect(self.screen, (20, 28, 39), tray, border_radius=13)
        pygame.draw.rect(
            self.screen,
            (90, 88, 113),
            tray,
            width=2,
            border_radius=13,
        )
        pygame.draw.rect(
            self.screen,
            (11, 18, 27),
            tray.inflate(-12, -12),
            width=1,
            border_radius=9,
        )
        hand_name = (
            "DIAGNOSIS OPTIONS"
            if self.showing_diagnosis_hand
            else "AVAILABLE TESTS"
        )
        name_plate = pygame.Rect(0, 0, 158, 24)
        name_plate.midtop = (tray.centerx, tray.y + 5)
        pygame.draw.rect(self.screen, (38, 48, 61), name_plate, border_radius=7)
        pygame.draw.rect(
            self.screen,
            (112, 119, 142),
            name_plate,
            width=1,
            border_radius=7,
        )
        self.draw_centered_label(hand_name, name_plate, name_plate.centery)

        for light_x, light_color in (
            (tray.x + 18, COLORS["accent"]),
            (tray.x + 29, (79, 151, 235)),
            (tray.right - 29, (79, 151, 235)),
            (tray.right - 18, COLORS["accent"]),
        ):
            pygame.draw.circle(self.screen, (8, 14, 21), (light_x, tray.y + 17), 4)
            pygame.draw.circle(self.screen, light_color, (light_x, tray.y + 17), 2)

        active_hand = self.get_active_hand()
        # Future draw-card code can update the hand data without managing coordinates.
        if len(self.card_rects) != len(active_hand):
            self.refresh_hand_layout()

        if not active_hand:
            empty_text = (
                "NO DIAGNOSIS CARDS"
                if self.showing_diagnosis_hand
                else "NO TEST CARDS"
            )
            empty = self.body_font.render(empty_text, True, COLORS["muted"])
            self.screen.blit(empty, empty.get_rect(center=panel.center))
            return

        mouse_position = pygame.mouse.get_pos()

        for index, card in enumerate(active_hand):
            if index == self.selected_card_index:
                continue

            card_rect = self.card_rects[index]
            hovered = (
                self.selected_card_index is None
                and card_rect.collidepoint(mouse_position)
            )
            display_rect = (
                self.get_hovered_card_rect(card_rect)
                if hovered
                else card_rect
            )
            if self.showing_diagnosis_hand:
                self.draw_diagnosis_card(card, display_rect, hovered=hovered)
            else:
                self.draw_test_card(card, display_rect, hovered=hovered)
            if self.selected_card_index is not None:
                self.draw_card_dimming_overlay(display_rect)

        if self.selected_card_index is not None:
            selected_card = active_hand[self.selected_card_index]
            selected_rect = self.get_selected_card_rect(self.selected_card_index)
            if self.showing_diagnosis_hand:
                self.draw_diagnosis_card(selected_card, selected_rect, selected=True)
            else:
                self.draw_test_card(selected_card, selected_rect, selected=True)

    def get_hovered_card_rect(self, card_rect):
        """Lift and gently enlarge a hovered card without changing its color."""

        width_growth = max(4, round(card_rect.width * 0.04))
        height_growth = max(6, round(card_rect.height * 0.04))
        return card_rect.inflate(width_growth, height_growth).move(0, -7)

    def get_card_shape_points(self, card_rect, corner_cut=7):
        """Return the clipped-corner outline shared by every card style."""

        return (
            (card_rect.x + corner_cut, card_rect.y),
            (card_rect.right - corner_cut, card_rect.y),
            (card_rect.right, card_rect.y + corner_cut),
            (card_rect.right, card_rect.bottom - corner_cut),
            (card_rect.right - corner_cut, card_rect.bottom),
            (card_rect.x + corner_cut, card_rect.bottom),
            (card_rect.x, card_rect.bottom - corner_cut),
            (card_rect.x, card_rect.y + corner_cut),
        )

    def draw_card_shell(
        self,
        card_rect,
        fill_color,
        border_color,
        border_width,
        selected,
        hovered=False,
    ):
        """Draw one reusable sci-fi card body with a clipped outline and shadow."""

        corner_cut = 10 if selected else 7
        if hovered:
            soft_shadow = card_rect.inflate(10, 10).move(6, 8)
            pygame.draw.polygon(
                self.screen,
                (9, 16, 24),
                self.get_card_shape_points(soft_shadow, corner_cut + 3),
            )

        shadow_offset = 7 if selected else 5 if hovered else 4
        shadow_rect = card_rect.move(shadow_offset, shadow_offset)
        pygame.draw.polygon(
            self.screen,
            (3, 8, 12),
            self.get_card_shape_points(shadow_rect, corner_cut),
        )
        card_points = self.get_card_shape_points(card_rect, corner_cut)
        pygame.draw.polygon(self.screen, fill_color, card_points)
        pygame.draw.polygon(
            self.screen,
            border_color,
            card_points,
            width=border_width,
        )

    def draw_card_dimming_overlay(self, card_rect):
        """Subtly dim unselected cards while an enlarged card has focus."""

        overlay = pygame.Surface(card_rect.size, pygame.SRCALPHA)
        local_rect = overlay.get_rect()
        pygame.draw.polygon(
            overlay,
            (5, 11, 17, 42),
            self.get_card_shape_points(local_rect, 7),
        )
        self.screen.blit(overlay, card_rect.topleft)

    def draw_fitted_card_title(self, title, area, selected=False):
        """Choose the largest existing font that keeps a card title inside its header."""

        fonts = (
            (self.body_font, self.small_font, self.card_font)
            if selected
            else (self.card_font, self.pile_font, self.tiny_font)
        )
        font = fonts[-1]
        for candidate in fonts:
            if candidate.size(title)[0] <= area.width - 8:
                font = candidate
                break
        title_surface = font.render(title, True, COLORS["card_text"])
        self.screen.blit(title_surface, title_surface.get_rect(center=area.center))

    def draw_rarity_badge(self, rarity, card_rect):
        """Show card rarity with both text and a shape so color is not the only cue."""

        rarity_color = RARITY_COLORS.get(rarity, COLORS["panel_border"])
        badge = pygame.Rect(
            card_rect.x + 7,
            card_rect.bottom - 23,
            card_rect.width - 14,
            16,
        )
        pygame.draw.rect(self.screen, (203, 214, 202), badge, border_radius=6)
        pygame.draw.rect(
            self.screen,
            rarity_color,
            badge,
            width=1,
            border_radius=6,
        )

        symbol_center = (badge.x + 11, badge.centery)
        if rarity == "Rare":
            symbol = (
                (symbol_center[0], symbol_center[1] - 5),
                (symbol_center[0] + 3, symbol_center[1] - 2),
                (symbol_center[0] + 5, symbol_center[1]),
                (symbol_center[0] + 2, symbol_center[1] + 2),
                (symbol_center[0], symbol_center[1] + 5),
                (symbol_center[0] - 2, symbol_center[1] + 2),
                (symbol_center[0] - 5, symbol_center[1]),
                (symbol_center[0] - 3, symbol_center[1] - 2),
            )
            pygame.draw.polygon(self.screen, rarity_color, symbol)
        elif rarity == "Uncommon":
            pygame.draw.polygon(
                self.screen,
                rarity_color,
                (
                    (symbol_center[0], symbol_center[1] - 5),
                    (symbol_center[0] + 5, symbol_center[1]),
                    (symbol_center[0], symbol_center[1] + 5),
                    (symbol_center[0] - 5, symbol_center[1]),
                ),
            )
        else:
            pygame.draw.circle(self.screen, rarity_color, symbol_center, 4)

        rarity_text = self.pile_font.render(rarity.upper(), True, rarity_color)
        self.screen.blit(
            rarity_text,
            rarity_text.get_rect(midleft=(badge.x + 20, badge.centery)),
        )

    def draw_diagnosis_card(self, card, card_rect, hovered=False, selected=False):
        """Draw one diagnosis card in either its compact or enlarged state."""

        diagnosis = card.value
        diagnosis_color = (183, 92, 211)
        border_color = diagnosis_color
        border_width = 4 if selected else 2
        self.draw_card_shell(
            card_rect,
            (235, 220, 239),
            border_color,
            border_width,
            selected,
            hovered=hovered,
        )

        if selected:
            self.draw_selected_diagnosis_details(
                diagnosis,
                card_rect,
                diagnosis_color,
            )
        else:
            self.draw_compact_diagnosis_card(
                diagnosis,
                card_rect,
                diagnosis_color,
            )

    def draw_compact_diagnosis_card(self, diagnosis, card_rect, diagnosis_color):
        """Draw a diagnosis option with the same hierarchy as a compact test card."""

        header = pygame.Rect(card_rect.x + 6, card_rect.y + 6, card_rect.width - 12, 30)
        pygame.draw.rect(self.screen, (218, 199, 226), header, border_radius=5)
        pygame.draw.line(
            self.screen,
            diagnosis_color,
            (header.x + 6, header.bottom),
            (header.right - 6, header.bottom),
        )
        # Base this decision on the resting 96-pixel card, not the slightly wider
        # hover rectangle, so titles never switch fonts while the mouse moves.
        resting_single_line_width = 80
        if (
            self.diagnosis_card_font.size(diagnosis.name)[0]
            <= resting_single_line_width
        ):
            title = self.diagnosis_card_font.render(
                diagnosis.name,
                True,
                COLORS["card_text"],
            )
            self.screen.blit(title, title.get_rect(center=header.center))
        else:
            name_parts = diagnosis.name.split(maxsplit=1)
            for line_index, line_text in enumerate(name_parts):
                title = self.pile_font.render(line_text, True, COLORS["card_text"])
                line_y = header.centery - 6 + line_index * 11
                self.screen.blit(
                    title,
                    title.get_rect(center=(header.centerx, line_y)),
                )

        icon = pygame.Rect(card_rect.centerx - 25, card_rect.y + 40, 50, 43)
        pygame.draw.rect(self.screen, (210, 211, 216), icon, border_radius=6)
        pygame.draw.rect(self.screen, diagnosis_color, icon, width=2, border_radius=6)
        self.draw_diagnosis_file_icon(icon, diagnosis_color)

        subtitle = self.card_font.render(
            "CASE FILE",
            True,
            COLORS["card_text"],
        )
        self.screen.blit(
            subtitle,
            subtitle.get_rect(center=(card_rect.centerx, card_rect.y + 90)),
        )
        self.draw_diagnosis_badge(card_rect, diagnosis_color)

    def draw_selected_diagnosis_details(self, diagnosis, card_rect, diagnosis_color):
        """Draw the enlarged diagnosis file with its description and play action."""

        header = pygame.Rect(card_rect.x + 9, card_rect.y + 8, card_rect.width - 18, 39)
        pygame.draw.rect(self.screen, (218, 199, 226), header, border_radius=7)
        self.draw_fitted_card_title(diagnosis.name, header, selected=True)
        type_label = self.card_font.render("FINAL DIAGNOSIS", True, diagnosis_color)
        self.screen.blit(
            type_label,
            type_label.get_rect(center=(card_rect.centerx, card_rect.y + 56)),
        )

        icon = pygame.Rect(card_rect.x + 16, card_rect.y + 68, 58, 58)
        pygame.draw.rect(self.screen, (210, 211, 216), icon, border_radius=7)
        pygame.draw.rect(self.screen, diagnosis_color, icon, width=2, border_radius=7)
        self.draw_diagnosis_file_icon(icon, diagnosis_color)

        description_box = pygame.Rect(
            card_rect.x + 84,
            card_rect.y + 69,
            card_rect.width - 100,
            100,
        )
        self.draw_wrapped_text(
            diagnosis.description,
            self.card_font,
            COLORS["card_text"],
            description_box,
        )

        self.play_diagnosis_button = self.get_card_action_button(card_rect)
        pygame.draw.rect(
            self.screen,
            diagnosis_color,
            self.play_diagnosis_button,
            border_radius=5,
        )
        pygame.draw.rect(
            self.screen,
            (218, 159, 235),
            self.play_diagnosis_button,
            width=2,
            border_radius=5,
        )
        play_text = self.small_font.render(
            "PLAY DIAGNOSIS",
            True,
            COLORS["background"],
        )
        self.screen.blit(
            play_text,
            play_text.get_rect(center=self.play_diagnosis_button.center),
        )

    def draw_diagnosis_file_icon(self, icon, diagnosis_color):
        """Draw a clipped patient-file symbol in place of the old letter placeholder."""

        icon_surface = pygame.Surface(icon.size, pygame.SRCALPHA)
        center_x, center_y = icon_surface.get_rect().center
        paper = pygame.Rect(center_x - 13, center_y - 14, 27, 30)
        pygame.draw.rect(icon_surface, (240, 234, 219), paper, border_radius=3)
        pygame.draw.rect(icon_surface, COLORS["card_text"], paper, width=2, border_radius=3)
        clip = pygame.Rect(center_x - 7, paper.y - 3, 14, 7)
        pygame.draw.rect(icon_surface, diagnosis_color, clip, border_radius=3)
        pygame.draw.line(
            icon_surface,
            (118, 122, 116),
            (paper.x + 5, paper.y + 9),
            (paper.right - 5, paper.y + 9),
            width=2,
        )
        pygame.draw.line(
            icon_surface,
            (118, 122, 116),
            (paper.x + 5, paper.y + 14),
            (paper.right - 8, paper.y + 14),
            width=2,
        )
        pygame.draw.line(
            icon_surface,
            diagnosis_color,
            (paper.x + 6, paper.bottom - 8),
            (paper.x + 11, paper.bottom - 4),
            width=2,
        )
        pygame.draw.line(
            icon_surface,
            diagnosis_color,
            (paper.x + 11, paper.bottom - 4),
            (paper.right - 5, paper.bottom - 12),
            width=2,
        )
        self.screen.blit(icon_surface, icon.topleft)

    def draw_diagnosis_badge(self, card_rect, diagnosis_color):
        """Draw the diagnosis-type badge in the same position as test rarity badges."""

        badge = pygame.Rect(
            card_rect.x + 7,
            card_rect.bottom - 23,
            card_rect.width - 14,
            16,
        )
        pygame.draw.rect(self.screen, (213, 205, 218), badge, border_radius=6)
        pygame.draw.rect(self.screen, diagnosis_color, badge, width=1, border_radius=6)
        symbol_center = (badge.x + 11, badge.centery)
        pygame.draw.polygon(
            self.screen,
            diagnosis_color,
            (
                (symbol_center[0], symbol_center[1] - 5),
                (symbol_center[0] + 5, symbol_center[1]),
                (symbol_center[0], symbol_center[1] + 5),
                (symbol_center[0] - 5, symbol_center[1]),
            ),
        )
        label = self.pile_font.render("DIAGNOSIS", True, diagnosis_color)
        self.screen.blit(
            label,
            label.get_rect(midleft=(badge.x + 20, badge.centery)),
        )

    def draw_test_card(self, card, card_rect, hovered=False, selected=False):
        """Draw one test card in either its compact or enlarged state."""

        test = card.value
        rarity_color = RARITY_COLORS.get(test.rarity, COLORS["panel_border"])
        card_color = RARITY_CARD_COLORS.get(test.rarity, COLORS["card"])
        border_color = rarity_color
        border_width = 4 if selected else 2
        self.draw_card_shell(
            card_rect,
            card_color,
            border_color,
            border_width,
            selected,
            hovered=hovered,
        )

        if selected:
            self.draw_selected_card_details(test, card_rect, rarity_color)
        else:
            self.draw_compact_card(test, card_rect, rarity_color)

    def draw_compact_card(self, test, card_rect, rarity_color):
        """Draw the compact header, artwork, subtitle, and rarity badge of a test card."""

        header = pygame.Rect(card_rect.x + 6, card_rect.y + 6, card_rect.width - 12, 25)
        header_color = tuple(max(0, channel - 18) for channel in RARITY_CARD_COLORS.get(
            test.rarity,
            COLORS["card"],
        ))
        pygame.draw.rect(self.screen, header_color, header, border_radius=5)
        pygame.draw.line(
            self.screen,
            rarity_color,
            (header.x + 6, header.bottom),
            (header.right - 6, header.bottom),
            width=1,
        )
        self.draw_fitted_card_title(test.name, header)

        icon = pygame.Rect(card_rect.centerx - 25, card_rect.y + 35, 50, 45)
        pygame.draw.rect(self.screen, (201, 214, 205), icon, border_radius=6)
        pygame.draw.rect(self.screen, rarity_color, icon, width=2, border_radius=6)
        self.draw_test_icon(test.name, icon, rarity_color)

        subtitle = self.tiny_font.render(
            TEST_SUBTITLES.get(test.name.upper(), "MEDICAL TEST"),
            True,
            COLORS["card_text"],
        )
        self.screen.blit(
            subtitle,
            subtitle.get_rect(center=(card_rect.centerx, card_rect.y + 88)),
        )
        self.draw_rarity_badge(test.rarity, card_rect)

    def draw_selected_card_details(self, test, card_rect, rarity_color):
        """Draw an enlarged test card with Run Test and Discard buttons."""

        header = pygame.Rect(card_rect.x + 9, card_rect.y + 8, card_rect.width - 18, 39)
        header_color = tuple(max(0, channel - 18) for channel in RARITY_CARD_COLORS.get(
            test.rarity,
            COLORS["card"],
        ))
        pygame.draw.rect(self.screen, header_color, header, border_radius=7)
        self.draw_fitted_card_title(test.name, header, selected=True)

        rarity = self.card_font.render(test.rarity.upper(), True, rarity_color)
        self.screen.blit(rarity, rarity.get_rect(center=(card_rect.centerx, card_rect.y + 55)))

        icon = pygame.Rect(card_rect.x + 16, card_rect.y + 65, 58, 58)
        pygame.draw.rect(self.screen, (201, 214, 205), icon, border_radius=7)
        pygame.draw.rect(self.screen, rarity_color, icon, width=2, border_radius=7)
        self.draw_test_icon(test.name, icon, rarity_color)

        subtitle = self.tiny_font.render(
            TEST_SUBTITLES.get(test.name.upper(), "MEDICAL TEST"),
            True,
            COLORS["card_text"],
        )
        self.screen.blit(
            subtitle,
            subtitle.get_rect(center=(icon.centerx, icon.bottom + 9)),
        )

        description_box = pygame.Rect(
            card_rect.x + 84,
            card_rect.y + 67,
            card_rect.width - 100,
            100,
        )
        self.draw_wrapped_text(
            test.description,
            self.card_font,
            COLORS["card_text"],
            description_box,
        )

        self.run_test_button = self.get_run_test_button(card_rect)
        pygame.draw.rect(
            self.screen, COLORS["panel_border"], self.run_test_button, border_radius=5
        )
        run_text = self.small_font.render("RUN TEST", True, COLORS["background"])
        self.screen.blit(run_text, run_text.get_rect(center=self.run_test_button.center))

        self.discard_button = self.get_discard_button(card_rect)
        pygame.draw.rect(
            self.screen,
            (205, 100, 100),
            self.discard_button,
            border_radius=5,
        )
        discard_text = self.small_font.render(
            "DISCARD",
            True,
            COLORS["background"],
        )
        self.screen.blit(
            discard_text,
            discard_text.get_rect(center=self.discard_button.center),
        )

    def draw_test_icon(self, test_name, icon, rarity_color):
        """Render a test symbol onto a clipped surface that cannot escape its frame."""

        icon_surface = pygame.Surface(icon.size, pygame.SRCALPHA)
        icon_area = icon_surface.get_rect()
        center_x, center_y = icon_area.center
        ink = COLORS["card_text"]
        test_name = test_name.upper()

        if test_name == "TEMPERATURE":
            pygame.draw.circle(icon_surface, rarity_color, (center_x, center_y + 8), 6)
            pygame.draw.rect(
                icon_surface,
                ink,
                pygame.Rect(center_x - 3, center_y - 13, 6, 20),
                border_radius=3,
            )
            pygame.draw.rect(
                icon_surface,
                rarity_color,
                pygame.Rect(center_x - 1, center_y - 9, 2, 16),
            )
            pygame.draw.circle(icon_surface, ink, (center_x, center_y + 8), 8, width=2)
        elif test_name == "ULTRASOUND":
            probe = pygame.Rect(center_x - 16, center_y - 8, 7, 16)
            pygame.draw.rect(icon_surface, ink, probe, border_radius=3)
            for wave_number, radius in enumerate((6, 10, 14)):
                wave = pygame.Rect(
                    center_x - 10,
                    center_y - radius,
                    radius * 2,
                    radius * 2,
                )
                pygame.draw.arc(
                    icon_surface,
                    rarity_color if wave_number == 2 else ink,
                    wave,
                    -math.pi / 3,
                    math.pi / 3,
                    width=2,
                )
        elif test_name == "X-RAY":
            for offset in (-4, 4):
                start = (center_x - 9, center_y + offset)
                end = (center_x + 9, center_y - offset)
                pygame.draw.line(icon_surface, ink, start, end, width=4)
                pygame.draw.circle(icon_surface, rarity_color, start, 4)
                pygame.draw.circle(icon_surface, rarity_color, end, 4)
                pygame.draw.circle(icon_surface, ink, start, 4, width=1)
                pygame.draw.circle(icon_surface, ink, end, 4, width=1)
        elif test_name == "ALLERGY":
            drop = (
                (center_x, center_y - 14),
                (center_x - 10, center_y + 3),
                (center_x - 8, center_y + 11),
                (center_x, center_y + 15),
                (center_x + 8, center_y + 11),
                (center_x + 10, center_y + 3),
            )
            pygame.draw.polygon(icon_surface, rarity_color, drop)
            pygame.draw.polygon(icon_surface, ink, drop, width=2)
            pygame.draw.circle(
                icon_surface,
                (238, 246, 228),
                (center_x + 3, center_y + 3),
                3,
            )
        else:
            icon_text = self.body_font.render(test_name[0], True, ink)
            icon_surface.blit(icon_text, icon_text.get_rect(center=icon_area.center))

        self.screen.blit(icon_surface, icon.topleft)

    def draw_diagnosis_cards(self):
        """Draw the diagnosis folder standing in a compact desktop file rack."""

        panel = self.layout["diagnosis"]
        mouse_position = pygame.mouse.get_pos()
        hovered = panel.collidepoint(mouse_position)
        folder_lift = 5 if hovered and not self.showing_diagnosis_hand else 0
        progress = self.get_diagnosis_folder_progress()

        rack = pygame.Rect(panel.x + 24, panel.y + 27, panel.width - 48, 105)
        pygame.draw.rect(self.screen, (8, 12, 20), rack.move(5, 6), border_radius=10)
        pygame.draw.rect(self.screen, (42, 37, 58), rack, border_radius=10)
        pygame.draw.rect(
            self.screen,
            (125, 98, 145),
            rack,
            width=2,
            border_radius=10,
        )
        for slot_offset in (20, 34):
            pygame.draw.line(
                self.screen,
                (76, 61, 94),
                (rack.x + slot_offset, rack.y + 12),
                (rack.x + slot_offset, rack.bottom - 10),
                width=2,
            )

        base = pygame.Rect(rack.x - 8, rack.bottom - 13, rack.width + 16, 19)
        pygame.draw.rect(self.screen, (31, 29, 45), base, border_radius=6)
        pygame.draw.rect(
            self.screen,
            (108, 92, 129),
            base,
            width=2,
            border_radius=6,
        )

        folder = pygame.Rect(
            rack.x + 18,
            rack.y + 25 - folder_lift,
            rack.width - 32,
            67,
        )
        folder_shadow = folder.move(4, 5)
        pygame.draw.rect(self.screen, (5, 10, 16), folder_shadow, border_radius=7)

        tab = pygame.Rect(folder.x + 5, folder.y - 13, folder.width - 18, 22)
        pygame.draw.rect(self.screen, (111, 72, 142), tab, border_radius=6)
        tab_text = self.card_font.render("DIAGNOSIS", True, COLORS["text"])
        self.screen.blit(tab_text, tab_text.get_rect(center=(tab.centerx, tab.y + 8)))

        pygame.draw.rect(self.screen, (92, 58, 119), folder, border_radius=7)
        pygame.draw.rect(self.screen, (181, 124, 207), folder, width=2, border_radius=7)

        page_rise = round(18 * progress)
        for page_number, page_color in enumerate(((215, 224, 204), (229, 235, 216))):
            page = pygame.Rect(
                folder.x + 10 + page_number * 5,
                folder.y + 11 - page_rise - page_number * 3,
                folder.width - 20,
                43,
            )
            pygame.draw.rect(self.screen, page_color, page, border_radius=4)
            pygame.draw.rect(
                self.screen,
                COLORS["card_text"],
                page,
                width=1,
                border_radius=4,
            )
            pygame.draw.line(
                self.screen,
                (146, 159, 144),
                (page.x + 7, page.y + 13),
                (page.right - 7, page.y + 13),
            )
            pygame.draw.line(
                self.screen,
                (146, 159, 144),
                (page.x + 7, page.y + 22),
                (page.right - 15, page.y + 22),
            )

        cover_y = folder.y + 20 + round(13 * progress)
        cover_height = max(27, folder.bottom - cover_y)
        cover = pygame.Rect(folder.x, cover_y, folder.width, cover_height)
        pygame.draw.rect(self.screen, (126, 78, 151), cover, border_radius=7)
        pygame.draw.rect(
            self.screen,
            (204, 145, 226),
            cover,
            width=2,
            border_radius=7,
        )

        seal_center = (cover.centerx, cover.y + min(16, cover.height // 2))
        pygame.draw.circle(self.screen, (216, 159, 238), seal_center, 8)
        warning_text = self.card_font.render("!", True, (43, 31, 60))
        self.screen.blit(warning_text, warning_text.get_rect(center=seal_center))

        if self.showing_diagnosis_hand:
            return_button = pygame.Rect(panel.x + 24, panel.bottom - 28, panel.width - 48, 23)
            return_hovered = return_button.collidepoint(mouse_position)
            button_color = COLORS["accent"] if return_hovered else (151, 101, 180)
            pygame.draw.rect(self.screen, button_color, return_button, border_radius=6)
            return_text = self.pile_font.render(
                "<  RETURN TO TESTS",
                True,
                COLORS["background"],
            )
            self.screen.blit(return_text, return_text.get_rect(center=return_button.center))
        elif hovered:
            open_text = self.pile_font.render("OPEN FILE", True, COLORS["accent"])
            self.screen.blit(
                open_text,
                open_text.get_rect(center=(panel.centerx, panel.bottom - 8)),
            )

    def get_diagnosis_folder_progress(self):
        """Return the eased opening progress for the diagnosis folder animation."""

        if not self.showing_diagnosis_hand:
            return 0.0
        if self.diagnosis_folder_animation_started_at is None:
            return 1.0
        elapsed = pygame.time.get_ticks() - self.diagnosis_folder_animation_started_at
        progress = min(1.0, elapsed / self.diagnosis_folder_animation_duration)
        return 1 - (1 - progress) ** 3

    def draw_diagnosis_confirmation(self):
        """Draw a modal that asks the player to confirm the selected diagnosis."""

        if self.selected_card_index is None:
            return

        diagnosis = self.player.diagnosis_hand[self.selected_card_index].value
        dim = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        dim.fill((3, 7, 12, 205))
        self.screen.blit(dim, (0, 0))

        panel = pygame.Rect(245, 155, 610, 335)
        pygame.draw.rect(self.screen, (3, 8, 12), panel.move(8, 9), border_radius=16)
        pygame.draw.rect(self.screen, (40, 28, 52), panel, border_radius=16)
        pygame.draw.rect(self.screen, (204, 145, 226), panel, width=3, border_radius=16)

        warning_circle = (panel.centerx, panel.y + 48)
        pygame.draw.circle(self.screen, (216, 159, 238), warning_circle, 22)
        warning_mark = self.heading_font.render("!", True, (43, 31, 60))
        self.screen.blit(warning_mark, warning_mark.get_rect(center=warning_circle))

        heading = self.heading_font.render(
            "FINAL DIAGNOSIS CONFIRMATION",
            True,
            COLORS["text"],
        )
        self.screen.blit(heading, heading.get_rect(center=(panel.centerx, panel.y + 93)))

        diagnosis_name = self.heading_font.render(
            diagnosis.name,
            True,
            (216, 159, 238),
        )
        self.screen.blit(
            diagnosis_name,
            diagnosis_name.get_rect(center=(panel.centerx, panel.y + 142)),
        )

        question = self.body_font.render(
            f"Submit {diagnosis.name} as your final diagnosis?",
            True,
            COLORS["text"],
        )
        self.screen.blit(question, question.get_rect(center=(panel.centerx, panel.y + 186)))

        warning = self.small_font.render(
            "An incorrect diagnosis will return you to the examination.",
            True,
            COLORS["muted"],
        )
        self.screen.blit(warning, warning.get_rect(center=(panel.centerx, panel.y + 222)))

        mouse_position = pygame.mouse.get_pos()
        cancel_color = (
            (120, 126, 139)
            if self.diagnosis_cancel_button.collidepoint(mouse_position)
            else (79, 83, 98)
        )
        confirm_color = (
            COLORS["accent"]
            if self.diagnosis_confirm_button.collidepoint(mouse_position)
            else (151, 101, 180)
        )
        pygame.draw.rect(
            self.screen,
            cancel_color,
            self.diagnosis_cancel_button,
            border_radius=8,
        )
        pygame.draw.rect(
            self.screen,
            confirm_color,
            self.diagnosis_confirm_button,
            border_radius=8,
        )

        cancel_text = self.body_font.render("GO BACK", True, COLORS["text"])
        confirm_text = self.body_font.render(
            "SUBMIT DIAGNOSIS",
            True,
            COLORS["background"],
        )
        self.screen.blit(
            cancel_text,
            cancel_text.get_rect(center=self.diagnosis_cancel_button.center),
        )
        self.screen.blit(
            confirm_text,
            confirm_text.get_rect(center=self.diagnosis_confirm_button.center),
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

    def draw_notebook_screen(self):
        """Dim the workspace and draw a decorated field-notebook spread."""

        dim = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        dim.fill((0, 0, 0, 185))
        self.screen.blit(dim, (0, 0))

        layout = self.notebook_layout
        book = layout["book"]
        pygame.draw.rect(self.screen, (4, 9, 13), book.move(9, 11), border_radius=16)
        pygame.draw.rect(self.screen, (70, 48, 88), book, border_radius=16)
        pygame.draw.rect(
            self.screen,
            (190, 132, 211),
            book,
            width=3,
            border_radius=16,
        )

        left_page = pygame.Rect(
            book.x + 14,
            book.y + 14,
            book.width // 2 - 14,
            book.height - 28,
        )
        right_page = pygame.Rect(
            book.centerx,
            book.y + 14,
            book.width // 2 - 14,
            book.height - 28,
        )
        self.draw_notebook_paper(left_page, (244, 239, 214))
        self.draw_notebook_paper(right_page, (240, 235, 209))

        spine = pygame.Rect(book.centerx - 8, book.y + 13, 16, book.height - 26)
        pygame.draw.rect(self.screen, (51, 42, 60), spine)
        pygame.draw.line(
            self.screen,
            (124, 103, 133),
            (spine.x + 3, spine.y),
            (spine.x + 3, spine.bottom),
            width=2,
        )
        pygame.draw.line(
            self.screen,
            (26, 31, 34),
            (spine.right - 3, spine.y),
            (spine.right - 3, spine.bottom),
            width=2,
        )
        for stitch_y in range(spine.y + 18, spine.bottom - 10, 28):
            pygame.draw.line(
                self.screen,
                (194, 174, 150),
                (spine.x + 5, stitch_y),
                (spine.right - 5, stitch_y + 7),
                width=2,
            )

        tab_data = (
            ("PATIENT FILE", pygame.Rect(left_page.x + 24, left_page.y - 5, 118, 25), (126, 78, 151)),
            ("TEST LOG", pygame.Rect(right_page.x + 24, right_page.y - 5, 96, 25), (72, 122, 158)),
        )
        for tab_text, tab, tab_color in tab_data:
            pygame.draw.rect(self.screen, tab_color, tab, border_radius=6)
            label = self.card_font.render(tab_text, True, (249, 240, 222))
            self.screen.blit(label, label.get_rect(center=tab.center))

        left, right = self.get_spread_columns(self.notebook_spread)
        if left is None:
            self.draw_notebook_id_page(layout["left"])
        else:
            self.draw_notebook_column(left, layout["left"], "CONTINUED NOTES")
        self.draw_notebook_column(right, layout["right"], "DIAGNOSTIC LOG")

        left_num = self.notebook_spread * 2 + 1
        for num, key in ((left_num, "left"), (left_num + 1, "right")):
            label = self.card_font.render(f"—  {num}  —", True, (112, 104, 86))
            self.screen.blit(
                label,
                label.get_rect(center=(layout[key].centerx, book.bottom - 22)),
            )

        mouse = pygame.mouse.get_pos()
        buttons = [
            ("CLOSE", layout["close"], True, COLORS["panel_border"]),
            ("< PREV", layout["prev"], self.notebook_spread > 0, (151, 101, 180)),
            (
                "NEXT >",
                layout["next"],
                self.notebook_spread < self.notebook_spread_count() - 1,
                (151, 101, 180),
            ),
        ]
        for text, rect, enabled, resting_color in buttons:
            if not enabled:
                continue
            color = COLORS["accent"] if rect.collidepoint(mouse) else resting_color
            pygame.draw.rect(self.screen, (20, 24, 29), rect.move(3, 4), border_radius=7)
            pygame.draw.rect(self.screen, color, rect, border_radius=6)
            label = self.small_font.render(text, True, COLORS["background"])
            self.screen.blit(label, label.get_rect(center=rect.center))

    def draw_notebook_paper(self, page, paper_color):
        """Draw one warm ruled page with stacked edges and a folded corner."""

        for offset in (6, 3):
            pygame.draw.rect(
                self.screen,
                (204, 198, 173),
                page.move(0, offset),
                border_radius=7,
            )
        pygame.draw.rect(self.screen, paper_color, page, border_radius=7)
        pygame.draw.rect(
            self.screen,
            (202, 194, 166),
            page,
            width=1,
            border_radius=7,
        )
        for line_y in range(page.y + 62, page.bottom - 18, 25):
            pygame.draw.line(
                self.screen,
                (203, 216, 203),
                (page.x + 18, line_y),
                (page.right - 18, line_y),
                width=1,
            )
        pygame.draw.line(
            self.screen,
            (224, 169, 163),
            (page.x + 31, page.y + 42),
            (page.x + 31, page.bottom - 18),
            width=1,
        )
        fold = (
            (page.right - 25, page.y),
            (page.right, page.y),
            (page.right, page.y + 25),
        )
        pygame.draw.polygon(self.screen, (218, 211, 184), fold)
        pygame.draw.line(
            self.screen,
            (187, 181, 158),
            (page.right - 25, page.y),
            (page.right, page.y + 25),
        )

    def draw_notebook_column(self, column, rect, page_heading):
        """Draw test results as clipped diagnostic entries on a ruled page."""

        ink = (54, 68, 67)
        heading = self.notebook_title_font.render(page_heading, True, ink)
        heading_y = rect.y + 18
        self.screen.blit(heading, (rect.x + 5, heading_y))
        entry_count = sum(
            1
            for kind, text, _ in column
            if kind == "title" and text.upper() != "NO TESTS"
        )
        count_text = (
            "NO RECORDS"
            if entry_count == 0
            else f"{entry_count} RECORD" + ("" if entry_count == 1 else "S")
        )
        count_label = self.card_font.render(
            count_text,
            True,
            (103, 117, 108),
        )
        self.screen.blit(
            count_label,
            count_label.get_rect(midright=(rect.right - 5, heading_y + 14)),
        )

        content = pygame.Rect(rect.x, rect.y + 63, rect.width, rect.height - 63)
        groups = []
        current_group = []
        for item in column:
            if item[0] == "title" and current_group:
                groups.append(current_group)
                current_group = []
            current_group.append(item)
        if current_group:
            groups.append(current_group)

        test_colors = {
            "TEMPERATURE": COLORS["panel_border"],
            "ULTRASOUND": (85, 145, 230),
            "X-RAY": (67, 178, 132),
            "ALLERGY": (191, 91, 211),
            "NO TESTS": (151, 101, 180),
        }
        for group in groups:
            title = group[0][1]
            first_y = group[0][2]
            last_kind, _, last_y = group[-1]
            last_height = (
                self.notebook_title_font.get_linesize()
                if last_kind == "title"
                else self.notebook_body_font.get_linesize()
            )
            card = pygame.Rect(
                content.x,
                content.y + first_y,
                content.width,
                max(58, last_y - first_y + last_height + 12),
            )
            accent = test_colors.get(title.upper(), COLORS["panel_border"])
            pygame.draw.rect(self.screen, (231, 227, 204), card, border_radius=8)
            pygame.draw.rect(self.screen, accent, card, width=2, border_radius=8)
            pygame.draw.rect(
                self.screen,
                accent,
                pygame.Rect(card.x, card.y, 6, card.height),
                border_radius=4,
            )
            icon = pygame.Rect(card.x + 15, card.y + 10, 33, 33)
            pygame.draw.rect(self.screen, (205, 216, 204), icon, border_radius=5)
            pygame.draw.rect(self.screen, accent, icon, width=2, border_radius=5)
            if title.upper() in TEST_SUBTITLES:
                self.draw_test_icon(title.upper(), icon, accent)
            else:
                question = self.small_font.render("?", True, accent)
                self.screen.blit(question, question.get_rect(center=icon.center))

            title_surface = self.notebook_title_font.render(title, True, ink)
            self.screen.blit(title_surface, (card.x + 57, card.y + 8))
            for kind, text, y in group[1:]:
                if kind != "body":
                    continue
                surface = self.notebook_body_font.render(text, True, (72, 91, 84))
                self.screen.blit(surface, (card.x + 57, content.y + y + 5))

    def draw_notebook_id_page(self, rect):
        """Draw a patient header and two clipped information cards."""

        ink = (54, 68, 67)
        header = pygame.Rect(rect.x, rect.y, rect.width, 58)
        pygame.draw.rect(self.screen, (229, 221, 204), header, border_radius=9)
        pygame.draw.rect(
            self.screen,
            (151, 101, 180),
            header,
            width=2,
            border_radius=9,
        )
        portrait = pygame.Rect(header.x + 9, header.y + 7, 44, 44)
        self.draw_notebook_patient_stamp(portrait)
        name = self.heading_font.render(self.patient.name, True, ink)
        self.screen.blit(name, name.get_rect(midleft=(portrait.right + 10, header.centery - 5)))
        case_id = self.card_font.render("CASE BLP-004-ZV", True, (111, 91, 124))
        self.screen.blit(case_id, case_id.get_rect(midleft=(portrait.right + 11, header.centery + 17)))

        y = header.bottom + 12
        y = self.draw_notebook_info_section(
            "INTERGALACTIC ID",
            self.patient.profile.items(),
            rect,
            y,
            (72, 122, 158),
        )
        self.draw_notebook_info_section(
            "HEALTH ID",
            self.patient.medical_info.items(),
            rect,
            y + 10,
            (126, 78, 151),
        )

    def draw_notebook_patient_stamp(self, portrait):
        """Draw a tiny stamped portrait of the current alien patient."""

        pygame.draw.rect(self.screen, (205, 190, 219), portrait, border_radius=6)
        pygame.draw.rect(self.screen, (126, 78, 151), portrait, width=2, border_radius=6)
        head_center = (portrait.centerx, portrait.y + 19)
        pygame.draw.line(
            self.screen,
            (70, 43, 94),
            (head_center[0] - 8, head_center[1] - 9),
            (head_center[0] - 11, head_center[1] - 15),
            width=2,
        )
        pygame.draw.line(
            self.screen,
            (70, 43, 94),
            (head_center[0] + 8, head_center[1] - 9),
            (head_center[0] + 11, head_center[1] - 15),
            width=2,
        )
        pygame.draw.circle(self.screen, (151, 99, 211), (head_center[0] - 11, head_center[1] - 15), 3)
        pygame.draw.circle(self.screen, (151, 99, 211), (head_center[0] + 11, head_center[1] - 15), 3)
        pygame.draw.ellipse(
            self.screen,
            (151, 99, 211),
            pygame.Rect(head_center[0] - 13, head_center[1] - 10, 26, 22),
        )
        pygame.draw.circle(self.screen, (50, 35, 68), (head_center[0] - 5, head_center[1]), 2)
        pygame.draw.circle(self.screen, (50, 35, 68), (head_center[0] + 5, head_center[1]), 2)
        pygame.draw.ellipse(
            self.screen,
            (151, 99, 211),
            pygame.Rect(portrait.centerx - 9, portrait.y + 29, 18, 13),
        )

    def draw_notebook_info_section(self, heading, items, rect, y, accent):
        """Draw one labeled patient-information card and return its bottom edge."""

        body_h = self.notebook_body_font.get_linesize()
        rows = []
        for label, value in items:
            rows.extend(
                self.wrap_text(
                    f"{label}: {value}",
                    self.notebook_body_font,
                    rect.width - 42,
                )
            )
        section = pygame.Rect(rect.x, y, rect.width, 36 + len(rows) * body_h + 8)
        pygame.draw.rect(self.screen, (231, 227, 204), section, border_radius=8)
        pygame.draw.rect(self.screen, accent, section, width=2, border_radius=8)
        title_bar = pygame.Rect(section.x, section.y, section.width, 30)
        pygame.draw.rect(self.screen, accent, title_bar, border_radius=8)
        pygame.draw.rect(
            self.screen,
            accent,
            pygame.Rect(title_bar.x, title_bar.bottom - 8, title_bar.width, 8),
        )
        title = self.card_font.render(heading, True, (249, 240, 222))
        self.screen.blit(title, title.get_rect(midleft=(title_bar.x + 12, title_bar.centery)))

        row_y = title_bar.bottom + 6
        for row_index, row in enumerate(rows):
            pygame.draw.circle(self.screen, accent, (section.x + 15, row_y + body_h // 2), 3)
            surface = self.notebook_body_font.render(row, True, (72, 91, 84))
            self.screen.blit(surface, (section.x + 25, row_y))
            row_y += body_h
            if row_index < len(rows) - 1:
                pygame.draw.line(
                    self.screen,
                    (205, 201, 180),
                    (section.x + 25, row_y - 2),
                    (section.right - 12, row_y - 2),
                )
        return section.bottom

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

    def build_notebook_columns(self):
        """Split the patient's test entries into page-sized columns.

        Each column is a list of (kind, text, y_offset) tuples.
        """
        width = self.notebook_layout["right"].width - 73
        height = self.notebook_layout["right"].height - 63
        title_h = self.notebook_title_font.get_linesize()
        body_h = self.notebook_body_font.get_linesize()
        card_gap = 10
        columns = [[]]
        used = 0
        for test_name, result in self.notebook.get_entries(self.patient).items():
            result_lines = self.wrap_text(result, self.notebook_body_font, width)
            card_height = max(58, title_h + len(result_lines) * body_h + 12)
            if columns[-1] and used + card_height > height:
                columns.append([])
                used = 0

            start_y = used
            columns[-1].append(("title", test_name.upper(), start_y))
            for line_index, line in enumerate(result_lines):
                columns[-1].append(
                    ("body", line, start_y + title_h + line_index * body_h)
                )
            used += card_height + card_gap

        self.notebook_columns = columns

    def notebook_spread_count(self):
        """Return the number of two-page spreads needed for all notebook columns."""

        extra = max(0, len(self.notebook_columns) - 1)
        return 1 + (extra + 1) // 2  # ceil(extra / 2)

    def get_spread_columns(self, spread):
        """Return (left, right) for a spread; left is None for the ID page."""
        cols = self.notebook_columns
        if spread == 0:
            return None, cols[0]
        left_i, right_i = 2 * spread - 1, 2 * spread
        left = cols[left_i] if left_i < len(cols) else []
        right = cols[right_i] if right_i < len(cols) else []
        return left, right

    def open_notebook(self):
        """Rebuild the current notes and open the notebook at its first spread."""

        self.build_notebook_columns()  # rebuild so new results appear
        self.notebook_spread = 0
        self.state = GameState.NOTEBOOK

    def flip_notebook(self, direction):
        """Move one notebook spread left or right when the destination exists."""

        new_spread = self.notebook_spread + direction
        if 0 <= new_spread < self.notebook_spread_count():
            self.notebook_spread = new_spread

    def handle_notebook_click(self, position):
        """Handle notebook close and page-navigation button clicks."""

        if self.notebook_layout["close"].collidepoint(position):
            self.state = GameState.PATIENT
        elif self.notebook_layout["prev"].collidepoint(position):
            self.flip_notebook(-1)
        elif self.notebook_layout["next"].collidepoint(position):
            self.flip_notebook(1)

def main():
    """Create and start the game"""

    AlienDoctorGUI().run()


if __name__ == "__main__":
    main()
