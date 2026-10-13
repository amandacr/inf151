"""Minimal Pygame shell for the Alien Doctor GUI prototype.

you can run this file without changing the old text based version.
"""

from enum import Enum, auto

import pygame

from PatientData import create_zorpa
from Player import Player


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
        """Set up Pygame, shared game data, layout rectangles, and fonts."""

        pygame.init()
        pygame.display.set_caption("Alien Doctor - GUI Prototype")

        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.TITLE
        self.patient = create_zorpa()
        self.player = Player("Dr GUI")
        self.showing_health_id = False
        self.selected_card_index = None
        self.card_message = ""
        self.run_test_button = None
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
        self.card_rects = self.build_card_rects()

        self.title_font = pygame.font.Font(None, 64)
        self.heading_font = pygame.font.Font(None, 38)
        self.body_font = pygame.font.Font(None, 26)
        self.small_font = pygame.font.Font(None, 20)
        self.card_font = pygame.font.Font(None, 17)

    def run(self):
        """Run the GUI loop until the player closes the window."""

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
                elif self.state == GameState.PATIENT:
                    self.handle_patient_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_RETURN and self.state == GameState.TITLE:
                    self.state = GameState.PATIENT
                elif event.key in state_keys:
                    self.state = state_keys[event.key]

    def handle_patient_click(self, position):
        """Handle ID-card and test-card clicks on the patient screen."""

        if self.layout["id_card"].collidepoint(position):
            self.showing_health_id = not self.showing_health_id

        self.handle_card_click(position)

    def build_card_rects(self):
        """Create the rectangles that position the test cards in the player's hand."""

        panel = self.layout["active_hand"]
        card_width = 96
        card_height = 118
        gap = 18
        card_count = len(self.player.test_hand)
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
        """Select, dismiss, switch, or activate a test card based on a mouse click."""

        if self.selected_card_index is not None:
            selected_rect = self.get_selected_card_rect(self.selected_card_index)
            run_button = self.get_run_test_button(selected_rect)

            if run_button.collidepoint(position):
                test = self.player.test_hand[self.selected_card_index].value
                self.card_message = (
                    test.name + " ready - test results will be connected later"
                )
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
            selected_rect.x + 24,
            selected_rect.bottom - 38,
            selected_rect.width - 48,
            28,
        )

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
        """Draw the welcome screen and its View Patient button."""

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
        """Draw every panel that makes up the main patient workspace."""

        self.draw_status_bar()
        self.draw_draw_deck()
        self.draw_alien_placeholder()
        self.draw_id_card()
        self.draw_throwaway_deck()
        self.draw_notebook()
        self.draw_active_hand()
        self.draw_diagnosis_cards()

    def draw_status_bar(self):
        """Draw the current patient, shift message, and player balance."""

        panel = self.layout["status_bar"]
        self.draw_panel(panel)

        patient = self.body_font.render(
            "PATIENT: " + self.patient.name, True, COLORS["text"]
        )
        center_text = self.card_message or "SHIFT 01"
        center_font = self.small_font if self.card_message else self.body_font
        shift = center_font.render(center_text, True, COLORS["muted"])
        money = self.body_font.render(
            "MONEY: $" + str(self.player.balance), True, COLORS["accent"]
        )

        self.screen.blit(patient, (panel.x + 18, panel.y + 15))
        self.screen.blit(shift, shift.get_rect(center=panel.center))
        self.screen.blit(money, (panel.right - money.get_width() - 18, panel.y + 15))

    def draw_draw_deck(self):
        """Draw the placeholder stack for the test-card draw deck."""

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
        """Draw a temporary alien portrait and the current patient's name."""

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
        """Draw either side of the patient's clickable ID card."""

        panel = self.layout["id_card"]
        pygame.draw.rect(self.screen, COLORS["card"], panel, border_radius=8)
        border_color = (
            COLORS["accent"]
            if panel.collidepoint(pygame.mouse.get_pos())
            else COLORS["panel_border"]
        )
        pygame.draw.rect(
            self.screen, border_color, panel, width=3, border_radius=8
        )

        if self.showing_health_id:
            title_text = "HEALTH ID"
            details = list(self.patient.medical_info.items())
            next_side = "CLICK TO VIEW ID"
        else:
            title_text = "INTERGALACTIC ID"
            details = [("Name", self.patient.name)] + list(self.patient.profile.items())
            next_side = "CLICK TO VIEW HEALTH ID"

        title = self.body_font.render(title_text, True, COLORS["card_text"])
        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 20)))

        detail_y = panel.y + 45
        for label, value in details:
            detail = self.card_font.render(
                f"{label}: {value}", True, (72, 101, 91)
            )
            self.screen.blit(detail, (panel.x + 16, detail_y))
            detail_y += 18

        flip_hint = self.card_font.render(next_side, True, COLORS["card_text"])
        self.screen.blit(
            flip_hint,
            flip_hint.get_rect(center=(panel.centerx, panel.bottom - 10)),
        )

    def draw_throwaway_deck(self):
        """Draw the placeholder pile for discarded test cards."""

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
        """Draw the placeholder notebook in the lower-left corner."""

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
        """Draw the player's test cards with hover and selection states."""

        panel = self.layout["active_hand"]
        self.draw_panel(panel)
        self.draw_centered_label("ACTIVE TEST HAND", panel, panel.y + 22)

        mouse_position = pygame.mouse.get_pos()

        for index, card in enumerate(self.player.test_hand):
            if index == self.selected_card_index:
                continue

            card_rect = self.card_rects[index]
            hovered = card_rect.collidepoint(mouse_position)
            display_rect = card_rect.move(0, -8 if hovered else 0)
            self.draw_test_card(card, display_rect, hovered=hovered)

        if self.selected_card_index is not None:
            selected_card = self.player.test_hand[self.selected_card_index]
            selected_rect = self.get_selected_card_rect(self.selected_card_index)
            self.draw_test_card(selected_card, selected_rect, selected=True)

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
        """Draw an enlarged card's details and its Run Test button."""

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

    def draw_diagnosis_cards(self):
        """Draw the placeholder stack for the player's diagnosis cards."""

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
        """Draw a text label centered horizontally inside a panel."""

        label = self.small_font.render(text, True, COLORS["text"])
        self.screen.blit(label, label.get_rect(center=(panel.centerx, y)))

    def draw_placeholder_screen(self):
        """Draw a temporary panel for GUI screens that are not implemented yet."""

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

def main():
    """Create and start the game"""

    AlienDoctorGUI().run()


if __name__ == "__main__":
    main()
