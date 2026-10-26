"""Intergalactic supply-shop screen for The Cosmic Clinic."""

import pygame

from gui_theme import COLORS
from Player import (
    CLINIC_OPERATING_FEE,
    DIAGNOSIS_REWARD,
    PERFECT_DAY_BONUS,
    WRONG_DIAGNOSIS_PENALTY,
)


SHOP_UPGRADES = (
    {"id": "temperature", "name": "THERMAL CALIBRATION", "category": "TEMPERATURE", "cost": 125,
     "description": "Upgrade to level 2. Halves the operating cost of every temperature card.", "machine": "TEMPERATURE"},
    {"id": "xray", "name": "FOCUSED X-RAY", "category": "X-RAY", "cost": 125,
     "description": "Upgrade to level 2. Halves the operating cost of every X-ray card.", "machine": "X-RAY"},
    {"id": "ultrasound", "name": "SONIC AMPLIFIER", "category": "ULTRASOUND", "cost": 175,
     "description": "Upgrade to level 2. Halves the operating cost of every ultrasound card.", "machine": "ULTRASOUND"},
    {"id": "allergy", "name": "ALLERGEN ANALYZER", "category": "ALLERGY", "cost": 200,
     "description": "Upgrade to level 2. Halves the operating cost of every allergy card.", "machine": "ALLERGY"},
    {"id": "power", "name": "EFFICIENT POWER CORE", "category": "ALL MACHINES", "cost": 150,
     "description": "Save another $2 on every test. Works with all machine calibrations.", "discount": 2},
    {"id": "smart_cards", "name": "SMART TEST CARDS", "category": "CARD UPGRADE", "cost": 100,
     "description": "Improved test cards save $1 on every test. Stacks with machine upgrades.", "discount": 1},
)


