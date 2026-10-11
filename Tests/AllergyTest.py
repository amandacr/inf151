from Test import Test

"""
ALLERGY Test.
"""

class AllergyTest(Test):
    def __init__(self, upgrade_level=1):
        Test.__init__(self,
                      "ALLERGY",
                      "Allergy tests your patient. Tests for common species' allergens as well as allergens within this hospital. Also determines the severity of any allergies.",
                      'Rare',
                      1,
                      upgrade_level)
