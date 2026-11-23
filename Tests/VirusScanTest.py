from Test import Test

"""
VIRUS SCAN Test (patient-specific: only dealt for software-based patients).
"""

class VirusScanTest(Test):
    def __init__(self, upgrade_level=1):
        Test.__init__(self,
                      "VIRUS SCAN",
                      "Scans memory and processes for malicious programs. Only useful on patients made of software, but invaluable when one has caught something.",
                      "Uncommon",
                      2,
                      upgrade_level)
