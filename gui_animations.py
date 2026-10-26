"""Reusable card-disposal and notebook-transfer animations for the GUI."""

import math

import pygame

from gui_theme import COLORS, RARITY_CARD_COLORS, RARITY_COLORS


class AnimationMixin:
    """Supply animation drawing helpers to the main GUI object."""

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
            self.layout["throwaway"].y + 45,
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
        """Create a compact snapshot of a discarded test or diagnosis card."""

        card_value = card.value
        is_diagnosis = card.type == "Diagnosis"
        if is_diagnosis:
            rarity_color = (205, 100, 235)
            fill_color = (235, 220, 239)
            footer_text = "DIAGNOSIS"
        else:
            rarity_color = RARITY_COLORS.get(
                card_value.rarity,
                COLORS["panel_border"],
            )
            fill_color = RARITY_CARD_COLORS.get(
                card_value.rarity,
                COLORS["card"],
            )
            footer_text = card_value.rarity.upper()
        card_surface = pygame.Surface((96, 118), pygame.SRCALPHA)
        shape = self.get_card_shape_points(card_surface.get_rect(), 7)
        pygame.draw.polygon(card_surface, fill_color, shape)
        pygame.draw.polygon(card_surface, rarity_color, shape, width=3)

        header = pygame.Rect(7, 7, 82, 25)
        header_color = tuple(max(0, channel - 18) for channel in fill_color)
        pygame.draw.rect(card_surface, header_color, header, border_radius=5)
        title_font = self.card_font
        if title_font.size(card_value.name)[0] > header.width - 6:
            title_font = self.pile_font
        title = title_font.render(card_value.name, True, COLORS["card_text"])
        card_surface.blit(title, title.get_rect(center=header.center))

        icon = pygame.Rect(28, 40, 40, 40)
        pygame.draw.rect(card_surface, (201, 214, 205), icon, border_radius=6)
        pygame.draw.rect(card_surface, rarity_color, icon, width=2, border_radius=6)
        initial = self.body_font.render(
            "D" if is_diagnosis else card_value.name[0],
            True,
            COLORS["card_text"],
        )
        card_surface.blit(initial, initial.get_rect(center=icon.center))

        footer = self.pile_font.render(footer_text, True, rarity_color)
        card_surface.blit(footer, footer.get_rect(center=(48, 101)))
        return card_surface

    def draw_med_waste_slot_lip(self):
        """Redraw the bin opening over the final frames so the card appears to enter it."""

        panel = self.layout["throwaway"]
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

    def draw_note_transfer_animation(self):
        """Fly a small diagnostic slip into the notebook before discarding its card."""

        if self.note_transfer_animation is None:
            return

        elapsed = pygame.time.get_ticks() - self.note_transfer_animation["started_at"]
        progress = min(1.0, elapsed / self.note_transfer_animation_duration)
        eased_progress = progress * progress * (3 - 2 * progress)
        start = (720, 330)
        notebook_panel = self.layout["notebook"]
        target = (notebook_panel.centerx + 34, notebook_panel.y + 58)
        control = (
            (start[0] + target[0]) / 2,
            min(start[1], target[1]) - 90,
        )
        center_x, center_y = self.get_quadratic_curve_point(
            start,
            control,
            target,
            eased_progress,
        )

        for lag, radius in ((0.11, 4), (0.06, 3), (0.025, 2)):
            trail_progress = max(0.0, eased_progress - lag)
            trail_x, trail_y = self.get_quadratic_curve_point(
                start,
                control,
                target,
                trail_progress,
            )
            pygame.draw.circle(
                self.screen,
                (117, 190, 255),
                (round(trail_x), round(trail_y)),
                radius,
            )

        slip = self.create_note_slip_surface(
            self.note_transfer_animation["test_name"],
            self.note_transfer_animation["result"],
        )
        scale = 1.0 - 0.48 * eased_progress
        scaled_size = (
            max(65, round(slip.get_width() * scale)),
            max(41, round(slip.get_height() * scale)),
        )
        slip = pygame.transform.smoothscale(slip, scaled_size)
        slip = pygame.transform.rotate(slip, 7 - 18 * eased_progress)
        if progress > 0.86:
            slip.set_alpha(round(255 * (1 - (progress - 0.86) / 0.14)))
        slip_rect = slip.get_rect(center=(round(center_x), round(center_y)))
        self.screen.blit(slip, slip_rect)

    def create_note_slip_surface(self, test_name, result):
        """Create the miniature paper report used by the notebook logging animation."""

        slip = pygame.Surface((126, 80), pygame.SRCALPHA)
        paper = slip.get_rect()
        pygame.draw.rect(slip, (244, 241, 215), paper, border_radius=6)
        pygame.draw.rect(slip, (117, 190, 255), paper, width=3, border_radius=6)
        pygame.draw.rect(
            slip,
            (214, 225, 205),
            pygame.Rect(7, 7, 112, 20),
            border_radius=4,
        )

        heading = self.pile_font.render("TEST RESULT", True, (53, 83, 91))
        slip.blit(heading, heading.get_rect(center=(63, 17)))
        test_label = self.card_font.render(test_name, True, COLORS["card_text"])
        if test_label.get_width() > 110:
            test_label = self.pile_font.render(test_name, True, COLORS["card_text"])
        slip.blit(test_label, test_label.get_rect(center=(63, 38)))

        result_line = result.splitlines()[0] if result else "Result recorded"
        while self.pile_font.size(result_line)[0] > 108 and len(result_line) > 4:
            result_line = result_line[:-4].rstrip() + "..."
        result_text = self.pile_font.render(result_line, True, (69, 91, 86))
        slip.blit(result_text, result_text.get_rect(center=(63, 57)))
        pygame.draw.line(slip, (190, 199, 177), (12, 70), (114, 70), width=1)
        return slip
