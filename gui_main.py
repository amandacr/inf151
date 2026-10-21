"""Minimal Pygame shell for The Cosmic Clinic GUI prototype.

you can run this file without changing the old text based version.
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


class GameState(Enum):
    """Screens planned for the GUI version of the prototype."""

    INTRO = auto()
    TITLE = auto()
    PATIENT = auto()
    TEST_RESULT = auto()
    OUTCOME = auto()
    NOTEBOOK = auto()
    SHOP = auto()
    CELEBRATION = auto()


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
        self.card_message = ""
        self.run_test_button = None
        self.discard_button = None
        self.play_diagnosis_button = None
        self.diagnosis_confirmation_open = False
        self.diagnosis_folder_animation_started_at = None
        self.diagnosis_folder_animation_duration = 360
        self.discard_pile = []
        self.discard_animation = None
        self.discard_animation_duration = 350
        self.last_test_name = ""
        self.last_test_result = ""
        self.last_diagnosis = None
        self.diagnosis_correct = None
        self.celebration_started_at = None
        self.celebration_duration = 2400
        self.firework_particles = []
        self.reception_transition_started_at = None
        self.reception_transition_duration = 3350
        self.reception_fade_duration = 650
        self.patient_fade_started_at = None
        self.patient_fade_duration = 650
        self.start_button = pygame.Rect(61, 505, 238, 43)
        self.continue_button = pygame.Rect(410, 430, 280, 52)
        self.outcome_button = pygame.Rect(410, 455, 280, 52)
        self.shop_button = pygame.Rect(400, 465, 300, 52)
        self.diagnosis_cancel_button = pygame.Rect(315, 410, 210, 48)
        self.diagnosis_confirm_button = pygame.Rect(575, 410, 210, 48)
        self.layout = {
            "status_bar": pygame.Rect(30, 100, 1040, 50),
            "draw_deck": pygame.Rect(45, 180, 125, 175),
            "alien": pygame.Rect(250, 165, 230, 195),
            "id_card": pygame.Rect(510, 180, 270, 155),
            "throwaway": pygame.Rect(910, 250, 125, 120),
            "notebook": pygame.Rect(40, 410, 155, 150),
            "active_hand": pygame.Rect(225, 390, 625, 170),
            "diagnosis": pygame.Rect(885, 400, 175, 160),
        }
        self.card_rects = self.build_card_rects()
        self.notebook_layout = self.build_notebook_rects()

        self.title_font = pygame.font.Font(None, 64)
        self.heading_font = pygame.font.Font(None, 38)
        self.body_font = pygame.font.Font(None, 26)
        self.small_font = pygame.font.Font(None, 20)
        self.card_font = pygame.font.Font(None, 17)
        self.pile_font = pygame.font.Font(None, 14)
        self.tiny_font = pygame.font.Font(None, 10)
        self.diagnosis_name_font = pygame.font.SysFont("Arial", 21, bold=True)
        self.diagnosis_card_font = pygame.font.SysFont("Arial", 13, bold=True)
        self.notebook_title_font = pygame.font.Font(None, 28)
        self.notebook_body_font = pygame.font.Font(None, 22)

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
                elif self.state == GameState.CELEBRATION:
                    self.finish_celebration()
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
                elif event.key == pygame.K_RETURN and self.state == GameState.CELEBRATION:
                    self.finish_celebration()
                elif event.key == pygame.K_LEFT and self.state == GameState.NOTEBOOK:
                    self.flip_notebook(-1)
                elif event.key == pygame.K_RIGHT and self.state == GameState.NOTEBOOK:
                    self.flip_notebook(1)

    def handle_patient_click(self, position):
        """Handle ID-card and test-card clicks on the patient screen."""

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
        self.card_message = ""
        self.card_rects = self.build_card_rects()

    def build_card_rects(self):
        """Create the rectangles that position the currently displayed cards."""

        panel = self.layout["active_hand"]
        card_width = 96
        card_height = 118
        gap = 18
        card_count = len(self.get_active_hand())

        if card_count == 0:
            return []

        total_width = (card_width * card_count) + (gap * (card_count - 1))
        start_x = panel.centerx - total_width // 2

        return [
            pygame.Rect(
                start_x + index * (card_width + gap),
                panel.y + 43,
                card_width,
                card_height,
            )
            for index in range(card_count)
        ]

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
                self.card_message = ""
                return

        for index in reversed(range(len(self.card_rects))):
            if self.card_rects[index].collidepoint(position):
                self.selected_card_index = index
                self.card_message = ""
                return

        if self.selected_card_index is not None:
            self.selected_card_index = None
            self.card_message = ""

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
        self.discard_pile.append(card)
        self.selected_card_index = None
        self.run_test_button = None
        self.card_rects = self.build_card_rects()
        self.card_message = self.last_test_name + " test complete"
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
        self.card_rects = self.build_card_rects()
        self.card_message = card.value.name + " discarded"

    def handle_test_result_click(self, position):
        """Return to the patient workspace when the result screen is continued."""

        if self.continue_button.collidepoint(position):
            self.state = GameState.PATIENT

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
                self.start_celebration()
            else:
                self.switch_active_hand(False)
                self.card_message = "Diagnosis incorrect - continue testing"
                self.state = GameState.PATIENT

    def start_celebration(self):
        """Start a short multicolored firework animation before opening the shop."""

        self.celebration_started_at = pygame.time.get_ticks()
        self.firework_particles = []
        firework_colors = (
            (255, 82, 95),
            (70, 150, 255),
            (177, 92, 255),
            (255, 198, 75),
            (70, 235, 205),
        )
        bursts = (
            ((220, 245), 0),
            ((875, 255), 250),
            ((350, 390), 500),
            ((745, 385), 750),
            ((550, 220), 1000),
        )

        for burst_number, (origin, delay) in enumerate(bursts):
            color = firework_colors[burst_number % len(firework_colors)]
            for particle_number in range(28):
                angle = (
                    2 * math.pi * particle_number / 28
                    + random.uniform(-0.06, 0.06)
                )
                speed = random.uniform(75, 145)
                self.firework_particles.append(
                    {
                        "origin": origin,
                        "delay": delay,
                        "velocity": (
                            math.cos(angle) * speed,
                            math.sin(angle) * speed,
                        ),
                        "color": color,
                        "size": random.randint(2, 4),
                        "lifetime": random.uniform(0.9, 1.25),
                    }
                )

        self.state = GameState.CELEBRATION

    def finish_celebration(self):
        """Skip or finish the celebration and open the shop."""

        self.firework_particles = []
        self.celebration_started_at = None
        self.state = GameState.SHOP

    def update(self):
        """Advance timed GUI transitions without pausing the event loop."""

        if self.state == GameState.INTRO:
            elapsed = pygame.time.get_ticks() - self.intro_started_at
            if elapsed >= self.intro_duration:
                self.finish_intro()
            return

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
            return

        if self.state != GameState.CELEBRATION:
            return
        if self.celebration_started_at is None:
            self.start_celebration()
            return

        elapsed = pygame.time.get_ticks() - self.celebration_started_at
        if elapsed >= self.celebration_duration:
            self.finish_celebration()

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
        self.card_message = ""
        self.run_test_button = None
        self.discard_button = None
        self.play_diagnosis_button = None
        self.diagnosis_confirmation_open = False
        self.diagnosis_folder_animation_started_at = None
        self.discard_pile = []
        self.discard_animation = None
        self.last_test_name = ""
        self.last_test_result = ""
        self.last_diagnosis = None
        self.diagnosis_correct = None
        self.celebration_started_at = None
        self.firework_particles = []
        self.reception_transition_started_at = None
        self.patient_fade_started_at = None
        self.card_rects = self.build_card_rects()

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

        title = self.title_font.render(
            "T H E   C O S M I C   C L I N I C",
            True,
            COLORS["accent"],
        )
        self.screen.blit(title, title.get_rect(center=(WINDOW_SIZE[0] // 2, 42)))

        subtitle_text = (
            "RECEPTION  •  SHIFT 01"
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
        elif self.state == GameState.CELEBRATION:
            self.draw_celebration_screen()

        footer_text = (
            "Press Esc to go back"
            if self.diagnosis_confirmation_open
            else "Press Esc to quit"
        )
        quit_hint = self.small_font.render(footer_text, True, COLORS["muted"])
        self.screen.blit(quit_hint, quit_hint.get_rect(center=(WINDOW_SIZE[0] // 2, 635)))
        self.draw_reception_transition_fade()

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

        title_text = "THE COSMIC CLINIC"
        shadow = self.title_font.render(title_text, True, (16, 45, 51))
        title = self.title_font.render(title_text, True, COLORS["accent"])
        scaled_size = (
            max(1, round(title.get_width() * title_scale)),
            max(1, round(title.get_height() * title_scale)),
        )
        scaled_shadow = pygame.transform.smoothscale(shadow, scaled_size)
        scaled_title = pygame.transform.smoothscale(title, scaled_size)
        scaled_title.set_alpha(round(255 * progress))
        scaled_shadow.set_alpha(round(190 * progress))

        title_center = (WINDOW_SIZE[0] // 2, 64)
        self.screen.blit(
            scaled_shadow,
            scaled_shadow.get_rect(center=(title_center[0] + 4, title_center[1] + 5)),
        )
        self.screen.blit(scaled_title, scaled_title.get_rect(center=title_center))

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
            "SHIFT 01     MONEY: $" + str(self.player.balance),
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
        self.draw_alien_placeholder()
        self.draw_id_card()
        self.draw_throwaway_deck()
        self.draw_notebook()
        self.draw_active_hand()
        self.draw_diagnosis_cards()
        self.draw_discard_animation()
        if self.diagnosis_confirmation_open:
            self.draw_diagnosis_confirmation()

    def draw_test_result_screen(self):
        """Draw the completed test report and a button back to the patient screen."""

        panel = pygame.Rect(180, 125, 740, 405)
        self.draw_panel(panel)

        test_name = self.last_test_name or "TEST"
        heading = self.heading_font.render(
            test_name + " RESULTS", True, COLORS["text"]
        )
        self.screen.blit(heading, heading.get_rect(center=(panel.centerx, 175)))

        patient = self.small_font.render(
            "PATIENT: " + self.patient.name, True, COLORS["muted"]
        )
        self.screen.blit(patient, patient.get_rect(center=(panel.centerx, 205)))

        report = pygame.Rect(255, 230, 590, 145)
        pygame.draw.rect(self.screen, COLORS["card"], report, border_radius=8)
        pygame.draw.rect(
            self.screen,
            COLORS["panel_border"],
            report,
            width=3,
            border_radius=8,
        )

        report_title = self.small_font.render(
            "MEDICAL TEST REPORT", True, COLORS["card_text"]
        )
        self.screen.blit(
            report_title,
            report_title.get_rect(center=(report.centerx, report.y + 25)),
        )

        result_text = self.last_test_result or "No test has been run yet."
        result_y = report.y + 57
        for line in result_text.splitlines():
            result_line = self.body_font.render(line, True, COLORS["card_text"])
            self.screen.blit(
                result_line,
                result_line.get_rect(center=(report.centerx, result_y)),
            )
            result_y += 32

        note = self.small_font.render(
            "The used card was moved to the throwaway pile.",
            True,
            COLORS["muted"],
        )
        self.screen.blit(note, note.get_rect(center=(panel.centerx, 402)))

        hovered = self.continue_button.collidepoint(pygame.mouse.get_pos())
        button_color = COLORS["accent"] if hovered else COLORS["panel_border"]
        pygame.draw.rect(
            self.screen, button_color, self.continue_button, border_radius=8
        )
        button_text = self.body_font.render(
            "CONTINUE", True, COLORS["background"]
        )
        self.screen.blit(
            button_text, button_text.get_rect(center=self.continue_button.center)
        )

    def draw_diagnosis_outcome(self):
        """Draw the result of the diagnosis card most recently played."""

        panel = pygame.Rect(180, 125, 740, 405)
        self.draw_panel(panel)

        correct = bool(self.diagnosis_correct)
        heading_text = "CORRECT DIAGNOSIS" if correct else "INCORRECT DIAGNOSIS"
        heading_color = COLORS["accent"] if correct else (245, 130, 115)
        heading = self.heading_font.render(heading_text, True, heading_color)
        self.screen.blit(heading, heading.get_rect(center=(panel.centerx, 175)))

        diagnosis_name = self.last_diagnosis.name if self.last_diagnosis else "Unknown"
        played = self.body_font.render(
            "You played: " + diagnosis_name,
            True,
            COLORS["text"],
        )
        self.screen.blit(played, played.get_rect(center=(panel.centerx, 220)))

        if correct:
            message = (
                f"You correctly diagnosed {self.patient.name}. "
                f"Recommended treatment: {self.last_diagnosis.treatment}"
            )
        else:
            message = (
                f"{diagnosis_name} does not match the available evidence. "
                "Return to the patient and gather more information before trying again."
            )

        message_box = pygame.Rect(panel.x + 80, 255, panel.width - 160, 125)
        self.draw_wrapped_text(
            message,
            self.body_font,
            COLORS["muted"],
            message_box,
            line_spacing=8,
        )

        hovered = self.outcome_button.collidepoint(pygame.mouse.get_pos())
        button_color = COLORS["accent"] if hovered else COLORS["panel_border"]
        pygame.draw.rect(
            self.screen,
            button_color,
            self.outcome_button,
            border_radius=8,
        )
        button_label = (
            "CONTINUE TO SHOP" if correct else "RETURN TO PATIENT"
        )
        button_text = self.body_font.render(
            button_label,
            True,
            COLORS["background"],
        )
        self.screen.blit(
            button_text,
            button_text.get_rect(center=self.outcome_button.center),
        )

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

    def draw_celebration_screen(self):
        """Draw the correct-diagnosis message and animated firework particles."""

        panel = pygame.Rect(190, 145, 720, 360)
        self.draw_panel(panel)
        self.draw_fireworks()

        heading = self.title_font.render(
            "D I A G N O S I S   C O R R E C T!",
            True,
            COLORS["accent"],
        )
        self.screen.blit(heading, heading.get_rect(center=(panel.centerx, 230)))

        patient_message = self.heading_font.render(
            self.patient.name + " is going to be okay!",
            True,
            COLORS["text"],
        )
        self.screen.blit(
            patient_message,
            patient_message.get_rect(center=(panel.centerx, 290)),
        )

        shop_message = self.body_font.render(
            "Opening the Intergalactic Supply Shop...",
            True,
            COLORS["muted"],
        )
        self.screen.blit(
            shop_message,
            shop_message.get_rect(center=(panel.centerx, 340)),
        )

        elapsed = pygame.time.get_ticks() - (self.celebration_started_at or 0)
        progress = min(1.0, elapsed / self.celebration_duration)
        progress_back = pygame.Rect(panel.x + 150, 385, panel.width - 300, 12)
        progress_fill = progress_back.copy()
        progress_fill.width = round(progress_back.width * progress)
        pygame.draw.rect(
            self.screen,
            COLORS["background"],
            progress_back,
            border_radius=6,
        )
        pygame.draw.rect(
            self.screen,
            COLORS["accent"],
            progress_fill,
            border_radius=6,
        )

        skip = self.small_font.render(
            "Click or press Enter to skip",
            True,
            COLORS["muted"],
        )
        self.screen.blit(skip, skip.get_rect(center=(panel.centerx, 435)))

    def draw_fireworks(self):
        """Draw every currently visible firework particle with a fading trail."""

        if self.celebration_started_at is None:
            return

        elapsed_ms = pygame.time.get_ticks() - self.celebration_started_at
        gravity = 85
        for particle in self.firework_particles:
            age = (elapsed_ms - particle["delay"]) / 1000
            if age < 0 or age > particle["lifetime"]:
                continue

            origin_x, origin_y = particle["origin"]
            velocity_x, velocity_y = particle["velocity"]
            x = origin_x + velocity_x * age
            y = origin_y + velocity_y * age + gravity * age * age / 2
            previous_age = max(0, age - 0.045)
            previous_x = origin_x + velocity_x * previous_age
            previous_y = (
                origin_y
                + velocity_y * previous_age
                + gravity * previous_age * previous_age / 2
            )

            fade = max(0, 1 - age / particle["lifetime"])
            color = tuple(
                round(
                    COLORS["panel"][channel]
                    + (particle["color"][channel] - COLORS["panel"][channel])
                    * fade
                )
                for channel in range(3)
            )
            pygame.draw.line(
                self.screen,
                color,
                (round(previous_x), round(previous_y)),
                (round(x), round(y)),
                width=max(1, particle["size"] - 1),
            )
            pygame.draw.circle(
                self.screen,
                color,
                (round(x), round(y)),
                particle["size"],
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

        planet = pygame.Rect(window.right - 190, window.y + 26, 145, 145)
        pygame.draw.ellipse(self.screen, (83, 70, 132), planet)
        pygame.draw.ellipse(
            self.screen,
            (112, 94, 164),
            pygame.Rect(planet.x + 16, planet.y + 13, 87, 55),
        )
        pygame.draw.arc(
            self.screen,
            (64, 54, 110),
            pygame.Rect(planet.x + 10, planet.y + 64, 121, 47),
            0,
            math.pi,
            width=4,
        )
        pygame.draw.arc(
            self.screen,
            (174, 133, 207),
            planet.inflate(24, -58),
            math.pi,
            math.pi * 2,
            width=4,
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

        for cabinet_x, cabinet_width in ((35, 170), (875, 185)):
            cabinet = pygame.Rect(cabinet_x, 394, cabinet_width, 163)
            pygame.draw.rect(self.screen, (57, 62, 84), cabinet, border_radius=8)
            pygame.draw.rect(
                self.screen,
                (107, 111, 138),
                cabinet,
                width=2,
                border_radius=8,
            )
            pygame.draw.line(
                self.screen,
                (107, 111, 138),
                (cabinet.x + 8, cabinet.centery),
                (cabinet.right - 8, cabinet.centery),
                width=1,
            )
            for handle_y in (cabinet.y + 35, cabinet.y + 115):
                handle = pygame.Rect(cabinet.centerx - 16, handle_y, 32, 4)
                pygame.draw.rect(self.screen, (154, 153, 174), handle, border_radius=2)

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


    def draw_status_bar(self):
        """Draw patient, shift, and balance data on a clinic-monitor display."""

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
        center_text = self.card_message or "SHIFT 01"
        center_font = self.small_font if self.card_message else self.body_font
        shift = center_font.render(center_text, True, COLORS["muted"])
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
        trace_y = display.centery
        trace_x = display.x + 326
        trace_points = (
            (trace_x, trace_y),
            (trace_x + 22, trace_y),
            (trace_x + 30, trace_y - 6),
            (trace_x + 38, trace_y + 10),
            (trace_x + 47, trace_y - 12),
            (trace_x + 58, trace_y),
            (trace_x + 120, trace_y),
        )
        pygame.draw.lines(
            self.screen,
            COLORS["accent"],
            False,
            trace_points,
            width=2,
        )

        self.screen.blit(shift, shift.get_rect(center=(panel.centerx + 75, panel.centery)))
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

    def draw_alien_placeholder(self):
        """Draw the temporary alien standing inside a softly lit examination bay."""

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

        alien_center_x = bay.centerx - 38
        platform = pygame.Rect(alien_center_x - 67, bay.bottom - 20, 134, 17)
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
        head = pygame.Rect(alien_center_x - 29, bay.y + 25, 58, 52)
        body = pygame.Rect(alien_center_x - 23, head.bottom - 3, 46, 43)

        pygame.draw.line(
            self.screen,
            alien_outline,
            (head.centerx - 14, head.y + 7),
            (head.centerx - 22, head.y - 6),
            width=5,
        )
        pygame.draw.line(
            self.screen,
            alien_color,
            (head.centerx - 14, head.y + 7),
            (head.centerx - 22, head.y - 6),
            width=2,
        )
        pygame.draw.line(
            self.screen,
            alien_outline,
            (head.centerx + 14, head.y + 7),
            (head.centerx + 22, head.y - 6),
            width=5,
        )
        pygame.draw.line(
            self.screen,
            alien_color,
            (head.centerx + 14, head.y + 7),
            (head.centerx + 22, head.y - 6),
            width=2,
        )
        for antenna_x in (head.centerx - 22, head.centerx + 22):
            pygame.draw.circle(
                self.screen,
                alien_outline,
                (antenna_x, head.y - 7),
                7,
            )
            pygame.draw.circle(
                self.screen,
                alien_color,
                (antenna_x, head.y - 7),
                5,
            )
            pygame.draw.circle(
                self.screen,
                alien_highlight,
                (antenna_x - 1, head.y - 9),
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
        pygame.draw.ellipse(self.screen, alien_outline, left_eye)
        pygame.draw.ellipse(self.screen, alien_outline, right_eye)
        pygame.draw.circle(self.screen, (245, 245, 255), (left_eye.x + 4, left_eye.y + 4), 2)
        pygame.draw.circle(self.screen, (245, 245, 255), (right_eye.x + 4, right_eye.y + 4), 2)

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

        pygame.draw.circle(
            self.screen,
            (255, 198, 75),
            (body.centerx + 11, body.y + 13),
            5,
        )
        pygame.draw.circle(
            self.screen,
            (255, 236, 164),
            (body.centerx + 10, body.y + 12),
            2,
        )

        monitor = pygame.Rect(bay.right - 38, bay.bottom - 55, 24, 35)
        pygame.draw.rect(self.screen, (13, 45, 50), monitor, border_radius=3)
        pygame.draw.rect(
            self.screen,
            COLORS["panel_border"],
            monitor,
            width=1,
            border_radius=3,
        )
        pygame.draw.line(
            self.screen,
            COLORS["accent"],
            (monitor.x + 4, monitor.centery),
            (monitor.x + 9, monitor.centery - 4),
            width=1,
        )
        pygame.draw.line(
            self.screen,
            COLORS["accent"],
            (monitor.x + 9, monitor.centery - 4),
            (monitor.x + 14, monitor.centery + 5),
            width=1,
        )
        pygame.draw.line(
            self.screen,
            COLORS["accent"],
            (monitor.x + 14, monitor.centery + 5),
            (monitor.right - 4, monitor.centery),
            width=1,
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
        """Animate a manually discarded card moving into the throwaway pile."""

        if self.discard_animation is None:
            return

        elapsed = pygame.time.get_ticks() - self.discard_animation["started_at"]
        progress = min(1.0, elapsed / self.discard_animation_duration)
        eased_progress = 1 - (1 - progress) ** 3
        start_x, start_y = self.discard_animation["start"]
        target = (self.layout["throwaway"].centerx, self.layout["throwaway"].y + 50)
        center_x = start_x + (target[0] - start_x) * eased_progress
        center_y = start_y + (target[1] - start_y) * eased_progress
        width = int(96 - 42 * eased_progress)
        height = int(118 - 84 * eased_progress)
        moving_card = pygame.Rect(0, 0, width, height)
        moving_card.center = (round(center_x), round(center_y))

        pygame.draw.rect(self.screen, COLORS["card"], moving_card, border_radius=6)
        pygame.draw.rect(
            self.screen,
            COLORS["panel_border"],
            moving_card,
            width=2,
            border_radius=6,
        )
        initial = self.body_font.render(
            self.discard_animation["card"].value.name[0],
            True,
            COLORS["card_text"],
        )
        self.screen.blit(initial, initial.get_rect(center=moving_card.center))

        if progress >= 1.0:
            self.discard_animation = None

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

    def get_notebook_preview_lines(self):
        """Turn the current notebook entries into short notes that fit the tiny pages."""

        entries = self.notebook.get_entries(self.patient)
        if not entries or "No tests" in entries:
            return ["NO TESTS YET", "AWAITING RESULTS"]

        preview_lines = []
        for test_name, result in entries.items():
            result_lines = [line.strip() for line in result.splitlines() if line.strip()]
            if test_name.upper() == "TEMPERATURE":
                current = next(
                    (line.split(":", 1)[1].strip() for line in result_lines
                     if line.lower().startswith("current temperature:")),
                    "RECORDED",
                )
                typical = next(
                    (line.split(":", 1)[1].strip() for line in result_lines
                     if line.lower().startswith("typical body temperature:")),
                    None,
                )
                preview_lines.append(f"TEMP: {current}")
                if typical:
                    preview_lines.append(f"NORM: {typical}")
            else:
                summary = "NORMAL" if result_lines and result_lines[0].lower().startswith(
                    "nothing remarkable"
                ) else "RECORDED"
                preview_lines.append(f"{test_name.upper()}: {summary}")

        return preview_lines[:4]

    def draw_notebook(self):
        """Draw a portrait notebook whose front cover swings open on hover."""

        panel = self.layout["notebook"]
        hovered = panel.collidepoint(pygame.mouse.get_pos())
        progress = self.update_notebook_preview_animation(hovered)
        lift = round(7 * progress)

        # Cover the cabinet handle before drawing the heading so no line crosses it.
        label = self.small_font.render("PATIENT NOTES", True, COLORS["muted"])
        label_rect = label.get_rect(center=(panel.centerx, panel.y + 20))
        pygame.draw.rect(
            self.screen,
            (57, 62, 84),
            label_rect.inflate(16, 8),
            border_radius=5,
        )
        self.screen.blit(label, label_rect)

        page_width = 54
        book_height = round(88 - 6 * progress)
        closed_spine_x = panel.centerx - page_width // 2
        spine_x = round(closed_spine_x + (panel.centerx - closed_spine_x) * progress)
        book_y = panel.y + 38 - lift
        book_bottom = book_y + book_height
        left_extent = round(page_width * progress)

        cover_color = (82, 58, 112)
        cover_dark = (54, 39, 78)
        cover_highlight = (171, 123, 203)
        page_color = (240, 237, 211)
        page_edge = (174, 160, 176)
        rule_color = (188, 196, 174)

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
                title = self.pile_font.render("PATIENT", True, (245, 225, 255))
                subtitle = self.pile_font.render("NOTES", True, (245, 225, 255))
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
            for index, note in enumerate(self.get_notebook_preview_lines()):
                page = 0 if index < 2 else 1
                row = index if index < 2 else index - 2
                page_center_x = spine_x + page_width // 2
                if page == 0:
                    page_center_x = spine_x - page_width // 2
                note_surface = self.tiny_font.render(note, True, COLORS["card_text"])
                note_surface.set_alpha(note_alpha)
                note_rect = note_surface.get_rect(
                    center=(page_center_x, book_y + 23 + row * 17)
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
                (right_page.right - 3, book_y + 8),
            )

        if hovered:
            hover_label = self.pile_font.render(
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
        pygame.draw.rect(
            self.screen,
            (5, 12, 18),
            panel.move(5, 6),
            border_radius=14,
        )
        pygame.draw.rect(self.screen, (24, 31, 43), panel, border_radius=14)
        pygame.draw.rect(
            self.screen,
            (71, 69, 92),
            panel,
            width=2,
            border_radius=14,
        )
        pygame.draw.line(
            self.screen,
            (98, 88, 118),
            (panel.x + 20, panel.y + 34),
            (panel.right - 20, panel.y + 34),
            width=1,
        )
        hand_name = (
            "ACTIVE DIAGNOSIS HAND"
            if self.showing_diagnosis_hand
            else "ACTIVE TEST HAND"
        )
        self.draw_centered_label(hand_name, panel, panel.y + 22)

        active_hand = self.get_active_hand()

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
            hovered = card_rect.collidepoint(mouse_position)
            display_rect = card_rect.move(0, -8 if hovered else 0)
            if self.showing_diagnosis_hand:
                self.draw_diagnosis_card(card, display_rect, hovered=hovered)
            else:
                self.draw_test_card(card, display_rect, hovered=hovered)

        if self.selected_card_index is not None:
            selected_card = active_hand[self.selected_card_index]
            selected_rect = self.get_selected_card_rect(self.selected_card_index)
            if self.showing_diagnosis_hand:
                self.draw_diagnosis_card(selected_card, selected_rect, selected=True)
            else:
                self.draw_test_card(selected_card, selected_rect, selected=True)

    def draw_diagnosis_card(self, card, card_rect, hovered=False, selected=False):
        """Draw one diagnosis card in either its compact or enlarged state."""

        diagnosis = card.value
        border_color = (
            COLORS["accent"] if hovered or selected else COLORS["panel_border"]
        )
        border_width = 4 if selected else 3 if hovered else 2

        if selected:
            shadow = card_rect.move(7, 7)
            pygame.draw.rect(self.screen, (3, 8, 10), shadow, border_radius=9)

        pygame.draw.rect(self.screen, COLORS["card"], card_rect, border_radius=8)
        pygame.draw.rect(
            self.screen,
            border_color,
            card_rect,
            width=border_width,
            border_radius=8,
        )

        name_font = (
            self.diagnosis_name_font if selected else self.diagnosis_card_font
        )
        if selected or name_font.size(diagnosis.name)[0] <= card_rect.width - 12:
            name_lines = [diagnosis.name]
        else:
            name_lines = diagnosis.name.split()

        name_y = card_rect.y + 22 if selected else card_rect.y + 14
        for line_number, line in enumerate(name_lines):
            name = name_font.render(line, True, COLORS["card_text"])
            line_y = name_y + line_number * 13
            self.screen.blit(name, name.get_rect(center=(card_rect.centerx, line_y)))

        icon_size = 48 if selected else 40
        icon_y = card_rect.y + 50 if selected else card_rect.y + 42
        icon = pygame.Rect(card_rect.centerx - icon_size // 2, icon_y, icon_size, icon_size)
        pygame.draw.rect(self.screen, (196, 211, 191), icon, border_radius=5)
        pygame.draw.rect(self.screen, COLORS["panel_border"], icon, width=2, border_radius=5)
        icon_text = self.heading_font.render("D", True, COLORS["card_text"])
        self.screen.blit(icon_text, icon_text.get_rect(center=icon.center))

        if selected:
            description_box = pygame.Rect(
                card_rect.x + 18,
                icon.bottom + 10,
                card_rect.width - 36,
                card_rect.bottom - icon.bottom - 55,
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
                COLORS["panel_border"],
                self.play_diagnosis_button,
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
        else:
            label = self.card_font.render("DIAGNOSIS", True, COLORS["panel_border"])
            self.screen.blit(
                label,
                label.get_rect(center=(card_rect.centerx, card_rect.bottom - 17)),
            )

    def draw_test_card(self, card, card_rect, hovered=False, selected=False):
        """Draw one test card in either its compact or enlarged state."""

        test = card.value
        rarity_color = RARITY_COLORS.get(test.rarity, COLORS["panel_border"])
        border_color = COLORS["accent"] if hovered or selected else rarity_color
        border_width = 4 if selected else 3 if hovered else 2

        if selected:
            shadow = card_rect.move(7, 7)
            pygame.draw.rect(self.screen, (3, 8, 10), shadow, border_radius=9)

        pygame.draw.rect(self.screen, COLORS["card"], card_rect, border_radius=8)
        pygame.draw.rect(
            self.screen,
            border_color,
            card_rect,
            width=border_width,
            border_radius=8,
        )

        if selected:
            self.draw_selected_card_details(test, card_rect, rarity_color)
        else:
            self.draw_compact_card(test, card_rect, rarity_color)

    def draw_compact_card(self, test, card_rect, rarity_color):
        """Draw the name, icon, and rarity shown on a card in the hand."""

        name = self.card_font.render(test.name, True, COLORS["card_text"])
        self.screen.blit(name, name.get_rect(center=(card_rect.centerx, card_rect.y + 18)))

        icon = pygame.Rect(card_rect.centerx - 20, card_rect.y + 36, 40, 40)
        pygame.draw.rect(self.screen, (196, 211, 191), icon, border_radius=5)
        pygame.draw.rect(self.screen, rarity_color, icon, width=2, border_radius=5)
        icon_text = self.body_font.render(test.name[0], True, COLORS["card_text"])
        self.screen.blit(icon_text, icon_text.get_rect(center=icon.center))

        rarity = self.card_font.render(test.rarity.upper(), True, rarity_color)
        self.screen.blit(
            rarity, rarity.get_rect(center=(card_rect.centerx, card_rect.bottom - 17))
        )

    def draw_selected_card_details(self, test, card_rect, rarity_color):
        """Draw an enlarged test card with Run Test and Discard buttons."""

        name = self.body_font.render(test.name, True, COLORS["card_text"])
        self.screen.blit(name, name.get_rect(center=(card_rect.centerx, card_rect.y + 20)))

        rarity = self.card_font.render(test.rarity.upper(), True, rarity_color)
        self.screen.blit(rarity, rarity.get_rect(center=(card_rect.centerx, card_rect.y + 42)))

        icon = pygame.Rect(card_rect.x + 18, card_rect.y + 57, 42, 42)
        pygame.draw.rect(self.screen, (196, 211, 191), icon, border_radius=5)
        pygame.draw.rect(self.screen, rarity_color, icon, width=2, border_radius=5)
        icon_text = self.heading_font.render(test.name[0], True, COLORS["card_text"])
        self.screen.blit(icon_text, icon_text.get_rect(center=icon.center))

        description_box = pygame.Rect(
            card_rect.x + 70,
            card_rect.y + 57,
            card_rect.width - 86,
            105,
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

    def draw_diagnosis_cards(self):
        """Draw the animated medical folder used to switch diagnosis cards on or off."""

        panel = self.layout["diagnosis"]
        tray = pygame.Rect(panel.x + 9, panel.y + 12, panel.width - 18, panel.height - 20)
        pygame.draw.rect(self.screen, (5, 12, 18), tray.move(5, 6), border_radius=12)
        pygame.draw.rect(self.screen, (35, 27, 49), tray, border_radius=12)
        pygame.draw.rect(self.screen, (122, 82, 148), tray, width=2, border_radius=12)

        warning = pygame.Rect(tray.x + 12, tray.y + 9, 20, 20)
        pygame.draw.circle(self.screen, (216, 159, 238), warning.center, 9)
        warning_text = self.card_font.render("!", True, (43, 31, 60))
        self.screen.blit(warning_text, warning_text.get_rect(center=warning.center))
        folder_title = self.card_font.render("FINAL DIAGNOSIS", True, COLORS["text"])
        self.screen.blit(
            folder_title,
            folder_title.get_rect(midleft=(warning.right + 5, warning.centery)),
        )

        progress = self.get_diagnosis_folder_progress()
        folder = pygame.Rect(tray.x + 17, tray.y + 49, tray.width - 34, 61)
        folder_shadow = folder.move(4, 5)
        pygame.draw.rect(self.screen, (5, 10, 16), folder_shadow, border_radius=7)

        tab = pygame.Rect(folder.x + 5, folder.y - 12, 69, 22)
        pygame.draw.rect(self.screen, (111, 72, 142), tab, border_radius=6)
        tab_text = self.tiny_font.render("PATIENT FILE", True, COLORS["text"])
        self.screen.blit(tab_text, tab_text.get_rect(center=(tab.centerx, tab.y + 8)))

        pygame.draw.rect(self.screen, (92, 58, 119), folder, border_radius=7)
        pygame.draw.rect(self.screen, (181, 124, 207), folder, width=2, border_radius=7)

        page_rise = round(18 * progress)
        for page_number, page_color in enumerate(((215, 224, 204), (229, 235, 216))):
            page = pygame.Rect(
                folder.x + 13 + page_number * 5,
                folder.y + 10 - page_rise - page_number * 3,
                folder.width - 26,
                43,
            )
            pygame.draw.rect(self.screen, page_color, page, border_radius=4)
            pygame.draw.rect(self.screen, COLORS["card_text"], page, width=1, border_radius=4)
            pygame.draw.line(
                self.screen,
                (146, 159, 144),
                (page.x + 8, page.y + 13),
                (page.right - 8, page.y + 13),
                width=1,
            )
            pygame.draw.line(
                self.screen,
                (146, 159, 144),
                (page.x + 8, page.y + 22),
                (page.right - 17, page.y + 22),
                width=1,
            )

        cover_y = folder.y + 20 + round(13 * progress)
        cover_height = max(27, folder.bottom - cover_y)
        cover = pygame.Rect(folder.x, cover_y, folder.width, cover_height)
        pygame.draw.rect(self.screen, (126, 78, 151), cover, border_radius=7)
        pygame.draw.rect(self.screen, (204, 145, 226), cover, width=2, border_radius=7)

        if self.showing_diagnosis_hand:
            return_button = pygame.Rect(tray.x + 12, tray.bottom - 30, tray.width - 24, 23)
            hovered = return_button.collidepoint(pygame.mouse.get_pos())
            button_color = COLORS["accent"] if hovered else (151, 101, 180)
            pygame.draw.rect(self.screen, button_color, return_button, border_radius=6)
            return_text = self.pile_font.render(
                "<  RETURN TO TESTS",
                True,
                COLORS["background"],
            )
            self.screen.blit(return_text, return_text.get_rect(center=return_button.center))
        else:
            open_text = self.pile_font.render("OPEN PATIENT FILE", True, COLORS["text"])
            self.screen.blit(
                open_text,
                open_text.get_rect(center=(folder.centerx, tray.bottom - 17)),
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
        """Dim the workspace and draw the open notebook spread."""
        dim = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        dim.fill((0, 0, 0, 170))
        self.screen.blit(dim, (0, 0))

        layout = self.notebook_layout
        book = layout["book"]
        pygame.draw.rect(self.screen, (40, 62, 52), book, border_radius=12)
        pygame.draw.rect(self.screen, COLORS["panel_border"], book, width=2, border_radius=12)

        for page in (pygame.Rect(book.x + 12, book.y + 12, book.width // 2 - 12, book.height - 24),
                     pygame.Rect(book.centerx, book.y + 12, book.width // 2 - 12, book.height - 24)):
            pygame.draw.rect(self.screen, COLORS["card"], page, border_radius=6)
        pygame.draw.line(self.screen, COLORS["card_text"],
                         (book.centerx, book.y + 12), (book.centerx, book.bottom - 12), 2)

        left, right = self.get_spread_columns(self.notebook_spread)
        if left is None:
            self.draw_notebook_id_page(layout["left"])
        else:
            self.draw_notebook_column(left, layout["left"])
        self.draw_notebook_column(right, layout["right"])

        # Page numbers
        left_num = self.notebook_spread * 2 + 1
        for num, key in ((left_num, "left"), (left_num + 1, "right")):
            label = self.card_font.render(str(num), True, COLORS["card_text"])
            self.screen.blit(label, label.get_rect(center=(layout[key].centerx, book.bottom - 22)))

        # Buttons
        mouse = pygame.mouse.get_pos()
        buttons = [("CLOSE", layout["close"], True),
                   ("< PREV", layout["prev"], self.notebook_spread > 0),
                   ("NEXT >", layout["next"],
                    self.notebook_spread < self.notebook_spread_count() - 1)]
        for text, rect, enabled in buttons:
            if not enabled:
                continue
            color = COLORS["accent"] if rect.collidepoint(mouse) else COLORS["panel_border"]
            pygame.draw.rect(self.screen, color, rect, border_radius=6)
            label = self.small_font.render(text, True, COLORS["background"])
            self.screen.blit(label, label.get_rect(center=rect.center))

    def draw_notebook_column(self, column, rect):
        """Draw one column of test titles and result lines."""
        for kind, text, y in column:
            if kind == "title":
                surface = self.notebook_title_font.render(text, True, COLORS["card_text"])
            else:
                surface = self.notebook_body_font.render(text, True, (72, 101, 91))
            self.screen.blit(surface, (rect.x, rect.y + y))

    def draw_notebook_id_page(self, rect):
        """Draw the patient's name and both ID cards as a single column."""
        y = rect.y
        name = self.heading_font.render(self.patient.name, True, COLORS["card_text"])
        self.screen.blit(name, (rect.x, y))
        y += name.get_height() + 12

        sections = [
            ("INTERGALACTIC ID", self.patient.profile.items()),
            ("HEALTH ID", self.patient.medical_info.items()),
        ]
        body_h = self.notebook_body_font.get_linesize()
        for heading, items in sections:
            title = self.notebook_title_font.render(heading, True, COLORS["card_text"])
            self.screen.blit(title, (rect.x, y))
            y += self.notebook_title_font.get_linesize()
            for label, value in items:
                for line in self.wrap_text(f"{label}: {value}", self.notebook_body_font, rect.width):
                    surface = self.notebook_body_font.render(line, True, (72, 101, 91))
                    self.screen.blit(surface, (rect.x, y))
                    y += body_h
            y += body_h

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
        width = self.notebook_layout["right"].width
        height = self.notebook_layout["right"].height
        title_h = self.notebook_title_font.get_linesize()
        body_h = self.notebook_body_font.get_linesize()
        gap = body_h

        blocks = []
        for test_name, result in self.notebook.get_entries(self.patient).items():
            block = [("title", test_name.upper(), title_h)]
            for line in self.wrap_text(result, self.notebook_body_font, width):
                block.append(("body", line, body_h))
            blocks.append(block)

        columns = [[]]
        used = 0
        for block in blocks:
            if columns[-1]:
                # Keep a title together with at least its first body line
                start_needed = block[0][2] + (block[1][2] if len(block) > 1 else 0)
                if used + gap + start_needed > height:
                    columns.append([])
                    used = 0
                else:
                    used += gap

            for kind, text, item_h in block:
                if used + item_h > height and columns[-1]:
                    columns.append([])  # runoff continues on the next page
                    used = 0
                columns[-1].append((kind, text, used))
                used += item_h

        self.notebook_columns = columns

    def notebook_spread_count(self):
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
        self.build_notebook_columns()  # rebuild so new results appear
        self.notebook_spread = 0
        self.state = GameState.NOTEBOOK

    def flip_notebook(self, direction):
        new_spread = self.notebook_spread + direction
        if 0 <= new_spread < self.notebook_spread_count():
            self.notebook_spread = new_spread

    def handle_notebook_click(self, position):
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
