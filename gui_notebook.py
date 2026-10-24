"""Notebook preview, layout, and navigation helpers for the GUI."""

import math

import pygame

from gui_state import GameState
from gui_theme import COLORS, TEST_SUBTITLES, WINDOW_SIZE


class NotebookMixin:
    """Supply notebook behavior and preview rendering to the main GUI object."""

    def build_notebook_rects(self):
        """Build the rectangles that position the notebook's pages and buttons."""

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

    def update_notebook_preview_animation(self, should_open):
        """Smoothly move the miniature notebook toward its requested open state."""

        now = pygame.time.get_ticks()
        elapsed = max(0, min(50, now - self.notebook_preview_last_tick))
        self.notebook_preview_last_tick = now
        direction = 1 if should_open else -1
        step = elapsed / self.notebook_preview_duration
        self.notebook_preview_progress = max(
            0.0,
            min(1.0, self.notebook_preview_progress + direction * step),
        )
        progress = self.notebook_preview_progress
        return 1 - (1 - progress) ** 3

    def get_notebook_test_count_label(self):
        """Return a compact test count that fits on the miniature notebook page."""

        entries = self.notebook.get_entries(self.patient)
        test_count = sum(test_name != "No tests" for test_name in entries)
        if test_count == 0:
            return "NO TESTS"
        if test_count == 1:
            return "1 TEST"
        return f"{test_count} TESTS"

    def notebook_has_test_results(self):
        """Return whether the notebook should remain open after its first recorded test."""

        return self.get_notebook_test_count_label() != "NO TESTS"

    def draw_notebook(self):
        """Draw notes that open on hover, then stay open after the first test."""

        panel = self.layout["notebook"]
        hovered = panel.collidepoint(pygame.mouse.get_pos())
        has_results = self.notebook_has_test_results()
        stays_open = has_results and self.state != GameState.TEST_RESULT
        progress = self.update_notebook_preview_animation(hovered or stays_open)

        attention_progress = 0.0
        if self.notebook_attention_started_at is not None:
            attention_elapsed = (
                pygame.time.get_ticks() - self.notebook_attention_started_at
            )
            attention_progress = max(
                0.0,
                min(1.0, attention_elapsed / self.notebook_attention_duration),
            )
        attention_bounce = math.sin(attention_progress * math.pi)
        lift = round(7 * progress + 5 * attention_bounce)

        page_width = 70
        book_height = round(110 - 6 * progress)
        closed_spine_x = panel.centerx - page_width // 2
        spine_x = round(closed_spine_x + (panel.centerx - closed_spine_x) * progress)
        book_y = panel.y + 13 - lift
        book_bottom = book_y + book_height
        left_extent = round(page_width * progress)

        cover_color = (82, 58, 112)
        cover_dark = (54, 39, 78)
        cover_highlight = (171, 123, 203)
        page_color = (240, 237, 211)
        page_edge = (174, 160, 176)
        rule_color = (188, 196, 174)

        glow = pygame.Surface(panel.size, pygame.SRCALPHA)
        pulse = (math.sin(pygame.time.get_ticks() / 650) + 1) / 2
        glow_alpha = round(
            18 + 12 * pulse + 16 * progress + 65 * attention_bounce
        )
        pygame.draw.ellipse(
            glow,
            (173, 118, 208, glow_alpha),
            pygame.Rect(8, 5, panel.width - 16, panel.height - 27),
        )
        self.screen.blit(glow, panel.topleft)

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
                title = self.card_font.render("PATIENT", True, (245, 225, 255))
                subtitle = self.card_font.render("NOTES", True, (245, 225, 255))
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
            count_label = self.get_notebook_test_count_label()
            note_surface = self.notebook_preview_font.render(
                count_label,
                True,
                COLORS["card_text"],
            )
            note_surface.set_alpha(note_alpha)
            note_rect = note_surface.get_rect(
                center=(right_page.centerx, book_y + 24)
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
                (right_page.right - 18, book_y + 18),
            )

        if hovered:
            hover_label = self.card_font.render(
                "VIEW NOTES" if has_results else "OPEN NOTEBOOK",
                True,
                COLORS["accent"],
            )
            self.screen.blit(
                hover_label,
                hover_label.get_rect(center=(panel.centerx, panel.bottom - 5)),
            )

        if attention_bounce > 0.05:
            notice = self.card_font.render(
                "NEW NOTE!",
                True,
                (117, 190, 255),
            )
            notice.set_alpha(round(255 * attention_bounce))
            self.screen.blit(
                notice,
                notice.get_rect(center=(panel.centerx, panel.y + 3 - lift)),
            )

    def draw_notebook_screen(self):
        """Dim the workspace and draw a decorated field-notebook spread."""

        dim = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        dim.fill((0, 0, 0, 185))
        self.screen.blit(dim, (0, 0))

        layout = self.notebook_layout
        book = layout["book"]
        pygame.draw.rect(self.screen, (4, 9, 13), book.move(9, 11), border_radius=16)
        pygame.draw.rect(self.screen, (70, 48, 88), book, border_radius=16)
        pygame.draw.rect(
            self.screen,
            (190, 132, 211),
            book,
            width=3,
            border_radius=16,
        )

        left_page = pygame.Rect(
            book.x + 14,
            book.y + 14,
            book.width // 2 - 14,
            book.height - 28,
        )
        right_page = pygame.Rect(
            book.centerx,
            book.y + 14,
            book.width // 2 - 14,
            book.height - 28,
        )
        self.draw_notebook_paper(left_page, (244, 239, 214))
        self.draw_notebook_paper(right_page, (240, 235, 209))

        spine = pygame.Rect(book.centerx - 8, book.y + 13, 16, book.height - 26)
        pygame.draw.rect(self.screen, (51, 42, 60), spine)
        pygame.draw.line(
            self.screen,
            (124, 103, 133),
            (spine.x + 3, spine.y),
            (spine.x + 3, spine.bottom),
            width=2,
        )
        pygame.draw.line(
            self.screen,
            (26, 31, 34),
            (spine.right - 3, spine.y),
            (spine.right - 3, spine.bottom),
            width=2,
        )
        for stitch_y in range(spine.y + 18, spine.bottom - 10, 28):
            pygame.draw.line(
                self.screen,
                (194, 174, 150),
                (spine.x + 5, stitch_y),
                (spine.right - 5, stitch_y + 7),
                width=2,
            )

        tab_data = (
            (
                "PATIENT FILE",
                pygame.Rect(left_page.x + 24, left_page.y - 5, 118, 25),
                (126, 78, 151),
            ),
            (
                "TEST LOG",
                pygame.Rect(right_page.x + 24, right_page.y - 5, 96, 25),
                (72, 122, 158),
            ),
        )
        for tab_text, tab, tab_color in tab_data:
            pygame.draw.rect(self.screen, tab_color, tab, border_radius=6)
            label = self.card_font.render(tab_text, True, (249, 240, 222))
            self.screen.blit(label, label.get_rect(center=tab.center))

        left, right = self.get_spread_columns(self.notebook_spread)
        if left is None:
            self.draw_notebook_id_page(layout["left"])
        else:
            self.draw_notebook_column(left, layout["left"], "CONTINUED NOTES")
        self.draw_notebook_column(right, layout["right"], "DIAGNOSTIC LOG")

        left_num = self.notebook_spread * 2 + 1
        for num, key in ((left_num, "left"), (left_num + 1, "right")):
            label = self.card_font.render(f"—  {num}  —", True, (112, 104, 86))
            self.screen.blit(
                label,
                label.get_rect(center=(layout[key].centerx, book.bottom - 22)),
            )

        mouse = pygame.mouse.get_pos()
        buttons = [
            ("CLOSE", layout["close"], True, COLORS["panel_border"]),
            ("< PREV", layout["prev"], self.notebook_spread > 0, (151, 101, 180)),
            (
                "NEXT >",
                layout["next"],
                self.notebook_spread < self.notebook_spread_count() - 1,
                (151, 101, 180),
            ),
        ]
        for text, rect, enabled, resting_color in buttons:
            if not enabled:
                continue
            color = COLORS["accent"] if rect.collidepoint(mouse) else resting_color
            pygame.draw.rect(
                self.screen,
                (20, 24, 29),
                rect.move(3, 4),
                border_radius=7,
            )
            pygame.draw.rect(self.screen, color, rect, border_radius=6)
            label = self.small_font.render(text, True, COLORS["background"])
            self.screen.blit(label, label.get_rect(center=rect.center))

    def draw_notebook_paper(self, page, paper_color):
        """Draw one warm ruled page with stacked edges and a folded corner."""

        for offset in (6, 3):
            pygame.draw.rect(
                self.screen,
                (204, 198, 173),
                page.move(0, offset),
                border_radius=7,
            )
        pygame.draw.rect(self.screen, paper_color, page, border_radius=7)
        pygame.draw.rect(
            self.screen,
            (202, 194, 166),
            page,
            width=1,
            border_radius=7,
        )
        for line_y in range(page.y + 62, page.bottom - 18, 25):
            pygame.draw.line(
                self.screen,
                (203, 216, 203),
                (page.x + 18, line_y),
                (page.right - 18, line_y),
                width=1,
            )
        pygame.draw.line(
            self.screen,
            (224, 169, 163),
            (page.x + 31, page.y + 42),
            (page.x + 31, page.bottom - 18),
            width=1,
        )
        fold = (
            (page.right - 25, page.y),
            (page.right, page.y),
            (page.right, page.y + 25),
        )
        pygame.draw.polygon(self.screen, (218, 211, 184), fold)
        pygame.draw.line(
            self.screen,
            (187, 181, 158),
            (page.right - 25, page.y),
            (page.right, page.y + 25),
        )

    def draw_notebook_column(self, column, rect, page_heading):
        """Draw test results as clipped diagnostic entries on a ruled page."""

        ink = (54, 68, 67)
        heading = self.notebook_title_font.render(page_heading, True, ink)
        heading_y = rect.y + 18
        self.screen.blit(heading, (rect.x + 5, heading_y))
        entry_count = sum(
            1
            for kind, text, _ in column
            if kind == "title" and text.upper() != "NO TESTS"
        )
        count_text = (
            "NO RECORDS"
            if entry_count == 0
            else f"{entry_count} RECORD" + ("" if entry_count == 1 else "S")
        )
        count_label = self.card_font.render(count_text, True, (103, 117, 108))
        self.screen.blit(
            count_label,
            count_label.get_rect(midright=(rect.right - 5, heading_y + 14)),
        )

        content = pygame.Rect(rect.x, rect.y + 63, rect.width, rect.height - 63)
        groups = []
        current_group = []
        for item in column:
            if item[0] == "title" and current_group:
                groups.append(current_group)
                current_group = []
            current_group.append(item)
        if current_group:
            groups.append(current_group)

        test_colors = {
            "TEMPERATURE": COLORS["panel_border"],
            "ULTRASOUND": (85, 145, 230),
            "X-RAY": (67, 178, 132),
            "ALLERGY": (191, 91, 211),
            "NO TESTS": (151, 101, 180),
        }
        for group in groups:
            title = group[0][1]
            first_y = group[0][2]
            last_kind, _, last_y = group[-1]
            last_height = (
                self.notebook_title_font.get_linesize()
                if last_kind == "title"
                else self.notebook_body_font.get_linesize()
            )
            card = pygame.Rect(
                content.x,
                content.y + first_y,
                content.width,
                max(58, last_y - first_y + last_height + 12),
            )
            accent = test_colors.get(title.upper(), COLORS["panel_border"])
            pygame.draw.rect(self.screen, (231, 227, 204), card, border_radius=8)
            pygame.draw.rect(self.screen, accent, card, width=2, border_radius=8)
            pygame.draw.rect(
                self.screen,
                accent,
                pygame.Rect(card.x, card.y, 6, card.height),
                border_radius=4,
            )
            icon = pygame.Rect(card.x + 15, card.y + 10, 33, 33)
            pygame.draw.rect(self.screen, (205, 216, 204), icon, border_radius=5)
            pygame.draw.rect(self.screen, accent, icon, width=2, border_radius=5)
            if title.upper() in TEST_SUBTITLES:
                self.draw_test_icon(title.upper(), icon, accent)
            else:
                question = self.small_font.render("?", True, accent)
                self.screen.blit(question, question.get_rect(center=icon.center))

            title_surface = self.notebook_title_font.render(title, True, ink)
            self.screen.blit(title_surface, (card.x + 57, card.y + 8))
            for kind, text, y in group[1:]:
                if kind != "body":
                    continue
                surface = self.notebook_body_font.render(text, True, (72, 91, 84))
                self.screen.blit(surface, (card.x + 57, content.y + y + 5))

    def draw_notebook_id_page(self, rect):
        """Draw a patient header and two clipped information cards."""

        ink = (54, 68, 67)
        header = pygame.Rect(rect.x, rect.y, rect.width, 58)
        pygame.draw.rect(self.screen, (229, 221, 204), header, border_radius=9)
        pygame.draw.rect(
            self.screen,
            (151, 101, 180),
            header,
            width=2,
            border_radius=9,
        )
        portrait = pygame.Rect(header.x + 9, header.y + 7, 44, 44)
        self.draw_notebook_patient_stamp(portrait)
        name = self.heading_font.render(self.patient.name, True, ink)
        self.screen.blit(
            name,
            name.get_rect(midleft=(portrait.right + 10, header.centery - 5)),
        )
        case_id = self.card_font.render(
            f"CASE {self.get_current_entry()['serial']}", True, (111, 91, 124)
        )
        self.screen.blit(
            case_id,
            case_id.get_rect(midleft=(portrait.right + 11, header.centery + 17)),
        )

        y = header.bottom + 12
        y = self.draw_notebook_info_section(
            "INTERGALACTIC ID",
            self.patient.profile.items(),
            rect,
            y,
            (72, 122, 158),
        )
        self.draw_notebook_info_section(
            "HEALTH ID",
            self.patient.medical_info.items(),
            rect,
            y + 10,
            (126, 78, 151),
        )

    def draw_notebook_patient_stamp(self, portrait):
        """Draw a tiny stamped portrait of the current alien patient."""

        entry = self.get_current_entry()
        if entry["exam"] is None:
            self.draw_zorpa_patient_stamp(portrait)
            return

        background, border = entry["portrait"][0], entry["portrait"][1]
        pygame.draw.rect(self.screen, background, portrait, border_radius=6)
        pygame.draw.rect(self.screen, border, portrait, width=2, border_radius=6)

        # Draw the exam sprite off-screen, then crop around the head
        layer = pygame.Surface((166, 133), pygame.SRCALPHA)
        bay = layer.get_rect()
        platform = pygame.Rect(bay.centerx - 67, bay.bottom - 20, 134, 17)
        real_screen = self.screen
        self.screen = layer
        try:
            head = entry["exam"](bay, bay.centerx, platform, 0, 0, False)
        finally:
            self.screen = real_screen

        side = max(head.width, head.height) + 16
        crop = pygame.Rect(0, 0, side, side)
        crop.center = head.center
        crop = crop.clip(layer.get_rect())
        face = layer.subsurface(crop).copy()

        target = portrait.width - 8
        scale = min(target / crop.width, target / crop.height)
        size = (max(1, round(crop.width * scale)), max(1, round(crop.height * scale)))
        face = pygame.transform.smoothscale(face, size)
        self.screen.blit(face, face.get_rect(center=portrait.center))

    def draw_zorpa_patient_stamp(self, portrait):
        """Draw a tiny stamped portrait of the current alien patient."""

        pygame.draw.rect(self.screen, (205, 190, 219), portrait, border_radius=6)
        pygame.draw.rect(
            self.screen,
            (126, 78, 151),
            portrait,
            width=2,
            border_radius=6,
        )
        head_center = (portrait.centerx, portrait.y + 19)
        pygame.draw.line(
            self.screen,
            (70, 43, 94),
            (head_center[0] - 8, head_center[1] - 9),
            (head_center[0] - 11, head_center[1] - 15),
            width=2,
        )
        pygame.draw.line(
            self.screen,
            (70, 43, 94),
            (head_center[0] + 8, head_center[1] - 9),
            (head_center[0] + 11, head_center[1] - 15),
            width=2,
        )
        pygame.draw.circle(
            self.screen,
            (151, 99, 211),
            (head_center[0] - 11, head_center[1] - 15),
            3,
        )
        pygame.draw.circle(
            self.screen,
            (151, 99, 211),
            (head_center[0] + 11, head_center[1] - 15),
            3,
        )
        pygame.draw.ellipse(
            self.screen,
            (151, 99, 211),
            pygame.Rect(head_center[0] - 13, head_center[1] - 10, 26, 22),
        )
        pygame.draw.circle(
            self.screen,
            (50, 35, 68),
            (head_center[0] - 5, head_center[1]),
            2,
        )
        pygame.draw.circle(
            self.screen,
            (50, 35, 68),
            (head_center[0] + 5, head_center[1]),
            2,
        )
        pygame.draw.ellipse(
            self.screen,
            (151, 99, 211),
            pygame.Rect(portrait.centerx - 9, portrait.y + 29, 18, 13),
        )

    def draw_notebook_info_section(self, heading, items, rect, y, accent):
        """Draw one labeled patient-information card and return its bottom edge."""

        body_h = self.notebook_body_font.get_linesize()
        rows = []
        for label, value in items:
            rows.extend(
                self.wrap_text(
                    f"{label}: {value}",
                    self.notebook_body_font,
                    rect.width - 42,
                )
            )
        section = pygame.Rect(rect.x, y, rect.width, 36 + len(rows) * body_h + 8)
        pygame.draw.rect(self.screen, (231, 227, 204), section, border_radius=8)
        pygame.draw.rect(self.screen, accent, section, width=2, border_radius=8)
        title_bar = pygame.Rect(section.x, section.y, section.width, 30)
        pygame.draw.rect(self.screen, accent, title_bar, border_radius=8)
        pygame.draw.rect(
            self.screen,
            accent,
            pygame.Rect(title_bar.x, title_bar.bottom - 8, title_bar.width, 8),
        )
        title = self.card_font.render(heading, True, (249, 240, 222))
        self.screen.blit(
            title,
            title.get_rect(midleft=(title_bar.x + 12, title_bar.centery)),
        )

        row_y = title_bar.bottom + 6
        for row_index, row in enumerate(rows):
            pygame.draw.circle(
                self.screen,
                accent,
                (section.x + 15, row_y + body_h // 2),
                3,
            )
            surface = self.notebook_body_font.render(row, True, (72, 91, 84))
            self.screen.blit(surface, (section.x + 25, row_y))
            row_y += body_h
            if row_index < len(rows) - 1:
                pygame.draw.line(
                    self.screen,
                    (205, 201, 180),
                    (section.x + 25, row_y - 2),
                    (section.right - 12, row_y - 2),
                )
        return section.bottom

    def build_notebook_columns(self):
        """Split the patient's test entries into page-sized columns."""

        width = self.notebook_layout["right"].width - 73
        height = self.notebook_layout["right"].height - 63
        title_h = self.notebook_title_font.get_linesize()
        body_h = self.notebook_body_font.get_linesize()
        card_gap = 10
        columns = [[]]
        used = 0
        for test_name, result in self.notebook.get_entries(self.patient).items():
            result_lines = self.wrap_text(result, self.notebook_body_font, width)
            card_height = max(58, title_h + len(result_lines) * body_h + 12)
            if columns[-1] and used + card_height > height:
                columns.append([])
                used = 0

            start_y = used
            columns[-1].append(("title", test_name.upper(), start_y))
            for line_index, line in enumerate(result_lines):
                columns[-1].append(
                    ("body", line, start_y + title_h + line_index * body_h)
                )
            used += card_height + card_gap

        self.notebook_columns = columns

    def notebook_spread_count(self):
        """Return the number of two-page spreads needed for all notebook columns."""

        extra = max(0, len(self.notebook_columns) - 1)
        return 1 + (extra + 1) // 2

    def get_spread_columns(self, spread):
        """Return the left and right columns for a notebook spread."""

        columns = self.notebook_columns
        if spread == 0:
            return None, columns[0]
        left_index, right_index = 2 * spread - 1, 2 * spread
        left = columns[left_index] if left_index < len(columns) else []
        right = columns[right_index] if right_index < len(columns) else []
        return left, right

    def open_notebook(self):
        """Rebuild the current notes and open the notebook at its first spread."""

        self.play_sfx("notebook")
        self.build_notebook_columns()
        self.notebook_spread = 0
        self.state = GameState.NOTEBOOK

    def flip_notebook(self, direction):
        """Move one notebook spread left or right when the destination exists."""

        new_spread = self.notebook_spread + direction
        if 0 <= new_spread < self.notebook_spread_count():
            self.notebook_spread = new_spread

    def handle_notebook_click(self, position):
        """Handle notebook close and page-navigation button clicks."""

        if self.notebook_layout["close"].collidepoint(position):
            self.play_sfx("button")
            self.state = GameState.PATIENT
        elif self.notebook_layout["prev"].collidepoint(position):
            self.play_sfx("button")
            self.flip_notebook(-1)
        elif self.notebook_layout["next"].collidepoint(position):
            self.play_sfx("button")
            self.flip_notebook(1)
