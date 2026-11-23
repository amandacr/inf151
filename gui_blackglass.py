"""Blackglass Outpost contracts: boss dialogue, shift tracking, and return.

Debt recovery sends the doctor to Blackglass for at most
``BLACKGLASS_MAX_DAYS`` shifts:

* ending any Blackglass shift with $0 or more clears the debt, or
* ending the final shift still in debt has the outpost boss forgive the rest,

Voluntary ticket contracts continue until the intended fare is funded, then
return to the Galactic Route Map with every earned credit intact. Neither path
changes the route controller's campaign order or ticket inventory.
"""

import pygame

from PlanetData import get_blackglass_destination, get_modifier
from Player import (
    BLACKGLASS_DEBT_THRESHOLD,
    BLACKGLASS_MAX_DAYS,
    CLINIC_OPERATING_FEE,
    DEBT_LIMIT,
)
from gui_state import GameState
from gui_theme import COLORS, WINDOW_SIZE


CLINIC_BOSS = "CLINIC BOSS"
OUTPOST_BOSS = "OUTPOST BOSS"
PLAYER_SPEAKER = "YOU"

# Interview lines get one of these prefixes at Blackglass ("rude patients").
RUDE_PREFIXES = ("Ugh. ", "Tch. ", "Hurry up, doc. ")

SPEAKER_STYLE = {
    CLINIC_BOSS: {"accent": (240, 128, 112), "fill": (62, 24, 30)},
    OUTPOST_BOSS: {"accent": (255, 160, 64), "fill": (66, 38, 16)},
    PLAYER_SPEAKER: {"accent": (136, 190, 255), "fill": (23, 43, 71)},
}


def build_entry_lines(debt_text, planet_name):
    """Boss dialogue shown when a shift ends at or below the debt threshold."""

    return (
        (CLINIC_BOSS, "Doctor. Sit down. I have reviewed your numbers."),
        (CLINIC_BOSS, f"You are {debt_text} in debt. Your performance is unacceptable."),
        (PLAYER_SPEAKER, "In my defense, I was abducted. I'm not even a doctor."),
        (CLINIC_BOSS, "Noted. And irrelevant. This clinic does not fund failure."),
        (
            CLINIC_BOSS,
            "You are being sent to the Blackglass Outpost while you earn back your keep.",
        ),
        (
            CLINIC_BOSS,
            f"You have {BLACKGLASS_MAX_DAYS} shifts. Make them count. "
            f"{planet_name} will be waiting.",
        ),
    )


def build_contract_entry_lines(destination_name, shortfall_text):
    """Supervisor dialogue for voluntary work that funds a route ticket."""

    return (
        (OUTPOST_BOSS, "Blackglass always has patients. It rarely has doctors."),
        (
            OUTPOST_BOSS,
            f"Your route to {destination_name} is short {shortfall_text}. "
            "Work here and keep what you earn.",
        ),
        (PLAYER_SPEAKER, "Transportation included?"),
        (OUTPOST_BOSS, "To Blackglass, yes. Your destination ticket is still your problem."),
    )


def build_still_in_debt_lines(balance_text):
    """Short note after a non-final Blackglass shift that did not clear the debt."""

    return (
        (OUTPOST_BOSS, f"Still {balance_text}. Blackglass is not a vacation, Doctor."),
        (OUTPOST_BOSS, "One more shift. Try harder. Try breathing less, too."),
    )


def build_contract_continue_lines(destination_name, shortfall_text):
    return (
        (OUTPOST_BOSS, f"You still need {shortfall_text} for {destination_name}."),
        (OUTPOST_BOSS, "Another shift is available. Blackglass never runs out of patients."),
    )


def build_contract_funded_lines(destination_name, balance_text):
    return (
        (OUTPOST_BOSS, f"Your balance is now {balance_text}. The contract is complete."),
        (OUTPOST_BOSS, f"Return to the Route Map and secure passage to {destination_name}."),
    )


