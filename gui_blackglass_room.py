"""Code-drawn Blackglass Outpost reception: grime, wrecked wall, swamp window."""

import math
import random

import pygame

from gui_theme import WINDOW_SIZE


def draw_jagged_crack(surface, rng, start, steps, dx, dy, bounds,
                      color=(24, 12, 6, 235), width=2, glow=None):
    """Draw a jagged crack (optionally glowing) and return its points."""

    x, y = start
    points = [(x, y)]
    for _ in range(steps):
        x = max(bounds.left, min(bounds.right, x + rng.randint(*dx)))
        y = max(bounds.top, min(bounds.bottom, y + rng.randint(*dy)))
        points.append((x, y))
    if glow is not None:
        pygame.draw.lines(surface, glow, False, points, width + 3)
    pygame.draw.lines(surface, (150, 106, 62), False,
                      [(px + 2, py) for px, py in points], 1)
    pygame.draw.lines(surface, color, False, points, width)
    return points


class BlackglassRoomMixin:
    """Blackglass reception decay, window panorama, and desk clutter."""

    # Screen-space (room) and window-local (pits, vents) layout constants.
    BLACKGLASS_PUDDLES = ((150, 520, 70, 16), (560, 548, 84, 18), (790, 478, 56, 12))
    BLACKGLASS_PILES = ((74, 540), (430, 556), (805, 548))
    BLACKGLASS_PITS = ((300, 200, 110, 22), (430, 214, 130, 18),
                       (560, 196, 90, 16), (690, 222, 110, 16))
    BLACKGLASS_VENTS = ((250, 198), (360, 212), (470, 210), (610, 202), (730, 216))
    BLACKGLASS_SPARK = (34, 200)

    def blit_alpha_shape(self, target, shape, color, rect, width=0):
        """Blend a translucent shape (pygame.draw alone will not blend alpha)."""

        tmp = pygame.Surface(rect.size, pygame.SRCALPHA)
        if shape == "ellipse":
            pygame.draw.ellipse(tmp, color, tmp.get_rect(), width)
        else:
            pygame.draw.rect(tmp, color, tmp.get_rect(), width)
        target.blit(tmp, rect.topleft)

    # ------------------------------------------------------------------ room

    def get_blackglass_decay_layer(self):
        layer = getattr(self, "blackglass_decay_layer", None)
        if layer is None:
            layer = self.build_blackglass_decay_layer()
            self.blackglass_decay_layer = layer
        return layer

    def build_blackglass_decay_layer(self):
        """Pre-render static grime: wall slivers, floor cracks, puddles, garbage."""

        rng = random.Random(404)
        layer = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        wall = pygame.Rect(21, 93, WINDOW_SIZE[0] - 42, 312)
        wall_bounds = pygame.Rect(22, 150, WINDOW_SIZE[0] - 44, 254)
        floor_bounds = pygame.Rect(24, 408, 1052, 166)

        # Translucent layers first (later alpha draws overwrite earlier pixels).
        for stripe_x in range(wall.x, wall.right, 34):
            pygame.draw.rect(layer, (160, 112, 62, 46), (stripe_x, wall.y, 14, wall.height))
            for diamond_y in range(wall.y + 10, wall.bottom, 38):
                cx = stripe_x + 24
                pygame.draw.polygon(layer, (70, 42, 24, 60), (
                    (cx, diamond_y - 6), (cx + 5, diamond_y),
                    (cx, diamond_y + 6), (cx - 5, diamond_y)))
        for _ in range(9):
            sx = rng.randrange(wall.x + 20, wall.right - 20)
            sw, sh = rng.randrange(50, 130), rng.randrange(40, 120)
            pygame.draw.ellipse(layer, (58, 34, 16, 34), (sx - sw // 2, wall.y - sh // 3, sw, sh))
        for i in range(26):  # baseboard grime
            pygame.draw.line(layer, (18, 9, 4, round(90 * (1 - i / 26))),
                             (wall.x, 404 - i), (wall.right, 404 - i))
        for _ in range(16):  # floor stains
            fx, fy = rng.randrange(40, 1040), rng.randrange(415, 565)
            pygame.draw.ellipse(layer, (20, 10, 6, 60),
                                (fx, fy, rng.randrange(30, 90), rng.randrange(8, 22)))
        for cx, cy, pw, ph in self.BLACKGLASS_PUDDLES:  # acid sludge
            pygame.draw.ellipse(layer, (34, 24, 12, 210), (cx - pw // 2 - 3, cy - ph // 2 - 2, pw + 6, ph + 4))
            pygame.draw.ellipse(layer, (92, 112, 28, 225), (cx - pw // 2, cy - ph // 2, pw, ph))
            pygame.draw.ellipse(layer, (60, 84, 22, 230), (cx - pw // 2 + 7, cy - ph // 2 + 3, pw - 14, ph - 6))
            pygame.draw.ellipse(layer, (176, 206, 72, 170), (cx - pw // 4, cy - ph // 4, pw // 4, max(2, ph // 4)))

        # Cracks in the visible wall slivers (left edge, beside the door).
        for start, lean in (((29, 166), (-1, 2)), ((838, 166), (-3, 3)), ((1070, 166), (-3, 1))):
            pts = draw_jagged_crack(layer, rng, start, 14, lean, (8, 16), wall_bounds)
            for pt in pts[3::4]:
                draw_jagged_crack(layer, rng, pt, 3, (-6, 6), (4, 9), wall_bounds, width=1)

        # Floor cracks; two glow from the heat underneath.
        for start, glow in (((60, 430), None), ((500, 572), (236, 112, 36, 140)),
                            ((860, 420), None), ((250, 410), (236, 112, 36, 140))):
            pts = draw_jagged_crack(layer, rng, start, 16, (10, 28), (-7, 9), floor_bounds, glow=glow)
            for pt in pts[3::4]:
                draw_jagged_crack(layer, rng, pt, 3, (-12, 12), (4, 9), floor_bounds, width=1)

        for hx, hy in ((262, 505), (690, 440)):  # missing tiles
            hole = ((hx - 22, hy), (hx - 6, hy - 10), (hx + 18, hy - 6),
                    (hx + 26, hy + 7), (hx, hy + 13), (hx - 18, hy + 9))
            pygame.draw.polygon(layer, (20, 10, 6, 255), hole)
            pygame.draw.ellipse(layer, (226, 100, 30, 210), (hx - 10, hy - 2, 20, 6))
            pygame.draw.polygon(layer, (150, 106, 62, 255), hole, 1)

        def trash(kind, x, y):
            if kind == 0:  # crumpled paper
                r = rng.randint(4, 7)
                pygame.draw.circle(layer, (176, 166, 140, 255), (x, y), r)
                pygame.draw.circle(layer, (110, 100, 84, 255), (x, y), r, 1)
                pygame.draw.line(layer, (120, 110, 92, 255), (x - r + 2, y - 1), (x + r - 2, y + 2), 1)
            elif kind == 1:  # tipped can
                pygame.draw.rect(layer, (150, 146, 138, 255), (x - 7, y - 3, 14, 7), border_radius=2)
                pygame.draw.rect(layer, (196, 70, 48, 255), (x - 3, y - 3, 6, 7))
            elif kind == 2:  # bottle
                pygame.draw.rect(layer, (66, 110, 52, 255), (x - 9, y - 3, 13, 6), border_radius=2)
                pygame.draw.rect(layer, (66, 110, 52, 255), (x + 3, y - 1, 7, 2))
                pygame.draw.line(layer, (150, 190, 120, 255), (x - 7, y - 2), (x + 1, y - 2), 1)
            elif kind == 3:  # wrapper
                pygame.draw.polygon(layer, (214, 168, 40, 255), (
                    (x - 6, y), (x - 1, y - 4), (x + 6, y - 1), (x + 3, y + 4), (x - 4, y + 3)))
                pygame.draw.line(layer, (150, 60, 30, 255), (x - 4, y), (x + 4, y), 1)
            elif kind == 4:  # something that used to be food
                pygame.draw.ellipse(layer, (88, 64, 30, 255), (x - 7, y - 3, 14, 7))
                pygame.draw.ellipse(layer, (122, 150, 40, 255), (x - 3, y - 2, 6, 3))
            else:  # fish bones
                bone = (222, 214, 190, 255)
                pygame.draw.line(layer, bone, (x - 9, y), (x + 9, y), 1)
                for rx in range(-6, 8, 3):
                    pygame.draw.line(layer, bone, (x + rx, y - 3), (x + rx, y + 3), 1)
                pygame.draw.circle(layer, bone, (x - 10, y), 3, 1)

        # Tipped trash bin spilling into the first pile.
        pygame.draw.polygon(layer, (74, 78, 70, 255), ((40, 498), (86, 494), (88, 520), (42, 524)))
        pygame.draw.ellipse(layer, (46, 50, 44, 255), (80, 494, 14, 26))
        pygame.draw.line(layer, (110, 114, 104, 255), (44, 503), (84, 499), 1)
        for px, py in self.BLACKGLASS_PILES:
            pygame.draw.ellipse(layer, (62, 44, 28, 255), (px - 30, py - 8, 60, 18))
            for _ in range(11):
                trash(rng.randrange(6), px + rng.randint(-28, 28), py + rng.randint(-8, 6))
        for _ in range(46):
            trash(rng.randrange(6), rng.randrange(30, 840), rng.randrange(420, 572))
        return layer

    def draw_blackglass_room_decay(self):
        """Blit the cached grime and add puddle ripples and flies."""

        elapsed = pygame.time.get_ticks()
        self.screen.blit(self.get_blackglass_decay_layer(), (0, 0))

        for index, (cx, cy, pw, ph) in enumerate(self.BLACKGLASS_PUDDLES):
            phase = (elapsed / 1400 + index * 0.3) % 1
            rx = max(2, round(pw * (0.1 + 0.35 * phase)))
            ry = max(2, round(ph * (0.1 + 0.35 * phase)))
            color = tuple(
                round(lo + (hi - lo) * (1 - phase))
                for lo, hi in zip((92, 112, 28), (176, 206, 72))
            )
            pygame.draw.ellipse(self.screen, color, (cx - rx, cy - ry, rx * 2, ry * 2), 1)

        for index in range(9):  # flies around the first two piles
            cx, cy = self.BLACKGLASS_PILES[index % 2]
            angle = elapsed / (120 + index * 17) + index * 1.7
            fx = cx + math.cos(angle) * (10 + index * 2) + math.sin(elapsed / 70 + index) * 2
            fy = cy - 8 + math.sin(angle * 1.3) * (7 + index)
            pygame.draw.circle(self.screen, (20, 14, 10), (round(fx), round(fy)), 1)

    # ---------------------------------------------------------------- window

    def get_blackglass_sprites(self):
        sprites = getattr(self, "blackglass_sprites", None)
        if sprites is not None:
            return sprites

        def soft_circle(radius, color, peak_alpha):
            surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            for step in range(radius, 0, -2):
                alpha = round(peak_alpha * (1 - step / radius))
                pygame.draw.circle(surf, (*color, alpha), (radius, radius), step)
            return surf

        acid_glow = soft_circle(54, (150, 236, 60), 170)
        haze = pygame.Surface((320, 70), pygame.SRCALPHA)
        for k in range(10, 0, -1):
            hw, hh = round(320 * k / 10), round(70 * k / 10)
            pygame.draw.ellipse(haze, (205, 120, 50, 110 - k * 10),
                                ((320 - hw) // 2, (70 - hh) // 2, hw, hh))
        self.blackglass_sprites = {
            "steam": [(r, soft_circle(r, (206, 190, 118), 200)) for r in (10, 16, 22, 30, 38, 46)],
            "sun_glow": soft_circle(120, (255, 176, 64), 150),
            "pit_glows": [pygame.transform.smoothscale(acid_glow, (int(w * 1.9), int(h * 5)))
                          for _, _, w, h in self.BLACKGLASS_PITS],
            "haze": haze,
        }
        return self.blackglass_sprites

    def get_blackglass_window_base(self):
        base = getattr(self, "blackglass_window_base", None)
        if base is None:
            base = self.build_blackglass_window_base()
            self.blackglass_window_base = base
        return base

    def build_blackglass_window_base(self):
        """Pre-render the window: panorama on the right, ruined wall in bay 1."""

        rng = random.Random(1313)
        w, h, pano_x, horizon = 792, 239, 198, 150
        base = pygame.Surface((w, h))

        top, bottom = (58, 22, 12), (226, 136, 48)  # smoggy sky
        for y in range(horizon):
            t = y / (horizon - 1)
            pygame.draw.line(base, tuple(round(a + (b - a) * t ** 1.3) for a, b in zip(top, bottom)),
                             (pano_x, y), (w, y))
        for _ in range(14):
            self.blit_alpha_shape(base, "ellipse", (120, 52, 20, rng.randint(30, 60)),
                                  pygame.Rect(rng.randint(pano_x - 40, w - 100), rng.randint(10, 130),
                                              rng.randint(120, 280), rng.randint(8, 22)))
        sun = (560, 112)  # swollen, sickly sun
        self.blit_alpha_shape(base, "ellipse", (255, 170, 60, 46), pygame.Rect(sun[0] - 120, sun[1] - 120, 240, 240))
        self.blit_alpha_shape(base, "ellipse", (255, 170, 60, 70), pygame.Rect(sun[0] - 86, sun[1] - 86, 172, 172))
        pygame.draw.circle(base, (214, 118, 36), sun, 68)
        pygame.draw.circle(base, (244, 164, 58), sun, 60)
        pygame.draw.circle(base, (250, 196, 86), (sun[0] - 8, sun[1] - 8), 38)
        for _ in range(7):
            pygame.draw.circle(base, (206, 112, 34), (sun[0] + rng.randint(-40, 40), sun[1] + rng.randint(-40, 40)), rng.randint(3, 8))
        self.blit_alpha_shape(base, "rect", (210, 98, 36, 90), pygame.Rect(480, 104, 160, 16))

        g_top, g_bottom = (170, 78, 26), (58, 24, 12)  # ground
        for y in range(horizon, h):
            t = (y - horizon) / (h - horizon - 1)
            pygame.draw.line(base, tuple(round(a + (b - a) * t) for a, b in zip(g_top, g_bottom)), (pano_x, y), (w, y))
        for i in range(11):  # black-glass spires
            cx = pano_x + 30 + i * 54 + rng.randint(-12, 12)
            sh, sw = rng.randint(26, 96), rng.randint(18, 34)
            pts = ((cx - sw // 2, horizon + 6), (cx - sw // 5, round(horizon - sh * 0.55)),
                   (cx + rng.randint(-4, 4), horizon - sh), (cx + sw // 4, round(horizon - sh * 0.5)),
                   (cx + sw // 2, horizon + 6))
            pygame.draw.polygon(base, (22, 10, 10), pts)
            pygame.draw.line(base, (190, 92, 40), pts[2], pts[1], 1)
            pygame.draw.line(base, (190, 92, 40), pts[1], pts[0], 1)
        for _ in range(9):  # murky swamp pools
            px, py = rng.randint(pano_x + 10, w - 80), rng.randint(horizon + 12, h - 14)
            pw = rng.randint(40, 90)
            pygame.draw.ellipse(base, (110, 50, 22), (px, py, pw, 9))
            pygame.draw.ellipse(base, (170, 96, 36), (px + 6, py + 2, pw // 3, 3))
        for _ in range(6):  # lava veins
            draw_jagged_crack(base, rng, (rng.randint(pano_x + 10, w - 30), horizon + 8), 6,
                              (-18, 18), (5, 12), pygame.Rect(pano_x, horizon, w - pano_x, h - horizon),
                              color=(240, 112, 30), width=1)
        for cx, cy, pw, ph in self.BLACKGLASS_PITS:  # acid pits
            self.blit_alpha_shape(base, "ellipse", (160, 240, 70, 50), pygame.Rect(cx - pw, cy - ph * 2, pw * 2, ph * 4))
            pygame.draw.ellipse(base, (46, 24, 12), (cx - pw // 2 - 4, cy - ph // 2 - 2, pw + 8, ph + 4))
            pygame.draw.ellipse(base, (96, 170, 34), (cx - pw // 2, cy - ph // 2, pw, ph))
            pygame.draw.ellipse(base, (150, 226, 60), (cx - pw // 2 + 8, cy - ph // 2 + 3, pw - 16, ph - 6))
            pygame.draw.ellipse(base, (214, 255, 150), (cx - pw // 4, cy - ph // 4, pw // 5, max(2, ph // 5)))
            for _ in range(8):
                pygame.draw.circle(base, (220, 200, 60), (cx + rng.randint(-pw // 2, pw // 2), cy + rng.choice((-1, 1)) * (ph // 2)), 1)
        for _ in range(14):  # dead thorny growths
            tx, th = rng.randint(pano_x + 6, w - 6), rng.randint(14, 34)
            pygame.draw.polygon(base, (30, 14, 10), ((tx - 3, h), (tx - 1, h - th), (tx + rng.randint(-5, 5), h - th - 8), (tx + 2, h - th), (tx + 4, h)))
        for _ in range(9):  # dirty glass streaks
            self.blit_alpha_shape(base, "rect", (40, 22, 12, 70),
                                  pygame.Rect(rng.randint(pano_x + 8, w - 10), 0, rng.randint(3, 6), rng.randint(40, 110)))
        impact = (470, 74)  # cracked glass
        for angle in range(7):
            direction = angle * 0.9 + rng.random() * 0.4
            px, py, pts = impact[0], impact[1], [impact]
            for _ in range(4):
                px += math.cos(direction) * rng.randint(10, 20) + rng.randint(-3, 3)
                py += math.sin(direction) * rng.randint(10, 20) + rng.randint(-3, 3)
                pts.append((round(px), round(py)))
            pygame.draw.lines(base, (240, 220, 180), False, pts, 1)

        # Bay 1: ruined wallpapered wall (drawn last so it covers the panorama).
        pygame.draw.rect(base, (116, 82, 50), (0, 0, pano_x, h))
        for sx in range(0, pano_x, 26):
            pygame.draw.rect(base, (132, 94, 56), (sx, 0, 12, h))
            for dy in range(10, h, 34):
                cx = sx + 19
                pygame.draw.polygon(base, (88, 58, 34), ((cx, dy - 6), (cx + 5, dy), (cx, dy + 6), (cx - 5, dy)))
        for sx_, sy_, sw_, sh_ in ((-20, -30, 120, 110), (110, -20, 110, 90), (60, 150, 90, 70)):
            self.blit_alpha_shape(base, "ellipse", (60, 36, 16, 70), pygame.Rect(sx_, sy_, sw_, sh_))
            self.blit_alpha_shape(base, "ellipse", (40, 22, 10, 90), pygame.Rect(sx_, sy_, sw_, sh_), 2)
        for dx_ in (40, 96, 150):
            self.blit_alpha_shape(base, "rect", (50, 30, 14, 70), pygame.Rect(dx_, 0, 5, rng.randint(60, 140)))
        pygame.draw.polygon(base, (92, 70, 52), ((96, 104), (190, 98), (196, 184), (158, 216), (104, 200), (90, 150)))
        base.set_clip(pygame.Rect(110, 116, 68, 60))  # exposed brick
        for row in range(7):
            for col in range(-1, 4):
                bx = 110 + col * 23 + (11 if row % 2 else 0)
                pygame.draw.rect(base, (150 + rng.randint(-14, 10), 74, 52), (bx, 116 + row * 10, 21, 9))
        base.set_clip(None)
        pygame.draw.polygon(base, (88, 66, 48), ((150, 0), (198, 0), (198, 70), (176, 56), (164, 30)))
        base.set_clip(pygame.Rect(150, 0, 48, 70))  # exposed lath
        for y_ in range(6, 70, 8):
            pygame.draw.line(base, (60, 42, 28), (150, y_), (198, y_), 2)
        base.set_clip(None)
        pygame.draw.polygon(base, (92, 70, 52), ((0, 150), (54, 160), (70, 200), (40, 232), (0, 232)))
        for pts in (((96, 104), (88, 150), (104, 160), (112, 118)),  # curled paper
                    ((54, 160), (78, 196), (64, 206), (48, 176)),
                    ((172, 70), (184, 120), (176, 132), (166, 86))):
            pygame.draw.polygon(base, (176, 128, 74), pts)
            pygame.draw.polygon(base, (110, 72, 40), pts, 2)
        for mx, my, mw, mh in ((6, 205, 70, 26), (120, 214, 70, 22)):  # mold
            self.blit_alpha_shape(base, "ellipse", (110, 150, 30, 80), pygame.Rect(mx, my, mw, mh))
        bay_bounds = pygame.Rect(0, 0, pano_x - 1, h - 1)
        for start in ((120, 0), (30, 95)):
            pts = draw_jagged_crack(base, rng, start, 11, (-8, 8), (8, 18), bay_bounds)
            for pt in pts[3::4]:
                draw_jagged_crack(base, rng, pt, 3, (-8, 8), (4, 9), bay_bounds, width=1)
        self.blit_alpha_shape(base, "ellipse", (14, 8, 6, 120), pygame.Rect(8, 140, 46, 40))
        pygame.draw.rect(base, (170, 160, 140), (22, 150, 16, 20))
        pygame.draw.rect(base, (60, 50, 40), (22, 150, 16, 20), 1)
        pygame.draw.line(base, (20, 16, 14), (30, 170), self.BLACKGLASS_SPARK, 2)
        pygame.draw.circle(base, (200, 120, 50), self.BLACKGLASS_SPARK, 2)
        pygame.draw.rect(base, (60, 38, 22), (0, h - 13, pano_x, 13))
        vig = pygame.Surface((w, h), pygame.SRCALPHA)
        for i in range(22):
            pygame.draw.rect(vig, (20, 8, 4, round(120 * (1 - i / 22) ** 2)), (i, i, w - 2 * i, h - 2 * i), 1)
        base.blit(vig, (0, 0))
        return base

    def draw_blackglass_waiting_room_windows(self):
        """Draw the hot, swampy Blackglass panorama and the wrecked bay-1 wall."""

        theme = self.get_reception_theme()
        window = pygame.Rect(37, 164, 792, 239)
        wx, wy = window.topleft
        elapsed = pygame.time.get_ticks()
        sprites = self.get_blackglass_sprites()
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(window)
        self.screen.blit(self.get_blackglass_window_base(), window.topleft)

        self.screen.set_clip(pygame.Rect(wx + 198, wy, 594, window.height))
        pulse = (math.sin(elapsed / 900) + 1) / 2
        glow = sprites["sun_glow"]
        glow.set_alpha(round(70 + 40 * pulse))
        self.screen.blit(glow, (wx + 560 - 120, wy + 112 - 120))
        for index, (cx, cy, pw, ph) in enumerate(self.BLACKGLASS_PITS):
            pit_glow = sprites["pit_glows"][index]
            pit_glow.set_alpha(round(80 + 40 * math.sin(elapsed / 500 + index)))
            self.screen.blit(pit_glow, pit_glow.get_rect(center=(wx + cx, wy + cy)))
        haze = sprites["haze"]
        haze.set_alpha(70)
        for k in range(3):  # drifting smog
            hx = ((elapsed / 70 + k * 260) % (window.width + 320)) - 320
            self.screen.blit(haze, (wx + hx, wy + 40 + k * 38))
        steam = sprites["steam"]
        for plume, (vx, vy) in enumerate(self.BLACKGLASS_VENTS):  # steam plumes
            for puff in range(7):
                t = (elapsed / 3200 + puff / 7 + plume * 0.23) % 1
                radius, sprite = steam[min(len(steam) - 1, int(t * len(steam)))]
                sprite.set_alpha(round(190 * (1 - t) ** 1.3 * min(1.0, t * 8)))
                self.screen.blit(sprite, (wx + vx + math.sin(t * 5 + plume) * 12 + t * 34 - radius,
                                          wy + vy - t * 135 - radius))
        for index, (cx, cy, pw, ph) in enumerate(self.BLACKGLASS_PITS):  # acid bubbles
            for k in range(3):
                phase = (elapsed / 1100 + k * 0.34 + index * 0.19) % 1
                bx, by = wx + cx + round((k - 1) * pw * 0.28), wy + cy - round(phase * 3)
                if phase < 0.8:
                    pygame.draw.circle(self.screen, (214, 255, 140), (bx, by), 1 + int(phase * 4), 1)
                elif phase < 0.9:
                    pygame.draw.circle(self.screen, (170, 230, 90), (bx, by), 6, 1)

        self.screen.set_clip(window)
        if (elapsed // 700) % 5 == 0 and elapsed % 700 < 140:  # sparking socket wire
            sx, sy = wx + self.BLACKGLASS_SPARK[0], wy + self.BLACKGLASS_SPARK[1]
            for angle in range(5):
                a = angle * 1.3 + elapsed / 40
                pygame.draw.line(self.screen, (255, 230, 120), (sx, sy),
                                 (sx + round(math.cos(a) * 7), sy + round(math.sin(a) * 7)), 1)
        for divider_x in (235, 433, 631):
            pygame.draw.line(self.screen, theme.structure_color, (divider_x, window.y + 4), (divider_x, window.bottom - 4), 3)
            for rivet_y in range(window.y + 20, window.bottom, 48):
                pygame.draw.circle(self.screen, (66, 40, 24), (divider_x, rivet_y), 2)
        pygame.draw.rect(self.screen, theme.structure_color, window, width=4, border_radius=13)
        self.screen.set_clip(previous_clip)

        plaque = getattr(self, "blackglass_plaque", None)  # crooked station plaque
        if plaque is None:
            plate = pygame.Surface((150, 73), pygame.SRCALPHA)
            pygame.draw.rect(plate, (58, 36, 22), plate.get_rect(), border_radius=7)
            pygame.draw.rect(plate, (180, 110, 40), plate.get_rect(), width=2, border_radius=7)
            for i, (text, color) in enumerate((
                ("BLACKGLASS OUTPOST", (232, 190, 120)),
                ("CARE (TERMS APPLY)", theme.sign_color),
                ("AIR: MOSTLY BREATHABLE", theme.secondary_color),
            )):
                label = self.pile_font.render(text, True, color)
                plate.blit(label, label.get_rect(center=(75, 17 + i * 19)))
            pygame.draw.line(plate, (20, 10, 6), (112, 0), (96, 30), 1)
            pygame.draw.line(plate, (20, 10, 6), (96, 30), (120, 47), 1)
            pygame.draw.circle(plate, (150, 150, 140), (9, 9), 3)
            self.blackglass_plaque = plaque = pygame.transform.rotate(plate, 3)
        self.screen.blit(plaque, plaque.get_rect(center=(58 + 75, 184 + 36)))

    # ------------------------------------------------------------------ desk

    def draw_blackglass_desk_clutter(self):
        """Replace the clinic plant with a dead one and some desk litter."""

        pygame.draw.ellipse(self.screen, (30, 22, 16), pygame.Rect(244, 447, 52, 10))
        for end in ((256, 410), (271, 399), (286, 414), (265, 420)):  # dead stalks
            pygame.draw.line(self.screen, (96, 74, 40), (270, 435), end, 2)
            pygame.draw.line(self.screen, (60, 46, 26), end, (end[0] + 4, end[1] + 6), 1)
        pot = pygame.Rect(249, 427, 40, 28)
        pygame.draw.rect(self.screen, (60, 38, 24), pot.move(2, 2), border_radius=7)
        pygame.draw.rect(self.screen, (98, 66, 42), pot, border_radius=7)
        pygame.draw.line(self.screen, (30, 20, 14), (262, 428), (270, 446), 1)  # crack
        pygame.draw.line(self.screen, (30, 20, 14), (270, 446), (264, 454), 1)
        pygame.draw.circle(self.screen, (176, 166, 140), (300, 452), 4)  # crumpled note
        pygame.draw.rect(self.screen, (150, 146, 138), (310, 449, 10, 6), border_radius=2)
