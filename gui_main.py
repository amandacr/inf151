"""Minimal Pygame shell for the Alien Doctor GUI prototype.

you can run this file without changing the old text based version.
"""

from enum import Enum, auto

import pygame

from PatientData import create_zorpa
from Player import Player
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

    TITLE = auto()
    PATIENT = auto()
    TEST_RESULT = auto()
    DIAGNOSIS = auto()
    OUTCOME = auto()
    NOTEBOOK = auto()


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
        self.notebook = Notebook()
        self.notebook.add_patient(self.patient)
        self.notebook_columns = []
        self.notebook_spread = 0
        self.showing_health_id = False
        self.selected_card_index = None
        self.card_message = ""
        self.run_test_button = None
        self.discard_pile = []
        self.last_test_name = ""
        self.last_test_result = ""
        self.start_button = pygame.Rect(410, 380, 280, 58)
        self.continue_button = pygame.Rect(410, 430, 280, 52)
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
        self.notebook_layout = self.build_notebook_rects()

        self.title_font = pygame.font.Font(None, 64)
        self.heading_font = pygame.font.Font(None, 38)
        self.body_font = pygame.font.Font(None, 26)
        self.small_font = pygame.font.Font(None, 20)
        self.card_font = pygame.font.Font(None, 17)
        self.notebook_title_font = pygame.font.Font(None, 28)
        self.notebook_body_font = pygame.font.Font(None, 22)

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
                elif self.state == GameState.TEST_RESULT:
                    self.handle_test_result_click(event.pos)
                elif self.state == GameState.NOTEBOOK:
                    self.handle_notebook_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_RETURN and self.state == GameState.TITLE:
                    self.state = GameState.PATIENT
                elif event.key == pygame.K_RETURN and self.state == GameState.TEST_RESULT:
                    self.handle_test_result_click(self.continue_button.center)
                elif event.key in state_keys:
                    self.state = state_keys[event.key]
                elif event.key == pygame.K_LEFT and self.state == GameState.NOTEBOOK:
                    self.flip_notebook(-1)
                elif event.key == pygame.K_RIGHT and self.state == GameState.NOTEBOOK:
                    self.flip_notebook(1)

    def handle_patient_click(self, position):
        """Handle ID-card and test-card clicks on the patient screen."""

        if self.layout["id_card"].collidepoint(position):
            self.showing_health_id = not self.showing_health_id
        if self.layout["notebook"].collidepoint(position):
            self.open_notebook()
            return

        self.handle_card_click(position)

    def build_card_rects(self):
        """Create the rectangles that position the test cards in the player's hand."""

        panel = self.layout["active_hand"]
        card_width = 96
        card_height = 118
        gap = 18
        card_count = len(self.player.test_hand)

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
        """Select, dismiss, switch, or activate a test card based on a mouse click."""

        if self.selected_card_index is not None:
            selected_rect = self.get_selected_card_rect(self.selected_card_index)
            run_button = self.get_run_test_button(selected_rect)

            if run_button.collidepoint(position):
                self.run_selected_test()
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
        elif self.state == GameState.TEST_RESULT:
            self.draw_test_result_screen()
        elif self.state == GameState.NOTEBOOK:
            self.draw_patient_screen()
            self.draw_notebook_screen()
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
        """Draw the pile of test cards that the player has already used."""

        panel = self.layout["throwaway"]
        self.draw_panel(panel)
        self.draw_centered_label("THROWAWAY", panel, panel.y + 22)

        if not self.discard_pile:
            empty = self.small_font.render("EMPTY", True, COLORS["muted"])
            self.screen.blit(empty, empty.get_rect(center=(panel.centerx, panel.y + 72)))
            return

        card = pygame.Rect(panel.centerx - 30, panel.y + 48, 60, 48)
        offsets = (7, 3, 0)[-min(3, len(self.discard_pile)):]
        for offset in offsets:
            shifted = card.move(offset, -offset)
            pygame.draw.rect(self.screen, COLORS["muted"], shifted, border_radius=4)
            pygame.draw.rect(
                self.screen, COLORS["background"], shifted, width=2, border_radius=4
            )

        last_test = self.discard_pile[-1].value.name[0]
        initial = self.body_font.render(last_test, True, COLORS["background"])
        self.screen.blit(initial, initial.get_rect(center=card.center))
        used = self.card_font.render(
            "USED: " + str(len(self.discard_pile)), True, COLORS["muted"]
        )
        self.screen.blit(used, used.get_rect(center=(panel.centerx, panel.bottom - 10)))

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

        if not self.player.test_hand:
            empty = self.body_font.render("NO TEST CARDS", True, COLORS["muted"])
            self.screen.blit(empty, empty.get_rect(center=panel.center))
            return

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
