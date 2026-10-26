from Test import Test

"""
ULTRASOUND Test.
"""

class UltrasoundTest(Test):
    def __init__(self, upgrade_level=1):
        Test.__init__(self,
                      "ULTRASOUND",
                      "Performs a full abdominal ultrasound on your patient. Shows internal organs, blood flow, or fetal growth.",
                      'Uncommon',
                      2,
                      upgrade_level)
