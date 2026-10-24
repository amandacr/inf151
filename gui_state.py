"""Screen states shared by The Cosmic Clinic GUI modules."""

from enum import Enum, auto


class GameState(Enum):
    """Screens used by the GUI version of the prototype."""

    INTRO = auto()
    TITLE = auto()
    PATIENT = auto()
    TEST_RESULT = auto()
    OUTCOME = auto()
    NOTEBOOK = auto()
    SHOP = auto()
    DAY_COMPLETE = auto()
