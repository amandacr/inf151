from Test import Test


class NeuralScanTest(Test):
    """Map electrical signals in an alien nervous system."""

    def __init__(self, upgrade_level=1):
        super().__init__(
            "NEURAL SCAN",
            "Maps nervous-system signals to reveal abnormal impulses, sensory disruption, and loss of motor control.",
            "Rare",
            2,
            upgrade_level,
        )
