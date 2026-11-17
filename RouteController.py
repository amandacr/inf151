"""Campaign-route progression and cross-shift performance tracking."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Sequence

from PlanetData import (
    DESTINATIONS,
    MAP_DESTINATIONS,
    Destination,
    DestinationType,
    get_map_destination,
    validate_destinations,
    validate_map_destinations,
)


@dataclass(frozen=True)
class ShiftPerformance:
    """Permanent results from one completed destination shift."""

    destination_key: str
    day_number: int
    patients_seen: int
    correct_diagnoses: int
    supported_diagnoses: int
    wrong_diagnoses: int
    patients_lost: int
    tests_run: int
    net_pay: int
    ending_balance: int


@dataclass(frozen=True)
class CampaignTravelState:
    """Immutable view of persistent campaign navigation and ticket progress."""

    current_location_key: str
    completed_destination_keys: tuple[str, ...]
    unlocked_destination_keys: frozenset[str]
    purchased_ticket_keys: frozenset[str]
    used_ticket_keys: frozenset[str]
    selected_map_destination_key: Optional[str]
    available_credits: int
    return_passage_purchased: bool


class DestinationState(str, Enum):
    """Player-facing route states used by the Galactic Route Map."""

    CURRENT_LOCATION = "Current Location"
    TICKET_REQUIRED = "Ticket Required"
    TICKET_OWNED = "Ticket Owned"
    READY_TO_TRAVEL = "Ready to Travel"
    SHIFT_COMPLETE = "Shift Complete"
    NO_NEW_PATIENTS = "No New Patients"
    LOCKED = "Locked"
    UNKNOWN_DESTINATION = "Unknown Destination"
    EMERGENCY_CONTRACT = "Emergency Contract"


class RouteController:
    """Own the current, next, and completed destinations for one campaign."""

    def __init__(
        self,
        destinations: Sequence[Destination] = DESTINATIONS,
        starting_credits: int = 0,
    ):
        validate_destinations(tuple(destinations))
        validate_map_destinations()
        if not isinstance(starting_credits, int) or isinstance(starting_credits, bool):
            raise ValueError("Starting credits must be an integer.")
        self._destinations = tuple(destinations)
        self._current_index = 0
        self._completed_keys = []
        self._shift_history = []
        self._arrival_pending = False
        self._current_location_key = self.current_destination.key
        self._unlocked_destination_keys = {self.current_destination.key}
        self._purchased_ticket_keys = set()
        self._used_ticket_keys = set()
        self._selected_map_destination_key = None
        self._available_credits = starting_credits
        self._return_passage_purchased = False

    @property
    def destinations(self):
        """Return the ordered clinic route."""

        return self._destinations

    @property
    def current_destination(self):
        """Return the planet currently hosting the clinic."""

        return self._destinations[self._current_index]

    @property
    def current_location(self):
        """Return the map location currently occupied by the clinic UFO."""

        return get_map_destination(self._current_location_key)

    @property
    def current_location_key(self):
        """Return the stable map key for the UFO's current location."""

        return self._current_location_key

    @property
    def current_day(self):
        """Return the configured day number of the current destination."""

        return self.current_destination.day_number

    @property
    def current_patient_roster(self):
        """Return the central patient definitions for the active destination."""

        return self.current_destination.patient_roster

    @property
    def next_destination(self) -> Optional[Destination]:
        """Return the next route stop, or None after the final configured stop."""

        next_index = self._current_index + 1
        if next_index >= len(self._destinations):
            return None
        return self._destinations[next_index]

    @property
    def completed_destinations(self):
        """Return completed route stops in completion order."""

        by_key = {destination.key: destination for destination in self._destinations}
        return tuple(by_key[key] for key in self._completed_keys)

    @property
    def unlocked_destinations(self):
        """Return map destinations unlocked by completed clinic work."""

        return tuple(
            destination
            for destination in MAP_DESTINATIONS
            if destination.key in self._unlocked_destination_keys
        )

    @property
    def unlocked_destination_keys(self):
        """Return an immutable set of unlocked map keys."""

        return frozenset(self._unlocked_destination_keys)

    @property
    def purchased_ticket_keys(self):
        """Return unused destination tickets owned by this campaign."""

        return frozenset(self._purchased_ticket_keys)

    @property
    def used_ticket_keys(self):
        """Return destination tickets already consumed by travel."""

        return frozenset(self._used_ticket_keys)

    @property
    def selected_map_destination(self):
        """Return the destination most recently inspected on the route map."""

        if self._selected_map_destination_key is None:
            return None
        return get_map_destination(self._selected_map_destination_key)

    @property
    def available_credits(self):
        """Return the latest player-balance snapshot available to the map."""

        return self._available_credits

    @property
    def return_passage_purchased(self):
        """Return whether the one-way Earth ticket has ever been purchased."""

        return self._return_passage_purchased

    @property
    def travel_state(self):
        """Return a safe immutable snapshot for screens, tests, and saves."""

        return CampaignTravelState(
            current_location_key=self._current_location_key,
            completed_destination_keys=tuple(self._completed_keys),
            unlocked_destination_keys=frozenset(
                self._unlocked_destination_keys
            ),
            purchased_ticket_keys=frozenset(self._purchased_ticket_keys),
            used_ticket_keys=frozenset(self._used_ticket_keys),
            selected_map_destination_key=self._selected_map_destination_key,
            available_credits=self._available_credits,
            return_passage_purchased=self._return_passage_purchased,
        )

    def get_destination_state(self, destination_key, selected=False):
        """Return the map state for one configured destination."""

        destination = get_map_destination(destination_key)
        if destination is None:
            raise ValueError(f"Unknown map destination: {destination_key}")
        if destination.map_data.destination_type is DestinationType.BLACKGLASS:
            if destination.key not in self._unlocked_destination_keys:
                return DestinationState.UNKNOWN_DESTINATION
            if self.current_is_complete:
                return DestinationState.EMERGENCY_CONTRACT
            return DestinationState.LOCKED
        if not destination.map_data.content_ready:
            return DestinationState.UNKNOWN_DESTINATION

        completed_keys = set(self._completed_keys)
        if destination.key == self._current_location_key:
            if destination.key in completed_keys:
                return DestinationState.SHIFT_COMPLETE
            return DestinationState.CURRENT_LOCATION
        if destination.key in completed_keys:
            return DestinationState.NO_NEW_PATIENTS

        if destination.key in self._purchased_ticket_keys:
            if selected and self.can_travel_to(destination.key):
                return DestinationState.READY_TO_TRAVEL
            return DestinationState.TICKET_OWNED
        if destination.key not in self._unlocked_destination_keys:
            return DestinationState.LOCKED
        if destination.map_data.ticket_price > 0:
            return DestinationState.TICKET_REQUIRED
        if selected and self.can_travel_to(destination.key, require_ticket=False):
            return DestinationState.READY_TO_TRAVEL
        return DestinationState.LOCKED

    def can_travel_to(self, destination_key, require_ticket=True):
        """Return whether route progress permits departure to a location."""

        destination = get_map_destination(destination_key)
        if destination is None or not destination.map_data.content_ready:
            return False
        if not self.current_is_complete:
            return False
        if destination.key not in self._unlocked_destination_keys:
            return False
        if require_ticket and destination.map_data.ticket_price > 0:
            if destination.key not in self._purchased_ticket_keys:
                return False
        if destination.key == "earth":
            return self.route_is_complete and self._return_passage_purchased
        next_destination = self.next_destination
        return next_destination is not None and destination.key == next_destination.key

    @property
    def shift_history(self):
        """Return permanent performance summaries for completed shifts."""

        return tuple(self._shift_history)

    @property
    def current_is_complete(self):
        """Return whether the current destination has been filed as complete."""

        return self.current_destination.key in self._completed_keys

    @property
    def arrival_pending(self):
        """Return whether the route reached a planet whose shift has not begun."""

        return self._arrival_pending

    @property
    def route_is_complete(self):
        """Return whether every configured destination has been completed."""

        return self.next_destination is None and self.current_is_complete

    @property
    def overall_performance(self):
        """Return campaign totals calculated from permanent shift history."""

        return {
            "shifts_completed": len(self._shift_history),
            "patients_seen": sum(item.patients_seen for item in self._shift_history),
            "correct_diagnoses": sum(
                item.correct_diagnoses for item in self._shift_history
            ),
            "supported_diagnoses": sum(
                item.supported_diagnoses for item in self._shift_history
            ),
            "wrong_diagnoses": sum(
                item.wrong_diagnoses for item in self._shift_history
            ),
            "patients_lost": sum(item.patients_lost for item in self._shift_history),
            "tests_run": sum(item.tests_run for item in self._shift_history),
            "net_pay": sum(item.net_pay for item in self._shift_history),
        }

    def record_current_shift(self, performance: ShiftPerformance):
        """Record the current destination exactly once."""

        current = self.current_destination
        if (
            performance.destination_key != current.key
            or performance.day_number != current.day_number
        ):
            raise ValueError("Shift performance must match the current destination.")
        if current.key in self._completed_keys:
            return False
        self._completed_keys.append(current.key)
        self._shift_history.append(performance)
        self.sync_available_credits(performance.ending_balance)
        self._unlock_destinations_after(current.key)
        return True

    def complete_current_shift(self, performance: ShiftPerformance):
        """File the current shift without selecting or starting travel."""

        if self._arrival_pending:
            raise ValueError("The route is already awaiting the next shift.")
        self.record_current_shift(performance)
        self._arrival_pending = False
        return self.next_destination

    def begin_travel(self, destination_key):
        """Consume a ticket and prepare arrival at the next clinic stop."""

        if self._arrival_pending:
            raise ValueError("The route is already awaiting the next shift.")
        if not self.current_is_complete:
            raise ValueError("Finish the current clinic shift before traveling.")
        destination = get_map_destination(destination_key)
        if destination is None:
            raise ValueError(f"Unknown map destination: {destination_key}")
        if not destination.map_data.content_ready:
            raise ValueError("That destination's playable content is not ready.")

        if destination.key == "earth":
            if not self.route_is_complete:
                raise ValueError("Earth travel requires the configured route to be complete.")
            return self.use_ticket(destination.key)

        next_destination = self.next_destination
        if next_destination is None or destination.key != next_destination.key:
            raise ValueError("Only the next configured clinic can begin a new shift.")
        if destination.key not in self._unlocked_destination_keys:
            raise ValueError("The selected destination is still locked.")

        self.use_ticket(destination.key)
        self._current_index += 1
        self._arrival_pending = True
        return self.current_destination

    def begin_current_shift(self):
        """Mark the arrived destination as ready for patient gameplay."""

        if not self._arrival_pending:
            raise ValueError("The route is not awaiting a destination shift.")
        self._arrival_pending = False
        return self.current_destination

    def reopen_current_shift(self):
        """Remove the current stop's filed result so that shift can be replayed."""

        current_key = self.current_destination.key
        if current_key not in self._completed_keys:
            self._arrival_pending = False
            return False
        self._completed_keys.remove(current_key)
        self._shift_history = [
            performance
            for performance in self._shift_history
            if performance.destination_key != current_key
        ]
        self._rebuild_unlocked_destinations()
        self._arrival_pending = False
        return True

    def sync_available_credits(self, credits):
        """Synchronize the route-map balance with the authoritative player."""

        if not isinstance(credits, int) or isinstance(credits, bool):
            raise ValueError("Available credits must be an integer.")
        self._available_credits = credits
        return self._available_credits

    def select_map_destination(self, destination_key):
        """Remember which map node is being inspected, even when locked."""

        if destination_key is None:
            self._selected_map_destination_key = None
            return None
        destination = get_map_destination(destination_key)
        if destination is None:
            raise ValueError(f"Unknown map destination: {destination_key}")
        self._selected_map_destination_key = destination.key
        return destination

    def unlock_destination(self, destination_key):
        """Unlock a configured location without starting travel to it."""

        destination = get_map_destination(destination_key)
        if destination is None:
            raise ValueError(f"Unknown map destination: {destination_key}")
        self._unlocked_destination_keys.add(destination.key)
        return destination

    def record_ticket_purchase(self, destination_key):
        """Record a paid ticket after the economy layer deducts its price."""

        destination = get_map_destination(destination_key)
        if destination is None:
            raise ValueError(f"Unknown map destination: {destination_key}")
        if destination.key not in self._unlocked_destination_keys:
            raise ValueError("A ticket cannot be recorded for a locked destination.")
        if destination.key in self._completed_keys:
            raise ValueError("Completed destinations have no new ticket inventory.")
        if destination.map_data.ticket_price <= 0:
            raise ValueError("This destination does not require a purchasable ticket.")
        if destination.key == self._current_location_key:
            raise ValueError("The clinic is already at that destination.")
        if destination.key in self._purchased_ticket_keys:
            raise ValueError("A ticket for that destination is already owned.")
        self._purchased_ticket_keys.add(destination.key)
        if destination.key == "earth":
            self._return_passage_purchased = True
        return destination

    def purchase_ticket(self, destination_key, available_credits):
        """Buy one destination-specific ticket without permitting debt.

        The player object remains the authoritative wallet, so this returns
        the exact charge for the GUI to apply.  Route credits are updated in
        the same operation, keeping map state and the displayed balance in
        sync while the unused ticket remains bound to its destination.
        """

        if not isinstance(available_credits, int) or isinstance(available_credits, bool):
            raise ValueError("Available credits must be an integer.")
        destination = get_map_destination(destination_key)
        if destination is None:
            raise ValueError(f"Unknown map destination: {destination_key}")
        price = destination.map_data.ticket_price
        if available_credits < price:
            raise ValueError("Destination tickets cannot be purchased with debt.")
        self.record_ticket_purchase(destination.key)
        self.sync_available_credits(available_credits - price)
        return price

    def record_return_passage_purchase(self):
        """Bridge the existing final-stop Shop purchase into travel state."""

        self._unlocked_destination_keys.add("earth")
        self._purchased_ticket_keys.add("earth")
        self._return_passage_purchased = True
        return get_map_destination("earth")

    def use_ticket(self, destination_key):
        """Move an owned ticket into permanent used-ticket history."""

        if destination_key not in self._purchased_ticket_keys:
            raise ValueError("Travel requires a purchased destination ticket.")
        self._purchased_ticket_keys.remove(destination_key)
        self._used_ticket_keys.add(destination_key)
        self._current_location_key = destination_key
        self._selected_map_destination_key = None
        return get_map_destination(destination_key)

    def _unlock_destinations_after(self, completed_key):
        """Unlock every map node whose requirement is the completed clinic."""

        for destination in MAP_DESTINATIONS:
            if destination.map_data.unlock_requirement == completed_key:
                self._unlocked_destination_keys.add(destination.key)

    def _rebuild_unlocked_destinations(self):
        """Recalculate route unlocks after a completed shift is reopened."""

        unlocked = {self.current_destination.key}
        unlocked.update(self._purchased_ticket_keys)
        unlocked.update(self._used_ticket_keys)
        for completed_key in self._completed_keys:
            for destination in MAP_DESTINATIONS:
                if destination.map_data.unlock_requirement == completed_key:
                    unlocked.add(destination.key)
        self._unlocked_destination_keys = unlocked

    def select_day(self, day_number):
        """Select a configured day directly for developer previews."""

        for index, destination in enumerate(self._destinations):
            if destination.day_number == day_number:
                self._current_index = index
                self._current_location_key = destination.key
                self._selected_map_destination_key = None
                self._arrival_pending = False
                return destination
        raise ValueError(f"Day {day_number} is not configured in the route.")

    def reset(self, starting_credits=0):
        """Start a new campaign at the first destination."""

        if not isinstance(starting_credits, int) or isinstance(starting_credits, bool):
            raise ValueError("Starting credits must be an integer.")
        self._current_index = 0
        self._completed_keys.clear()
        self._shift_history.clear()
        self._arrival_pending = False
        self._current_location_key = self.current_destination.key
        self._unlocked_destination_keys = {self.current_destination.key}
        self._purchased_ticket_keys.clear()
        self._used_ticket_keys.clear()
        self._selected_map_destination_key = None
        self._available_credits = starting_credits
        self._return_passage_purchased = False
        return self.current_destination
