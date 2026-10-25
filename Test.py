"""
Parent class for tests.
"""


TEST_COSTS_BY_RARITY = {
    "Common": 10,
    "Uncommon": 15,
    "Rare": 20,
}


def get_test_cost(test_or_rarity):
    """Return the operating cost for a test object or rarity label."""

    rarity = getattr(test_or_rarity, "rarity", test_or_rarity)
    return TEST_COSTS_BY_RARITY.get(rarity, TEST_COSTS_BY_RARITY["Common"])

class Test:

    def __init__(self, name, description, rarity, max_level, upgrade_level = 1):
        self.name = name
        self.description = description
        self.rarity = rarity
        self.max_level = max_level
        self.upgrade_level = upgrade_level
        self.occurrences = 0
        if self.rarity == "Common": self.occurrences = 8
        elif self.rarity == "Uncommon": self.occurrences = 5
        elif self.rarity == "Rare": self.occurrences = 3

    def __str__(self):
        return f"\n{self.name} Level: {self.upgrade_level}/{self.max_level}\n{self.description}\nRarity: {self.rarity}"

    def upgrade(self):
        if self.max_level >= self.upgrade_level + 1:
            self.upgrade_level += 1
            return True
        return False
