from Test import Test


class OxygenScanTest(Test):
    """Measure respiratory exchange across unfamiliar alien anatomies."""

    def __init__(self, upgrade_level=1):
        super().__init__(
            "OXYGEN SCAN",
            "Measures respiratory exchange and checks whether each lung or breathing organ is working efficiently.",
            "Common",
            2,
            upgrade_level,
        )
