"""Intergalactic supply-shop screen for The Cosmic Clinic."""

import math

import pygame

from gui_theme import COLORS
from Player import (
    BLACKGLASS_DEBT_THRESHOLD,
    CLINIC_OPERATING_FEE,
    DEBT_LIMIT,
    DIAGNOSIS_REWARD,
    LIMITED_EVIDENCE_REWARD,
    MIN_TEST_OPERATING_COST,
    NO_EVIDENCE_REWARD,
    PERFECT_DAY_BONUS,
    WRONG_DIAGNOSIS_PENALTY,
)
from Test import get_test_cost as get_base_test_cost


SHOP_UPGRADES = (
    {"id": "temperature", "name": "THERMAL CALIBRATION", "category": "TEMPERATURE", "cost": 25,
     "description": "Level 2: temperature tests cost 50% less.", "machine": "TEMPERATURE"},
    {"id": "xray", "name": "FOCUSED X-RAY", "category": "X-RAY", "cost": 25,
     "description": "Level 2: X-ray tests cost 50% less.", "machine": "X-RAY"},
    {"id": "ultrasound", "name": "SONIC AMPLIFIER", "category": "ULTRASOUND", "cost": 35,
     "description": "Level 2: ultrasound tests cost 50% less.", "machine": "ULTRASOUND"},
    {"id": "allergy", "name": "ALLERGEN ANALYZER", "category": "ALLERGY", "cost": 45,
     "description": "Level 2: allergy tests cost 50% less.", "machine": "ALLERGY"},
    {"id": "blood", "name": "PLASMA SEPARATOR", "category": "BLOOD CHEMISTRY", "cost": 25,
     "description": "Level 2: blood chemistry tests cost 50% less.", "machine": "BLOOD CHEMISTRY"},
    {"id": "oxygen", "name": "RESPIRATORY TUNER", "category": "OXYGEN SCAN", "cost": 25,
     "description": "Level 2: oxygen scans cost 50% less.", "machine": "OXYGEN SCAN"},
    {"id": "toxin", "name": "TOXIN SPECTROMETER", "category": "TOXIN SCREEN", "cost": 35,
     "description": "Level 2: toxin screens cost 50% less.", "machine": "TOXIN SCREEN"},
    {"id": "neural", "name": "SYNAPSE MAPPER", "category": "NEURAL SCAN", "cost": 45,
     "description": "Level 2: neural scans cost 50% less.", "machine": "NEURAL SCAN"},
    {"id": "power", "name": "EFFICIENT POWER CORE", "category": "ALL MACHINES", "cost": 50,
     "description": "Every test costs $2 less. Stacks with calibrations.", "discount": 2},
    {"id": "smart_cards", "name": "SMART TEST CARDS", "category": "CARD UPGRADE", "cost": 30,
     "description": "Random draws cost $2 less; targeted prices rise by only $3."},
    {"id": "recycler", "name": "CARD RECYCLER", "category": "CARD MANAGEMENT", "cost": 50,
     "description": "Once per patient, swap a test card for a random one free."},
    {"id": "clinic_membership", "name": "CLINIC MEMBERSHIP", "category": "CLINIC SERVICE", "cost": 35,
     "description": "The first targeted Card Shop purchase costs only $5."},
    {"id": "expanded_case", "name": "EXPANDED CARD CASE", "category": "CARD CAPACITY", "cost": 45,
     "description": "Carry nine test cards instead of eight."},
    {"id": "deck_scanner", "name": "DECK SCANNER", "category": "CARD INTEL", "cost": 30,
     "description": "Preview the next random test card before paying to draw."},
    {"id": "recycler_mk2", "name": "RECYCLER MK II", "category": "CARD MANAGEMENT", "cost": 35,
     "description": "Recycle twice per patient instead of once.", "requires": "recycler"},
    {"id": "diagnostic_grant", "name": "DIAGNOSTIC GRANT", "category": "CARD FUNDING", "cost": 40,
     "description": "The first random draw for each patient is free."},
    {"id": "priority_processing", "name": "PRIORITY PROCESSING", "category": "CLINIC SERVICE", "cost": 45,
     "description": "Test-result scans and reports finish 40% faster."},
)

# Existing calibrations are the Efficiency path; free-use offers share their price.
_MACHINE_UPGRADES = tuple(item for item in SHOP_UPGRADES if "machine" in item)
for _item in _MACHINE_UPGRADES:
    _item["path"] = "efficiency"
    _item["description"] = "Efficiency: tests cost 50% less. Choose one path."
SHOP_UPGRADES += tuple(
    {"id": item["id"] + "_free", "name": "SHIFT ALLOWANCE",
     "category": item["machine"], "machine": item["machine"],
     "cost": item["cost"], "path": "free_use", "art_id": item["id"],
     "description": "First test free each shift; then normal cost. Choose one path."}
    for item in _MACHINE_UPGRADES
)

SHOP_SHELVES = tuple(item for item in SHOP_UPGRADES if item.get("path") != "free_use")

SHOP_COLUMNS = 2
SHOP_VISIBLE_ROWS = 2
SHOP_CATEGORY_KEYS = ("machines", "cards", "clinic", "installed")
SHOP_CATEGORY_LABELS = {
    "machines": "MACHINES",
    "cards": "CARDS",
    "clinic": "CLINIC",
    "installed": "INSTALLED",
}
SHOP_CARD_UPGRADE_IDS = {
    "smart_cards",
    "recycler",
    "expanded_case",
    "deck_scanner",
    "recycler_mk2",
    "diagnostic_grant",
}
SHOP_PRODUCT_COLORS = {
    "recycler": (105, 230, 180),
    "temperature": (242, 160, 83),
    "xray": (103, 176, 244),
    "ultrasound": (105, 201, 222),
    "allergy": (215, 126, 226),
    "blood": (245, 126, 112),
    "oxygen": (82, 209, 235),
    "toxin": (202, 226, 91),
    "neural": (195, 132, 245),
    "power": (112, 255, 181),
    "smart_cards": (190, 143, 229),
    "clinic_membership": (244, 190, 91),
    "expanded_case": (112, 181, 244),
    "deck_scanner": (93, 219, 208),
    "recycler_mk2": (89, 244, 176),
    "diagnostic_grant": (244, 153, 94),
    "priority_processing": (224, 127, 239),
}

for _item in SHOP_UPGRADES:
    if "art_id" in _item:
        SHOP_PRODUCT_COLORS[_item["id"]] = SHOP_PRODUCT_COLORS[_item["art_id"]]


