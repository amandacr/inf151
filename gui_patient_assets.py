"""Cached patient art and runtime roster construction."""

from functools import partial
from pathlib import Path

import pygame

from PlanetData import get_destination


SHIFT_CHAIR_POSITIONS = (782, 640, 498, 356)


class PatientAssetMixin:
    def roster_for_destination(self, destination):
        """Bind destination patient data to this GUI's drawing callbacks."""

        if destination is None:
            return []
        roster = []
        render_style = destination.theme.alien_render_style
        for patient_slot, chair_x in zip(
            destination.patient_roster,
            SHIFT_CHAIR_POSITIONS,
        ):
            roster.append(
                {
                    "chair_x": chair_x,
                    "draw": partial(
                        self.draw_waiting_asset,
                        patient_slot.asset,
                        chair_x,
                        render_style=render_style,
                        presentation_scale=patient_slot.presentation_scale,
                    ),
                    "create": patient_slot.create,
                    "exam": partial(
                        self.draw_exam_asset,
                        patient_slot.asset,
                        render_style=render_style,
                        presentation_scale=patient_slot.presentation_scale,
                    ),
                    "serial": patient_slot.serial,
                    "portrait": patient_slot.portrait,
                    "asset": patient_slot.asset,
                    "destination_key": destination.key,
                    "render_style": render_style,
                    "presentation_scale": patient_slot.presentation_scale,
                }
            )
        return roster

    def roster_for_day(self, day_number):
        """Return fresh runtime entries for one configured campaign day."""

        return self.roster_for_destination(get_destination(day_number))

    def patient_source(self, name):
        """Load one original alien asset and retain it for every presentation."""

        source_key = (name, "source")
        if source_key not in self.patient_sprite_cache:
            asset_path = Path(__file__).parent / "assets" / "patients" / f"{name}.png"
            self.patient_sprite_cache[source_key] = pygame.image.load(
                str(asset_path)
            ).convert_alpha()
        return self.patient_sprite_cache[source_key]

    def patient_sprite(self, name, size, render_style="smooth"):
        """Scale an alien with the interpolation assigned to its destination."""

        key = (name, tuple(size), render_style)
        if key not in self.patient_sprite_cache:
            source = self.patient_source(name)
            scaler = (
                pygame.transform.scale
                if render_style == "pixel"
                else pygame.transform.smoothscale
            )
            self.patient_sprite_cache[key] = scaler(source, size)
        return self.patient_sprite_cache[key]

    def outlined_patient_sprite(
        self,
        name,
        size,
        render_style="smooth",
        outline_width=1,
    ):
        """Give every planet's artwork the same outer silhouette treatment."""

        outline_color = (48, 24, 63, 255)
        key = (
            name,
            tuple(size),
            render_style,
            "outline",
            outline_width,
            outline_color,
        )
        if key in self.patient_sprite_cache:
            return self.patient_sprite_cache[key]

        sprite = self.patient_sprite(name, size, render_style)
        if outline_width <= 0:
            return sprite
        mask = pygame.mask.from_surface(sprite)
        silhouette = mask.to_surface(
            setcolor=outline_color,
            unsetcolor=(0, 0, 0, 0),
        ).convert_alpha()
        presented = pygame.Surface(
            (
                sprite.get_width() + outline_width * 2,
                sprite.get_height() + outline_width * 2,
            ),
            pygame.SRCALPHA,
        )
        for offset_x in range(-outline_width, outline_width + 1):
            for offset_y in range(-outline_width, outline_width + 1):
                if offset_x == 0 and offset_y == 0:
                    continue
                presented.blit(
                    silhouette,
                    (outline_width + offset_x, outline_width + offset_y),
                )
        presented.blit(sprite, (outline_width, outline_width))
        self.patient_sprite_cache[key] = presented
        return presented

    def fit_patient_sprite(
        self,
        name,
        bounds,
        render_style="smooth",
        presentation_scale=1.0,
        anchor="midbottom",
        outline_width=1,
    ):
        """Fit an alien into a common stage or portrait frame."""

        source = self.patient_source(name)
        scale = min(bounds.width / source.get_width(), bounds.height / source.get_height())
        scale *= presentation_scale
        size = (
            max(1, round(source.get_width() * scale)),
            max(1, round(source.get_height() * scale)),
        )
        sprite = self.outlined_patient_sprite(
            name,
            size,
            render_style,
            outline_width,
        )
        rect = sprite.get_rect()
        if anchor == "center":
            rect.center = bounds.center
        else:
            rect.midbottom = bounds.midbottom
        self.screen.blit(sprite, rect)
        return rect

    def draw_waiting_asset(
        self,
        name,
        x,
        width=90,
        height=133,
        bottom=469,
        render_style="smooth",
        presentation_scale=1.0,
    ):
        """Present every waiting alien on the same grounded chair stage."""

        shadow_width = round(width * 0.68)
        pygame.draw.ellipse(
            self.screen,
            (35, 27, 44),
            pygame.Rect(x - shadow_width // 2, bottom - 8, shadow_width, 11),
        )
        self.fit_patient_sprite(
            name,
            pygame.Rect(x - width // 2, bottom - height, width, height),
            render_style=render_style,
            presentation_scale=presentation_scale,
        )

    def draw_exam_asset(
        self,
        name,
        bay,
        center_x,
        platform,
        shake_x,
        shake_y,
        blinking,
        render_style="smooth",
        presentation_scale=1.0,
    ):
        bounds = pygame.Rect(0, 0, 100, bay.height - 32)
        bounds.midbottom = (center_x + shake_x, platform.centery + shake_y)
        rect = self.fit_patient_sprite(
            name,
            bounds,
            render_style=render_style,
            presentation_scale=presentation_scale,
        )
        return pygame.Rect(rect.x, rect.y, rect.width, max(20, rect.height // 3))
