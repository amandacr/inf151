from Test import Test


class ToxinScreenTest(Test):
    """Screen a patient sample for dangerous foreign compounds."""

    def __init__(self, upgrade_level=1):
        super().__init__(
            "TOXIN SCREEN",
            "Screens body fluids and surface residue for poisons, contaminants, and hazardous cosmic compounds.",
            "Uncommon",
            2,
            upgrade_level,
        )