class ShopMixin:
    def format_count(self, count, singular, plural=None):
        """Return a count with grammatically correct singular/plural wording."""

        noun = singular if count == 1 else (plural or singular + "s")
        return f"{count} {noun}"

    def format_money(self, amount, include_plus=False):
        """Format currency with the sign before the dollar symbol."""

        amount = round(amount)
        if amount < 0:
            return f"-${abs(amount)}"
        if include_plus and amount > 0:
            return f"+${amount}"
        return f"${amount}"

    def get_balance_color(self, amount):
        """Use warning red for debt and clinic green for non-negative money."""

        return (245, 130, 115) if amount < 0 else COLORS["accent"]

    def can_spend_clinic_funds(self, amount):
        """Return whether an optional charge stays inside the clinic credit line."""

        return amount <= 0 or self.get_live_balance() - amount >= self.get_debt_limit()

    def get_test_charge_state(self, test):
        """Return (allowed, charged cost, emergency) for one test run."""

        normal_cost = self.player.get_test_cost(test)
        if self.can_spend_clinic_funds(normal_cost):
            return True, normal_cost, False
        if test.rarity == "Common" and not self.emergency_test_used:
            return True, 0, True
        return False, normal_cost, False

    def is_shop_path_locked(self, upgrade):
        if "machine" not in upgrade:
            return False
        machine = upgrade["machine"]
        return (self.player.machine_levels.get(machine, 1) > 1
                or machine in self.player.free_test_machines)

    def get_missing_shop_requirement(self, upgrade):
        """Return the prerequisite upgrade when this item is not yet available."""

        requirement_id = upgrade.get("requires")
        if not requirement_id or requirement_id in self.purchased_shop_upgrades:
            return None
        return next(
            (item for item in SHOP_UPGRADES if item["id"] == requirement_id),
            None,
        )

    def get_live_balance(self):
        """Return the balance players see after costs accrued this shift.

        Test and diagnosis costs remain part of the shift ledger until payday,
        so this preview must not mutate ``Player.balance`` or they would be
        charged twice when ``settle_daily_pay`` applies the final net total.
        """

        if self.daily_payout_applied:
            return self.player.balance
        penalties = self.daily_wrong_diagnoses * WRONG_DIAGNOSIS_PENALTY
        return (
            self.player.balance
            - self.daily_test_expenses
            - self.daily_draw_expenses
            - self.daily_card_shop_expenses
            - penalties
        )

    def get_displayed_balance(self):
        """Interpolate the visible balance during a live deduction."""

        animation = self.money_deduction_animation
        if animation is None:
            return self.get_live_balance()
        elapsed = pygame.time.get_ticks() - animation["started_at"]
        if elapsed >= self.money_count_duration:
            return self.get_live_balance()
        progress = max(0.0, min(1.0, elapsed / self.money_count_duration))
        eased = progress * progress * (3 - 2 * progress)
        value = animation["from"] + (animation["to"] - animation["from"]) * eased
        return round(value)

    def start_live_money_deduction(self, amount, reason):
        """Animate one immediate cost without altering end-of-day accounting."""

        if amount <= 0:
            return
        current_balance = self.get_displayed_balance()
        target_balance = self.get_live_balance() - amount
        self.money_deduction_animation = {
            "from": current_balance,
            "to": target_balance,
            "amount": amount,
            "reason": reason,
            "started_at": pygame.time.get_ticks(),
        }

    def draw_money_deduction_popup(self, center):
        """Float a short red cost label beside the current balance display."""

        animation = self.money_deduction_animation
        if animation is None:
            return
        elapsed = pygame.time.get_ticks() - animation["started_at"]
        if elapsed >= self.money_popup_duration:
            return
        progress = max(0.0, min(1.0, elapsed / self.money_popup_duration))
        rise = round(15 * progress)
        alpha = 255 if progress < 0.62 else round(255 * (1 - progress) / 0.38)
        label = self.card_font.render(
            f"-${animation['amount']}  {animation['reason']}",
            True,
            (255, 139, 126),
        )
        panel = pygame.Surface((label.get_width() + 18, label.get_height() + 10), pygame.SRCALPHA)
        pygame.draw.rect(panel, (49, 19, 27, 232), panel.get_rect(), border_radius=7)
        pygame.draw.rect(panel, (232, 98, 91, 245), panel.get_rect(), width=1, border_radius=7)
        panel.blit(label, (9, 5))
        panel.set_alpha(alpha)
        self.screen.blit(panel, panel.get_rect(center=(center[0], center[1] - rise)))

    def draw_modal_balance(self, header, status_badge):
        """Keep live money feedback visible above full-screen result panels."""

        displayed_balance = self.get_displayed_balance()
        balance = self.small_font.render(
            f"MONEY  {self.format_money(displayed_balance)}",
            True,
            self.get_balance_color(displayed_balance),
        )
        anchor = (status_badge.x - 18, header.y + 23)
        self.screen.blit(balance, balance.get_rect(midright=anchor))
        self.draw_money_deduction_popup(
            (anchor[0] - balance.get_width() // 2, header.y + 58)
        )

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
        self.draw_shop_category_tabs()

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
            f"MONEY  {self.format_money(self.player.balance)}",
            True,
            self.get_balance_color(self.player.balance),
        )
        self.screen.blit(balance, balance.get_rect(center=(balance_badge.centerx + 10, balance_badge.centery)))
        self.draw_shop_ticket_badge()

        visible_upgrades = self.get_visible_shop_upgrades()
        shop_rects = self.get_shop_upgrade_rects()
        for upgrade, rect in zip(visible_upgrades, shop_rects):
            self.draw_shop_shelf(upgrade, rect)
        if (
            len(visible_upgrades) < len(shop_rects)
            and self.shop_scroll_row == self.get_shop_max_scroll_row()
        ):
            self.draw_shop_loadout_summary(shop_rects[-1])
        self.draw_shop_scroll_controls()
        selected = self.get_selected_shop_upgrade()
        owned = selected and selected["id"] in self.purchased_shop_upgrades
        path_locked = selected and not owned and self.is_shop_path_locked(selected)
        missing_requirement = selected and self.get_missing_shop_requirement(selected)
        can_buy = (
            selected
            and not owned
            and not path_locked
            and not missing_requirement
            and self.player.balance >= selected["cost"]
        )
        label = "SELECT AN UPGRADE"
        if selected:
            if path_locked:
                label = "OTHER PATH CHOSEN"
            elif missing_requirement:
                label = f"REQUIRES {missing_requirement['name']}"
            elif owned:
                label = "INSTALLED"
            elif can_buy and "machine" in selected:
                label = f"CONFIRM INSTALL  ${selected['cost']}"
            elif can_buy:
                label = f"BUY & INSTALL  ${selected['cost']}"
            else:
                label = f"NEED ${selected['cost'] - self.player.balance} MORE"
        mouse_position = self.get_mouse_position()
        for rect, text, enabled, accent in (
            (self.shop_purchase_button, label, can_buy, (112, 255, 181)),
            (self.shop_button, "OPEN ROUTE MAP", True, (206, 158, 233)),
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
            label_center = rect.center
            if rect == self.shop_purchase_button and selected:
                icon_center = (rect.x + 24, rect.centery)
                self.draw_shop_purchase_icon(selected, icon_center)
                label_center = (rect.centerx + 14, rect.centery)
            rendered = self.small_font.render(
                text,
                True,
                COLORS["background"] if enabled and hovered else border,
            )
            self.screen.blit(rendered, rendered.get_rect(center=label_center))
        message_color = (
            SHOP_PRODUCT_COLORS[selected["id"]]
            if selected
            and "machine" in selected
            and not owned
            and not path_locked
            else COLORS["text"]
        )
        message = self.compact_ui_font.render(
            self.shop_message,
            True,
            message_color,
        )
        self.screen.blit(message, message.get_rect(center=(550, 588)))

    def draw_shop_ticket_badge(self):
        """Keep the next route fare visible while players consider upgrades."""

        destination = self.get_intended_route_destination()
        if destination is None:
            return
        badge = pygame.Rect(548, 132, 250, 38)
        price = destination.map_data.ticket_price
        owned = destination.key in self.route.purchased_ticket_keys
        shortfall = 0 if owned else max(0, price - self.player.balance)
        accent = (112, 255, 181) if owned else (117, 190, 255)
        pygame.draw.rect(self.screen, (20, 29, 43), badge, border_radius=8)
        pygame.draw.rect(self.screen, accent, badge, width=1, border_radius=8)
        destination_label = (
            "RETURN PASSAGE"
            if destination.map_data.destination_type.value == "earth"
            else destination.planet_name.split()[0].upper()
        )
        title = self.card_font.render(
            f"NEXT TICKET  •  {destination_label}  {self.format_money(price)}",
            True,
            accent,
        )
        detail = self.card_font.render(
            "TICKET OWNED"
            if owned
            else (
                f"{self.format_money(self.player.balance)} SAVED  •  "
                f"{self.format_money(shortfall)} NEEDED"
            ),
            True,
            COLORS["text"],
        )
        self.screen.blit(title, title.get_rect(center=(badge.centerx, badge.y + 11)))
        self.screen.blit(detail, detail.get_rect(center=(badge.centerx, badge.y + 26)))
        track = pygame.Rect(badge.x + 8, badge.bottom - 5, badge.width - 16, 3)
        pygame.draw.rect(self.screen, (6, 11, 20), track, border_radius=2)
        progress = 1.0 if owned else min(1.0, max(0.0, self.player.balance / max(1, price)))
        if progress > 0:
            pygame.draw.rect(
                self.screen,
                accent,
                pygame.Rect(track.x, track.y, max(2, round(track.width * progress)), track.height),
                border_radius=2,
            )

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
        supported_cases = min(
            self.daily_evidence_cases,
            self.daily_correct_diagnoses,
        )
        partial_cases = min(
            self.daily_partial_evidence_cases,
            self.daily_correct_diagnoses - supported_cases,
        )
        no_evidence_cases = (
            self.daily_correct_diagnoses - supported_cases - partial_cases
        )
        care_parts = []
        if supported_cases:
            care_parts.append(
                f"{supported_cases} full × ${self.scale_case_reward(DIAGNOSIS_REWARD)}"
            )
        if partial_cases:
            care_parts.append(
                f"{partial_cases} partial × ${self.scale_case_reward(LIMITED_EVIDENCE_REWARD)}"
            )
        if no_evidence_cases:
            care_parts.append(
                f"{no_evidence_cases} no-clue × ${self.scale_case_reward(NO_EVIDENCE_REWARD)}"
            )
        care_detail = "  •  ".join(care_parts) or "No confirmed cases"
        if self.daily_patients_lost:
            care_detail += f"  •  {self.daily_patients_lost} walked out"
        cards_drawn = self.daily_random_draw_count
        diagnostic_costs = (
            self.daily_test_expenses
            + self.daily_draw_expenses
            + self.daily_card_shop_expenses
        )
        mistake_label = (
            "WRONG DIAGNOSIS"
            if self.daily_wrong_diagnoses == 1
            else "WRONG DIAGNOSES"
        )
        recap_rows = (
            (
                "PATIENT CARE REVENUE",
                care_detail,
                f"+${base_pay}",
                COLORS["accent"],
            ),
            (
                "DIAGNOSTIC & CARD COSTS",
                (
                    f"{self.format_count(self.daily_test_count, 'test')}  •  "
                    f"{self.format_count(cards_drawn, 'random draw')}  •  "
                    f"{self.format_count(self.daily_card_shop_purchases, 'shop card')}"
                ),
                f"-${diagnostic_costs}",
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
                    "Every case supported by test evidence"
                    if bonus
                    else (
                        f"Fully supported cases: {self.daily_evidence_cases}/"
                        f"{len(self.waiting_room_queue)}"
                    )
                ),
                f"+${bonus}",
                (216, 159, 238),
            ),
            (
                "CLINIC OPERATING FEE",
                (
                    "Daily rent, power, and medical supplies"
                    if self.get_operating_fee() > 0
                    else "Waived  •  nobody inspects Blackglass"
                ),
                f"-${self.get_operating_fee()}",
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
        remaining_pay = base_pay - self.get_operating_fee() + bonus
        if self.daily_payout_applied:
            resulting_balance = self.player.balance
            current_balance = resulting_balance - remaining_pay
        else:
            current_balance = self.get_live_balance()
            resulting_balance = current_balance + remaining_pay
        current = self.card_font.render(
            f"LIVE BALANCE  {self.format_money(current_balance)}",
            True,
            self.get_balance_color(current_balance),
        )
        resulting = self.small_font.render(
            f"AFTER PAY & OVERHEAD  {self.format_money(resulting_balance)}",
            True,
            self.get_balance_color(resulting_balance),
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

        if self.blackglass_detour is not None:
            self.draw_blackglass_debt_panel(resulting_balance, panel)
        elif resulting_balance <= BLACKGLASS_DEBT_THRESHOLD:
            self.draw_debt_alert_panel(resulting_balance, panel)
        else:
            self.draw_payroll_travel_fund(resulting_balance, panel)

        hovered = self.day_complete_button.collidepoint(self.get_mouse_position())
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
            self.get_day_complete_button_label(resulting_balance),
            True,
            COLORS["accent"],
        )
        self.screen.blit(
            button_text,
            button_text.get_rect(center=self.day_complete_button.center),
        )

    def draw_payroll_travel_fund(self, projected_balance, panel):
        """Show how the completed shift funds the next required ticket."""

        destination = self.get_intended_route_destination()
        if destination is None:
            return
        price = destination.map_data.ticket_price
        shortfall = max(0, price - projected_balance)
        fund = pygame.Rect(panel.x + 130, panel.y + 386, panel.width - 260, 36)
        accent = (112, 255, 181) if shortfall == 0 else (117, 190, 255)
        pygame.draw.rect(self.screen, (8, 20, 29), fund, border_radius=9)
        pygame.draw.rect(self.screen, accent, fund, width=1, border_radius=9)
        destination_label = (
            "RETURN PASSAGE"
            if destination.map_data.destination_type.value == "earth"
            else destination.planet_name.upper()
        )
        title = self.card_font.render(
            f"TRAVEL FUND  •  {destination_label} TICKET {self.format_money(price)}",
            True,
            accent,
        )
        detail = self.card_font.render(
            (
                "TICKET FULLY FUNDED"
                if shortfall == 0
                else f"AFTER PAY: {self.format_money(projected_balance)}  •  STILL NEEDED: {self.format_money(shortfall)}"
            ),
            True,
            COLORS["text"],
        )
        self.screen.blit(title, title.get_rect(center=(fund.centerx, fund.y + 10)))
        self.screen.blit(detail, detail.get_rect(center=(fund.centerx, fund.y + 23)))
        track = pygame.Rect(fund.x + 12, fund.bottom - 5, fund.width - 24, 3)
        pygame.draw.rect(self.screen, (4, 10, 17), track, border_radius=2)
        progress = min(1.0, max(0.0, projected_balance / max(1, price)))
        if progress > 0:
            pygame.draw.rect(
                self.screen,
                accent,
                pygame.Rect(track.x, track.y, max(2, round(track.width * progress)), track.height),
                border_radius=2,
            )

    def get_daily_pay_breakdown(self):
        """Return earnings, diagnosis penalties, bonus, and net shift payout."""

        supported_cases = min(
            self.daily_evidence_cases,
            self.daily_correct_diagnoses,
        )
        partial_cases = min(
            self.daily_partial_evidence_cases,
            self.daily_correct_diagnoses - supported_cases,
        )
        no_evidence_cases = (
            self.daily_correct_diagnoses - supported_cases - partial_cases
        )
        base_pay = (
            supported_cases * self.scale_case_reward(DIAGNOSIS_REWARD)
            + partial_cases * self.scale_case_reward(LIMITED_EVIDENCE_REWARD)
            + no_evidence_cases * self.scale_case_reward(NO_EVIDENCE_REWARD)
        )
        penalties = self.daily_wrong_diagnoses * WRONG_DIAGNOSIS_PENALTY
        perfect_day = (
            self.daily_correct_diagnoses == len(self.waiting_room_queue)
            and self.daily_wrong_diagnoses == 0
            and self.daily_evidence_cases == len(self.waiting_room_queue)
        )
        bonus = self.scale_case_reward(PERFECT_DAY_BONUS) if perfect_day else 0
        total = (
            base_pay
            - penalties
            - self.daily_test_expenses
            - self.daily_draw_expenses
            - self.daily_card_shop_expenses
            - self.get_operating_fee()
            + bonus
        )
        return base_pay, penalties, bonus, total

    def settle_daily_pay(self):
        """Deposit the calculated shift pay exactly once."""

        if self.daily_payout_applied:
            return
        self.player.earn(self.get_daily_pay_breakdown()[3])
        self.route.sync_available_credits(self.player.balance)
        self.daily_payout_applied = True
        self.money_deduction_animation = None

    def get_shop_upgrade_rects(self):
        """Return four roomy shelf positions inside the scrolling viewport."""

        return [
            pygame.Rect(x, y, 420, 154)
            for y in (198, 367)
            for x in (92, 532)
        ]

    def get_shop_category_rects(self):
        """Return the compact header tabs for permanent-upgrade categories."""

        return {
            key: pygame.Rect(108 + index * 90, 153, 84, 24)
            for index, key in enumerate(SHOP_CATEGORY_KEYS)
        }

    def get_shop_category_for_upgrade(self, upgrade):
        """Return the catalog category for one permanent upgrade."""

        if "machine" in upgrade:
            return "machines"
        if upgrade["id"] in SHOP_CARD_UPGRADE_IDS:
            return "cards"
        return "clinic"

    def get_shop_category_upgrades(self, category=None):
        """Return products belonging to the selected category."""

        category = category or self.shop_category
        if category == "installed":
            return tuple(
                upgrade
                for upgrade in SHOP_SHELVES
                if upgrade["id"] in self.purchased_shop_upgrades
                or (
                    "machine" in upgrade
                    and upgrade["id"] + "_free" in self.purchased_shop_upgrades
                )
            )
        return tuple(
            upgrade
            for upgrade in SHOP_SHELVES
            if self.get_shop_category_for_upgrade(upgrade) == category
        )

    def draw_shop_category_tabs(self):
        """Draw filters so the growing permanent catalog stays scannable."""

        mouse = self.get_mouse_position()
        for key, rect in self.get_shop_category_rects().items():
            selected = key == self.shop_category
            hovered = rect.collidepoint(mouse)
            count = len(self.get_shop_category_upgrades(key))
            border = COLORS["accent"] if selected else (151, 113, 184)
            fill = (
                (31, 70, 66)
                if selected
                else (55, 42, 72)
                if hovered
                else (22, 27, 41)
            )
            pygame.draw.rect(self.screen, fill, rect, border_radius=6)
            pygame.draw.rect(self.screen, border, rect, width=2 if selected else 1,
                             border_radius=6)
            label = self.card_font.render(
                f"{SHOP_CATEGORY_LABELS[key]} {count}",
                True,
                COLORS["accent"] if selected else COLORS["text"],
            )
            self.screen.blit(label, label.get_rect(center=rect.center))

    def handle_shop_category_click(self, position):
        """Switch catalog filters without purchasing or installing anything."""

        for key, rect in self.get_shop_category_rects().items():
            if not rect.collidepoint(position):
                continue
            self.play_sfx("button")
            self.shop_category = key
            self.shop_scroll_row = 0
            self.selected_shop_upgrade = None
            if key == "installed":
                self.shop_message = "Review the permanent upgrades installed in this campaign."
            else:
                self.shop_message = f"Showing {SHOP_CATEGORY_LABELS[key].title()} upgrades."
            return True
        return False

    def get_shop_total_rows(self):
        """Return the number of six-product pages in the selected category."""

        item_count = len(self.get_shop_category_upgrades())
        visible_count = SHOP_COLUMNS * SHOP_VISIBLE_ROWS
        return max(1, (item_count + visible_count - 1) // visible_count)

    def get_shop_max_scroll_row(self):
        """Return the last valid first-row position in the Shop viewport."""

        return max(0, self.get_shop_total_rows() - 1)

    def get_visible_shop_upgrades(self):
        """Return the products represented by the six visible Shop shelves."""

        visible_count = SHOP_COLUMNS * SHOP_VISIBLE_ROWS
        first_index = self.shop_scroll_row * visible_count
        upgrades = self.get_shop_category_upgrades()
        return upgrades[first_index:first_index + visible_count]

    def scroll_shop(self, row_delta):
        """Move the Shop viewport by complete product rows."""

        old_row = self.shop_scroll_row
        self.shop_scroll_row = max(
            0,
            min(self.shop_scroll_row + row_delta, self.get_shop_max_scroll_row()),
        )
        return self.shop_scroll_row != old_row

    def get_shop_scroll_rects(self):
        """Return up button, down button, and scrollbar track rectangles."""

        return (
            pygame.Rect(975, 183, 34, 27),
            pygame.Rect(975, 509, 34, 27),
            pygame.Rect(987, 214, 12, 291),
        )

    def handle_shop_scroll_click(self, position):
        """Scroll when either catalog navigation button is clicked."""

        up_button, down_button, _track = self.get_shop_scroll_rects()
        if up_button.collidepoint(position):
            if self.scroll_shop(-1):
                self.play_sfx("button")
            return True
        if down_button.collidepoint(position):
            if self.scroll_shop(1):
                self.play_sfx("button")
            return True
        return False

    def draw_shop_scroll_controls(self):
        """Draw paging arrows, a proportional thumb, and the visible item count."""

        up_button, down_button, track = self.get_shop_scroll_rects()
        max_scroll = self.get_shop_max_scroll_row()
        mouse_position = self.get_mouse_position()
        for button, direction, enabled in (
            (up_button, -1, self.shop_scroll_row > 0),
            (down_button, 1, self.shop_scroll_row < max_scroll),
        ):
            hovered = enabled and button.collidepoint(mouse_position)
            border = (206, 158, 233) if enabled else (71, 67, 84)
            fill = (50, 37, 68) if hovered else (20, 25, 37)
            pygame.draw.rect(self.screen, fill, button, border_radius=6)
            pygame.draw.rect(self.screen, border, button, width=2, border_radius=6)
            arrow_y = button.centery + (2 if direction > 0 else -2)
            arrow = (
                (button.centerx - 7, arrow_y - 4 * direction),
                (button.centerx + 7, arrow_y - 4 * direction),
                (button.centerx, arrow_y + 6 * direction),
            )
            pygame.draw.polygon(self.screen, border, arrow)

        pygame.draw.rect(self.screen, (13, 18, 29), track, border_radius=6)
        pygame.draw.rect(self.screen, (79, 65, 96), track, width=1, border_radius=6)
        total_rows = self.get_shop_total_rows()
        thumb_height = max(42, round(track.height / total_rows))
        thumb_travel = track.height - thumb_height
        thumb_y = track.y
        if max_scroll:
            thumb_y += round(thumb_travel * self.shop_scroll_row / max_scroll)
        thumb = pygame.Rect(track.x + 2, thumb_y + 2, track.width - 4, thumb_height - 4)
        pygame.draw.rect(self.screen, (206, 158, 233), thumb, border_radius=4)

        category_label = (
            "INSTALLED UPGRADES"
            if self.shop_category == "installed"
            else f"{SHOP_CATEGORY_LABELS[self.shop_category][:-1]} UPGRADES"
            if self.shop_category in ("machines", "cards")
            else "CLINIC UPGRADES"
        )
        page = self.shop_scroll_row + 1
        page_count = max_scroll + 1
        count = self.shop_label_font.render(
            f"{category_label}  —  PAGE {page}/{page_count}",
            True,
            (232, 211, 242),
        )
        self.screen.blit(count, count.get_rect(center=(550, 190)))

    def get_selected_shop_upgrade(self):
        return next((item for item in SHOP_UPGRADES if item["id"] == self.selected_shop_upgrade), None)

    def handle_shop_upgrade_click(self, position):
        for upgrade, rect in zip(
            self.get_visible_shop_upgrades(),
            self.get_shop_upgrade_rects(),
        ):
            if rect.collidepoint(position):
                if "machine" in upgrade:
                    for path, button in zip(("efficiency", "free_use"), self.get_machine_path_buttons(rect)):
                        if button.collidepoint(position):
                            selected_id = upgrade["id"] + ("_free" if path == "free_use" else "")
                            selected_path = next(
                                item for item in SHOP_UPGRADES
                                if item["id"] == selected_id
                            )
                            self.play_sfx("button")
                            if selected_id in self.purchased_shop_upgrades:
                                self.selected_shop_upgrade = selected_id
                                self.shop_message = f"{selected_path['name']} is already installed."
                            elif self.is_shop_path_locked(selected_path):
                                self.shop_message = (
                                    f"{upgrade['machine']} already has a permanent path installed."
                                )
                            else:
                                self.selected_shop_upgrade = selected_id
                                alternate = (
                                    "Shift Allowance"
                                    if path == "efficiency"
                                    else "Efficiency"
                                )
                                path_name = (
                                    "Efficiency"
                                    if path == "efficiency"
                                    else "Shift Allowance"
                                )
                                self.shop_message = (
                                    f"{path_name} selected for {upgrade['machine']}. "
                                    f"Confirm installation; {alternate} will lock."
                                )
                            return
                    self.play_sfx("button")
                    # Clicking the shared machine header defaults to the
                    # Efficiency path, but still requires the same explicit
                    # confirmation as either path button.
                    self.selected_shop_upgrade = upgrade["id"]
                    self.shop_message = (
                        f"Efficiency selected for {upgrade['machine']}. "
                        "Confirm installation; Shift Allowance will lock."
                    )
                    return
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
        elif self.is_shop_path_locked(upgrade):
            self.shop_message = "This machine already has a permanent path. Choose another machine."
        elif self.get_missing_shop_requirement(upgrade):
            requirement = self.get_missing_shop_requirement(upgrade)
            self.shop_message = f"Install {requirement['name']} before {upgrade['name']}."
        elif self.player.balance < upgrade["cost"]:
            self.shop_message = f"Not enough money for {upgrade['name']} — need ${upgrade['cost']}."
        else:
            self.player.pay(upgrade["cost"])
            self.route.sync_available_credits(self.player.balance)
            if upgrade.get("path") == "free_use":
                self.player.free_test_machines.add(upgrade["machine"])
            elif "machine" in upgrade:
                self.player.machine_levels[upgrade["machine"]] = 2
            elif "discount" in upgrade:
                self.player.test_discount += upgrade["discount"]
            self.purchased_shop_upgrades.add(upgrade["id"])
            if upgrade["id"] == "recycler":
                self.shop_message = (
                    "Recycler installed! Select a test card to recycle once per patient."
                )
            elif upgrade["id"] == "recycler_mk2":
                self.shop_message = "Recycler Mk II installed! Two swaps are ready per patient."
            elif upgrade["id"] == "priority_processing":
                self.test_result_reveal_duration = 850
                self.shop_message = "Priority Processing installed! Test reports now finish faster."
            elif "machine" in upgrade:
                installed_path = (
                    "Shift Allowance"
                    if upgrade.get("path") == "free_use"
                    else "Efficiency"
                )
                locked_path = (
                    "Efficiency"
                    if upgrade.get("path") == "free_use"
                    else "Shift Allowance"
                )
                self.shop_message = (
                    f"{installed_path} installed for {upgrade['machine']}; "
                    f"{locked_path} is now locked."
                )
            else:
                self.shop_message = f"Installed {upgrade['name']}. Test costs updated!"

    def get_machine_path_buttons(self, shelf):
        """Return the clickable columns below the shared machine header."""
        return (
            pygame.Rect(shelf.left + 2, shelf.top + 47, shelf.width // 2 - 2, shelf.height - 49),
            pygame.Rect(shelf.centerx + 1, shelf.top + 47, shelf.width // 2 - 3, shelf.height - 49),
        )

    def get_machine_path_cost_details(self, machine):
        """Return real current and post-upgrade costs for a test machine."""

        test = next(
            (item for item in self.card_shop_catalog if item.name == machine),
            None,
        )
        if test is None:
            return None
        base_cost = get_base_test_cost(test)
        current_cost = self.player.get_test_cost(test)
        efficiency_cost = max(
            MIN_TEST_OPERATING_COST,
            (base_cost + 1) // 2 - self.player.test_discount,
        )
        later_allowance_cost = max(
            MIN_TEST_OPERATING_COST,
            base_cost - self.player.test_discount,
        )
        return current_cost, efficiency_cost, later_allowance_cost

    def draw_shop_loadout_summary(self, shelf):
        """Use the spare final shelf to summarize the current permanent loadout."""

        installed_count = len(self.purchased_shop_upgrades)
        free_count = len(self.player.free_test_machines)
        path_count = sum(
            1
            for machine in self.player.machine_levels
            if self.player.machine_levels[machine] > 1
        ) + free_count
        recycler = (
            "MK II • 2 SWAPS"
            if "recycler_mk2" in self.purchased_shop_upgrades
            else "READY • 1 SWAP"
            if "recycler" in self.purchased_shop_upgrades
            else "NOT INSTALLED"
        )
        accent = (206, 158, 233)
        pygame.draw.rect(self.screen, (3, 8, 13), shelf.move(3, 4), border_radius=11)
        pygame.draw.rect(self.screen, (25, 23, 39), shelf, border_radius=11)
        pygame.draw.rect(self.screen, accent, shelf, width=2, border_radius=11)

        title = self.shop_label_font.render("INSTALLED LOADOUT", True, accent)
        self.screen.blit(title, (shelf.x + 13, shelf.y + 10))
        subtitle = self.shop_detail_font.render(
            "CAMPAIGN-WIDE PERMANENT EFFECTS",
            True,
            COLORS["muted"],
        )
        self.screen.blit(subtitle, (shelf.x + 13, shelf.y + 31))
        pygame.draw.line(
            self.screen,
            (91, 69, 111),
            (shelf.x + 12, shelf.y + 49),
            (shelf.right - 12, shelf.y + 49),
        )

        summary_rows = (
            ("UPGRADES INSTALLED", str(installed_count)),
            (
                "GLOBAL TEST DISCOUNT",
                f"-${self.player.test_discount}" if self.player.test_discount else "$0",
            ),
            ("FREE MACHINE ALLOWANCES", str(free_count)),
            ("RECYCLER", recycler),
            ("MACHINE PATHS CHOSEN", str(path_count)),
        )
        for index, (label_text, value_text) in enumerate(summary_rows):
            y = shelf.y + 58 + index * 17
            label = self.shop_detail_font.render(label_text, True, COLORS["muted"])
            value = self.shop_detail_font.render(value_text, True, COLORS["accent"])
            self.screen.blit(label, (shelf.x + 13, y))
            self.screen.blit(value, value.get_rect(topright=(shelf.right - 13, y)))

    def draw_machine_shop_shelf(self, upgrade, shelf):
        """Draw a shared header and two side-by-side purchase options."""
        color = SHOP_PRODUCT_COLORS[upgrade["id"]]
        pygame.draw.rect(self.screen, (3, 8, 13), shelf.move(3, 4), border_radius=11)
        pygame.draw.rect(self.screen, (18, 27, 40), shelf, border_radius=11)
        title = self.tutorial_subtitle_font.render(upgrade["machine"], True, color)
        self.screen.blit(title, (shelf.x + 12, shelf.y + 7))
        hint = self.shop_detail_font.render("CHOOSE ONE PERMANENT PATH", True, COLORS["muted"])
        self.screen.blit(hint, (shelf.x + 12, shelf.y + 26))
        self.draw_shop_purchase_icon(upgrade, (shelf.right - 24, shelf.y + 23))

        cost_details = self.get_machine_path_cost_details(upgrade["machine"])
        if cost_details is None:
            efficiency_details = ("50% LOWER COST", "ON EVERY USE")
            allowance_details = ("FIRST USE: FREE", "THEN NORMAL COST")
        else:
            current_cost, efficiency_cost, later_allowance_cost = cost_details
            efficiency_details = (
                f"CURRENT COST: ${current_cost}",
                f"AFTER UPGRADE: ${efficiency_cost}",
            )
            allowance_details = (
                "FIRST USE / SHIFT: FREE",
                f"LATER USES: ${later_allowance_cost}",
            )
        options = (
            ("", "EFFICIENCY", efficiency_details),
            ("_free", "SHIFT ALLOWANCE", allowance_details),
        )
        mouse = self.get_mouse_position()
        for (suffix, label, details), rect in zip(options, self.get_machine_path_buttons(shelf)):
            option_id = upgrade["id"] + suffix
            selected = option_id == self.selected_shop_upgrade
            owned = option_id in self.purchased_shop_upgrades
            locked = not owned and self.is_shop_path_locked(upgrade)
            available = not owned and not locked
            hovered = available and rect.collidepoint(mouse)
            fill = (
                (38, 63, 66)
                if selected
                else (41, 67, 68)
                if hovered
                else (23, 41, 43)
                if owned
                else (14, 21, 32)
            )
            pygame.draw.rect(self.screen, fill, rect, border_radius=7)
            if selected:
                pygame.draw.rect(self.screen, color, rect, width=3, border_radius=7)

            label_color = (
                COLORS["accent"]
                if owned
                else color
                if available or selected
                else COLORS["muted"]
            )
            title = self.shop_label_font.render(label, True, label_color)
            self.screen.blit(title, title.get_rect(midtop=(rect.centerx, rect.top + 10)))
            for index, detail in enumerate(details):
                line = self.shop_detail_font.render(detail, True, COLORS["muted"])
                self.screen.blit(line, line.get_rect(midtop=(rect.centerx, rect.top + 29 + 14 * index)))

            footer = pygame.Rect(rect.x + 8, rect.bottom - 30, rect.width - 16, 24)
            pygame.draw.rect(self.screen, (7, 15, 24), footer, border_radius=5)
            if available or owned or selected:
                pygame.draw.rect(self.screen, label_color, footer, width=1, border_radius=5)
            status = (
                "INSTALLED"
                if owned
                else "LOCKED"
                if locked
                else f"SELECTED  ${upgrade['cost']}"
                if selected
                else f"${upgrade['cost']}"
            )
            font = self.shop_label_font
            price = font.render(status, True, label_color)
            self.screen.blit(price, price.get_rect(center=footer.center))

        pygame.draw.line(self.screen, color, (shelf.left + 2, shelf.top + 46),
                         (shelf.right - 3, shelf.top + 46))
        pygame.draw.line(self.screen, color, (shelf.centerx, shelf.top + 46),
                         (shelf.centerx, shelf.bottom - 2))
        pygame.draw.rect(self.screen, color, shelf, width=2, border_radius=11)

    def draw_shop_shelf(self, upgrade, shelf):
        """Draw one illuminated shelf with a unique product illustration."""

        if "machine" in upgrade:
            self.draw_machine_shop_shelf(upgrade, shelf)
            return
        selected = upgrade["id"] == self.selected_shop_upgrade
        owned = upgrade["id"] in self.purchased_shop_upgrades
        hovered = shelf.collidepoint(self.get_mouse_position())
        affordable = self.player.balance >= upgrade["cost"]
        missing_requirement = self.get_missing_shop_requirement(upgrade)
        product_color = SHOP_PRODUCT_COLORS[upgrade["id"]]
        border = (
            COLORS["accent"]
            if owned
            else product_color
            if selected or hovered
            else (103, 87, 124)
        )
        display = shelf.move(0, -2 if hovered and not selected else 0)

        if selected:
            glow_rect = display.inflate(18, 18)
            glow = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(
                glow,
                (*product_color, 38),
                glow.get_rect(),
                border_radius=16,
            )
            pygame.draw.rect(
                glow,
                (*product_color, 105),
                glow.get_rect().inflate(-7, -7),
                width=3,
                border_radius=13,
            )
            self.screen.blit(glow, glow_rect.topleft)

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
            width=4 if selected else 2 if hovered or owned else 1,
            border_radius=11,
        )

        art = pygame.Rect(display.x + 12, display.y + 13, 76, 94)
        self.draw_shop_product_illustration(
            upgrade,
            art,
            product_color,
            dimmed=(not affordable or bool(missing_requirement)) and not owned,
        )

        text_x = art.right + 10
        text_width = display.right - text_x - 10
        category_text = upgrade["category"]
        if owned and "machine" in upgrade:
            category_text += " / " + ("FREE" if upgrade.get("path") == "free_use" else "LV.2")
        category = self.shop_detail_font.render(category_text, True, product_color)
        self.screen.blit(category, (text_x, display.y + 12))

        name = self.tutorial_subtitle_font.render(upgrade["name"], True, COLORS["text"])
        self.screen.blit(name, (text_x, display.y + 32))

        description_lines = self.wrap_text(
            upgrade["description"],
            self.shop_detail_font,
            text_width,
        )
        if len(description_lines) > 3:
            description_lines = description_lines[:3]
            final_line = description_lines[-1]
            while final_line and self.shop_detail_font.size(final_line + "...")[0] > text_width:
                final_line = final_line[:-1]
            description_lines[-1] = final_line.rstrip() + "..."
        for line_index, line in enumerate(description_lines):
            rendered = self.shop_detail_font.render(line, True, COLORS["muted"])
            self.screen.blit(rendered, (text_x, display.y + 56 + line_index * 18))

        footer = pygame.Rect(display.x + 5, display.bottom - 34, display.width - 10, 29)
        pygame.draw.rect(self.screen, (8, 13, 22), footer, border_radius=6)
        pygame.draw.line(
            self.screen,
            border,
            (footer.x + 4, footer.y),
            (footer.right - 4, footer.y),
            width=2,
        )
        price = self.shop_label_font.render(f"${upgrade['cost']}", True, product_color)
        self.screen.blit(price, price.get_rect(midleft=(footer.x + 10, footer.centery)))
        if owned:
            status_text = "INSTALLED"
            status_color = COLORS["accent"]
        elif self.is_shop_path_locked(upgrade):
            status_text = "OTHER PATH CHOSEN"
            status_color = COLORS["muted"]
        elif missing_requirement:
            status_text = "REQUIRES RECYCLER"
            status_color = COLORS["muted"]
        elif affordable:
            status_text = "SELECT" if not selected else "READY TO INSTALL"
            status_color = COLORS["text"]
        else:
            status_text = "LOCKED"
            status_color = (224, 126, 126)
        status = self.shop_detail_font.render(status_text, True, status_color)
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

    def draw_shop_purchase_icon(self, upgrade, center):
        """Show the selected product's symbol inside the purchase control."""

        color = SHOP_PRODUCT_COLORS[upgrade["id"]]
        pygame.draw.circle(self.screen, (9, 17, 27), center, 14)
        pygame.draw.circle(self.screen, color, center, 14, width=2)
        item_id = upgrade.get("art_id", upgrade["id"])
        if item_id == "temperature":
            pygame.draw.line(self.screen, color, (center[0], center[1] - 7), (center[0], center[1] + 4), width=3)
            pygame.draw.circle(self.screen, color, (center[0], center[1] + 7), 4)
        elif item_id == "xray":
            pygame.draw.line(self.screen, color, (center[0] - 6, center[1] + 6), (center[0] + 6, center[1] - 6), width=3)
            pygame.draw.circle(self.screen, color, (center[0] - 7, center[1] + 7), 3)
            pygame.draw.circle(self.screen, color, (center[0] + 7, center[1] - 7), 3)
        elif item_id == "ultrasound":
            for radius in (6, 11):
                pygame.draw.arc(self.screen, color, pygame.Rect(center[0] - radius, center[1] - radius, radius * 2, radius * 2), -0.8, 0.8, width=2)
        elif item_id == "allergy":
            pygame.draw.circle(self.screen, color, (center[0], center[1] + 3), 6)
            pygame.draw.polygon(self.screen, color, ((center[0], center[1] - 9), (center[0] - 5, center[1] + 1), (center[0] + 5, center[1] + 1)))
        elif item_id in ("blood", "oxygen", "toxin", "neural"):
            self.draw_test_icon(
                upgrade["machine"],
                pygame.Rect(center[0] - 11, center[1] - 11, 22, 22),
                color,
            )
        elif item_id == "power":
            pygame.draw.polygon(self.screen, color, ((center[0] + 2, center[1] - 10), (center[0] - 6, center[1] + 1), (center[0], center[1] + 1), (center[0] - 2, center[1] + 10), (center[0] + 7, center[1] - 2), (center[0] + 1, center[1] - 2)))
        else:
            pygame.draw.rect(self.screen, color, pygame.Rect(center[0] - 7, center[1] - 8, 12, 15), width=2, border_radius=2)
            pygame.draw.line(self.screen, color, (center[0] - 3, center[1] - 4), (center[0] + 8, center[1] - 4), width=2)

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

        item_id = upgrade.get("art_id", upgrade["id"])
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
        elif item_id == "blood":
            vial = pygame.Rect(cx - 17, cy - 27, 34, 58)
            pygame.draw.rect(self.screen, (20, 34, 43), vial, border_radius=8)
            pygame.draw.rect(self.screen, color, vial, width=2, border_radius=8)
            pygame.draw.rect(
                self.screen,
                color,
                pygame.Rect(vial.x + 4, vial.centery, vial.width - 8, 24),
                border_radius=5,
            )
            pygame.draw.rect(self.screen, color, pygame.Rect(cx - 12, cy - 34, 24, 9), border_radius=3)
            for offset_x, offset_y in ((-7, 7), (6, 13), (-2, 21)):
                pygame.draw.circle(self.screen, (255, 227, 212), (cx + offset_x, cy + offset_y), 2)
        elif item_id == "oxygen":
            pygame.draw.line(self.screen, color, (cx, cy - 28), (cx, cy + 15), width=3)
            for direction in (-1, 1):
                lung = pygame.Rect(0, 0, 27, 49)
                lung.midtop = (cx + direction * 15, cy - 14)
                pygame.draw.ellipse(self.screen, (20, 46, 55), lung)
                pygame.draw.ellipse(self.screen, color, lung, width=3)
                pygame.draw.line(self.screen, color, (cx, cy - 10), (lung.centerx, lung.y + 13), width=2)
            for bubble_x, bubble_y, radius in ((26, -24, 3), (33, -12, 2), (-28, -27, 2)):
                pygame.draw.circle(self.screen, color, (cx + bubble_x, cy + bubble_y), radius, width=1)
        elif item_id == "toxin":
            neck = pygame.Rect(cx - 7, cy - 31, 14, 24)
            pygame.draw.rect(self.screen, (24, 37, 43), neck, border_radius=3)
            pygame.draw.rect(self.screen, color, neck, width=2, border_radius=3)
            flask = (
                (neck.x + 2, neck.bottom - 2),
                (neck.right - 2, neck.bottom - 2),
                (cx + 25, cy + 28),
                (cx - 25, cy + 28),
            )
            pygame.draw.polygon(self.screen, (20, 38, 43), flask)
            pygame.draw.polygon(self.screen, color, flask, width=2)
            fluid = ((cx - 19, cy + 12), (cx + 19, cy + 12), (cx + 24, cy + 26), (cx - 24, cy + 26))
            pygame.draw.polygon(self.screen, color, fluid)
            pygame.draw.circle(self.screen, (239, 250, 206), (cx - 6, cy + 18), 3)
            pygame.draw.circle(self.screen, (239, 250, 206), (cx + 9, cy + 22), 2)
        elif item_id == "neural":
            nodes = (
                (cx, cy - 28),
                (cx - 25, cy - 10),
                (cx + 25, cy - 10),
                (cx - 17, cy + 24),
                (cx + 17, cy + 24),
                (cx, cy + 7),
            )
            links = ((0, 1), (0, 2), (1, 3), (2, 4), (1, 5), (2, 5), (3, 5), (4, 5))
            for start, end in links:
                pygame.draw.line(self.screen, color, nodes[start], nodes[end], width=2)
            for index, node in enumerate(nodes):
                pygame.draw.circle(self.screen, (234, 221, 246), node, 5)
                pygame.draw.circle(self.screen, color, node, 5, width=2)
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
