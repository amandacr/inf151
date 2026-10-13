"""Minimal Pygame shell for the Alien Doctor GUI prototype.

you can run this file without changing the old text based version.
"""

from enum import Enum, auto

import pygame

from PatientData import create_zorpa


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


class GameState(Enum):
    """Screens planned for the GUI version of the prototype."""

    TITLE = auto()
    PATIENT = auto()
    TEST_RESULT = auto()
    DIAGNOSIS = auto()
    OUTCOME = auto()


STATE_LABELS = {
    GameState.TITLE: "Title Screen",
    GameState.PATIENT: "Patient Screen",
    GameState.TEST_RESULT: "Test Result Screen",
    GameState.DIAGNOSIS: "Diagnosis Screen",
    GameState.OUTCOME: "Outcome Screen",
}


class AlienDoctorGUI:

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Alien Doctor - GUI Prototype")

        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.TITLE
        self.patient = create_zorpa()
        self.start_button = pygame.Rect(410, 380, 280, 58)
        self.layout = {
            "status_bar": pygame.Rect(30, 100, 1040, 50),
            "draw_deck": pygame.Rect(45, 180, 125, 175),
            "alien": pygame.Rect(250, 165, 230, 195),
            "id_card": pygame.Rect(510, 180, 270, 155),
            "throwaway": pygame.Rect(910, 235, 125, 120),
            "notebook": pygame.Rect(40, 410, 155, 150),
            "active_hand": pygame.Rect(225, 390, 625, 170),
            "diagnosis": pygame.Rect(885, 400, 175, 160),
        }

        self.title_font = pygame.font.Font(None, 64)
        self.heading_font = pygame.font.Font(None, 38)
        self.body_font = pygame.font.Font(None, 26)
        self.small_font = pygame.font.Font(None, 20)

    def run(self):
        """Runs until closed"""

        while self.running:
            self.handle_events()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

    def handle_events(self):
        """Process window events and controls."""

        state_keys = {
            pygame.K_1: GameState.TITLE,
            pygame.K_2: GameState.PATIENT,
            pygame.K_3: GameState.TEST_RESULT,
            pygame.K_4: GameState.DIAGNOSIS,
            pygame.K_5: GameState.OUTCOME,
        }

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == GameState.TITLE and self.start_button.collidepoint(event.pos):
                    self.state = GameState.PATIENT
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_RETURN and self.state == GameState.TITLE:
                    self.state = GameState.PATIENT
                elif event.key in state_keys:
                    self.state = state_keys[event.key]

    def draw(self):
        """Draws shell + active screen."""

        self.screen.fill(COLORS["background"])

        title = self.title_font.render("A L I E N  D O C T O R", True, COLORS["accent"])
        self.screen.blit(title, title.get_rect(center=(WINDOW_SIZE[0] // 2, 42)))

        subtitle = self.small_font.render(
            "Pygame interface framework - not done yet",
            True,
            COLORS["muted"],
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(WINDOW_SIZE[0] // 2, 76)))

        if self.state == GameState.TITLE:
            self.draw_title_screen()
        elif self.state == GameState.PATIENT:
            self.draw_patient_screen()
        else:
            self.draw_placeholder_screen()

        controls = self.small_font.render(
            "Preview screens: 1 Title  |  2 Patient  |  3 Result  |  4 Diagnosis  |  5 Outcome",
            True,
            COLORS["text"],
        )
        self.screen.blit(controls, controls.get_rect(center=(WINDOW_SIZE[0] // 2, 610)))

        quit_hint = self.small_font.render(
            "Press Esc to quit", True, COLORS["muted"]
        )
        self.screen.blit(quit_hint, quit_hint.get_rect(center=(WINDOW_SIZE[0] // 2, 635)))

    def draw_title_screen(self):
        panel = pygame.Rect(160, 120, 780, 390)
        self.draw_panel(panel)

        heading = self.heading_font.render("Welcome, Doctor", True, COLORS["text"])
        self.screen.blit(heading, heading.get_rect(center=(550, 220)))

        description = self.body_font.render(
            "Your first intergalactic patient is waiting.",
            True,
            COLORS["muted"],
        )
        self.screen.blit(description, description.get_rect(center=(550, 270)))

        hovered = self.start_button.collidepoint(pygame.mouse.get_pos())
        button_color = COLORS["accent"] if hovered else COLORS["panel_border"]
        pygame.draw.rect(self.screen, button_color, self.start_button, border_radius=8)

        button_text = self.body_font.render("VIEW PATIENT", True, COLORS["background"])
        self.screen.blit(button_text, button_text.get_rect(center=self.start_button.center))

        hint = self.small_font.render(
            "Click the button or press Enter", True, COLORS["muted"]
        )
        self.screen.blit(hint, hint.get_rect(center=(550, 465)))

    def draw_patient_screen(self):
        self.draw_status_bar()
        self.draw_draw_deck()
        self.draw_alien_placeholder()
        self.draw_id_card()
        self.draw_throwaway_deck()
        self.draw_notebook()
        self.draw_active_hand()
        self.draw_diagnosis_cards()

    def draw_status_bar(self):
        panel = self.layout["status_bar"]
        self.draw_panel(panel)

        patient = self.body_font.render(
            "PATIENT: " + self.patient.name, True, COLORS["text"]
        )
        shift = self.body_font.render("SHIFT 01", True, COLORS["muted"])
        money = self.body_font.render("MONEY: $500", True, COLORS["accent"])

        self.screen.blit(patient, (panel.x + 18, panel.y + 15))
        self.screen.blit(shift, shift.get_rect(center=panel.center))
        self.screen.blit(money, (panel.right - money.get_width() - 18, panel.y + 15))

    def draw_draw_deck(self):
        panel = self.layout["draw_deck"]
        self.draw_panel(panel)
        self.draw_centered_label("DRAW DECK", panel, panel.y + 22)

        card = pygame.Rect(panel.x + 31, panel.y + 54, 72, 96)
        for offset in (8, 4, 0):
            shifted = card.move(offset, -offset)
            pygame.draw.rect(self.screen, COLORS["card"], shifted, border_radius=5)
            pygame.draw.rect(
                self.screen, COLORS["card_text"], shifted, width=2, border_radius=5
            )

    def draw_alien_placeholder(self):
        panel = self.layout["alien"]
        self.draw_panel(panel)
        self.draw_centered_label("ALIEN PLACEHOLDER", panel, panel.y + 20)

        head = pygame.Rect(panel.centerx - 48, panel.y + 47, 96, 112)
        pygame.draw.ellipse(self.screen, (126, 172, 154), head)
        pygame.draw.ellipse(
            self.screen,
            COLORS["background"],
            pygame.Rect(head.x + 20, head.y + 43, 14, 25),
        )
        pygame.draw.ellipse(
            self.screen,
            COLORS["background"],
            pygame.Rect(head.right - 34, head.y + 43, 14, 25),
        )

        name = self.small_font.render(self.patient.name, True, COLORS["muted"])
        self.screen.blit(name, name.get_rect(center=(panel.centerx, panel.bottom - 19)))

    def draw_id_card(self):
        panel = self.layout["id_card"]
        pygame.draw.rect(self.screen, COLORS["card"], panel, border_radius=8)
        pygame.draw.rect(
            self.screen, COLORS["panel_border"], panel, width=3, border_radius=8
        )

        title = self.heading_font.render("ID / HEALTH ID", True, COLORS["card_text"])
        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 40)))

        placeholder = self.body_font.render(
            "Click-to-flip area", True, (72, 101, 91)
        )
        self.screen.blit(
            placeholder, placeholder.get_rect(center=(panel.centerx, panel.y + 87))
        )

        note = self.small_font.render(
            "information will be added later", True, (72, 101, 91)
        )
        self.screen.blit(note, note.get_rect(center=(panel.centerx, panel.y + 121)))

    def draw_throwaway_deck(self):
        panel = self.layout["throwaway"]
        self.draw_panel(panel)
        self.draw_centered_label("THROWAWAY", panel, panel.y + 22)

        card = pygame.Rect(panel.centerx - 30, panel.y + 48, 60, 48)
        for offset in (7, 3, 0):
            shifted = card.move(offset, -offset)
            pygame.draw.rect(self.screen, COLORS["muted"], shifted, border_radius=4)
            pygame.draw.rect(
                self.screen, COLORS["background"], shifted, width=2, border_radius=4
            )

    def draw_notebook(self):
        panel = self.layout["notebook"]
        self.draw_panel(panel)
        self.draw_centered_label("NOTEBOOK", panel, panel.y + 24)

        book = pygame.Rect(panel.x + 24, panel.y + 52, panel.width - 48, 72)
        pygame.draw.rect(self.screen, COLORS["card"], book, border_radius=5)
        pygame.draw.line(
            self.screen,
            COLORS["card_text"],
            (book.centerx, book.y + 5),
            (book.centerx, book.bottom - 5),
            width=2,
        )

    def draw_active_hand(self):
        panel = self.layout["active_hand"]
        self.draw_panel(panel)
        self.draw_centered_label("ACTIVE TEST HAND", panel, panel.y + 22)

        card_width = 88
        gap = 18
        total_width = (card_width * 5) + (gap * 4)
        start_x = panel.centerx - total_width // 2

        for index in range(5):
            card = pygame.Rect(
                start_x + index * (card_width + gap), panel.y + 49, card_width, 100
            )
            pygame.draw.rect(self.screen, COLORS["card"], card, border_radius=6)
            pygame.draw.rect(
                self.screen, COLORS["panel_border"], card, width=2, border_radius=6
            )
            label = self.small_font.render(
                "TEST " + str(index + 1), True, COLORS["card_text"]
            )
            self.screen.blit(label, label.get_rect(center=card.center))

    def draw_diagnosis_cards(self):
        panel = self.layout["diagnosis"]
        self.draw_panel(panel)
        self.draw_centered_label("DIAGNOSIS", panel, panel.y + 22)

        card = pygame.Rect(panel.x + 42, panel.y + 50, 92, 82)
        for offset in (12, 6, 0):
            shifted = card.move(offset, -offset)
            pygame.draw.rect(self.screen, COLORS["card"], shifted, border_radius=5)
            pygame.draw.rect(
                self.screen, COLORS["card_text"], shifted, width=2, border_radius=5
            )

    def draw_centered_label(self, text, panel, y):
        label = self.small_font.render(text, True, COLORS["text"])
        self.screen.blit(label, label.get_rect(center=(panel.centerx, y)))

    def draw_placeholder_screen(self):

        panel = pygame.Rect(90, 145, 780, 285)
        panel.centerx = WINDOW_SIZE[0] // 2
        self.draw_panel(panel)

        screen_name = self.heading_font.render(
            STATE_LABELS[self.state], True, COLORS["text"]
        )
        self.screen.blit(screen_name, screen_name.get_rect(center=(550, 235)))

        placeholder = self.body_font.render(
            "will be implemented later",
            True,
            COLORS["muted"],
        )
        self.screen.blit(placeholder, placeholder.get_rect(center=(550, 290)))

    def draw_panel(self, panel):
        pygame.draw.rect(self.screen, COLORS["panel"], panel, border_radius=12)
        pygame.draw.rect(
            self.screen,
            COLORS["panel_border"],
            panel,
            width=2,
            border_radius=12,
        )

def main():
    AlienDoctorGUI().run()


if __name__ == "__main__":
    main()
