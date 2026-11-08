"""Screen states shared by The Cosmic Clinic GUI modules."""

from enum import Enum, auto


class GameState(Enum):
    """Screens used by The Cosmic Clinic's playable game loop."""

    INTRO = auto()
    TITLE = auto()
    PATIENT = auto()
    TEST_RESULT = auto()
    OUTCOME = auto()
    NOTEBOOK = auto()
    SHOP = auto()
    DAY_COMPLETE = auto()
    ENDING = auto()
    FINAL = auto()
