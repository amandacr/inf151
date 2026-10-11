from Test import Test

"""
X-Ray Test
"""
class XrayTest(Test):
    def __init__(self, upgrade_level = 1):
        Test.__init__(self,
                      "X-RAY",
                      "Performs a full body X-RAY of your patient. Shows broken/fractured bones and tissue damage.",
                      'Common',
                      1,
                      upgrade_level)
