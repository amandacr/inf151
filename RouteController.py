"""Campaign-route progression and cross-shift performance tracking."""

from dataclasses import dataclass
from typing import Optional, Sequence

from PlanetData import DESTINATIONS, Destination, validate_destinations


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


class RouteController:
    """Own the current, next, and completed destinations for one campaign."""

    def __init__(self, destinations: Sequence[Destination] = DESTINATIONS):
        validate_destinations(tuple(destinations))
        self._destinations = tuple(destinations)
        self._current_index = 0
        self._completed_keys = []
        self._shift_history = []
        self._arrival_pending = False

    @property
    def destinations(self):
        """Return the ordered clinic route."""

        return self._destinations

    @property
    def current_destination(self):
        """Return the planet currently hosting the clinic."""

        return self._destinations[self._current_index]

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
        return True

    def complete_current_shift(self, performance: ShiftPerformance):
        """File the current shift and travel to the next destination, if any."""

        if self._arrival_pending:
            raise ValueError("The route is already awaiting the next shift.")
        self.record_current_shift(performance)
        if self.next_destination is None:
            self._arrival_pending = False
            return None
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
        self._arrival_pending = False
        return True

    def select_day(self, day_number):
        """Select a configured day directly for developer previews."""

        for index, destination in enumerate(self._destinations):
            if destination.day_number == day_number:
                self._current_index = index
                self._arrival_pending = False
                return destination
        raise ValueError(f"Day {day_number} is not configured in the route.")

    def reset(self):
        """Start a new campaign at the first destination."""

        self._current_index = 0
        self._completed_keys.clear()
        self._shift_history.clear()
        self._arrival_pending = False
        return self.current_destination
