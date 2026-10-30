"""Earth-abduction and wake-up cinematic for The Cosmic Clinic."""

import math

import pygame

from gui_theme import COLORS, WINDOW_SIZE


class IntroMixin:
    """Draw the opening abduction before handing control to reception."""

    INTRO_EARTH_END = 9700
    INTRO_WAKE_START = 9700
    INTRO_DIALOGUE = (
        ("CLINIC SYSTEM", "Consciousness detected. Good morning, Doctor."),
        ("YOU", "Doctor? Where am I?"),
        ("CLINIC SYSTEM", "You are aboard the Cosmic Clinic."),
        ("YOU", "Did you abduct me?"),
        ("CLINIC SYSTEM", "Yes. You are our new doctor now."),
        ("YOU", "I'm not a doctor!"),
        ("CLINIC SYSTEM", "That is unfortunate. Four patients are waiting."),
        (
            "CLINIC SYSTEM",
            "Complete your shift. Then we can discuss returning you home.",
        ),
    )

    @staticmethod
    def _intro_clamp(value):
        """Return a number constrained to the zero-to-one animation range."""

        return max(0.0, min(1.0, value))

    @staticmethod
    def _intro_smooth(progress):
        """Ease a zero-to-one progress value at both ends."""

        progress = max(0.0, min(1.0, progress))
        return progress * progress * (3 - 2 * progress)

    def draw_intro_screen(self):
        """Draw the Earth abduction followed by the reception-room wake-up."""

        elapsed = pygame.time.get_ticks() - self.intro_started_at
        if elapsed < self.INTRO_EARTH_END:
            self.draw_earth_abduction(elapsed)
        else:
            self.draw_reception_wake(elapsed - self.INTRO_WAKE_START)

        if elapsed < self.intro_duration - 250:
            skip = self.small_font.render(
                "Click anywhere or press Enter to skip",
                True,
                (184, 202, 216),
            )
            shadow = self.small_font.render(
                "Click anywhere or press Enter to skip",
                True,
                (3, 7, 14),
            )
            skip_rect = skip.get_rect(center=(WINDOW_SIZE[0] // 2, 624))
            self.screen.blit(shadow, skip_rect.move(1, 2))
            self.screen.blit(skip, skip_rect)

    def draw_earth_abduction(self, elapsed):
        """Draw a quiet hill, the arriving clinic UFO, and its tractor beam."""

        self.screen.fill((4, 9, 25))
        self.draw_earth_sky(elapsed)

        beam_on = self._intro_smooth((elapsed - 5600) / 900)
        beam_off = 1.0 - self._intro_smooth((elapsed - 7450) / 500)
        beam_progress = beam_on * beam_off
        beam_strength = beam_progress * (1.0 - 0.16 * math.sin(elapsed / 75))
        shake_progress = self._intro_clamp((elapsed - 6200) / 1100) * beam_off
        shake_x = round(math.sin(elapsed / 37) * 4 * shake_progress)
        shake_y = round(math.sin(elapsed / 51) * 2 * shake_progress)

        self.draw_earth_landscape(elapsed)
        self.draw_hill_house(elapsed, shake_x, shake_y, beam_progress)
        if beam_progress > 0:
            self.draw_intro_tractor_beam(beam_strength)
            self.draw_intro_floating_debris(elapsed, beam_progress)

        approach = self._intro_smooth((elapsed - 1700) / 3300)
        if approach > 0:
            departure = self._intro_smooth((elapsed - 7900) / 1250)
            if departure > 0:
                ship_scale = 0.44 - 0.405 * departure
                ship_center = (
                    round(550 + 255 * departure),
                    round(160 - 118 * departure),
                )
                self.draw_intro_ufo_woosh(ship_center, departure)
                self.draw_approaching_ufo(
                    ship_center,
                    max(0.035, ship_scale),
                    elapsed,
                    rotation=round(-11 * departure),
                )
            else:
                ship_scale = 0.035 + 0.405 * approach
                ship_center = (
                    round(125 + 425 * approach),
                    round(72 + 88 * approach),
                )
                self.draw_approaching_ufo(ship_center, ship_scale, elapsed)

        location_progress = self._intro_clamp(elapsed / 650)
        location_fade = 1.0 - self._intro_clamp((elapsed - 2900) / 650)
        location_alpha = round(255 * location_progress * location_fade)
        if location_alpha > 0:
            location = self.heading_font.render(
                "EARTH  —  11:47 PM",
                True,
                (218, 230, 244),
            )
            location.set_alpha(location_alpha)
            self.screen.blit(location, location.get_rect(center=(550, 72)))

        # The abduction flashes white before the ship snaps away into the distance.
        flash_in = self._intro_smooth((elapsed - 7500) / 280)
        flash_out = 1.0 - self._intro_smooth((elapsed - 7790) / 360)
        flash_progress = flash_in * flash_out
        if flash_progress > 0:
            flash = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
            flash.fill((225, 251, 255, round(255 * flash_progress)))
            self.screen.blit(flash, (0, 0))
        blackout_progress = self._intro_smooth((elapsed - 9150) / 550)
        if blackout_progress > 0:
            blackout = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
            blackout.fill((1, 3, 9, round(255 * blackout_progress)))
            self.screen.blit(blackout, (0, 0))

    def draw_earth_sky(self, elapsed):
        """Draw stars, a moon, clouds, and a tiny crossing satellite."""

        pygame.draw.circle(self.screen, (196, 213, 224), (908, 105), 46)
        pygame.draw.circle(self.screen, (169, 190, 208), (892, 91), 8)
        pygame.draw.circle(self.screen, (174, 196, 211), (925, 117), 11)
        pygame.draw.circle(self.screen, (184, 204, 218), (921, 83), 5)

        for star_index, (star_x, star_y, star_size) in enumerate(self.intro_stars):
            if star_y > 360:
                continue
            twinkle = (elapsed // 210 + star_index) % 6 == 0
            star_color = (231, 240, 255) if twinkle else (124, 153, 190)
            pygame.draw.circle(
                self.screen,
                star_color,
                (star_x, star_y),
                star_size + int(twinkle and star_size == 1),
            )

        cloud_shift = round((elapsed / 95) % 140)
        for cloud_x, cloud_y, cloud_scale in ((90, 170, 1.0), (770, 245, 0.72)):
            x = (cloud_x + cloud_shift) % 1220 - 90
            cloud = pygame.Surface((180, 55), pygame.SRCALPHA)
            pygame.draw.ellipse(cloud, (44, 57, 89, 62), pygame.Rect(0, 20, 170, 28))
            pygame.draw.ellipse(cloud, (48, 63, 96, 68), pygame.Rect(35, 5, 72, 43))
            pygame.draw.ellipse(cloud, (48, 63, 96, 62), pygame.Rect(88, 13, 62, 34))
            if cloud_scale != 1.0:
                cloud = pygame.transform.smoothscale(
                    cloud,
                    (round(cloud.get_width() * cloud_scale), round(cloud.get_height() * cloud_scale)),
                )
            self.screen.blit(cloud, (x, cloud_y))

        satellite_progress = self._intro_clamp((elapsed - 450) / 3000)
        if 0 < satellite_progress < 1:
            satellite_x = round(80 + 500 * satellite_progress)
            satellite_y = round(132 - 55 * satellite_progress)
            pygame.draw.line(
                self.screen,
                (107, 150, 184),
                (satellite_x - 12, satellite_y + 4),
                (satellite_x + 12, satellite_y - 4),
                width=2,
            )
            pygame.draw.rect(
                self.screen,
                (91, 142, 181),
                pygame.Rect(satellite_x - 19, satellite_y - 2, 10, 7),
                width=1,
            )
            pygame.draw.rect(
                self.screen,
                (91, 142, 181),
                pygame.Rect(satellite_x + 9, satellite_y - 5, 10, 7),
                width=1,
            )
            pygame.draw.circle(self.screen, (218, 230, 228), (satellite_x, satellite_y), 4)

    def draw_earth_landscape(self, elapsed):
        """Draw layered mountains, rolling fields, fencing, and natural trees."""

        pygame.draw.polygon(
            self.screen,
            (10, 22, 42),
            (
                (0, 416), (105, 335), (210, 411), (392, 294),
                (575, 409), (748, 310), (916, 386), (1100, 326),
                (1100, 650), (0, 650),
            ),
        )
        pygame.draw.polygon(
            self.screen,
            (15, 35, 49),
            (
                (0, 455), (155, 373), (312, 438), (493, 350),
                (692, 445), (875, 368), (1100, 432), (1100, 650), (0, 650),
            ),
        )
        pygame.draw.ellipse(self.screen, (18, 45, 48), pygame.Rect(-150, 390, 1400, 410))
        pygame.draw.ellipse(self.screen, (24, 61, 55), pygame.Rect(-25, 440, 1150, 330))
        pygame.draw.ellipse(self.screen, (30, 72, 61), pygame.Rect(115, 485, 870, 260))

        # A winding drive and old fence ground the house in the hillside.
        pygame.draw.polygon(
            self.screen,
            (58, 61, 58),
            ((524, 501), (578, 501), (681, 650), (389, 650)),
        )
        pygame.draw.polygon(
            self.screen,
            (72, 71, 64),
            ((536, 501), (568, 501), (622, 650), (451, 650)),
        )
        for fence_x in (96, 151, 206, 812, 867, 922, 977):
            pygame.draw.polygon(
                self.screen,
                (75, 69, 63),
                (
                    (fence_x - 4, 469), (fence_x + 4, 467),
                    (fence_x + 3, 528), (fence_x - 5, 530),
                ),
            )
        for rail_y in (484, 507):
            pygame.draw.line(self.screen, (82, 75, 67), (94, rail_y), (225, rail_y - 5), width=4)
            pygame.draw.line(self.screen, (82, 75, 67), (810, rail_y - 2), (986, rail_y + 5), width=4)

        sway = math.sin(elapsed / 580) * 4
        for tree_x, tree_y, tree_scale in (
            (145, 460, 1.08),
            (255, 477, 0.72),
            (845, 458, 1.13),
            (967, 482, 0.68),
        ):
            self.draw_intro_tree(tree_x, tree_y, tree_scale, sway)

        for grass_x in range(32, 1080, 47):
            grass_y = 548 + (grass_x * 13) % 72
            grass_color = (42, 92, 68) if grass_x % 3 else (50, 104, 73)
            pygame.draw.line(self.screen, grass_color, (grass_x, grass_y), (grass_x - 4, grass_y - 8), width=1)
            pygame.draw.line(self.screen, grass_color, (grass_x, grass_y), (grass_x + 5, grass_y - 10), width=1)

    def draw_intro_tree(self, x, ground_y, scale, sway):
        """Draw a shaded trunk, branches, and an irregular layered canopy."""

        trunk_half = round(7 * scale)
        trunk_top = round(ground_y - 82 * scale)
        pygame.draw.polygon(
            self.screen,
            (45, 38, 39),
            (
                (x - trunk_half - 3, ground_y),
                (x + trunk_half + 3, ground_y),
                (x + trunk_half, trunk_top),
                (x - trunk_half + 2, trunk_top),
            ),
        )
        pygame.draw.polygon(
            self.screen,
            (66, 48, 42),
            (
                (x - 2, ground_y), (x + trunk_half + 1, ground_y),
                (x + trunk_half - 1, trunk_top), (x + 1, trunk_top + 3),
            ),
        )
        branch_color = (57, 43, 41)
        pygame.draw.line(
            self.screen,
            branch_color,
            (x, trunk_top + round(25 * scale)),
            (x - round(27 * scale), trunk_top + round(5 * scale)),
            width=max(2, round(5 * scale)),
        )
        pygame.draw.line(
            self.screen,
            branch_color,
            (x + round(2 * scale), trunk_top + round(20 * scale)),
            (x + round(30 * scale), trunk_top - round(5 * scale)),
            width=max(2, round(5 * scale)),
        )

        crown_x = round(x + sway * scale)
        crown_y = trunk_top - round(12 * scale)
        canopy = (
            (-32, 4, 29, (13, 48, 43)),
            (29, 7, 28, (15, 55, 47)),
            (-13, -28, 31, (16, 62, 50)),
            (18, -24, 29, (19, 70, 55)),
            (0, 4, 36, (20, 68, 53)),
            (-32, -19, 22, (24, 75, 57)),
            (34, -15, 21, (26, 81, 59)),
        )
        for offset_x, offset_y, radius, color in canopy:
            pygame.draw.circle(
                self.screen,
                color,
                (
                    crown_x + round(offset_x * scale),
                    crown_y + round(offset_y * scale),
                ),
                round(radius * scale),
            )
        pygame.draw.ellipse(
            self.screen,
            (44, 102, 70),
            pygame.Rect(
                crown_x - round(22 * scale),
                crown_y - round(35 * scale),
                round(31 * scale),
                round(13 * scale),
            ),
        )

    def draw_hill_house(self, elapsed, shake_x, shake_y, beam_progress):
        """Draw a detailed two-story home and rattle it inside the tractor beam."""

        house_x = 430 + shake_x
        house_y = 390 + shake_y
        beam_lift = round(20 * beam_progress)
        wall_color = (72 + beam_lift, 76 + beam_lift, 84 + beam_lift)
        trim_color = (147, 142, 140)
        wall = pygame.Rect(house_x, house_y, 240, 151)

        # Deep shadow, foundation, and clapboard siding add depth to the facade.
        pygame.draw.ellipse(
            self.screen,
            (9, 24, 27),
            pygame.Rect(house_x - 42, house_y + 132, 324, 44),
        )
        pygame.draw.rect(self.screen, (43, 45, 52), wall)
        pygame.draw.rect(self.screen, wall_color, wall.inflate(-6, -4))
        for siding_y in range(house_y + 10, house_y + 140, 13):
            pygame.draw.line(
                self.screen,
                (59 + beam_lift, 63 + beam_lift, 72 + beam_lift),
                (house_x + 4, siding_y),
                (house_x + 236, siding_y),
                width=1,
            )
        foundation = pygame.Rect(house_x - 3, house_y + 137, 246, 17)
        pygame.draw.rect(self.screen, (48, 48, 53), foundation)
        pygame.draw.line(self.screen, (99, 96, 94), foundation.topleft, foundation.topright, width=2)

        roof_points = (
            (house_x - 26, house_y + 7),
            (house_x + 120, house_y - 104),
            (house_x + 266, house_y + 7),
        )
        pygame.draw.polygon(
            self.screen,
            (34 + beam_lift // 2, 35 + beam_lift // 2, 45 + beam_lift // 2),
            roof_points,
        )
        pygame.draw.lines(
            self.screen,
            (124, 116, 119),
            False,
            roof_points,
            width=5,
        )
        for roof_y in range(house_y - 72, house_y - 2, 13):
            width = round((roof_y - (house_y - 104)) * 1.28)
            pygame.draw.line(
                self.screen,
                (56, 55, 67),
                (house_x + 120 - width, roof_y),
                (house_x + 120 + width, roof_y),
                width=2,
            )
        pygame.draw.line(
            self.screen,
            (167, 153, 149),
            (house_x - 27, house_y + 8),
            (house_x + 267, house_y + 8),
            width=5,
        )

        chimney = pygame.Rect(house_x + 198, house_y - 75, 30, 72)
        pygame.draw.rect(self.screen, (72, 58, 58), chimney)
        pygame.draw.rect(self.screen, (133, 105, 98), chimney, width=3)
        for brick_y in range(chimney.y + 11, chimney.bottom, 13):
            pygame.draw.line(self.screen, (102, 79, 76), (chimney.x + 2, brick_y), (chimney.right - 2, brick_y), width=1)
        pygame.draw.rect(self.screen, (42, 40, 45), pygame.Rect(chimney.x - 3, chimney.y - 4, chimney.width + 6, 7))

        flicker = beam_progress > 0 and int(elapsed / 105) % 4 == 0
        warm_light = (116, 101, 80) if flicker else (255, 202, 104)
        upper_window = pygame.Rect(house_x + 91, house_y - 55, 58, 45)
        pygame.draw.rect(self.screen, warm_light, upper_window, border_radius=3)
        pygame.draw.rect(self.screen, trim_color, upper_window, width=4, border_radius=3)
        pygame.draw.line(self.screen, (84, 70, 60), upper_window.midtop, upper_window.midbottom, width=3)
        pygame.draw.line(self.screen, (84, 70, 60), upper_window.midleft, upper_window.midright, width=3)
        pygame.draw.polygon(
            self.screen,
            (39, 39, 49),
            (
                (upper_window.x - 11, upper_window.y + 2),
                (upper_window.centerx, upper_window.y - 29),
                (upper_window.right + 11, upper_window.y + 2),
            ),
        )
        pygame.draw.lines(
            self.screen,
            (125, 117, 119),
            False,
            (
                (upper_window.x - 11, upper_window.y + 2),
                (upper_window.centerx, upper_window.y - 29),
                (upper_window.right + 11, upper_window.y + 2),
            ),
            width=3,
        )

        for window_x in (house_x + 25, house_x + 169):
            window = pygame.Rect(window_x, house_y + 48, 45, 51)
            pygame.draw.rect(self.screen, (45, 65, 79), window)
            pygame.draw.rect(self.screen, trim_color, window, width=5)
            pygame.draw.line(self.screen, (110, 123, 128), window.midtop, window.midbottom, width=2)
            pygame.draw.line(self.screen, (110, 123, 128), window.midleft, window.midright, width=2)
            pygame.draw.polygon(
                self.screen,
                (70, 55, 67),
                ((window.x + 5, window.y + 4), (window.centerx - 2, window.y + 4), (window.x + 5, window.y + 25)),
            )

        door = pygame.Rect(house_x + 97, house_y + 62, 47, 78)
        pygame.draw.rect(self.screen, (38, 38, 47), door, border_radius=2)
        pygame.draw.rect(self.screen, (111, 103, 100), door, width=3, border_radius=2)
        pygame.draw.rect(self.screen, (48, 55, 64), pygame.Rect(door.x + 8, door.y + 10, 31, 22), width=2)
        pygame.draw.circle(self.screen, (239, 199, 103), (door.right - 9, door.centery + 9), 3)

        porch_roof = pygame.Rect(house_x + 72, house_y + 48, 96, 10)
        pygame.draw.polygon(
            self.screen,
            (46, 46, 53),
            ((porch_roof.x - 10, porch_roof.y), (porch_roof.centerx, porch_roof.y - 25), (porch_roof.right + 10, porch_roof.y)),
        )
        pygame.draw.rect(self.screen, (133, 124, 119), porch_roof)
        for post_x in (porch_roof.x + 4, porch_roof.right - 8):
            pygame.draw.rect(self.screen, (126, 119, 114), pygame.Rect(post_x, porch_roof.bottom, 5, 81))
        for step_index in range(3):
            step = pygame.Rect(
                house_x + 89 - step_index * 6,
                house_y + 140 + step_index * 5,
                63 + step_index * 12,
                6,
            )
            pygame.draw.rect(self.screen, (73, 71, 70), step)

        for bush_x, bush_y, radius in (
            (house_x + 9, house_y + 126, 19),
            (house_x + 29, house_y + 130, 16),
            (house_x + 210, house_y + 128, 18),
            (house_x + 231, house_y + 131, 14),
        ):
            pygame.draw.circle(self.screen, (19, 61, 49), (bush_x, bush_y), radius)
            pygame.draw.circle(self.screen, (31, 83, 59), (bush_x - 4, bush_y - 5), max(4, radius - 6))

    def draw_approaching_ufo(self, center, scale, elapsed, rotation=0):
        """Scale the established Cosmic Clinic saucer from a distant light."""

        scaled_size = (
            max(1, round(self.intro_ufo_surface.get_width() * scale)),
            max(1, round(self.intro_ufo_surface.get_height() * scale)),
        )
        ship = pygame.transform.smoothscale(self.intro_ufo_surface, scaled_size)
        if rotation:
            ship = pygame.transform.rotate(ship, rotation)
        pulse = 0.82 + 0.18 * math.sin(elapsed / 95)
        # Multiply the existing per-pixel alpha instead of setting alpha on the
        # entire transformed surface. This preserves truly transparent corners
        # around the rotated ship instead of displaying a rectangular layer.
        ship.fill(
            (255, 255, 255, round(255 * pulse)),
            special_flags=pygame.BLEND_RGBA_MULT,
        )
        self.screen.blit(ship, ship.get_rect(center=center))

    def draw_intro_tractor_beam(self, strength):
        """Draw the widening translucent beam that surrounds the house."""

        beam = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        alpha = round(80 * strength)
        pygame.draw.polygon(
            beam,
            (116, 229, 237, alpha),
            ((515, 238), (585, 238), (722, 550), (378, 550)),
        )
        pygame.draw.polygon(
            beam,
            (194, 244, 246, round(alpha * 0.45)),
            ((535, 242), (565, 242), (646, 548), (454, 548)),
        )
        pygame.draw.ellipse(
            beam,
            (151, 241, 231, round(alpha * 0.75)),
            pygame.Rect(378, 525, 344, 54),
            width=3,
        )
        self.screen.blit(beam, (0, 0))

    def draw_intro_floating_debris(self, elapsed, beam_progress):
        """Lift distinct leaves, papers, twigs, petals, and yard decorations."""

        rise = self._intro_smooth((elapsed - 6100) / 2100)
        for index in range(27):
            base_x = 382 + (index * 47) % 338
            base_y = 535 + (index % 5) * 15
            drift = math.sin(elapsed / 145 + index * 1.7) * (9 + index % 7)
            x = round(base_x + drift)
            y = round(base_y - rise * (58 + (index * 37) % 205))
            leaf_color = (
                (73, 116, 66)
                if index % 3 == 0
                else (111, 145, 74)
                if index % 3 == 1
                else (151, 126, 65)
            )
            leaf = pygame.Surface((13, 8), pygame.SRCALPHA)
            pygame.draw.ellipse(leaf, leaf_color, pygame.Rect(1, 2, 11, 5))
            pygame.draw.line(leaf, (61, 85, 54), (2, 5), (11, 3), width=1)
            leaf = pygame.transform.rotate(
                leaf,
                (elapsed / 7 + index * 41) % 360,
            )
            self.screen.blit(leaf, leaf.get_rect(center=(x, y)))

        # Loose notes flip through the cone with visible ruled-paper details.
        for index in range(5):
            paper_x = round(
                430
                + index * 62
                + math.sin(elapsed / 130 + index) * (15 + index * 2)
            )
            paper_y = round(568 - rise * (105 + index * 42))
            paper = pygame.Surface((25, 18), pygame.SRCALPHA)
            pygame.draw.polygon(
                paper,
                (220, 217, 188),
                ((1, 1), (21, 0), (24, 15), (4, 17)),
            )
            for rule_y in (5, 9, 13):
                pygame.draw.line(paper, (118, 137, 132), (6, rule_y), (19, rule_y - 1), width=1)
            paper = pygame.transform.rotate(
                paper,
                math.sin(elapsed / 120 + index) * 32,
            )
            self.screen.blit(paper, paper.get_rect(center=(paper_x, paper_y)))

        # Twigs and flower petals make the beam feel like it is pulling up the yard.
        for index in range(6):
            twig_x = round(404 + index * 53 + math.sin(elapsed / 115 + index) * 13)
            twig_y = round(555 - rise * (72 + index * 31))
            angle = elapsed / 170 + index
            end_x = round(twig_x + math.cos(angle) * 16)
            end_y = round(twig_y + math.sin(angle) * 16)
            pygame.draw.line(self.screen, (91, 67, 51), (twig_x, twig_y), (end_x, end_y), width=3)
            pygame.draw.line(self.screen, (116, 83, 59), (twig_x, twig_y), (end_x, end_y), width=1)

        for index in range(12):
            petal_x = round(395 + (index * 59) % 315 + math.sin(elapsed / 90 + index) * 10)
            petal_y = round(550 - rise * (35 + (index * 29) % 160))
            petal_color = (230, 133, 176) if index % 2 else (235, 188, 116)
            pygame.draw.ellipse(self.screen, petal_color, pygame.Rect(petal_x, petal_y, 5, 3))

        # A loose trash-can lid tumbles slowly above the driveway.
        lid_x = round(405 + math.sin(elapsed / 180) * 20)
        lid_y = round(575 - rise * 150)
        pygame.draw.ellipse(self.screen, (69, 82, 87), pygame.Rect(lid_x - 18, lid_y - 6, 36, 12))
        pygame.draw.arc(
            self.screen,
            (157, 171, 171),
            pygame.Rect(lid_x - 18, lid_y - 6, 36, 12),
            math.pi,
            math.pi * 2,
            width=2,
        )
        pygame.draw.rect(self.screen, (112, 124, 126), pygame.Rect(lid_x - 5, lid_y - 9, 10, 4), border_radius=2)

        # A tiny garden flamingo is the last wonderfully unnecessary object to lift.
        flamingo_y = round(548 - rise * 105)
        flamingo_x = round(675 + math.sin(elapsed / 190) * 10)
        pygame.draw.circle(self.screen, (233, 113, 167), (flamingo_x, flamingo_y), 5)
        pygame.draw.line(
            self.screen,
            (233, 113, 167),
            (flamingo_x - 4, flamingo_y + 3),
            (flamingo_x - 10, flamingo_y + 12),
            width=2,
        )
        pygame.draw.line(
            self.screen,
            (210, 144, 172),
            (flamingo_x, flamingo_y + 5),
            (flamingo_x, flamingo_y + 17),
            width=1,
        )

    def draw_intro_ufo_woosh(self, center, departure):
        """Draw tapered speed trails behind the saucer as it leaves the hill."""

        trails = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        alpha = round(180 * math.sin(departure * math.pi))
        trail_origin = (455, 232)
        for index, offset in enumerate((-38, -19, 0, 19, 38)):
            start = (trail_origin[0] + offset, trail_origin[1] + abs(offset) // 3)
            end = (
                center[0] - round((34 - abs(index - 2) * 4) * departure),
                center[1] + round((18 + abs(index - 2) * 5) * departure),
            )
            pygame.draw.line(
                trails,
                (102, 217, 232, max(0, alpha - abs(index - 2) * 24)),
                start,
                end,
                width=max(1, 4 - abs(index - 2)),
            )
        self.screen.blit(trails, (0, 0))

    def draw_reception_wake(self, wake_elapsed):
        """Reveal the real reception room through two groggy blinks."""

        openness = self.get_intro_blink_openness(wake_elapsed)
        wake_progress = self._intro_clamp(wake_elapsed / 3100)
        sign_progress = self._intro_clamp((wake_elapsed - 1150) / 1350)
        sign_flicker = 1.0
        if 0 < sign_progress < 0.82:
            sign_flicker = 0.35 if int(wake_elapsed / 105) % 3 == 0 else 1.0

        reception = pygame.Surface(WINDOW_SIZE).convert()
        real_screen = self.screen
        self.screen = reception
        self.intro_wake_active = True
        try:
            self.draw_intro_reception_view(round(255 * sign_progress * sign_flicker))
        finally:
            self.intro_wake_active = False
            self.screen = real_screen

        blur_progress = self._intro_clamp(wake_elapsed / 2300)
        if blur_progress < 1:
            blur_factor = 5 if blur_progress < 0.45 else 3
            reduced = pygame.transform.smoothscale(
                reception,
                (WINDOW_SIZE[0] // blur_factor, WINDOW_SIZE[1] // blur_factor),
            )
            reception = pygame.transform.smoothscale(reduced, WINDOW_SIZE)
        self.screen.blit(reception, (0, 0))

        dim_alpha = round(145 * (1 - wake_progress))
        if dim_alpha > 0:
            dim = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
            dim.fill((3, 8, 18, dim_alpha))
            self.screen.blit(dim, (0, 0))

        self.draw_intro_eyelids(openness)

    def start_intro_dialogue(self):
        """Start the short conversation that follows the player's abduction."""

        self.intro_dialogue_active = True
        self.intro_dialogue_index = 0
        self.intro_dialogue_started_at = pygame.time.get_ticks()

    def advance_intro_dialogue(self):
        """Advance one line, then hand control to the first-shift orientation."""

        if not self.intro_dialogue_active:
            return
        if self.intro_dialogue_index < len(self.INTRO_DIALOGUE) - 1:
            self.intro_dialogue_index += 1
            self.intro_dialogue_started_at = pygame.time.get_ticks()
        else:
            self.finish_intro_dialogue()

    def finish_intro_dialogue(self):
        """Close the abduction conversation and reveal the gameplay briefing."""

        self.intro_dialogue_active = False
        self.intro_dialogue_started_at = None
        self.start_guided_tutorial()

    def draw_intro_dialogue(self):
        """Draw the clinic system and player conversation over reception."""

        speaker, line = self.INTRO_DIALOGUE[self.intro_dialogue_index]
        elapsed = pygame.time.get_ticks() - self.intro_dialogue_started_at

        # The clinic scans its unwilling new employee after the protest.
        if self.intro_dialogue_index == 6:
            scan_progress = (elapsed % 1700) / 1700
            scan_y = round(110 + 365 * scan_progress)
            scan = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
            pygame.draw.line(
                scan,
                (100, 238, 221, 42),
                (45, scan_y),
                (1055, scan_y),
                width=18,
            )
            pygame.draw.line(
                scan,
                (166, 255, 237, 150),
                (45, scan_y),
                (1055, scan_y),
                width=2,
            )
            self.screen.blit(scan, (0, 0))

        dim = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        dim.fill((1, 4, 10, 72))
        self.screen.blit(dim, (0, 0))

        system_speaking = speaker == "CLINIC SYSTEM"
        accent = (100, 238, 193) if system_speaking else (136, 190, 255)
        panel = pygame.Rect(132, 451, 836, 153)
        cut = 15
        panel_points = (
            (panel.x + cut, panel.y),
            (panel.right - cut, panel.y),
            (panel.right, panel.y + cut),
            (panel.right, panel.bottom - cut),
            (panel.right - cut, panel.bottom),
            (panel.x + cut, panel.bottom),
            (panel.x, panel.bottom - cut),
            (panel.x, panel.y + cut),
        )
        shadow_points = tuple((x + 7, y + 8) for x, y in panel_points)

        glow = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        pygame.draw.polygon(glow, (*accent, 20), panel_points)
        pygame.draw.lines(glow, (*accent, 40), True, panel_points, width=12)
        self.screen.blit(glow, (0, 0))
        pygame.draw.polygon(self.screen, (1, 5, 10), shadow_points)
        pygame.draw.polygon(self.screen, (9, 22, 31), panel_points)

        # Faint terminal scan lines keep the panel technological without hurting readability.
        panel_texture = pygame.Surface(panel.size, pygame.SRCALPHA)
        for texture_y in range(8, panel.height, 8):
            pygame.draw.line(
                panel_texture,
                (*accent, 9),
                (12, texture_y),
                (panel.width - 12, texture_y),
            )
        self.screen.blit(panel_texture, panel.topleft)
        pygame.draw.lines(self.screen, accent, True, panel_points, width=2)
        pygame.draw.line(
            self.screen,
            (*accent,),
            (panel.x + 22, panel.y + 52),
            (panel.right - 22, panel.y + 52),
            width=1,
        )

        icon_center = (panel.x + 37, panel.y + 27)
        pygame.draw.circle(self.screen, (4, 13, 20), icon_center, 15)
        pygame.draw.circle(self.screen, accent, icon_center, 15, width=2)
        if system_speaking:
            pygame.draw.circle(self.screen, accent, icon_center, 4)
            for offset_x, offset_y in ((0, -9), (9, 0), (0, 9), (-9, 0)):
                endpoint = (icon_center[0] + offset_x, icon_center[1] + offset_y)
                pygame.draw.line(self.screen, accent, icon_center, endpoint, width=1)
                pygame.draw.circle(self.screen, accent, endpoint, 2)
        else:
            pygame.draw.circle(
                self.screen,
                accent,
                (icon_center[0], icon_center[1] - 4),
                4,
            )
            pygame.draw.arc(
                self.screen,
                accent,
                pygame.Rect(icon_center[0] - 8, icon_center[1] + 2, 16, 10),
                math.pi,
                math.pi * 2,
                width=2,
            )

        badge = pygame.Rect(panel.x + 61, panel.y + 12, 176, 31)
        badge_fill = (15, 57, 54) if system_speaking else (23, 43, 71)
        pygame.draw.rect(self.screen, badge_fill, badge, border_radius=5)
        pygame.draw.rect(self.screen, accent, badge, width=1, border_radius=5)
        speaker_label = self.dialogue_speaker_font.render(speaker, True, accent)
        self.screen.blit(speaker_label, speaker_label.get_rect(center=badge.center))

        line_surface = self.dialogue_body_font.render(line, True, (232, 240, 235))
        self.screen.blit(line_surface, (panel.x + 31, panel.y + 71))

        dot_start_x = panel.x + 32
        dot_y = panel.bottom - 23
        for dot_index in range(len(self.INTRO_DIALOGUE)):
            completed = dot_index <= self.intro_dialogue_index
            dot_color = accent if completed else (55, 76, 84)
            dot_radius = 4 if dot_index == self.intro_dialogue_index else 3
            pygame.draw.circle(
                self.screen,
                dot_color,
                (dot_start_x + dot_index * 17, dot_y),
                dot_radius,
            )

    def draw_intro_reception_view(self, sign_alpha):
        """Draw reception without controls so it can power on during the blink."""

        self.screen.fill(COLORS["background"])
        self.draw_game_logo((WINDOW_SIZE[0] // 2, 38), scale=0.86, alpha=sign_alpha)
        subtitle = self.small_font.render("RECEPTION", True, COLORS["muted"])
        subtitle.set_alpha(sign_alpha)
        self.screen.blit(subtitle, subtitle.get_rect(center=(WINDOW_SIZE[0] // 2, 76)))
        self.draw_reception_room()
        self.draw_reception_status()
        self.draw_waiting_room_windows()
        self.draw_waiting_room_door()
        self.draw_waiting_room_chairs()
        self.draw_waiting_room_aliens()
        self.draw_reception_desk()

    def get_intro_blink_openness(self, wake_elapsed):
        """Return eyelid openness for a small blink, a wider blink, then waking."""

        keyframes = (
            (0, 0.0),
            (360, 0.24),
            (590, 0.0),
            (1120, 0.58),
            (1390, 0.0),
            (2350, 1.0),
        )
        if wake_elapsed <= keyframes[0][0]:
            return keyframes[0][1]
        for (start_time, start_value), (end_time, end_value) in zip(keyframes, keyframes[1:]):
            if wake_elapsed <= end_time:
                progress = self._intro_smooth(
                    (wake_elapsed - start_time) / (end_time - start_time)
                )
                return start_value + (end_value - start_value) * progress
        return 1.0

    def draw_intro_eyelids(self, openness):
        """Cover the reception view with curved upper and lower eyelids."""

        if openness >= 0.995:
            return
        center_y = WINDOW_SIZE[1] // 2
        half_gap = openness * 335
        points_x = list(range(0, WINDOW_SIZE[0] + 1, 44))
        if points_x[-1] != WINDOW_SIZE[0]:
            points_x.append(WINDOW_SIZE[0])

        top_curve = []
        bottom_curve = []
        for x in points_x:
            edge = abs(x - WINDOW_SIZE[0] / 2) / (WINDOW_SIZE[0] / 2)
            curve = half_gap * edge * edge
            top_curve.append((x, round(center_y - half_gap + curve)))
            bottom_curve.append((x, round(center_y + half_gap - curve)))

        eyelid_color = (1, 3, 8)
        pygame.draw.polygon(
            self.screen,
            eyelid_color,
            [(0, 0), (WINDOW_SIZE[0], 0)] + list(reversed(top_curve)),
        )
        pygame.draw.polygon(
            self.screen,
            eyelid_color,
            [(0, WINDOW_SIZE[1]), (WINDOW_SIZE[0], WINDOW_SIZE[1])]
            + list(reversed(bottom_curve)),
        )
