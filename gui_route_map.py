"""Galactic Route Map screen and code-drawn destination artwork."""

import math
import random

import pygame

from PlanetData import DestinationType, MAP_DESTINATIONS, get_destination
from Player import RETURN_PASSAGE_COST
from RouteController import DestinationState
from gui_state import GameState
from gui_theme import COLORS, WINDOW_SIZE


class RouteMapMixin:
    """Draw and inspect the campaign's persistent interplanetary route."""

    def has_return_passage(self):
        """Return whether the campaign has purchased transport back to Earth."""

        return self.route.return_passage_purchased

    def get_return_passage_progress(self):
        """Return the persistent fraction of the Earth-ticket goal funded."""

        if self.has_return_passage():
            return 1.0
        return min(1.0, max(0.0, self.player.balance / RETURN_PASSAGE_COST))

    def get_intended_route_destination(self):
        """Return the paid destination the player is currently working toward."""

        if self.route.next_destination is not None:
            return self.route.next_destination
        if (
            self.route.route_is_complete
            or self.route.current_destination is self.route.destinations[-1]
        ):
            return next(
                destination
                for destination in MAP_DESTINATIONS
                if destination.map_data.destination_type is DestinationType.EARTH
            )
        return None

    def get_blackglass_credit_shortfall(self):
        """Return the exact amount Blackglass work must recover for travel."""

        destination = self.get_intended_route_destination()
        if destination is None:
            return 0
        return max(0, destination.map_data.ticket_price - self.player.balance)

    def setup_route_map(self):
        """Create stable star positions and layout data for the route map."""

        self.route_map_started_at = pygame.time.get_ticks()
        star_random = random.Random(151_404)
        self.route_map_stars = tuple(
            (
                star_random.randrange(12, WINDOW_SIZE[0] - 12),
                star_random.randrange(78, WINDOW_SIZE[1] - 18),
                star_random.choice((1, 1, 1, 1, 2)),
                star_random.randrange(0, 1400),
                star_random.choice(
                    (
                        (151, 202, 234),
                        (211, 190, 238),
                        (218, 239, 232),
                    )
                ),
            )
            for _ in range(92)
        )
        self.route_map_area = pygame.Rect(35, 132, 690, 410)
        self.route_map_ticket_panel = pygame.Rect(750, 132, 315, 426)
        self.route_map_purchase_button = pygame.Rect(775, 488, 265, 42)
        self.route_map_travel_button = pygame.Rect(775, 488, 265, 42)
        self.route_map_tutorial_skip_button = pygame.Rect(930, 54, 138, 27)
        self.blackglass_contract_return_button = pygame.Rect(385, 523, 330, 46)
        self.route_map_message = "Select a destination to inspect its ticket."
        self.route_map_tutorial_active = False
        self.route_map_tutorial_seen = False
        self.route_map_tutorial_step = None
        self.route_map_tutorial_nudge = ""

    def get_route_map_node_center(self, destination):
        """Convert normalized destination data into the map's base coordinates."""

        position_x, position_y = destination.map_data.position
        return (
            round(self.route_map_area.x + position_x * self.route_map_area.width),
            round(self.route_map_area.y + position_y * self.route_map_area.height),
        )

    def get_route_map_node_radius(self, destination):
        return round(27 * destination.map_data.icon.size_scale)

    def get_route_map_node_rect(self, destination):
        center = self.get_route_map_node_center(destination)
        radius = self.get_route_map_node_radius(destination)
        return pygame.Rect(
            center[0] - radius - 12,
            center[1] - radius - 12,
            (radius + 12) * 2,
            (radius + 12) * 2,
        )

    def handle_route_map_click(self, position):
        """Select a destination for inspection without authorizing travel."""

        selected = self.route.selected_map_destination
        if selected is not None:
            state = self.route.get_destination_state(selected.key, selected=True)
            if (
                state is DestinationState.EMERGENCY_CONTRACT
                and self.route_map_purchase_button.collidepoint(position)
            ):
                self.play_sfx("button")
                if self.get_blackglass_credit_shortfall() <= 0:
                    self.route_map_message = (
                        "Your intended destination is already fully funded."
                    )
                else:
                    self.state = GameState.BLACKGLASS_CONTRACT
                return selected
            if (
                state is DestinationState.TICKET_REQUIRED
                and self.route_map_purchase_button.collidepoint(position)
            ):
                self.play_sfx("button")
                try:
                    ticket_cost = self.route.purchase_ticket(
                        selected.key,
                        self.player.balance,
                    )
                except ValueError as error:
                    self.route_map_message = str(error)
                else:
                    self.player.pay(ticket_cost)
                    self.route_map_message = (
                        "Return Passage paid. Earth travel is ready."
                        if selected.map_data.destination_type is DestinationType.EARTH
                        else f"Ticket paid. Route to {selected.planet_name} is ready."
                    )
                return selected
            if (
                state is DestinationState.READY_TO_TRAVEL
                and self.route_map_travel_button.collidepoint(position)
            ):
                self.play_sfx("button")
                if selected.map_data.destination_type is DestinationType.EARTH:
                    self.begin_homecoming_sequence()
                else:
                    self.begin_ending_sequence(selected.key)
                return selected

        for destination in reversed(MAP_DESTINATIONS):
            if self.get_route_map_node_rect(destination).collidepoint(position):
                self.play_sfx("button")
                self.route.select_map_destination(destination.key)
                self.route_map_message = self.get_route_map_selection_message(
                    destination
                )
                return destination
        return None

    def draw_route_map_screen(self):
        """Draw the map shell, route, planet nodes, credits, and legend."""

        elapsed = pygame.time.get_ticks() - self.route_map_started_at
        self.draw_route_map_background(elapsed)

        title = self.heading_font.render(
            "GALACTIC ROUTE MAP",
            True,
            (225, 238, 235),
        )
        self.screen.blit(title, title.get_rect(center=(550, 37)))
        subtitle = self.small_font.render(
            "COSMIC CLINIC NAVIGATION  //  DESTINATION TICKETS REQUIRED",
            True,
            (122, 164, 177),
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(550, 68)))

        self.draw_route_map_status_bar()
        self.draw_route_map_connections()
        for destination in MAP_DESTINATIONS:
            self.draw_route_map_destination(destination, elapsed)
        self.draw_route_map_ufo(elapsed)
        self.draw_route_map_legend()
        self.draw_route_map_ticket_panel()

        footer = self.small_font.render(
            f"Select a planet to inspect  •  Esc for exit options  •  {self.get_fullscreen_hint()}",
            True,
            (104, 132, 145),
        )
        self.screen.blit(footer, footer.get_rect(center=(550, 635)))

    def draw_route_map_background(self, elapsed):
        """Draw a deep animated star chart behind the route."""

        for y in range(WINDOW_SIZE[1]):
            blend_amount = y / WINDOW_SIZE[1]
            color = (
                round(5 + 8 * blend_amount),
                round(11 + 8 * blend_amount),
                round(27 + 19 * blend_amount),
            )
            pygame.draw.line(self.screen, color, (0, y), (WINDOW_SIZE[0], y))

        haze = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        pygame.draw.ellipse(haze, (47, 82, 117, 30), (-160, 90, 640, 430))
        pygame.draw.ellipse(haze, (94, 46, 111, 24), (650, 130, 620, 410))
        self.screen.blit(haze, (0, 0))

        for star_x, star_y, radius, phase, color in self.route_map_stars:
            pulse = 0.58 + 0.42 * math.sin((elapsed + phase) / 360)
            star_color = tuple(round(channel * pulse) for channel in color)
            pygame.draw.circle(self.screen, star_color, (star_x, star_y), radius)

        # Faint navigation grid rings make the map feel like a ship console
        # without obscuring the planets or their status labels.
        grid = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        for radius in (125, 220, 330, 445):
            pygame.draw.circle(grid, (91, 143, 168, 22), (550, 338), radius, 1)
        for angle in (0.22, 0.83, 1.47, 2.18, 2.76):
            end = (
                round(550 + math.cos(angle) * 560),
                round(338 + math.sin(angle) * 420),
            )
            pygame.draw.line(grid, (91, 143, 168, 18), (550, 338), end, 1)
        self.screen.blit(grid, (0, 0))

    def draw_route_map_status_bar(self):
        """Show the current location and map-ready credit balance."""

        current = self.route.current_location
        current_name = current.planet_name if current is not None else "UNKNOWN"
        location_panel = pygame.Rect(48, 86, 674, 38)
        credits_panel = pygame.Rect(830, 86, 222, 38)
        for panel in (location_panel, credits_panel):
            pygame.draw.rect(self.screen, (7, 18, 31), panel, border_radius=9)
            pygame.draw.rect(self.screen, (75, 132, 149), panel, width=1, border_radius=9)

        location = self.small_font.render(
            f"CURRENT LOCATION   {current_name.upper()}",
            True,
            (193, 222, 219),
        )
        self.screen.blit(location, location.get_rect(midleft=(location_panel.x + 15, location_panel.centery)))
        credits = self.small_font.render(
            f"CREDITS   {self.format_money(self.route.available_credits)}",
            True,
            self.get_balance_color(self.route.available_credits),
        )
        self.screen.blit(credits, credits.get_rect(center=credits_panel.center))

    def draw_route_map_connections(self):
        """Draw dotted travel lanes behind their destination nodes."""

        by_key = {destination.key: destination for destination in MAP_DESTINATIONS}
        for destination in MAP_DESTINATIONS:
            link_key = (
                destination.map_data.previous_destination
                or destination.map_data.unlock_requirement
            )
            previous = by_key.get(link_key)
            if previous is None:
                continue
            start = pygame.Vector2(self.get_route_map_node_center(previous))
            end = pygame.Vector2(self.get_route_map_node_center(destination))
            distance = start.distance_to(end)
            if distance <= 0:
                continue
            unlocked = destination.key in self.route.unlocked_destination_keys
            owned = destination.key in self.route.purchased_ticket_keys
            color = (
                (112, 238, 190)
                if owned
                else (109, 181, 205)
                if unlocked
                else (62, 76, 96)
            )
            for dot_index in range(max(2, int(distance // 15)) + 1):
                amount = dot_index / max(1, int(distance // 15))
                point = start.lerp(end, min(1.0, amount))
                pygame.draw.circle(self.screen, color, (round(point.x), round(point.y)), 2)

    def get_route_map_state_style(self, state):
        """Return the map label and color assigned to a destination state."""

        colors = {
            DestinationState.CURRENT_LOCATION: (108, 231, 191),
            DestinationState.TICKET_REQUIRED: (115, 194, 221),
            DestinationState.TICKET_OWNED: (244, 198, 91),
            DestinationState.READY_TO_TRAVEL: (116, 244, 169),
            DestinationState.SHIFT_COMPLETE: (142, 211, 207),
            DestinationState.NO_NEW_PATIENTS: (117, 165, 191),
            DestinationState.LOCKED: (94, 101, 118),
            DestinationState.UNKNOWN_DESTINATION: (174, 111, 151),
            DestinationState.EMERGENCY_CONTRACT: (238, 121, 102),
        }
        return state.value.upper(), colors[state]

    def get_route_map_status(self, destination, selected=False):
        """Return state, label, and color for one map destination."""

        state = self.route.get_destination_state(
            destination.key,
            selected=selected,
        )
        label, color = self.get_route_map_state_style(state)
        return state, label, color

    def draw_route_map_destination(self, destination, elapsed):
        """Draw one coded planet icon and its route-state label."""

        center = self.get_route_map_node_center(destination)
        radius = self.get_route_map_node_radius(destination)
        icon = destination.map_data.icon
        selected = (
            self.route.selected_map_destination is not None
            and self.route.selected_map_destination.key == destination.key
        )
        _, status_text, status_color = self.get_route_map_status(
            destination,
            selected=selected,
        )
        unlocked = destination.key in self.route.unlocked_destination_keys

        glow = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        if unlocked or selected or destination.key == self.route.current_location_key:
            glow_alpha = 40 + round(18 * (0.5 + 0.5 * math.sin(elapsed / 420)))
            pygame.draw.circle(glow, (*status_color, glow_alpha), center, radius + 15)
        self.screen.blit(glow, (0, 0))

        if icon.ring_color is not None:
            ring = pygame.Rect(
                center[0] - radius - 13,
                center[1] - round(radius * 0.38),
                (radius + 13) * 2,
                round(radius * 0.76),
            )
            pygame.draw.ellipse(self.screen, icon.ring_color, ring, width=3)

        pygame.draw.circle(self.screen, (4, 8, 16), (center[0] + 3, center[1] + 5), radius + 2)
        pygame.draw.circle(self.screen, icon.base_color, center, radius)
        self.draw_route_map_planet_details(destination, center, radius)

        shade = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        pygame.draw.ellipse(
            shade,
            (3, 8, 20, 88),
            pygame.Rect(center[0] + 2, center[1] - radius, radius, radius * 2),
        )
        self.screen.blit(shade, (0, 0))
        pygame.draw.circle(self.screen, status_color, center, radius, width=2)
        if selected:
            pygame.draw.circle(self.screen, (237, 222, 167), center, radius + 8, width=2)

        name = self.tutorial_label_font.render(
            destination.planet_name.upper(),
            True,
            (218, 228, 226) if unlocked else (130, 137, 149),
        )
        self.screen.blit(name, name.get_rect(center=(center[0], center[1] + radius + 18)))
        status = self.pile_font.render(status_text, True, status_color)
        status_panel = status.get_rect(center=(center[0], center[1] + radius + 36)).inflate(14, 5)
        pygame.draw.rect(self.screen, (8, 15, 26), status_panel, border_radius=6)
        pygame.draw.rect(self.screen, status_color, status_panel, width=1, border_radius=6)
        self.screen.blit(status, status.get_rect(center=status_panel.center))

    def draw_route_map_planet_details(self, destination, center, radius):
        """Give every initial map planet a readable coded identity."""

        icon = destination.map_data.icon
        cx, cy = center
        if icon.style == "earth":
            pygame.draw.ellipse(
                self.screen,
                icon.accent_color,
                (cx - radius + 7, cy - radius // 2, radius, radius // 2),
            )
            pygame.draw.ellipse(
                self.screen,
                icon.accent_color,
                (cx - 2, cy + 1, radius - 2, radius // 2),
            )
            pygame.draw.arc(
                self.screen,
                icon.detail_color,
                (cx - radius + 3, cy - radius // 3, radius * 2 - 6, radius // 2),
                0,
                math.pi,
                2,
            )
        elif icon.style == "blackglass_industrial":
            pygame.draw.circle(self.screen, icon.accent_color, (cx - radius // 3, cy - radius // 4), max(3, radius // 5))
            pygame.draw.lines(
                self.screen,
                icon.detail_color,
                False,
                ((cx - radius // 2, cy + radius // 2), (cx - 2, cy), (cx + radius // 3, cy + radius // 3)),
                2,
            )
        elif icon.style == "triska_desert":
            pygame.draw.ellipse(self.screen, icon.accent_color, (cx - radius, cy - radius // 2, radius * 2, radius // 2))
            pygame.draw.circle(self.screen, icon.detail_color, (cx + radius // 3, cy - radius // 3), max(3, radius // 6))
        elif icon.style == "lumora_jungle":
            pygame.draw.circle(self.screen, icon.accent_color, (cx - radius // 3, cy - radius // 4), max(4, radius // 3))
            for offset_x, offset_y in ((10, -9), (-8, 11), (13, 8), (-2, -14)):
                pygame.draw.circle(self.screen, icon.detail_color, (cx + offset_x, cy + offset_y), 2)
        else:
            pygame.draw.arc(
                self.screen,
                icon.accent_color,
                (cx - radius + 4, cy - radius + 7, radius * 2 - 8, radius * 2 - 14),
                0.2,
                math.pi * 1.7,
                3,
            )
            pygame.draw.circle(self.screen, icon.detail_color, (cx + radius // 4, cy - radius // 3), max(3, radius // 7))

    def draw_route_map_ufo(self, elapsed):
        """Mark the clinic's current map location with a tiny hovering UFO."""

        current = self.route.current_location
        if current is None:
            return
        planet_center = self.get_route_map_node_center(current)
        bob = round(math.sin(elapsed / 320) * 2)
        center = (planet_center[0] - 42, planet_center[1] - 36 + bob)
        pygame.draw.ellipse(self.screen, (72, 147, 173), (center[0] - 9, center[1] - 8, 18, 11))
        pygame.draw.ellipse(self.screen, (113, 125, 149), (center[0] - 19, center[1] - 3, 38, 12))
        pygame.draw.arc(self.screen, (184, 226, 230), (center[0] - 18, center[1] - 2, 36, 8), 0, math.pi, 2)
        for light_x in (-10, 0, 10):
            pygame.draw.circle(self.screen, (100, 242, 185), (center[0] + light_x, center[1] + 7), 1)

    def draw_route_map_legend(self):
        """Explain every destination state in a compact two-row legend."""

        legend_states = (
            DestinationState.CURRENT_LOCATION,
            DestinationState.TICKET_REQUIRED,
            DestinationState.TICKET_OWNED,
            DestinationState.READY_TO_TRAVEL,
            DestinationState.SHIFT_COMPLETE,
            DestinationState.NO_NEW_PATIENTS,
            DestinationState.LOCKED,
            DestinationState.EMERGENCY_CONTRACT,
        )
        for index, state in enumerate(legend_states):
            label_text, color = self.get_route_map_state_style(state)
            item_x = 51 + (index % 4) * 170
            item_y = 568 + (index // 4) * 24
            pygame.draw.circle(self.screen, color, (item_x, item_y), 4)
            label = self.tutorial_label_font.render(label_text, True, (190, 207, 211))
            self.screen.blit(label, label.get_rect(midleft=(item_x + 9, item_y)))

    def get_route_map_selection_message(self, destination):
        """Return concise ticket-terminal guidance for the selected node."""

        state = self.route.get_destination_state(destination.key, selected=True)
        if state is DestinationState.EMERGENCY_CONTRACT:
            if self.get_blackglass_credit_shortfall() <= 0:
                return "Intended ticket funded; no contract needed."
            return (
                f"Contract covers the {self.format_money(self.get_blackglass_credit_shortfall())} "
                "travel shortfall."
            )
        return {
            DestinationState.CURRENT_LOCATION: "The Cosmic Clinic is stationed here.",
            DestinationState.TICKET_REQUIRED: "Purchase this ticket to authorize travel.",
            DestinationState.TICKET_OWNED: "Ticket secured for this destination.",
            DestinationState.READY_TO_TRAVEL: "Ticket verified. Confirm to depart.",
            DestinationState.SHIFT_COMPLETE: "Shift complete. Choose the next stop.",
            DestinationState.NO_NEW_PATIENTS: "No new patients are currently available.",
            DestinationState.LOCKED: "Complete the previous clinic first.",
            DestinationState.UNKNOWN_DESTINATION: "Clinic records are not available yet.",
        }[state]

    def get_route_map_patient_text(self, destination):
        """Return the patient count presented by the ticket terminal."""

        if destination.map_data.destination_type is DestinationType.BLACKGLASS:
            return "CONSTANT INTAKE"
        if not destination.map_data.has_patients or destination.day_number is None:
            return "NO PATIENTS"
        clinic = get_destination(destination.day_number)
        return f"{len(clinic.patient_roster)} WAITING"

    def draw_route_map_ticket_panel(self):
        """Draw destination details, ticket status, and the contextual action."""

        panel = self.route_map_ticket_panel
        pygame.draw.rect(self.screen, (2, 7, 15), panel.move(5, 6), border_radius=16)
        pygame.draw.rect(self.screen, (10, 22, 35), panel, border_radius=16)
        pygame.draw.rect(self.screen, (78, 139, 157), panel, width=2, border_radius=16)

        selected = self.route.selected_map_destination
        if selected is None:
            title = self.tutorial_subtitle_font.render(
                "DESTINATION TICKET",
                True,
                (151, 202, 211),
            )
            self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 32)))
            prompt = pygame.Rect(panel.x + 27, panel.y + 92, panel.width - 54, 110)
            self.draw_wrapped_text(
                "Select a planet on the route map to inspect its ticket and patient status.",
                self.body_font,
                (197, 213, 215),
                prompt,
                line_spacing=5,
            )
            return

        state, status_text, status_color = self.get_route_map_status(
            selected,
            selected=True,
        )
        badge = pygame.Rect(panel.x + 20, panel.y + 15, panel.width - 40, 28)
        pygame.draw.rect(self.screen, (17, 32, 44), badge, border_radius=7)
        pygame.draw.rect(self.screen, status_color, badge, width=1, border_radius=7)
        badge_label = self.compact_ui_font.render(status_text, True, status_color)
        self.screen.blit(badge_label, badge_label.get_rect(center=badge.center))

        name = self.tutorial_subtitle_font.render(
            selected.planet_name.upper(),
            True,
            (229, 235, 228),
        )
        self.screen.blit(name, name.get_rect(center=(panel.centerx, panel.y + 65)))
        subtitle = self.compact_ui_font.render(
            selected.subtitle.upper(),
            True,
            (128, 166, 178),
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(panel.centerx, panel.y + 87)))

        description_box = pygame.Rect(panel.x + 22, panel.y + 105, panel.width - 44, 64)
        self.draw_wrapped_text(
            selected.map_data.description,
            self.small_font,
            (187, 204, 204),
            description_box,
            line_spacing=2,
        )
        pygame.draw.line(
            self.screen,
            (59, 92, 105),
            (panel.x + 20, panel.y + 177),
            (panel.right - 20, panel.y + 177),
            1,
        )

        if selected.map_data.destination_type is DestinationType.BLACKGLASS:
            self.draw_blackglass_contract_panel(selected, state, status_color)
            self.draw_route_map_ticket_action(selected, state, status_color)
            self.draw_route_map_message((205, 187, 187))
            return

        ticket_price = selected.map_data.ticket_price
        ticket_funded = (
            selected.key in self.route.purchased_ticket_keys
            or selected.key in self.route.used_ticket_keys
        )
        remaining = (
            0
            if ticket_funded
            else max(0, ticket_price - self.route.available_credits)
        )
        details = (
            ("PATIENTS", self.get_route_map_patient_text(selected)),
            ("TICKET PRICE", "FREE" if ticket_price == 0 else self.format_money(ticket_price)),
            (
                "CURRENT SAVINGS"
                if selected.map_data.destination_type is DestinationType.EARTH
                else "CURRENT CREDITS",
                self.format_money(self.route.available_credits),
            ),
            (
                "ROUTE ACCESS"
                if state in (DestinationState.LOCKED, DestinationState.UNKNOWN_DESTINATION)
                else "STILL REQUIRED",
                status_text.upper()
                if state in (DestinationState.LOCKED, DestinationState.UNKNOWN_DESTINATION)
                else self.format_money(remaining),
            ),
        )
        for row_index, (label_text, value_text) in enumerate(details):
            row_y = panel.y + 197 + row_index * 25
            label = self.compact_ui_font.render(label_text, True, (113, 146, 157))
            value_color = (
                self.get_balance_color(self.route.available_credits)
                if label_text in ("CURRENT CREDITS", "CURRENT SAVINGS")
                else status_color
                if label_text == "ROUTE ACCESS"
                else (229, 233, 221)
            )
            value = self.compact_ui_font.render(value_text, True, value_color)
            self.screen.blit(label, label.get_rect(midleft=(panel.x + 25, row_y)))
            self.screen.blit(value, value.get_rect(midright=(panel.right - 25, row_y)))

        if selected.map_data.destination_type is DestinationType.EARTH:
            self.draw_route_map_earth_progress(selected)
        self.draw_route_map_ticket_stub(selected, state, status_color)
        self.draw_route_map_ticket_action(selected, state, status_color)

        self.draw_route_map_message((190, 211, 215))

    def draw_route_map_message(self, color):
        """Fit complete destination guidance beneath the action button."""

        panel = self.route_map_ticket_panel
        message_box = pygame.Rect(
            panel.x + 18,
            panel.bottom - 27,
            panel.width - 36,
            23,
        )
        fonts = (
            self.compact_ui_font,
            self.legible_micro_font,
            self.tiny_font,
        )
        for font in fonts:
            lines = self.wrap_text(self.route_map_message, font, message_box.width)
            line_height = font.get_linesize()
            if len(lines) <= 2 and len(lines) * line_height <= message_box.height:
                break
        else:
            font = fonts[-1]
            lines = self.wrap_text(self.route_map_message, font, message_box.width)[:2]

        previous_clip = self.screen.get_clip()
        self.screen.set_clip(message_box)
        try:
            total_height = len(lines) * font.get_linesize()
            y = message_box.centery - total_height // 2
            for line in lines:
                rendered = font.render(line, True, color)
                self.screen.blit(
                    rendered,
                    rendered.get_rect(center=(message_box.centerx, y + font.get_linesize() // 2)),
                )
                y += font.get_linesize()
        finally:
            self.screen.set_clip(previous_clip)

    def draw_blackglass_contract_panel(self, destination, state, status_color):
        """Draw Blackglass as emergency employment rather than paid travel."""

        panel = self.route_map_ticket_panel
        intended = self.get_intended_route_destination()
        intended_name = (
            intended.planet_name.split()[0].upper()
            if intended is not None
            else "NO ACTIVE DESTINATION"
        )
        shortfall = self.get_blackglass_credit_shortfall()
        details = (
            ("PATIENTS", "CONSTANT INTAKE"),
            ("CONTRACT", "EMERGENCY CLINIC"),
            ("TRANSPORT", "PROVIDED"),
            (f"NEEDED FOR {intended_name}", self.format_money(shortfall)),
        )
        for row_index, (label_text, value_text) in enumerate(details):
            row_y = panel.y + 197 + row_index * 25
            label = self.compact_ui_font.render(label_text, True, (139, 126, 129))
            value = self.compact_ui_font.render(
                value_text,
                True,
                status_color if row_index in (1, 3) else (229, 233, 221),
            )
            self.screen.blit(label, label.get_rect(midleft=(panel.x + 25, row_y)))
            self.screen.blit(value, value.get_rect(midright=(panel.right - 25, row_y)))

        contract = pygame.Rect(panel.x + 24, panel.y + 294, panel.width - 48, 54)
        pygame.draw.rect(self.screen, (42, 35, 39), contract, border_radius=7)
        pygame.draw.rect(self.screen, status_color, contract, width=2, border_radius=7)
        pygame.draw.circle(self.screen, (10, 22, 35), (contract.x, contract.centery), 7)
        pygame.draw.circle(self.screen, (10, 22, 35), (contract.right, contract.centery), 7)
        heading = self.compact_ui_font.render(
            "EMERGENCY CLINIC CONTRACT",
            True,
            (244, 197, 184),
        )
        transport = self.small_font.render(
            "TRANSPORTATION PROVIDED",
            True,
            status_color,
        )
        self.screen.blit(heading, heading.get_rect(center=(contract.centerx, contract.y + 18)))
        self.screen.blit(transport, transport.get_rect(center=(contract.centerx, contract.y + 38)))

    def draw_route_map_earth_progress(self, destination):
        """Show the permanent savings goal directly above Earth's ticket."""

        panel = self.route_map_ticket_panel
        track = pygame.Rect(panel.x + 25, panel.y + 278, panel.width - 50, 7)
        price = max(1, destination.map_data.ticket_price)
        progress = 1.0 if self.has_return_passage() else min(
            1.0,
            max(0.0, self.route.available_credits / price),
        )
        pygame.draw.rect(self.screen, (3, 8, 16), track, border_radius=4)
        if progress > 0:
            fill = pygame.Rect(
                track.x,
                track.y,
                max(3, round(track.width * progress)),
                track.height,
            )
            pygame.draw.rect(self.screen, (255, 200, 75), fill, border_radius=4)
        pygame.draw.rect(self.screen, (151, 118, 52), track, width=1, border_radius=4)

    def draw_route_map_ticket_stub(self, destination, state, status_color):
        """Draw a physical ticket that gains PAID or USED stamps."""

        panel = self.route_map_ticket_panel
        ticket = pygame.Rect(panel.x + 24, panel.y + 294, panel.width - 48, 54)
        is_earth = destination.map_data.destination_type is DestinationType.EARTH
        unavailable = state in (
            DestinationState.LOCKED,
            DestinationState.UNKNOWN_DESTINATION,
        )
        ticket_fill = (
            (93, 99, 105)
            if unavailable
            else (248, 220, 132)
            if is_earth
            else (227, 222, 193)
        )
        ticket_border = (
            (119, 128, 138)
            if unavailable
            else (255, 198, 75)
            if is_earth
            else status_color
        )
        pygame.draw.rect(self.screen, ticket_fill, ticket, border_radius=7)
        pygame.draw.rect(self.screen, ticket_border, ticket, width=2, border_radius=7)
        pygame.draw.circle(self.screen, (10, 22, 35), (ticket.x, ticket.centery), 7)
        pygame.draw.circle(self.screen, (10, 22, 35), (ticket.right, ticket.centery), 7)
        pygame.draw.line(
            self.screen,
            (132, 126, 109),
            (ticket.x + 164, ticket.y + 6),
            (ticket.x + 164, ticket.bottom - 6),
            1,
        )
        ticket_labels = {
            "training_orbit": "TRAINING ORBIT",
            "triska_station": "TRISKA STATION",
            "lumora_canopy": "LUMORA CANOPY",
        }
        ticket_text_color = (205, 211, 214) if unavailable else (31, 39, 43)
        ticket_name = self.compact_ui_font.render(
            "RETURN PASSAGE"
            if is_earth
            else ticket_labels.get(destination.key, destination.planet_name.upper()),
            True,
            ticket_text_color,
        )
        self.screen.blit(ticket_name, ticket_name.get_rect(midleft=(ticket.x + 15, ticket.y + 18)))
        price_text = (
            f"EARTH  //  {self.format_money(destination.map_data.ticket_price)}"
            if is_earth
            else
            "FREE CONTRACT"
            if destination.map_data.ticket_price == 0
            else self.format_money(destination.map_data.ticket_price)
        )
        price = self.small_font.render(
            price_text,
            True,
            (211, 216, 218) if unavailable else (44, 53, 55),
        )
        self.screen.blit(price, price.get_rect(midleft=(ticket.x + 15, ticket.y + 37)))

        stamp_text = None
        if destination.key in self.route.purchased_ticket_keys:
            stamp_text = "PAID"
        elif destination.key in self.route.used_ticket_keys:
            stamp_text = "USED"
        elif state is DestinationState.NO_NEW_PATIENTS:
            stamp_text = "CLOSED"
        elif state is DestinationState.SHIFT_COMPLETE:
            stamp_text = "COMPLETE"
        elif state is DestinationState.CURRENT_LOCATION:
            stamp_text = "ACTIVE"
        elif state is DestinationState.LOCKED:
            stamp_text = "LOCKED"
        elif state is DestinationState.UNKNOWN_DESTINATION:
            stamp_text = "UNAVAILABLE"
        if stamp_text:
            stamp = self.tutorial_label_font.render(stamp_text, True, status_color)
            stamp_rect = stamp.get_rect(center=(ticket.right - 48, ticket.centery))
            pygame.draw.rect(self.screen, status_color, stamp_rect.inflate(15, 8), width=2, border_radius=5)
            self.screen.blit(stamp, stamp_rect)

    def draw_route_map_ticket_action(self, destination, state, status_color):
        """Draw the purchase, travel, or unavailable action for this node."""

        button = self.route_map_purchase_button
        enabled = False
        if state is DestinationState.TICKET_REQUIRED:
            enabled = self.route.available_credits >= destination.map_data.ticket_price
            if enabled:
                label_text = (
                    f"PURCHASE RETURN PASSAGE  {self.format_money(destination.map_data.ticket_price)}"
                    if destination.map_data.destination_type is DestinationType.EARTH
                    else f"PURCHASE TICKET  {self.format_money(destination.map_data.ticket_price)}"
                )
            else:
                shortfall = destination.map_data.ticket_price - self.route.available_credits
                label_text = f"NEED {self.format_money(shortfall)} MORE"
        elif state is DestinationState.READY_TO_TRAVEL:
            label_text = (
                "CONFIRM TRAVEL HOME"
                if destination.map_data.destination_type is DestinationType.EARTH
                else "CONFIRM TRAVEL"
            )
            enabled = True
            button = self.route_map_travel_button
        elif state is DestinationState.EMERGENCY_CONTRACT:
            enabled = self.get_blackglass_credit_shortfall() > 0
            label_text = (
                "ACCEPT CONTRACT"
                if enabled
                else "CONTRACT NOT REQUIRED"
            )
        elif state is DestinationState.SHIFT_COMPLETE:
            label_text = "SHIFT COMPLETE"
        elif state is DestinationState.NO_NEW_PATIENTS:
            label_text = "NO NEW PATIENTS"
        elif state is DestinationState.CURRENT_LOCATION:
            label_text = "CURRENT LOCATION"
        elif state is DestinationState.UNKNOWN_DESTINATION:
            label_text = "DESTINATION UNKNOWN"
        elif state is DestinationState.LOCKED:
            label_text = "DESTINATION LOCKED"
        else:
            label_text = "TICKET OWNED"

        hovered = enabled and button.collidepoint(self.get_mouse_position())
        emergency_action = state is DestinationState.EMERGENCY_CONTRACT
        fill = (
            (252, 151, 127)
            if emergency_action and hovered
            else (232, 119, 101)
            if emergency_action and enabled
            else tuple(min(255, channel + 24) for channel in status_color)
            if hovered
            else status_color
            if enabled
            else (24, 31, 41)
        )
        border = (
            tuple(min(255, channel + 28) for channel in status_color)
            if enabled
            else (66, 76, 87)
        )
        pygame.draw.rect(self.screen, (2, 6, 12), button.move(3, 4), border_radius=9)
        pygame.draw.rect(self.screen, fill, button, border_radius=9)
        pygame.draw.rect(self.screen, border, button, width=2, border_radius=9)
        if enabled:
            pygame.draw.line(
                self.screen,
                tuple(min(255, channel + 45) for channel in fill),
                (button.x + 12, button.y + 5),
                (button.right - 12, button.y + 5),
                width=1,
            )
        label = self.tutorial_label_font.render(
            label_text,
            True,
            (15, 24, 28)
            if enabled
            else (112, 122, 132),
        )
        self.screen.blit(label, label.get_rect(center=button.center))

    def handle_blackglass_contract_click(self, position):
        """Return from the safe contract placeholder without changing campaign state."""

        if self.blackglass_contract_return_button.collidepoint(position):
            self.play_sfx("button")
            self.state = GameState.ROUTE_MAP
            self.route_map_message = (
                "Blackglass clinic operations are still being prepared."
            )

    def draw_blackglass_contract_screen(self):
        """Draw the temporary destination shown after accepting the contract."""

        elapsed = pygame.time.get_ticks() - self.route_map_started_at
        self.draw_route_map_background(elapsed)
        haze = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        pygame.draw.ellipse(haze, (113, 44, 53, 54), (70, 65, 960, 510))
        self.screen.blit(haze, (0, 0))

        panel = pygame.Rect(160, 92, 780, 490)
        pygame.draw.rect(self.screen, (1, 5, 10), panel.move(8, 9), border_radius=18)
        pygame.draw.rect(self.screen, (21, 25, 31), panel, border_radius=18)
        pygame.draw.rect(self.screen, (221, 102, 87), panel, width=3, border_radius=18)
        pygame.draw.line(
            self.screen,
            (107, 129, 94),
            (panel.x + 30, panel.y + 90),
            (panel.right - 30, panel.y + 90),
            2,
        )

        eyebrow = self.tutorial_label_font.render(
            "EMERGENCY CLINIC CONTRACT",
            True,
            (221, 102, 87),
        )
        heading = self.heading_font.render(
            "BLACKGLASS OUTPOST",
            True,
            (235, 232, 219),
        )
        self.screen.blit(eyebrow, eyebrow.get_rect(center=(panel.centerx, panel.y + 27)))
        self.screen.blit(heading, heading.get_rect(center=(panel.centerx, panel.y + 59)))

        warning = pygame.Rect(panel.x + 70, panel.y + 122, panel.width - 140, 72)
        pygame.draw.rect(self.screen, (44, 29, 32), warning, border_radius=11)
        pygame.draw.rect(self.screen, (221, 102, 87), warning, width=2, border_radius=11)
        warning_title = self.tutorial_subtitle_font.render(
            "CONTRACT INTAKE OFFLINE",
            True,
            (244, 179, 159),
        )
        warning_body = self.small_font.render(
            "The playable Blackglass clinic and patient roster are being prepared.",
            True,
            (205, 199, 193),
        )
        self.screen.blit(warning_title, warning_title.get_rect(center=(warning.centerx, warning.y + 25)))
        self.screen.blit(warning_body, warning_body.get_rect(center=(warning.centerx, warning.y + 51)))

        intended = self.get_intended_route_destination()
        destination_name = intended.planet_name if intended is not None else "the next route stop"
        shortfall = self.get_blackglass_credit_shortfall()
        copy_box = pygame.Rect(panel.x + 105, panel.y + 225, panel.width - 210, 112)
        self.draw_wrapped_text(
            (
                f"When this contract becomes playable, the clinic will treat emergency patients "
                f"until it earns the {self.format_money(shortfall)} still needed for "
                f"{destination_name}. Transportation will be provided."
            ),
            self.body_font,
            (220, 222, 213),
            copy_box,
            line_spacing=5,
        )

        badge = pygame.Rect(panel.centerx - 205, panel.y + 357, 410, 46)
        pygame.draw.rect(self.screen, (28, 39, 39), badge, border_radius=9)
        pygame.draw.rect(self.screen, (126, 161, 86), badge, width=2, border_radius=9)
        badge_text = self.small_font.render(
            "TRANSPORTATION PROVIDED  //  NO TICKET COST",
            True,
            (186, 217, 149),
        )
        self.screen.blit(badge_text, badge_text.get_rect(center=badge.center))

        button = self.blackglass_contract_return_button
        hovered = button.collidepoint(self.get_mouse_position())
        pygame.draw.rect(self.screen, (3, 8, 13), button.move(3, 4), border_radius=9)
        pygame.draw.rect(
            self.screen,
            (239, 128, 108) if hovered else (103, 58, 60),
            button,
            border_radius=9,
        )
        pygame.draw.rect(self.screen, (238, 121, 102), button, width=2, border_radius=9)
        label = self.tutorial_label_font.render(
            "RETURN TO ROUTE MAP",
            True,
            (10, 18, 23) if hovered else (245, 216, 207),
        )
        self.screen.blit(label, label.get_rect(center=button.center))

    def start_route_map_tutorial(self):
        """Begin the one-time post-training navigation walkthrough."""

        if self.route_map_tutorial_seen or self.route.next_destination is None:
            return False
        self.route_map_tutorial_active = True
        self.set_route_map_tutorial_step("introduction")
        return True

    def set_route_map_tutorial_step(self, step):
        """Advance the map lesson and clear any correction from the prior step."""

        self.route_map_tutorial_step = step
        self.route_map_tutorial_nudge = ""

    def finish_route_map_tutorial(self):
        """Restore the intended destination after the map lesson."""

        self.route_map_tutorial_active = False
        self.route_map_tutorial_seen = True
        self.route_map_tutorial_step = None
        self.route_map_tutorial_nudge = ""
        intended = self.get_intended_route_destination()
        if intended is not None:
            self.route.select_map_destination(intended.key)
            self.route_map_message = self.get_route_map_selection_message(intended)

    def get_route_map_tutorial_target(self):
        """Return the live map control highlighted by the current lesson."""

        step = self.route_map_tutorial_step
        intended = self.get_intended_route_destination()
        by_type = {
            destination.map_data.destination_type: destination
            for destination in MAP_DESTINATIONS
        }
        if step == "introduction":
            return self.route_map_area
        if step == "next_destination" and intended is not None:
            return self.get_route_map_node_rect(intended)
        if step in ("inspect_ticket", "earth_goal", "blackglass_contract", "completed_status"):
            return self.route_map_ticket_panel
        if step == "ticket_price":
            panel = self.route_map_ticket_panel
            return pygame.Rect(panel.x + 16, panel.y + 174, panel.width - 32, 112)
        if step == "earth":
            return self.get_route_map_node_rect(by_type[DestinationType.EARTH])
        if step == "blackglass":
            return self.get_route_map_node_rect(by_type[DestinationType.BLACKGLASS])
        if step == "completed_planet":
            return self.get_route_map_node_rect(self.route.current_location)
        return None

    def get_route_map_tutorial_prompt(self):
        """Return the adaptive map lesson copy and its seven-part number."""

        intended = self.get_intended_route_destination()
        intended_name = intended.planet_name if intended is not None else "the next destination"
        shortfall = self.get_blackglass_credit_shortfall()
        prompts = {
            "introduction": (
                1,
                "This is the Galactic Route Map. Every completed shift returns you here to choose the clinic's next destination.",
            ),
            "next_destination": (
                2,
                f"{intended_name} is the next clinic stop. Select the highlighted planet to inspect it.",
            ),
            "inspect_ticket": (
                3,
                "The destination panel shows its patients, travel ticket, current credits, and the amount still required.",
            ),
            "ticket_price": (
                4,
                "Tickets are paid before departure and can never create debt. A paid ticket belongs only to that destination.",
            ),
            "earth": (
                5,
                "Earth is always visible on the map. Select it to review the long-term Return Passage goal.",
            ),
            "earth_goal": (
                5,
                f"Return Passage costs {self.format_money(RETURN_PASSAGE_COST)}. Your savings and remaining amount stay visible here.",
            ),
            "blackglass": (
                6,
                f"You are {self.format_money(shortfall)} short for {intended_name}. Select Blackglass for an Emergency Clinic Contract.",
            ),
            "blackglass_contract": (
                6,
                "Blackglass provides transportation. Emergency clinic work will earn exactly what the intended ticket still needs.",
            ),
            "completed_planet": (
                7,
                "Select the completed Training Orbit to review its current patient status.",
            ),
            "completed_status": (
                7,
                "Completed planets have no new patients after departure until a new roster is reported. You can still inspect them on the map.",
            ),
        }
        return prompts[self.route_map_tutorial_step]

    def handle_route_map_tutorial_click(self, position):
        """Advance the map lesson without spending credits or accepting work."""

        if self.route_map_tutorial_skip_button.collidepoint(position):
            self.play_sfx("button")
            self.finish_route_map_tutorial()
            return

        step = self.route_map_tutorial_step
        target = self.get_route_map_tutorial_target()
        target_clicked = target is not None and target.collidepoint(position)
        if step == "introduction":
            self.set_route_map_tutorial_step("next_destination")
        elif step == "next_destination" and target_clicked:
            intended = self.get_intended_route_destination()
            self.route.select_map_destination(intended.key)
            self.route_map_message = self.get_route_map_selection_message(intended)
            self.set_route_map_tutorial_step("inspect_ticket")
        elif step == "inspect_ticket":
            self.set_route_map_tutorial_step("ticket_price")
        elif step == "ticket_price":
            self.set_route_map_tutorial_step("earth")
        elif step == "earth" and target_clicked:
            earth = next(
                destination
                for destination in MAP_DESTINATIONS
                if destination.map_data.destination_type is DestinationType.EARTH
            )
            self.route.select_map_destination(earth.key)
            self.route_map_message = self.get_route_map_selection_message(earth)
            self.set_route_map_tutorial_step("earth_goal")
        elif step == "earth_goal":
            self.set_route_map_tutorial_step(
                "blackglass"
                if self.get_blackglass_credit_shortfall() > 0
                else "completed_planet"
            )
        elif step == "blackglass" and target_clicked:
            blackglass = next(
                destination
                for destination in MAP_DESTINATIONS
                if destination.map_data.destination_type is DestinationType.BLACKGLASS
            )
            self.route.select_map_destination(blackglass.key)
            self.route_map_message = self.get_route_map_selection_message(blackglass)
            self.set_route_map_tutorial_step("blackglass_contract")
        elif step == "blackglass_contract":
            self.set_route_map_tutorial_step("completed_planet")
        elif step == "completed_planet" and target_clicked:
            current = self.route.current_location
            self.route.select_map_destination(current.key)
            self.route_map_message = self.get_route_map_selection_message(current)
            self.set_route_map_tutorial_step("completed_status")
        elif step == "completed_status":
            self.finish_route_map_tutorial()
        else:
            self.route_map_tutorial_nudge = "Select the highlighted map control."
            self.play_sfx("button")

    def handle_route_map_tutorial_key(self, key):
        """Support Enter for reading steps and Escape for exit options."""

        if key == pygame.K_ESCAPE:
            self.open_exit_confirmation()
            return
        if key not in (pygame.K_RETURN, pygame.K_SPACE):
            return
        if self.route_map_tutorial_step in (
            "introduction",
            "inspect_ticket",
            "ticket_price",
            "earth_goal",
            "blackglass_contract",
            "completed_status",
        ):
            self.handle_route_map_tutorial_click((10, 10))
        else:
            self.route_map_tutorial_nudge = "Select the highlighted planet."

    def draw_route_map_tutorial(self):
        """Reuse the clinic spotlight language for the first route lesson."""

        if not self.route_map_tutorial_active:
            return
        target = self.get_route_map_tutorial_target()
        pulse = (math.sin(pygame.time.get_ticks() / 210) + 1) / 2
        dim = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        dim.fill((2, 6, 12, 150))
        if target is not None:
            pygame.draw.rect(
                dim,
                (0, 0, 0, 0),
                target.inflate(18, 18),
                border_radius=15,
            )
        self.screen.blit(dim, (0, 0))
        if target is not None:
            glow = target.inflate(round(14 + 6 * pulse), round(14 + 6 * pulse))
            pygame.draw.rect(
                self.screen,
                (106, 246, 198),
                glow,
                width=2 + round(pulse),
                border_radius=13,
            )
            arrow_x = target.centerx
            tip_y = target.y - 7
            base_y = tip_y - 15 - round(4 * pulse)
            pygame.draw.polygon(
                self.screen,
                (106, 246, 198),
                ((arrow_x, tip_y), (arrow_x - 9, base_y), (arrow_x + 9, base_y)),
            )

        panel = pygame.Rect(246, 548, 608, 76)
        pygame.draw.rect(self.screen, (1, 5, 10), panel.move(4, 5), border_radius=12)
        pygame.draw.rect(self.screen, (10, 29, 36), panel, border_radius=12)
        pygame.draw.rect(self.screen, (106, 246, 198), panel, width=2, border_radius=12)
        step_number, prompt = self.get_route_map_tutorial_prompt()
        label = self.tutorial_label_font.render(
            f"GALACTIC ROUTE TRAINING  •  STEP {step_number} OF 7",
            True,
            (106, 246, 198),
        )
        self.screen.blit(label, (panel.x + 16, panel.y + 9))
        prompt_box = pygame.Rect(panel.x + 16, panel.y + 30, panel.width - 32, 38)
        self.draw_wrapped_text(
            prompt,
            self.small_font,
            (225, 234, 231),
            prompt_box,
            line_spacing=1,
        )

        skip = self.route_map_tutorial_skip_button
        hovered = skip.collidepoint(self.get_mouse_position())
        pygame.draw.rect(
            self.screen,
            (54, 40, 66) if hovered else (22, 28, 42),
            skip,
            border_radius=7,
        )
        pygame.draw.rect(self.screen, (183, 130, 207), skip, width=1, border_radius=7)
        skip_text = self.pile_font.render("SKIP MAP TOUR", True, (224, 202, 234))
        self.screen.blit(skip_text, skip_text.get_rect(center=skip.center))

        if self.route_map_tutorial_nudge:
            nudge = self.card_font.render(
                self.route_map_tutorial_nudge,
                True,
                (255, 157, 139),
            )
            nudge_panel = nudge.get_rect(center=(550, 530)).inflate(18, 8)
            pygame.draw.rect(self.screen, (45, 24, 31), nudge_panel, border_radius=6)
            pygame.draw.rect(self.screen, (216, 105, 95), nudge_panel, width=1, border_radius=6)
            self.screen.blit(nudge, nudge.get_rect(center=nudge_panel.center))
