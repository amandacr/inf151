"""First-shift briefing and reusable reception help overlay."""

import pygame

from gui_state import GameState
from gui_theme import COLORS, WINDOW_SIZE
from Player import (
    CLINIC_OPERATING_FEE,
    DIAGNOSIS_REWARD,
    WRONG_DIAGNOSIS_PENALTY,
)
from Test import TEST_COSTS_BY_RARITY


class TutorialMixin:
    """Explain the core loop before the player's first patient call."""

    def open_tutorial(self):
        """Open the reception briefing without resetting any game progress."""

        if not self.tutorial_open:
            self.tutorial_opened_at = pygame.time.get_ticks()
        self.tutorial_open = True

    def close_tutorial(self):
        """Dismiss the briefing for the rest of this launch unless reopened."""

        if self.tutorial_opened_at is not None:
            paused_for = pygame.time.get_ticks() - self.tutorial_opened_at
            self.offset_animation_timers(paused_for)
        self.play_sfx("button")
        self.tutorial_open = False
        self.tutorial_opened_at = None

    def handle_tutorial_click(self, position):
        """Close the briefing when its contextual return control is selected."""

        if self.tutorial_begin_button.collidepoint(position):
            self.close_tutorial()

    def get_tutorial_action_label(self):
        """Describe where the player will return when closing the briefing."""

        if self.state == GameState.TITLE:
            return "BEGIN SHIFT" if self.patients_called == 0 else "CONTINUE SHIFT"
        return {
            GameState.PATIENT: "RETURN TO PATIENT",
            GameState.TEST_RESULT: "RETURN TO TEST RESULT",
            GameState.NOTEBOOK: "RETURN TO NOTEBOOK",
            GameState.OUTCOME: "RETURN TO CASE RESULT",
            GameState.DAY_COMPLETE: "RETURN TO SHIFT RECAP",
            GameState.SHOP: "RETURN TO SHOP",
            GameState.ENDING: "CONTINUE ENDING",
            GameState.FINAL: "RETURN TO SUMMARY",
        }.get(self.state, "CONTINUE SHIFT")

    def draw_help_button(self):
        """Draw the top-right control that reopens instructions during gameplay."""

        rect = self.help_button
        hovered = rect.collidepoint(self.get_mouse_position())
        border = (206, 158, 233) if hovered else (155, 116, 190)
        fill = (50, 37, 68) if hovered else (27, 29, 45)
        pygame.draw.rect(self.screen, (3, 8, 13), rect.move(2, 3), border_radius=8)
        pygame.draw.rect(self.screen, fill, rect, border_radius=8)
        pygame.draw.rect(self.screen, border, rect, width=2, border_radius=8)
        label = self.card_font.render("?  HELP", True, (232, 211, 242))
        self.screen.blit(label, label.get_rect(center=rect.center))

    def draw_tutorial_overlay(self):
        """Draw a clipboard-style summary of the complete patient workflow."""

        dim = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        dim.fill((2, 6, 12, 220))
        self.screen.blit(dim, (0, 0))

        panel = pygame.Rect(165, 92, 770, 510)
        paper = panel.inflate(-18, -18)
        pygame.draw.rect(self.screen, (3, 8, 13), panel.move(9, 10), border_radius=18)
        pygame.draw.rect(self.screen, (79, 55, 94), panel, border_radius=18)
        pygame.draw.rect(self.screen, (187, 137, 211), panel, width=3, border_radius=18)
        pygame.draw.rect(self.screen, (232, 229, 207), paper, border_radius=12)

        clip = pygame.Rect(panel.centerx - 78, panel.y - 7, 156, 34)
        pygame.draw.rect(self.screen, (33, 46, 55), clip, border_radius=9)
        pygame.draw.rect(self.screen, (123, 151, 152), clip, width=2, border_radius=9)
        pygame.draw.rect(
            self.screen,
            (12, 20, 27),
            pygame.Rect(clip.centerx - 29, clip.y + 9, 58, 9),
            border_radius=4,
        )

        ink = (35, 47, 50)
        muted_ink = (77, 91, 86)
        purple = (126, 75, 158)

        orientation_text = self.tutorial_label_font.render(
            "NEW DOCTOR ORIENTATION",
            True,
            purple,
        )
        orientation = orientation_text.get_rect(
            center=(panel.x + 130, panel.y + 43)
        ).inflate(22, 10)
        pygame.draw.rect(self.screen, (222, 208, 230), orientation, border_radius=12)
        self.screen.blit(
            orientation_text,
            orientation_text.get_rect(center=orientation.center),
        )

        heading = self.tutorial_title_font.render("YOUR FIRST SHIFT", True, ink)
        self.screen.blit(heading, heading.get_rect(center=(panel.centerx, 137)))
        subtitle = self.tutorial_subtitle_font.render(
            "Treat 4 patients  •  Follow the clues  •  Protect your pay",
            True,
            muted_ink,
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(panel.centerx, 169)))

        common = TEST_COSTS_BY_RARITY["Common"]
        uncommon = TEST_COSTS_BY_RARITY["Uncommon"]
        rare = TEST_COSTS_BY_RARITY["Rare"]
        steps = (
            (
                "1",
                "INSPECT",
                "Read the symptoms. Flip the ID to view the patient's alien anatomy.",
                "ID  +  HEALTH ID",
                (73, 128, 169),
            ),
            (
                "2",
                "TEST CAREFULLY",
                "Run only the tests you need. Every machine use is billed at shift end.",
                f"COMMON ${common}   •   UNCOMMON ${uncommon}   •   RARE ${rare}",
                (49, 150, 135),
            ),
            (
                "3",
                "DIAGNOSE",
                "Compare your notebook clues, then submit one final diagnosis.",
                f"CORRECT +${DIAGNOSIS_REWARD}   •   INCORRECT -${WRONG_DIAGNOSIS_PENALTY}",
                purple,
            ),
            (
                "4",
                "COMPLETE THE SHIFT",
                "Finish all four cases. Clinic overhead is deducted before you visit the Shop.",
                f"4 PATIENTS   •   ${CLINIC_OPERATING_FEE} CLINIC OVERHEAD",
                (192, 124, 46),
            ),
        )
        step_rects = (
            pygame.Rect(200, 194, 335, 126),
            pygame.Rect(565, 194, 335, 126),
            pygame.Rect(200, 334, 335, 126),
            pygame.Rect(565, 334, 335, 126),
        )
        for step, rect in zip(steps, step_rects):
            number, title, description, footer, step_color = step
            pygame.draw.rect(self.screen, (220, 218, 197), rect.move(3, 4), border_radius=10)
            pygame.draw.rect(self.screen, (245, 241, 217), rect, border_radius=10)
            pygame.draw.rect(self.screen, (168, 157, 143), rect, width=1, border_radius=10)
            pygame.draw.rect(
                self.screen,
                step_color,
                pygame.Rect(rect.x, rect.y, 7, rect.height),
                border_top_left_radius=10,
                border_bottom_left_radius=10,
            )
            pygame.draw.circle(self.screen, step_color, (rect.x + 32, rect.y + 29), 18)
            number_label = self.tutorial_step_font.render(number, True, (255, 252, 241))
            self.screen.blit(
                number_label,
                number_label.get_rect(center=(rect.x + 32, rect.y + 29)),
            )
            title_label = self.tutorial_step_font.render(title, True, step_color)
            self.screen.blit(title_label, (rect.x + 61, rect.y + 19))
            description_rect = pygame.Rect(rect.x + 19, rect.y + 52, rect.width - 38, 40)
            self.draw_wrapped_text(
                description,
                self.tutorial_body_font,
                ink,
                description_rect,
                line_spacing=2,
            )

            footer_rect = pygame.Rect(rect.x + 16, rect.bottom - 35, rect.width - 32, 28)
            footer_fill = tuple(
                round(channel * 0.2 + 245 * 0.8)
                for channel in step_color
            )
            pygame.draw.rect(self.screen, footer_fill, footer_rect, border_radius=10)
            pygame.draw.rect(
                self.screen,
                step_color,
                footer_rect,
                width=1,
                border_radius=10,
            )
            footer_label = self.tutorial_label_font.render(footer, True, step_color)
            self.screen.blit(
                footer_label,
                footer_label.get_rect(center=footer_rect.center),
            )

        hovered = self.tutorial_begin_button.collidepoint(self.get_mouse_position())
        button_color = COLORS["accent"] if hovered else COLORS["panel_border"]
        pygame.draw.rect(
            self.screen,
            (118, 102, 91),
            self.tutorial_begin_button.move(0, 4),
            border_radius=9,
        )
        pygame.draw.rect(
            self.screen,
            button_color,
            self.tutorial_begin_button,
            border_radius=9,
        )
        begin = self.tutorial_step_font.render(
            self.get_tutorial_action_label(),
            True,
            COLORS["background"],
        )
        self.screen.blit(begin, begin.get_rect(center=self.tutorial_begin_button.center))
        hint = self.tutorial_label_font.render(
            "Shown once per launch  •  Select ? HELP anytime to view this again",
            True,
            muted_ink,
        )
        self.screen.blit(hint, hint.get_rect(center=(panel.centerx, 584)))
