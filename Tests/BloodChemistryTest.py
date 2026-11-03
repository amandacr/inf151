from Test import Test


class BloodChemistryTest(Test):
    """Analyze an alien patient's circulating fluids and metabolic markers."""

    def __init__(self, upgrade_level=1):
        super().__init__(
            "BLOOD CHEMISTRY",
            "Analyzes circulating fluids for metabolic changes, mineral imbalance, and unusual cell activity.",
            "Common",
            2,
            upgrade_level,
        )
