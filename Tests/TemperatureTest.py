from Test import Test

"""
TEMPERATURE Test.
"""

class TemperatureTest(Test):
    def __init__(self, upgrade_level=1):
        Test.__init__(self,
                      "TEMPERATURE",
                      "Takes the temperature of your patient. Can reveal fevers as well as hypothermic temperatures. Automatically adjusted for each species' normal range.",
                      'Common',
                      1,
                      upgrade_level)