class ShopMixin:
    def draw_shop_screen(self):
        """Draw the illustrated intergalactic equipment shop."""

        panel = pygame.Rect(70, 108, 960, 508)
        pygame.draw.rect(self.screen, (3, 8, 13), panel.move(8, 9), border_radius=18)
        pygame.draw.rect(self.screen, (24, 28, 43), panel, border_radius=18)
        pygame.draw.rect(self.screen, (155, 116, 190), panel, width=3, border_radius=18)
        pygame.draw.rect(
            self.screen,
            (63, 219, 144),
            panel.inflate(-10, -10),
            width=1,
            border_radius=14,
        )

        header = pygame.Rect(90, 121, 920, 61)
        pygame.draw.rect(self.screen, (9, 17, 27), header, border_radius=10)
        pygame.draw.rect(self.screen, (93, 72, 119), header, width=1, border_radius=10)
        title = self.heading_font.render(
            "INTERGALACTIC SUPPLY SHOP",
            True,
            (232, 211, 242),
        )
        self.screen.blit(title, (109, 129))
        hint = self.card_font.render(
            "PERMANENT CLINIC UPGRADES  //  SELECT EQUIPMENT TO INSPECT",
            True,
            COLORS["muted"],
        )
        self.screen.blit(hint, (110, 158))

        balance_badge = pygame.Rect(814, 132, 176, 38)
        pygame.draw.rect(self.screen, (50, 37, 68), balance_badge, border_radius=19)
        pygame.draw.rect(
            self.screen,
            (206, 158, 233),
            balance_badge,
            width=2,
            border_radius=19,
        )
        pygame.draw.circle(
            self.screen,
            (232, 211, 242),
            (balance_badge.x + 22, balance_badge.centery),
            10,
            width=2,
        )
        credit_mark = self.card_font.render("$", True, (232, 211, 242))
        self.screen.blit(
            credit_mark,
            credit_mark.get_rect(center=(balance_badge.x + 22, balance_badge.centery)),
        )
        balance = self.small_font.render(
            f"CREDITS  {self.player.balance}",
            True,
            (232, 211, 242),
        )
        self.screen.blit(balance, balance.get_rect(center=(balance_badge.centerx + 10, balance_badge.centery)))

        for upgrade, rect in zip(SHOP_UPGRADES, self.get_shop_upgrade_rects()):
            self.draw_shop_shelf(upgrade, rect)
        selected = self.get_selected_shop_upgrade()
        owned = selected and selected["id"] in self.purchased_shop_upgrades
        can_buy = selected and not owned and self.player.balance >= selected["cost"]
        label = "SELECT AN UPGRADE"
        if selected:
            label = "INSTALLED" if owned else (f"BUY & INSTALL  ${selected['cost']}" if can_buy else f"NEED ${selected['cost'] - self.player.balance} MORE")
        mouse_position = pygame.mouse.get_pos()
        for rect, text, enabled, accent in (
            (self.shop_purchase_button, label, can_buy, (112, 255, 181)),
            (self.shop_button, "FINISH SHIFT", True, (206, 158, 233)),
        ):
            hovered = rect.collidepoint(mouse_position)
            border = accent if enabled else (71, 83, 91)
            fill = (
                tuple(min(255, channel + 25) for channel in accent)
                if enabled and hovered
                else (38, 57, 57) if enabled and accent == (112, 255, 181)
                else (50, 37, 68) if enabled
                else (25, 31, 39)
            )
            pygame.draw.rect(self.screen, (3, 8, 13), rect.move(2, 3), border_radius=8)
            pygame.draw.rect(self.screen, fill, rect, border_radius=8)
            pygame.draw.rect(self.screen, border, rect, width=2, border_radius=8)
            rendered = self.small_font.render(
                text,
                True,
                COLORS["background"] if enabled and hovered else border,
            )
            self.screen.blit(rendered, rendered.get_rect(center=rect.center))
        message = self.card_font.render(self.shop_message, True, COLORS["text"])
        self.screen.blit(message, message.get_rect(center=(550, 588)))

    def draw_day_complete_screen(self):
        """Draw the end-of-day recap as a polished clinic payroll terminal."""

        panel = pygame.Rect(130, 105, 840, 500)
        pygame.draw.rect(self.screen, (3, 8, 13), panel.move(7, 8), border_radius=16)
        pygame.draw.rect(self.screen, COLORS["panel"], panel, border_radius=16)
        pygame.draw.rect(
            self.screen,
            (103, 135, 126),
            panel,
            width=3,
            border_radius=16,
        )
        pygame.draw.rect(
            self.screen,
            COLORS["accent"],
            panel.inflate(-10, -10),
            width=1,
            border_radius=12,
        )

        header = pygame.Rect(panel.x + 24, panel.y + 20, panel.width - 48, 68)
        pygame.draw.rect(self.screen, (7, 22, 28), header, border_radius=10)
        pygame.draw.rect(self.screen, (65, 101, 98), header, width=1, border_radius=10)

        status_icon = pygame.Rect(header.x + 13, header.y + 10, 48, 48)
        pygame.draw.rect(self.screen, (12, 38, 38), status_icon, border_radius=8)
        pygame.draw.rect(
            self.screen,
            COLORS["accent"],
            status_icon,
            width=2,
            border_radius=8,
        )
        pygame.draw.line(
            self.screen,
            COLORS["accent"],
            (status_icon.x + 13, status_icon.centery),
            (status_icon.x + 21, status_icon.bottom - 14),
            width=3,
        )
        pygame.draw.line(
            self.screen,
            COLORS["accent"],
            (status_icon.x + 21, status_icon.bottom - 14),
            (status_icon.right - 11, status_icon.y + 13),
            width=3,
        )

        heading = self.heading_font.render("SHIFT COMPLETE", True, COLORS["text"])
        self.screen.blit(
            heading,
            heading.get_rect(midleft=(status_icon.right + 15, header.y + 25)),
        )
        subheading = self.card_font.render(
            "CLINIC PAYROLL REPORT  //  ALL PATIENT FILES CLOSED",
            True,
            COLORS["muted"],
        )
        self.screen.blit(
            subheading,
            subheading.get_rect(midleft=(status_icon.right + 16, header.y + 49)),
        )

        case_badge = pygame.Rect(header.right - 154, header.y + 17, 138, 34)
        pygame.draw.rect(self.screen, (11, 28, 34), case_badge, border_radius=17)
        pygame.draw.rect(
            self.screen,
            COLORS["accent"],
            case_badge,
            width=2,
            border_radius=17,
        )
        badge_text = self.card_font.render(
            f"{len(self.waiting_room_queue)} CASES FILED",
            True,
            COLORS["accent"],
        )
        self.screen.blit(badge_text, badge_text.get_rect(center=case_badge.center))

        base_pay, penalties, bonus, total = self.get_daily_pay_breakdown()
        mistake_label = (
            "WRONG DIAGNOSIS"
            if self.daily_wrong_diagnoses == 1
            else "WRONG DIAGNOSES"
        )
        recap_rows = (
            (
                "PATIENT CARE REVENUE",
                f"{self.daily_correct_diagnoses} confirmed cases × ${DIAGNOSIS_REWARD}",
                f"+${base_pay}",
                COLORS["accent"],
            ),
            (
                "DIAGNOSTIC TEST COSTS",
                f"{self.daily_test_count} machines operated",
                f"-${self.daily_test_expenses}",
                (117, 190, 255),
            ),
            (
                "DIAGNOSIS PENALTIES",
                f"{self.daily_wrong_diagnoses} {mistake_label.lower()} × ${WRONG_DIAGNOSIS_PENALTY}",
                f"-${penalties}",
                (245, 130, 115),
            ),
            (
                "PERFORMANCE BONUS",
                (
                    "Perfect-shift accuracy award"
                    if bonus
                    else "No perfect-shift bonus earned"
                ),
                f"+${bonus}",
                (216, 159, 238),
            ),
            (
                "CLINIC OPERATING FEE",
                "Daily rent, power, and medical supplies",
                f"-${CLINIC_OPERATING_FEE}",
                (232, 168, 92),
            ),
        )

        summary = pygame.Rect(panel.x + 24, header.bottom + 14, panel.width - 48, 250)
        pygame.draw.rect(self.screen, (7, 18, 24), summary, border_radius=10)
        pygame.draw.rect(self.screen, (45, 72, 72), summary, width=1, border_radius=10)
        row_height = 38
        for index, (label_text, detail_text, amount_text, row_color) in enumerate(recap_rows):
            row = pygame.Rect(
                summary.x + 10,
                summary.y + 8 + index * row_height,
                summary.width - 20,
                row_height,
            )
            pygame.draw.rect(self.screen, (10, 26, 32), row, border_radius=6)
            pygame.draw.rect(
                self.screen,
                row_color,
                pygame.Rect(row.x, row.y, 4, row.height),
                border_radius=2,
            )
            label = self.small_font.render(label_text, True, COLORS["text"])
            detail = self.card_font.render(detail_text, True, COLORS["muted"])
            amount = self.body_font.render(amount_text, True, row_color)
            self.screen.blit(label, (row.x + 16, row.y + 4))
            self.screen.blit(detail, (row.x + 16, row.y + 21))
            self.screen.blit(amount, amount.get_rect(midright=(row.right - 16, row.centery)))

        net_row = pygame.Rect(
            summary.x + 10,
            summary.bottom - 43,
            summary.width - 20,
            35,
        )
        net_color = COLORS["accent"] if total >= 0 else (245, 130, 115)
        pygame.draw.rect(self.screen, (12, 38, 38), net_row, border_radius=7)
        pygame.draw.rect(self.screen, net_color, net_row, width=2, border_radius=7)
        net_label = self.small_font.render("NET SHIFT PAY", True, net_color)
        net_amount_text = f"-${abs(total)}" if total < 0 else f"+${total}"
        net_amount = self.heading_font.render(net_amount_text, True, net_color)
        self.screen.blit(net_label, net_label.get_rect(midleft=(net_row.x + 16, net_row.centery)))
        self.screen.blit(
            net_amount,
            net_amount.get_rect(midright=(net_row.right - 16, net_row.centery)),
        )

        balance_y = summary.bottom + 17
        if self.daily_payout_applied:
            resulting_balance = self.player.balance
            current_balance = resulting_balance - total
        else:
            current_balance = self.player.balance
            resulting_balance = current_balance + total
        current = self.card_font.render(
            f"CURRENT BALANCE  ${current_balance}",
            True,
            COLORS["muted"],
        )
        resulting = self.small_font.render(
            f"AFTER PAY  ${resulting_balance}",
            True,
            COLORS["accent"],
        )
        arrow_width = 28
        balance_group_width = current.get_width() + arrow_width + resulting.get_width() + 34
        balance_x = panel.centerx - balance_group_width // 2
        self.screen.blit(current, current.get_rect(midleft=(balance_x, balance_y)))
        arrow_start = balance_x + current.get_width() + 15
        pygame.draw.line(
            self.screen,
            COLORS["panel_border"],
            (arrow_start, balance_y),
            (arrow_start + 17, balance_y),
            width=2,
        )
        pygame.draw.polygon(
            self.screen,
            COLORS["panel_border"],
            (
                (arrow_start + 17, balance_y),
                (arrow_start + 11, balance_y - 4),
                (arrow_start + 11, balance_y + 4),
            ),
        )
        self.screen.blit(
            resulting,
            resulting.get_rect(
                midleft=(
                    balance_x + current.get_width() + arrow_width + 34,
                    balance_y,
                )
            ),
        )

        hovered = self.day_complete_button.collidepoint(pygame.mouse.get_pos())
        button_fill = (23, 49, 54) if hovered else (21, 27, 39)
        pygame.draw.rect(
            self.screen,
            (3, 8, 13),
            self.day_complete_button.move(2, 3),
            border_radius=8,
        )
        pygame.draw.rect(
            self.screen,
            button_fill,
            self.day_complete_button,
            border_radius=8,
        )
        pygame.draw.rect(
            self.screen,
            COLORS["accent"],
            self.day_complete_button,
            width=2,
            border_radius=8,
        )
        coin_center = (
            self.day_complete_button.x + 24,
            self.day_complete_button.centery,
        )
        pygame.draw.circle(self.screen, COLORS["accent"], coin_center, 9, width=2)
        coin = self.card_font.render("$", True, COLORS["accent"])
        self.screen.blit(coin, coin.get_rect(center=coin_center))
        button_text = self.small_font.render(
            "COLLECT PAY  •  OPEN SUPPLY SHOP",
            True,
            COLORS["accent"],
        )
        self.screen.blit(
            button_text,
            button_text.get_rect(center=self.day_complete_button.center),
        )

    def get_daily_pay_breakdown(self):
        """Return earnings, diagnosis penalties, bonus, and net shift payout."""

        base_pay = self.daily_correct_diagnoses * DIAGNOSIS_REWARD
        penalties = self.daily_wrong_diagnoses * WRONG_DIAGNOSIS_PENALTY
        perfect_day = (
            self.daily_correct_diagnoses == len(self.waiting_room_queue)
            and self.daily_wrong_diagnoses == 0
        )
        bonus = PERFECT_DAY_BONUS if perfect_day else 0
        total = (
            base_pay
            - penalties
            - self.daily_test_expenses
            - CLINIC_OPERATING_FEE
            + bonus
        )
        return base_pay, penalties, bonus, total

    def settle_daily_pay(self):
        """Deposit the calculated shift pay exactly once."""

        if self.daily_payout_applied:
            return
        self.player.earn(self.get_daily_pay_breakdown()[3])
        self.daily_payout_applied = True

    def get_shop_upgrade_rects(self):
        """Stable three-column, two-row layout matching the concept art."""
        return [pygame.Rect(x, y, 290, 154) for y in (198, 367) for x in (95, 405, 715)]

    def get_selected_shop_upgrade(self):
        return next((item for item in SHOP_UPGRADES if item["id"] == self.selected_shop_upgrade), None)

    def handle_shop_upgrade_click(self, position):
        for upgrade, rect in zip(SHOP_UPGRADES, self.get_shop_upgrade_rects()):
            if rect.collidepoint(position):
                self.play_sfx("button")
                self.selected_shop_upgrade = upgrade["id"]
                self.shop_message = f"{upgrade['name']} " + ("is installed." if upgrade["id"] in self.purchased_shop_upgrades else "selected. Buy to install immediately.")
                return
        if not self.shop_purchase_button.collidepoint(position):
            return
        self.play_sfx("button")
        upgrade = self.get_selected_shop_upgrade()
        if upgrade is None:
            self.shop_message = "Select an upgrade first."
        elif upgrade["id"] in self.purchased_shop_upgrades:
            self.shop_message = f"{upgrade['name']} is already installed."
        elif self.player.balance < upgrade["cost"]:
            self.shop_message = f"Not enough money for {upgrade['name']} — need ${upgrade['cost']}."
        else:
            self.player.pay(upgrade["cost"])
            if "machine" in upgrade:
                self.player.machine_levels[upgrade["machine"]] = 2
            else:
                self.player.test_discount += upgrade["discount"]
            self.purchased_shop_upgrades.add(upgrade["id"])
            self.shop_message = f"Installed {upgrade['name']}. Test costs updated!"

    def draw_shop_shelf(self, upgrade, shelf):
        """Draw one illuminated shelf with a unique product illustration."""

        selected = upgrade["id"] == self.selected_shop_upgrade
        owned = upgrade["id"] in self.purchased_shop_upgrades
        hovered = shelf.collidepoint(pygame.mouse.get_pos())
        affordable = self.player.balance >= upgrade["cost"]
        product_colors = {
            "temperature": (242, 160, 83),
            "xray": (103, 176, 244),
            "ultrasound": (105, 201, 222),
            "allergy": (215, 126, 226),
            "power": (112, 255, 181),
            "smart_cards": (190, 143, 229),
        }
        product_color = product_colors[upgrade["id"]]
        border = (
            COLORS["accent"]
            if owned
            else product_color
            if selected or hovered
            else (103, 87, 124)
        )
        display = shelf.move(0, -2 if hovered and not selected else 0)

        pygame.draw.rect(self.screen, (3, 8, 13), display.move(4, 5), border_radius=11)
        pygame.draw.rect(self.screen, (12, 18, 29), display, border_radius=11)
        pygame.draw.rect(
            self.screen,
            (20, 30, 44),
            display.inflate(-8, -8),
            border_radius=8,
        )
        pygame.draw.rect(
            self.screen,
            border,
            display,
            width=3 if selected else 2 if hovered or owned else 1,
            border_radius=11,
        )

        art = pygame.Rect(display.x + 12, display.y + 13, 76, 94)
        self.draw_shop_product_illustration(
            upgrade,
            art,
            product_color,
            dimmed=not affordable and not owned,
        )

        text_x = art.right + 10
        text_width = display.right - text_x - 10
        category_text = upgrade["category"]
        if owned and "machine" in upgrade:
            category_text += "  //  LV.2"
        category = self.card_font.render(category_text, True, product_color)
        self.screen.blit(category, (text_x, display.y + 12))

        name = self.small_font.render(upgrade["name"], True, COLORS["text"])
        self.screen.blit(name, (text_x, display.y + 32))

        description_lines = self.wrap_text(
            upgrade["description"],
            self.card_font,
            text_width,
        )
        if len(description_lines) > 3:
            description_lines = description_lines[:3]
            final_line = description_lines[-1]
            while final_line and self.card_font.size(final_line + "...")[0] > text_width:
                final_line = final_line[:-1]
            description_lines[-1] = final_line.rstrip() + "..."
        for line_index, line in enumerate(description_lines):
            rendered = self.card_font.render(line, True, COLORS["muted"])
            self.screen.blit(rendered, (text_x, display.y + 56 + line_index * 16))

        footer = pygame.Rect(display.x + 5, display.bottom - 34, display.width - 10, 29)
        pygame.draw.rect(self.screen, (8, 13, 22), footer, border_radius=6)
        pygame.draw.line(
            self.screen,
            border,
            (footer.x + 4, footer.y),
            (footer.right - 4, footer.y),
            width=2,
        )
        price = self.small_font.render(f"${upgrade['cost']}", True, product_color)
        self.screen.blit(price, price.get_rect(midleft=(footer.x + 10, footer.centery)))
        if owned:
            status_text = "INSTALLED"
            status_color = COLORS["accent"]
        elif affordable:
            status_text = "SELECT" if not selected else "READY TO INSTALL"
            status_color = COLORS["text"]
        else:
            status_text = "LOCKED"
            status_color = (224, 126, 126)
        status = self.card_font.render(status_text, True, status_color)
        status_rect = status.get_rect(midright=(footer.right - 10, footer.centery))
        if owned:
            installed_icon = (status_rect.x - 9, footer.centery)
            pygame.draw.circle(self.screen, status_color, installed_icon, 5, width=1)
            pygame.draw.line(
                self.screen,
                status_color,
                (installed_icon[0] - 2, installed_icon[1]),
                (installed_icon[0], installed_icon[1] + 2),
                width=1,
            )
            pygame.draw.line(
                self.screen,
                status_color,
                (installed_icon[0], installed_icon[1] + 2),
                (installed_icon[0] + 3, installed_icon[1] - 2),
                width=1,
            )
        self.screen.blit(status, status_rect)

    def draw_shop_product_illustration(self, upgrade, frame, color, dimmed=False):
        """Draw a compact UI illustration for one shop product."""

        if dimmed:
            color = tuple((channel + 65) // 2 for channel in color)
        cx, cy = frame.center
        pygame.draw.rect(self.screen, (5, 12, 20), frame, border_radius=9)
        pygame.draw.rect(self.screen, (43, 49, 67), frame, width=1, border_radius=9)
        glow = pygame.Surface((frame.width, frame.height), pygame.SRCALPHA)
        pygame.draw.circle(
            glow,
            (*color, 24),
            (frame.width // 2, frame.height // 2),
            30,
        )
        self.screen.blit(glow, frame.topleft)
        for grid_x in range(frame.x + 13, frame.right, 17):
            pygame.draw.line(
                self.screen,
                (19, 31, 43),
                (grid_x, frame.y + 6),
                (grid_x, frame.bottom - 6),
            )

        item_id = upgrade["id"]
        if item_id == "temperature":
            pygame.draw.rect(
                self.screen,
                (22, 32, 42),
                pygame.Rect(cx - 17, cy - 29, 34, 53),
                border_radius=8,
            )
            pygame.draw.rect(
                self.screen,
                color,
                pygame.Rect(cx - 17, cy - 29, 34, 53),
                width=2,
                border_radius=8,
            )
            pygame.draw.line(self.screen, color, (cx, cy - 20), (cx, cy + 10), width=4)
            pygame.draw.circle(self.screen, color, (cx, cy + 14), 9)
            pygame.draw.circle(self.screen, (244, 223, 178), (cx - 3, cy + 11), 3)
            for offset in (-10, 0, 10):
                pygame.draw.arc(
                    self.screen,
                    color,
                    pygame.Rect(cx + offset - 5, cy - 40, 10, 16),
                    0,
                    3.14,
                    width=2,
                )
        elif item_id == "xray":
            monitor = pygame.Rect(cx - 27, cy - 27, 54, 52)
            pygame.draw.rect(self.screen, (19, 34, 48), monitor, border_radius=6)
            pygame.draw.rect(self.screen, color, monitor, width=2, border_radius=6)
            pygame.draw.line(self.screen, color, (cx - 15, cy + 18), (cx + 15, cy - 18), width=5)
            pygame.draw.circle(self.screen, (210, 235, 244), (cx - 17, cy + 20), 7)
            pygame.draw.circle(self.screen, (210, 235, 244), (cx + 17, cy - 20), 7)
            pygame.draw.circle(self.screen, (8, 18, 28), (cx - 17, cy + 20), 3)
            pygame.draw.circle(self.screen, (8, 18, 28), (cx + 17, cy - 20), 3)
        elif item_id == "ultrasound":
            emitter = pygame.Rect(cx - 28, cy - 19, 19, 38)
            pygame.draw.rect(self.screen, color, emitter, border_radius=5)
            pygame.draw.circle(self.screen, (8, 19, 28), (cx - 19, cy), 6)
            for radius in (18, 28, 38):
                pygame.draw.arc(
                    self.screen,
                    color,
                    pygame.Rect(cx - radius // 2, cy - radius, radius, radius * 2),
                    -1.05,
                    1.05,
                    width=3,
                )
        elif item_id == "allergy":
            vial = pygame.Rect(cx - 18, cy - 22, 36, 45)
            pygame.draw.rect(self.screen, (31, 26, 44), vial, border_radius=9)
            pygame.draw.rect(self.screen, color, vial, width=2, border_radius=9)
            pygame.draw.rect(self.screen, color, pygame.Rect(cx - 12, cy - 31, 24, 10), border_radius=3)
            drop = (
                (cx, cy - 11),
                (cx - 10, cy + 5),
                (cx - 7, cy + 15),
                (cx, cy + 19),
                (cx + 7, cy + 15),
                (cx + 10, cy + 5),
            )
            pygame.draw.polygon(self.screen, color, drop)
            pygame.draw.circle(self.screen, (247, 230, 250), (cx + 3, cy + 5), 3)
        elif item_id == "power":
            pygame.draw.circle(self.screen, (16, 41, 39), (cx, cy), 30)
            pygame.draw.circle(self.screen, color, (cx, cy), 30, width=3)
            pygame.draw.circle(self.screen, color, (cx, cy), 20, width=2)
            pygame.draw.circle(self.screen, (222, 255, 234), (cx, cy), 8)
            bolt = (
                (cx + 2, cy - 23),
                (cx - 11, cy + 1),
                (cx - 2, cy + 1),
                (cx - 7, cy + 23),
                (cx + 13, cy - 6),
                (cx + 3, cy - 6),
            )
            pygame.draw.polygon(self.screen, (222, 255, 234), bolt)
        else:
            card_colors = ((93, 72, 119), (49, 86, 105), (72, 122, 158))
            for index, offset in enumerate((-10, 0, 10)):
                card = pygame.Rect(cx - 23 + offset, cy - 27 + abs(offset) // 3, 37, 55)
                pygame.draw.rect(self.screen, card_colors[index], card, border_radius=5)
                pygame.draw.rect(self.screen, color, card, width=2, border_radius=5)
                pygame.draw.line(
                    self.screen,
                    (225, 235, 214),
                    (card.x + 7, card.y + 13),
                    (card.right - 7, card.y + 13),
                    width=2,
                )
                pygame.draw.circle(self.screen, (225, 235, 214), card.center, 6, width=2)

        if dimmed:
            lock = pygame.Rect(frame.right - 20, frame.bottom - 22, 14, 13)
            pygame.draw.rect(self.screen, (224, 126, 126), lock, border_radius=3)
            pygame.draw.arc(
                self.screen,
                (224, 126, 126),
                pygame.Rect(lock.x + 2, lock.y - 8, 10, 12),
                0,
                3.14,
                width=2,
            )