def build_cleared_lines(planet_name, balance_text):
    """Boss dialogue when the doctor ends a Blackglass shift out of debt."""

    return (
        (OUTPOST_BOSS, "Your balance is back in the black. I did not see that coming."),
        (
            OUTPOST_BOSS,
            f"Debt cleared. You kept {balance_text}. Back to {planet_name} with you.",
        ),
        (OUTPOST_BOSS, "Try not to lose it this time."),
    )


def build_forgiven_lines(owed_text, planet_name, return_text):
    """Boss dialogue when the final Blackglass shift ends with debt remaining."""

    return (
        (
            OUTPOST_BOSS,
            f"{BLACKGLASS_MAX_DAYS} days in this place. Nobody has ever lasted that long.",
        ),
        (OUTPOST_BOSS, f"You still owe {owed_text}. Consider it paid."),
        (PLAYER_SPEAKER, "You're... forgiving the debt?"),
        (
            OUTPOST_BOSS,
            "The outpost is covering the rest in exchange for the hard work you put in. "
            "Do not make it a habit.",
        ),
        (
            OUTPOST_BOSS,
            f"Your balance is now {return_text}. Your clinic is waiting on {planet_name}.",
        ),
    )


class BlackglassMixin:
    """Debt-triggered Blackglass detour, destination modifiers, and boss scenes."""

    # ------------------------------------------------------------------ setup

    def setup_blackglass_detour(self):
        """Create the idle detour state used by a new campaign."""

        self.blackglass_detour = None
        self.blackglass_boss_lines = ()
        self.blackglass_boss_index = 0
        self.blackglass_boss_action = None
        self.blackglass_boss_scene = "clinic"
        self.blackglass_boss_started_at = None

    def reset_blackglass_detour(self):
        """Forget any detour (new game, developer jump, or restart)."""

        self.setup_blackglass_detour()

    # ------------------------------------------------- destination modifiers

    def get_destination_modifier(self, name, default=1.0):
        """Read a gameplay modifier from the active destination."""

        return get_modifier(self.current_destination, name, default)

    def scale_case_reward(self, amount):
        """Apply the destination's pay multiplier to a case reward or bonus."""

        multiplier = self.get_destination_modifier("reward_multiplier", 1.0)
        return amount if multiplier == 1.0 else round(amount * multiplier)

    def get_operating_fee(self):
        """Return today's clinic operating fee after destination modifiers."""

        multiplier = self.get_destination_modifier("operating_fee_multiplier", 1.0)
        return round(CLINIC_OPERATING_FEE * multiplier)

    def get_debt_limit(self):
        """Return the credit floor for optional spending at this destination."""

        return int(self.get_destination_modifier("debt_limit", DEBT_LIMIT))

    def apply_destination_modifiers(self):
        """Push destination pricing onto the freshly created Player."""

        self.player.test_cost_multiplier = self.get_destination_modifier(
            "test_cost_multiplier", 1.0
        )

    def apply_patient_rudeness(self, patient):
        """Prefix interview lines with a rude interjection where configured."""

        if self.get_destination_modifier("patient_rudeness", 0.0) <= 0:
            return patient
        patient.dialogue = tuple(
            RUDE_PREFIXES[index % len(RUDE_PREFIXES)] + line
            for index, line in enumerate(patient.dialogue)
        )
        return patient

    # ------------------------------------------------------------ detour state

    @property
    def blackglass_detour_active(self):
        return self.blackglass_detour is not None

    def get_blackglass_location_subtitle(self):
        """Return the header label shown during a Blackglass shift."""

        detour = self.blackglass_detour
        if detour.get("mode") == "ticket":
            return f"CONTRACT SHIFT {detour['day']}  •  BLACKGLASS OUTPOST"
        return f"DEBT SHIFT {detour['day']} OF {BLACKGLASS_MAX_DAYS}  •  BLACKGLASS OUTPOST"

    def get_day_complete_button_label(self, resulting_balance):
        """Name the day-complete action according to where it leads."""

        if self.blackglass_detour is not None:
            return "COLLECT PAY  •  SEE THE BOSS"
        if resulting_balance <= BLACKGLASS_DEBT_THRESHOLD:
            return "COLLECT PAY  •  MEET WITH THE BOSS"
        return "COLLECT PAY  •  OPEN SUPPLY SHOP"

    # ------------------------------------------------------------ end of day

    def route_after_daily_pay(self):
        """Decide what follows a settled shift; return True if the flow was taken over.

        Called right after ``settle_daily_pay``.  Outside a detour it checks the
        debt threshold; inside one it clears, continues, or forgives the debt.
        """

        if self.blackglass_detour is None:
            if self.player.balance <= BLACKGLASS_DEBT_THRESHOLD:
                self.start_blackglass_debt_detour()
                return True
            return False
        self.finish_blackglass_day()
        return True

    def start_blackglass_detour(self):
        """Compatibility wrapper for the automatic debt-recovery flow."""

        self.start_blackglass_debt_detour()

    def start_blackglass_debt_detour(self):
        """File the current shift, then open the clinic boss's reprimand."""

        planet = self.route.current_destination
        if not self.route.current_is_complete:
            self.record_current_route_performance()
        debt_text = self.format_money(self.player.balance)
        self.blackglass_detour = {
            "mode": "debt",
            "day": 1,
            "return_key": planet.key,
            "return_planet": planet.planet_name,
            "entry_balance": self.player.balance,
            "destination": get_blackglass_destination(1),
        }
        self.open_blackglass_boss_dialogue(
            build_entry_lines(debt_text, "Blackglass Outpost"), "arrive", "clinic"
        )

    def start_blackglass_ticket_contract(self):
        """Begin voluntary work to fund a ticket without calling it debt."""

        target = self.get_intended_route_destination()
        if target is None:
            self.route_map_message = "No destination currently needs contract funding."
            return
        shortfall = max(0, target.map_data.ticket_price - self.player.balance)
        if shortfall <= 0:
            self.route_map_message = "Your intended destination is already fully funded."
            return
        if not self.route.current_is_complete:
            self.record_current_route_performance()
        self.blackglass_detour = {
            "mode": "ticket",
            "day": 1,
            "return_key": self.route.current_destination.key,
            "return_planet": self.route.current_destination.planet_name,
            "target_key": target.key,
            "target_name": target.planet_name,
            "required_balance": target.map_data.ticket_price,
            "entry_balance": self.player.balance,
            "destination": get_blackglass_destination(1),
        }
        self.open_blackglass_boss_dialogue(
            build_contract_entry_lines(target.planet_name, self.format_money(shortfall)),
            "arrive",
            "outpost",
        )

    def finish_blackglass_day(self):
        """Evaluate a completed Blackglass shift and queue the right dialogue."""

        detour = self.blackglass_detour
        if detour.get("mode") == "ticket":
            shortfall = max(0, detour["required_balance"] - self.player.balance)
            if shortfall == 0:
                lines = build_contract_funded_lines(
                    detour["target_name"], self.format_money(self.player.balance)
                )
                action = "return"
            else:
                lines = build_contract_continue_lines(
                    detour["target_name"], self.format_money(shortfall)
                )
                action = "next_day"
            self.open_blackglass_boss_dialogue(lines, action, "outpost")
            return
        planet_name = detour["return_planet"]
        balance = self.player.balance
        if balance >= 0:
            lines = build_cleared_lines(planet_name, self.format_money(balance))
            action = "return"
        elif detour["day"] >= BLACKGLASS_MAX_DAYS:
            lines = build_forgiven_lines(
                self.format_money(abs(balance)), planet_name, self.format_money(0)
            )
            action = "return"
        else:
            lines = build_still_in_debt_lines(self.format_money(balance))
            action = "next_day"
        self.open_blackglass_boss_dialogue(lines, action, "outpost")

    def end_blackglass_detour(self):
        """Return without erasing legitimate earnings from outpost work."""

        detour = self.blackglass_detour
        ticket_contract = detour.get("mode") == "ticket"
        target_key = detour.get("target_key")
        if not ticket_contract and self.player.balance < 0:
            # Final-shift forgiveness clears only the debt. It never invents a
            # replacement balance or overwrites a profitable result.
            self.player.balance = 0
        self.blackglass_detour = None
        self.route.sync_available_credits(self.player.balance)
        if ticket_contract:
            self.route.select_map_destination(target_key)
            self.open_route_map()
            return
        self.waiting_room_queue = self.roster_for_destination(
            self.route.current_destination
        )
        self.exit_confirmation_open = False
        self.exit_confirmation_opened_at = None
        self.reset_day()
        # The planet's shift was already paid and filed before the detour, so
        # resume at its Supply Shop exactly where the doctor left off.
        self.daily_payout_applied = True
        self.state = GameState.SHOP

    # --------------------------------------------------------- boss dialogue

    def open_blackglass_boss_dialogue(self, lines, action, scene):
        self.blackglass_boss_lines = tuple(lines)
        self.blackglass_boss_index = 0
        self.blackglass_boss_action = action
        self.blackglass_boss_scene = scene
        self.blackglass_boss_started_at = pygame.time.get_ticks()
        self.state = GameState.BLACKGLASS_BOSS

    def advance_blackglass_boss_dialogue(self):
        """Advance one line, or finish the conversation on the last one."""

        if self.blackglass_boss_index < len(self.blackglass_boss_lines) - 1:
            self.blackglass_boss_index += 1
            return
        self.finish_blackglass_boss_dialogue()

    def finish_blackglass_boss_dialogue(self):
        """Run the action that follows the conversation."""

        action = self.blackglass_boss_action
        self.blackglass_boss_action = None
        self.blackglass_boss_lines = ()
        self.blackglass_boss_started_at = None
        if action == "arrive":
            self.arrival_started_at = pygame.time.get_ticks()
            self.state = GameState.ARRIVAL
        elif action == "next_day":
            self.blackglass_detour["day"] += 1
            self.blackglass_detour["destination"] = get_blackglass_destination(
                self.blackglass_detour["day"]
            )
            self.load_current_destination()
        elif action == "return":
            self.end_blackglass_detour()

    # -------------------------------------------------------------- drawing

    def draw_blackglass_debt_panel(self, projected_balance, panel):
        """Show the correct contract goal on the Blackglass payroll recap."""

        detour = self.blackglass_detour
        fund = pygame.Rect(panel.x + 130, panel.y + 386, panel.width - 260, 36)
        ticket_contract = detour.get("mode") == "ticket"
        target_balance = detour.get("required_balance", 0)
        cleared = (
            projected_balance >= target_balance
            if ticket_contract
            else projected_balance >= 0
        )
        accent = (255, 160, 64) if not cleared else (112, 255, 181)
        pygame.draw.rect(self.screen, (28, 17, 10), fund, border_radius=9)
        pygame.draw.rect(self.screen, accent, fund, width=1, border_radius=9)
        if ticket_contract:
            title_text = (
                f"TICKET FUND  •  {detour['target_name'].upper()}  •  "
                f"CONTRACT SHIFT {detour['day']}"
            )
            shortfall = max(0, target_balance - projected_balance)
            detail_text = (
                "TICKET FUNDED  •  REPORT TO THE OUTPOST BOSS"
                if cleared
                else f"AFTER PAY: {self.format_money(projected_balance)}  •  "
                f"STILL NEEDED: {self.format_money(shortfall)}"
            )
        else:
            title_text = (
                f"BLACKGLASS DEBT RECOVERY  •  SHIFT {detour['day']} OF "
                f"{BLACKGLASS_MAX_DAYS}"
            )
            detail_text = (
                "DEBT CLEARED  •  REPORT TO THE OUTPOST BOSS"
                if cleared
                else f"AFTER PAY: {self.format_money(projected_balance)}  •  "
                f"STILL OWED: {self.format_money(abs(projected_balance))}"
            )
        title = self.card_font.render(title_text, True, accent)
        detail = self.card_font.render(detail_text, True, COLORS["text"])
        self.screen.blit(title, title.get_rect(center=(fund.centerx, fund.y + 10)))
        self.screen.blit(detail, detail.get_rect(center=(fund.centerx, fund.y + 23)))

    def draw_debt_alert_panel(self, projected_balance, panel):
        """Warn that this shift's result will trigger a Blackglass reassignment."""

        fund = pygame.Rect(panel.x + 130, panel.y + 386, panel.width - 260, 36)
        accent = (245, 130, 115)
        pygame.draw.rect(self.screen, (40, 14, 20), fund, border_radius=9)
        pygame.draw.rect(self.screen, accent, fund, width=1, border_radius=9)
        title = self.card_font.render(
            f"DEBT ALERT  •  BALANCE {self.format_money(projected_balance)}  •  "
            f"LIMIT {self.format_money(BLACKGLASS_DEBT_THRESHOLD)}",
            True,
            accent,
        )
        detail = self.card_font.render(
            "THE BOSS WANTS A WORD ABOUT YOUR PERFORMANCE", True, COLORS["text"]
        )
        self.screen.blit(title, title.get_rect(center=(fund.centerx, fund.y + 10)))
        self.screen.blit(detail, detail.get_rect(center=(fund.centerx, fund.y + 23)))

    def draw_boss_portrait(self, center, scene, speaking, elapsed):
        """Draw a simple code-made portrait for the boss on the call."""

        outpost = scene == "outpost"
        skin = (176, 118, 70) if outpost else (150, 126, 178)
        dark = (60, 36, 22) if outpost else (46, 36, 66)
        glow = (255, 160, 64) if outpost else (240, 128, 112)
        cx, cy = center
        frame = pygame.Rect(0, 0, 250, 270)
        frame.center = (cx, cy)
        pygame.draw.rect(self.screen, (10, 12, 18), frame, border_radius=16)
        pygame.draw.rect(self.screen, glow, frame, width=3, border_radius=16)
        shoulders = ((cx - 100, frame.bottom - 4), (cx - 70, cy + 52),
                     (cx + 70, cy + 52), (cx + 100, frame.bottom - 4))
        pygame.draw.polygon(self.screen, dark, shoulders)
        head = pygame.Rect(0, 0, 118, 138)
        head.center = (cx, cy - 22)
        pygame.draw.ellipse(self.screen, dark, head.inflate(10, 10))
        pygame.draw.ellipse(self.screen, skin, head)
        blink = elapsed > 400 and (elapsed // 170) % 19 == 0
        for side in (-1, 1):
            eye = (cx + side * 26, cy - 34)
            if blink:
                pygame.draw.line(self.screen, dark, (eye[0] - 10, eye[1]), (eye[0] + 10, eye[1]), 3)
            else:
                pygame.draw.ellipse(self.screen, (245, 240, 220), pygame.Rect(eye[0] - 12, eye[1] - 8, 24, 16))
                pygame.draw.circle(self.screen, (30, 20, 20), eye, 5)
                pygame.draw.line(self.screen, dark, (eye[0] - 14, eye[1] - 12 - 3 * side), (eye[0] + 14, eye[1] - 12 + 3 * side), 3)
        if outpost:
            mask = pygame.Rect(0, 0, 70, 40)
            mask.center = (cx, cy + 6)
            pygame.draw.rect(self.screen, (84, 90, 70), mask, border_radius=12)
            for dx in (-16, 0, 16):
                pygame.draw.circle(self.screen, (40, 44, 34), (cx + dx, cy + 8), 5)
        else:
            mouth_open = speaking and (elapsed // 120) % 2 == 0
            pygame.draw.ellipse(
                self.screen, (40, 14, 22),
                pygame.Rect(cx - 18, cy + 8, 36, 16 if mouth_open else 6),
            )
        if not speaking:
            dim = pygame.Surface(frame.size, pygame.SRCALPHA)
            dim.fill((4, 6, 12, 120))
            self.screen.blit(dim, frame.topleft)

    def draw_blackglass_boss_screen(self):
        """Draw a boss conversation as a full-screen transmission."""

        elapsed = (
            0
            if self.blackglass_boss_started_at is None
            else pygame.time.get_ticks() - self.blackglass_boss_started_at
        )
        scene = self.blackglass_boss_scene
        if scene == "outpost":
            self.screen.fill((30, 16, 10))
            haze = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
            pygame.draw.ellipse(haze, (224, 96, 36, 46), pygame.Rect(520, 40, 640, 360))
            pygame.draw.ellipse(haze, (176, 196, 52, 22), pygame.Rect(-120, 300, 720, 320))
            self.screen.blit(haze, (0, 0))
            header_text = "BLACKGLASS OUTPOST  //  SUPERVISOR'S OFFICE"
            header_color = (255, 160, 64)
        else:
            self.draw_space_background(elapsed)
            header_text = "INCOMING TRANSMISSION  //  CLINIC HEADQUARTERS"
            header_color = (240, 128, 112)
        header = self.small_font.render(header_text, True, header_color)
        header_rect = header.get_rect(center=(WINDOW_SIZE[0] // 2, 52))
        self.screen.blit(header, header_rect)
        if (elapsed // 500) % 2 == 0 and scene == "clinic":
            pygame.draw.circle(self.screen, (240, 70, 70), (header_rect.left - 14, 52), 5)

        speaker, line = self.blackglass_boss_lines[self.blackglass_boss_index]
        style = SPEAKER_STYLE.get(speaker, SPEAKER_STYLE[PLAYER_SPEAKER])
        accent = style["accent"]
        boss_speaking = speaker != PLAYER_SPEAKER
        self.draw_boss_portrait((WINDOW_SIZE[0] // 2, 205), scene, boss_speaking, elapsed)

        panel = pygame.Rect(145, 365, 810, 205)
        pygame.draw.rect(self.screen, (1, 5, 10), panel.move(8, 9), border_radius=18)
        pygame.draw.rect(self.screen, (9, 22, 31), panel, border_radius=18)
        pygame.draw.rect(self.screen, accent, panel, width=3, border_radius=18)
        badge = pygame.Rect(panel.x + 26, panel.y + 20, 190, 34)
        pygame.draw.rect(self.screen, style["fill"], badge, border_radius=7)
        pygame.draw.rect(self.screen, accent, badge, width=1, border_radius=7)
        speaker_label = self.dialogue_speaker_font.render(speaker, True, accent)
        self.screen.blit(speaker_label, speaker_label.get_rect(center=badge.center))
        line_box = pygame.Rect(panel.x + 28, panel.y + 74, panel.width - 56, 70)
        self.draw_wrapped_text(
            line, self.dialogue_body_font, COLORS["text"], line_box, line_spacing=4
        )
        total = len(self.blackglass_boss_lines)
        for dot_index in range(total):
            dot_color = accent if dot_index <= self.blackglass_boss_index else (55, 76, 84)
            pygame.draw.circle(
                self.screen,
                dot_color,
                (panel.x + 32 + dot_index * 18, panel.bottom - 25),
                4 if dot_index == self.blackglass_boss_index else 3,
            )
        final_line = self.blackglass_boss_index == total - 1
        action = self.blackglass_boss_action
        prompt_text = (
            "CONTINUE"
            if not final_line
            else "TRAVEL TO BLACKGLASS"
            if action == "arrive"
            else f"BEGIN SHIFT {self.blackglass_detour['day'] + 1}"
            if action == "next_day"
            else "RETURN TO YOUR CLINIC"
        )
        if not final_line:
            prompt_text = "CLICK OR PRESS ENTER TO CONTINUE"
        prompt = self.tutorial_label_font.render(prompt_text, True, accent)
        prompt_panel = prompt.get_rect(
            center=(panel.right - 28 - prompt.get_width() // 2 - 12, panel.bottom - 25)
        ).inflate(24, 12)
        pygame.draw.rect(self.screen, (12, 30, 40), prompt_panel, border_radius=10)
        pygame.draw.rect(self.screen, accent, prompt_panel, width=2, border_radius=10)
        self.screen.blit(prompt, prompt.get_rect(center=prompt_panel.center))
