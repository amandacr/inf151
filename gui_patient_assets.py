"""Cached patient art and runtime roster construction."""

import math
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

    def patient_source(self, name, expression=None):
        """Load one original alien asset and retain it for every presentation."""

        source_key = (name, expression, "source")
        if source_key not in self.patient_sprite_cache:
            suffix = f"_{expression}" if expression else ""
            asset_path = (
                Path(__file__).parent
                / "assets"
                / "patients"
                / f"{name}{suffix}.png"
            )
            if asset_path.is_file():
                source = pygame.image.load(str(asset_path)).convert_alpha()
            else:
                source = self.build_pending_patient_source(name)
            self.patient_sprite_cache[source_key] = source
        return self.patient_sprite_cache[source_key]

    def build_pending_patient_source(self, name):
        """Return unmistakable temporary art for a configured patient asset.

        Day data can safely enter the route before every final sprite is
        approved. Once ``assets/patients/<name>.png`` exists, the loader uses it
        automatically and this fallback disappears without another data edit.
        """

        accent_by_name = {
            "gribble": (177, 132, 190),
            "oola": (81, 178, 174),
            "krix": (225, 151, 70),
        }
        accent = accent_by_name.get(name, (150, 150, 170))
        outline = (48, 24, 63)
        highlight = tuple(min(255, component + 58) for component in accent)
        source = pygame.Surface((240, 360), pygame.SRCALPHA)

        # Shared temporary body keeps scale predictable in every GUI context.
        pygame.draw.line(source, outline, (86, 225), (58, 305), width=22)
        pygame.draw.line(source, outline, (154, 225), (182, 305), width=22)
        pygame.draw.line(source, accent, (86, 225), (58, 305), width=12)
        pygame.draw.line(source, accent, (154, 225), (182, 305), width=12)
        pygame.draw.ellipse(source, outline, pygame.Rect(48, 292, 46, 25))
        pygame.draw.ellipse(source, outline, pygame.Rect(146, 292, 46, 25))
        pygame.draw.ellipse(source, accent, pygame.Rect(54, 298, 35, 14))
        pygame.draw.ellipse(source, accent, pygame.Rect(151, 298, 35, 14))
        pygame.draw.ellipse(source, outline, pygame.Rect(65, 125, 110, 135))
        pygame.draw.ellipse(source, accent, pygame.Rect(73, 133, 94, 119))
        for direction in (-1, 1):
            start = (120 + direction * 42, 168)
            end = (120 + direction * 79, 235)
            pygame.draw.line(source, outline, start, end, width=20)
            pygame.draw.line(source, accent, start, end, width=11)

        if name == "gribble":
            pygame.draw.ellipse(source, outline, pygame.Rect(30, 45, 180, 95))
            pygame.draw.ellipse(source, accent, pygame.Rect(39, 53, 162, 78))
            for spot in ((83, 76, 13), (137, 66, 10), (161, 96, 9)):
                pygame.draw.circle(source, highlight, spot[:2], spot[2])
            face_center_y = 115
        elif name == "oola":
            pygame.draw.ellipse(source, outline, pygame.Rect(49, 44, 142, 125))
            pygame.draw.ellipse(source, accent, pygame.Rect(58, 53, 124, 107))
            pygame.draw.polygon(
                source,
                outline,
                ((54, 86), (21, 113), (56, 127)),
            )
            pygame.draw.polygon(
                source,
                outline,
                ((186, 86), (219, 113), (184, 127)),
            )
            pygame.draw.circle(source, highlight, (120, 184), 28)
            face_center_y = 102
        elif name == "krix":
            pygame.draw.circle(source, outline, (120, 105), 70)
            pygame.draw.circle(source, accent, (120, 105), 61)
            for angle in range(0, 360, 60):
                radians = math.radians(angle)
                center = (
                    round(120 + math.cos(radians) * 45),
                    round(105 + math.sin(radians) * 45),
                )
                pygame.draw.circle(source, highlight, center, 13)
            face_center_y = 103
        else:
            pygame.draw.circle(source, outline, (120, 105), 68)
            pygame.draw.circle(source, accent, (120, 105), 59)
            face_center_y = 103

        for eye_x in (98, 142):
            pygame.draw.ellipse(
                source,
                outline,
                pygame.Rect(eye_x - 8, face_center_y - 11, 16, 25),
            )
            pygame.draw.circle(source, (245, 249, 245), (eye_x - 3, face_center_y - 5), 3)
        pygame.draw.arc(
            source,
            outline,
            pygame.Rect(101, face_center_y + 8, 38, 23),
            0.15,
            math.pi - 0.15,
            width=4,
        )

        # A small question-mark badge announces that this is review-stage art.
        badge_center = (120, 206)
        pygame.draw.circle(source, outline, badge_center, 25)
        pygame.draw.circle(source, highlight, badge_center, 20)
        pygame.draw.arc(
            source,
            outline,
            pygame.Rect(109, 191, 22, 20),
            math.pi,
            math.pi * 2.1,
            width=4,
        )
        pygame.draw.line(source, outline, (121, 208), (121, 216), width=4)
        pygame.draw.circle(source, outline, (121, 224), 3)
        return source.convert_alpha()

    def patient_sprite(self, name, size, render_style="smooth", expression=None):
        """Scale an alien with the interpolation assigned to its destination."""

        key = (name, tuple(size), render_style, expression)
        if key not in self.patient_sprite_cache:
            source = self.patient_source(name, expression)
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
        expression=None,
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
            expression,
        )
        if key in self.patient_sprite_cache:
            return self.patient_sprite_cache[key]

        sprite = self.patient_sprite(
            name,
            size,
            render_style,
            expression=expression,
        )
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
        expression=None,
        rotation_degrees=0.0,
    ):
        """Fit an alien into a common stage or portrait frame."""

        source = self.patient_source(name, expression)
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
            expression=expression,
        )
        if rotation_degrees:
            sprite = pygame.transform.rotozoom(sprite, rotation_degrees, 1.0)
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

        idle_time = pygame.time.get_ticks()
        idle_bob = 0
        idle_sway = 0.0
        if name == "velli":
            # Velli's leaf crown drifts like a plant following a faint breeze.
            # The movement stays small enough to keep every chair grounded.
            idle_bob = round(math.sin(idle_time / 620) * 1.5)
            idle_sway = math.sin(idle_time / 910) * 1.1
        elif name == "gribble":
            # Gribble's broad cap rises and settles like a slow breath without
            # turning the patient's involuntary movement into a free clue.
            idle_bob = round(math.sin(idle_time / 690) * 1.2)
            idle_sway = math.sin(idle_time / 1050) * 0.7
        elif name == "oola":
            # Oola's light waterborne float complements her translucent gills.
            idle_bob = round(math.sin(idle_time / 610) * 1.4)
            idle_sway = math.sin(idle_time / 980) * 0.65
        elif name == "krix":
            # Krix's heavier lantern shell stays grounded with a slower pulse.
            idle_bob = round(math.sin(idle_time / 760) * 1.0)
            idle_sway = math.sin(idle_time / 1180) * 0.45
        shadow_width = round(width * 0.68)
        pygame.draw.ellipse(
            self.screen,
            (35, 27, 44),
            pygame.Rect(x - shadow_width // 2, bottom - 8, shadow_width, 11),
        )
        self.fit_patient_sprite(
            name,
            pygame.Rect(
                x - width // 2,
                bottom - height + idle_bob,
                width,
                height,
            ),
            render_style=render_style,
            presentation_scale=presentation_scale,
            rotation_degrees=idle_sway,
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
        idle_time = pygame.time.get_ticks()
        expression = None
        idle_bob = 0
        idle_sway = 0.0
        stage_offset_y = 0
        if name == "velli":
            # The examination sprite uses Velli's attentive interview face while
            # retaining a calm breathing bob and gentle leaf sway.
            expression = "interview"
            idle_bob = round(math.sin(idle_time / 470) * 1.5)
            idle_sway = math.sin(idle_time / 820) * 1.2
        elif name == "gribble":
            expression = "interview"
            idle_bob = round(math.sin(idle_time / 560) * 1.2)
            idle_sway = math.sin(idle_time / 940) * 0.7
        elif name == "oola":
            expression = "interview"
            idle_bob = round(math.sin(idle_time / 520) * 1.3)
            idle_sway = math.sin(idle_time / 900) * 0.65
            # Oola's tall reed crest needs a slightly lower stage anchor so it
            # remains inside the examination-bay window at its readable scale.
            stage_offset_y = 11
        elif name == "krix":
            expression = "interview"
            idle_bob = round(math.sin(idle_time / 680) * 1.0)
            idle_sway = math.sin(idle_time / 1080) * 0.45
            # Krix's pointed seed-cone crown uses the same lower stage anchor
            # as Oola so the readable-scale sprite stays inside the bay frame.
            stage_offset_y = 11
        bounds = pygame.Rect(0, 0, 100, bay.height - 32)
        bounds.midbottom = (
            center_x + shake_x,
            platform.centery + shake_y + idle_bob + stage_offset_y,
        )
        rect = self.fit_patient_sprite(
            name,
            bounds,
            render_style=render_style,
            presentation_scale=presentation_scale,
            expression=expression,
            rotation_degrees=idle_sway,
        )
        return pygame.Rect(rect.x, rect.y, rect.width, max(20, rect.height // 3))
