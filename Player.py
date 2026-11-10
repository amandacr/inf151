from Diagnosis import DIAGNOSES
from Card import Card
from Test import get_test_cost as get_base_test_cost


STARTING_BALANCE = 100
DIAGNOSIS_REWARD = 50
LIMITED_EVIDENCE_REWARD = 10
WRONG_DIAGNOSIS_PENALTY = 35
DRAW_COST = 5
STARTING_TEST_HAND_SIZE = 5
MAX_TEST_HAND_SIZE = 8
PERFECT_DAY_BONUS = 25
CLINIC_OPERATING_FEE = 50
RETURN_PASSAGE_COST = 400
PATIENT_WALKOUT_THRESHOLD = 2
PATIENT_LEAVES_CHANCE = 0.25

PATIENT_LEAVES_TEXT = [
    "{name} lost confidence and left the clinic to seek a second opinion.",
    "{name} grabbed their Health ID and slipped out before you could continue.",
    "{name}'s ride pod arrived. They ended the appointment and left.",
    "{name} called the diagnosis 'amateur hour' and teleported away.",
]

DEFAULT_DIAGNOSIS_KEYS = (
    "hypothermia",
    "acute_water_reaction",
    "skeletal_resonance",
    "lava_flow_blockage",
    "lactose_intolerance",
)


class Player:

    def __init__(self, name):
        """
        Initializes a player at the beginning of the game.
        Players start with $100 and five diagnosis cards. Test cards are dealt
        from the shuffled clinic deck by the GUI at the start of each case.
        """
        self.name = name
        self.machine_levels = {}
        self.free_test_machines = set()
        self.free_tests_used = set()
        self.test_discount = 0
        self.balance = STARTING_BALANCE
        self.test_hand = []
        self.diagnosis_hand = []
        self.set_diagnosis_hand(
            DIAGNOSES[key] for key in DEFAULT_DIAGNOSIS_KEYS
        )

    def set_diagnosis_hand(self, diagnoses):
        """Replace the case files with one patient's curated five-card set."""

        self.diagnosis_hand = [
            Card("Diagnosis", diagnosis)
            for diagnosis in diagnoses
        ]

    def get_machine_level(self, test):
        """Return the installed level for a test machine.

        Machine upgrades belong to the clinic, not to individual cards. Keeping
        this as the single source of truth prevents a card label and its billed
        cost from disagreeing after a new hand or deck is created.
        """

        return self.machine_levels.get(getattr(test, "name", ""), 1)

    def get_test_cost(self, test):
        if test.name in self.free_test_machines and test.name not in self.free_tests_used:
            return 0
        base = get_base_test_cost(test)
        level = self.get_machine_level(test)
        return max(1, (base + 1) // 2 - self.test_discount) if level > 1 else max(1, base - self.test_discount)

    def consume_test_use(self, test):
        """Consume the free allowance only when a machine actually runs."""
        if test.name in self.free_test_machines:
            self.free_tests_used.add(test.name)

    def draw(self, card):
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
