from Test import Test

"""
SYSTEM LOG Test (patient-specific: only dealt for software-based patients).
"""

class SystemLogTest(Test):
    def __init__(self, upgrade_level=1):
        Test.__init__(self,
                      "SYSTEM LOG",
                      "Reads the patient's activity history to reveal what changed and when. Only works on patients that keep logs.",
                      "Common",
                      2,
                      upgrade_level)
