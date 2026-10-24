from Card import Card
import random
"""
DECK Class represents the draw-deck for players. 

It is generated once at the start of a round based on the fixed card types & their rarities.
Rarities are implemented as follows:
A COMMON card will appear 8 times in the deck.
An UNCOMMON card will appear 5 times in the deck.
A RARE card will appear 3 times in the deck.
"""

class Deck:

    def __init__(self):
        self.contents = []

    def populate(self, card_types):
        self.contents = []
        for test in card_types:
            self.contents.extend(Card("Test", test) for i in range (test.occurrences))
        random.shuffle(self.contents)

    def draw(self):
        if len(self.contents) <= 0:
            return None
        return self.contents.pop()

    def add_card(self, test):
        """
        Randomly inserts a new test card type within the deck. Used when player unlocks a new test mid-round.
        """
        self.contents.extend(Card("Test", test) for i in range(test.occurrences))
        random.shuffle(self.contents)
