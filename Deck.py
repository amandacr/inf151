from Card import Card
import random
import secrets
"""
DECK Class represents the draw-deck for players. 

It is generated once at the start of a round based on the fixed card types & their rarities.
Rarities are implemented as follows:
A COMMON card will appear 8 times in the deck.
An UNCOMMON card will appear 5 times in the deck.
A RARE card will appear 3 times in the deck.
"""

class Deck:

    def __init__(self, seed=None):
        """Create a deck with its own random-number generator.

        Normal games use fresh operating-system entropy, so starting hands and
        later draws do not repeat between launches.  Tests may pass a seed to
        reproduce an exact deal without weakening production randomness.
        """

        self.contents = []
        self.seed = secrets.randbits(128) if seed is None else seed
        self._random = random.Random(self.seed)

    def populate(self, card_types):
        self.contents = []
        for test in card_types:
            self.contents.extend(Card("Test", test) for i in range (test.occurrences))
        self._random.shuffle(self.contents)

    def draw(self):
        if len(self.contents) <= 0:
            return None
        return self.contents.pop()

    def draw_matching(self, test_name):
        """Remove and return a random card matching ``test_name`` if present."""

        matching_indices = [
            index
            for index, card in enumerate(self.contents)
            if getattr(card.value, "name", None) == test_name
        ]
        if not matching_indices:
            return None
        return self.contents.pop(self._random.choice(matching_indices))

    def shuffle_cards(self, cards):
        """Shuffle a dealt group using the same session RNG as the deck."""

        self._random.shuffle(cards)

    def return_cards(self, cards):
        """Return unused cards to the live deck and randomize their positions."""

        returned = list(cards)
        if not returned:
            return
        self.contents.extend(returned)
        self._random.shuffle(self.contents)

    def add_card(self, test):
        """
        Randomly inserts a new test card type within the deck. Used when player unlocks a new test mid-round.
        """
        self.contents.extend(Card("Test", test) for i in range(test.occurrences))
        self._random.shuffle(self.contents)
