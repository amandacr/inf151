from Diagnosis import DIAGNOSES
from Tests.AllergyTest import AllergyTest
from Card import Card
from Test import get_test_cost
from Tests.TemperatureTest import TemperatureTest
from Tests.UltrasoundTest import UltrasoundTest
from Tests.XrayTest import XrayTest


DIAGNOSIS_REWARD = 50
WRONG_DIAGNOSIS_PENALTY = 10
PERFECT_DAY_BONUS = 25


class Player:

    def __init__(self, name):
        """
        Initializes a player at the beginning of the game.
        Players start with $500, five diagnosis cards, and five test cards.
        """
        self.name = name
        self.machine_levels = {}
        self.test_discount = 0
        self.balance = 500  # start with 500 alien dollars
        self.test_hand = [
            Card("Test", TemperatureTest()),
            Card("Test", TemperatureTest()),
            Card("Test", UltrasoundTest()),
            Card("Test", XrayTest()),
            Card("Test", AllergyTest())
        ]
        self.diagnosis_hand = [
            Card("Diagnosis", DIAGNOSES["hypothermia"]),
            Card("Diagnosis", DIAGNOSES["acute_water_reaction"]),
            Card("Diagnosis", DIAGNOSES["skeletal_resonance"]),
            Card("Diagnosis", DIAGNOSES["lava_flow_blockage"]),
            Card("Diagnosis", DIAGNOSES["lactose_intolerance"]),
        ]

    def sync_machine_levels(self, cards):
        for card in cards:
            if card.type == "Test":
                target = self.machine_levels.get(card.value.name, 1)
                while card.value.upgrade_level < target:
                    if not card.value.upgrade():
                        break

    def get_test_cost(self, test):
        base = get_test_cost(test)
        level = self.machine_levels.get(getattr(test, "name", ""), 1)
        return max(1, (base + 1) // 2 - self.test_discount) if level > 1 else max(1, base - self.test_discount)

    def draw(self, card):
        self.sync_machine_levels([card])
        self.test_hand.append(card)

    def play(self, card):
        if card in self.test_hand:
            self.test_hand.remove(card)
            return True
        if card in self.diagnosis_hand:
            # doesn't remove card so diagnoses can be reused
            return True
        return False

    def pay(self, amt):
        # player can go into debt / negative money so no need to have a balance check
        # just like real life!
        self.balance -= amt

    def earn(self, amt):
        self.balance += amt

    def draw_diagnosis(self, card):
        self.diagnosis_hand.append(card)
