
class Diagnosis:

    def __init__(
            self,
            name,
            description,
            treatment,
            evidence_combinations=(),
    ):
        self.name = name
        self.description = description
        self.treatment = treatment
        self.evidence_combinations = tuple(
            frozenset(test_name.upper() for test_name in combination)
            for combination in evidence_combinations
        )

    def has_supporting_evidence(self, test_names):
        """Return whether the performed tests satisfy any valid clue combination."""

        performed_tests = {test_name.upper() for test_name in test_names}
        return any(
            combination.issubset(performed_tests)
            for combination in self.evidence_combinations
        )

    def get_evidence_progress(self, test_names):
        """Return the strongest collected-clue count and its required total.

        Only the progress count is exposed to the player; the valid card pairs
        remain hidden so the notebook helps without solving the case for them.
        """

        if not self.evidence_combinations:
            return 0, 0
        performed_tests = {test_name.upper() for test_name in test_names}
        best_combination = max(
            self.evidence_combinations,
            key=lambda combination: (
                len(combination.intersection(performed_tests)) / len(combination),
                len(combination.intersection(performed_tests)),
            ),
        )
        return (
            len(best_combination.intersection(performed_tests)),
            len(best_combination),
        )

    def __str__(self):
        return (
            f"{self.name}\n\n{self.description}\n"
            f"Recommended treatment: {self.treatment}"
        )

DIAGNOSES = {
    "hypothermia": Diagnosis(
        "Hypothermia",
        "The patient is suffering from hypothermia, a critically low body "
        "temperature that requires prompt treatment.",
        "Apply heated blankets, provide warm food or beverages, and remove any "
        "wet or cold clothing.",
        evidence_combinations=(
            ("TEMPERATURE", "BLOOD CHEMISTRY"),
            ("TEMPERATURE", "NEURAL SCAN"),
        ),
    ),
    "missing_intestine": Diagnosis(
        "Missing Intestine",
        "The patient's intestine appears to be missing, preventing normal "
        "digestion and nutrient absorption.",
        "Perform an intestinal transplant.",
        evidence_combinations=(
            ("ULTRASOUND", "X-RAY"),
            ("ULTRASOUND", "BLOOD CHEMISTRY"),
        ),
    ),
    "acute_water_reaction": Diagnosis(
        "Acute Water Reaction",
        "The patient is experiencing a severe allergic response following "
        "contact with water, causing shaking and systemic distress.",
        "Remove all water exposure and administer a species-safe antihistamine.",
        evidence_combinations=(
            ("ALLERGY", "BLOOD CHEMISTRY"),
            ("ALLERGY", "TOXIN SCREEN"),
        ),
    ),
    "skeletal_resonance": Diagnosis(
        "Skeletal Resonance",
        "The patient's bones are vibrating at an unstable frequency, causing "
        "uncontrollable shaking and skeletal strain.",
        "Stabilize the patient in a resonance-dampening chamber.",
        evidence_combinations=(
            ("X-RAY", "NEURAL SCAN"),
            ("X-RAY", "ULTRASOUND"),
        ),
    ),
    "lava_flow_blockage": Diagnosis(
        "Lava-Flow Blockage",
        "The patient's lava blood is not circulating normally, causing shaking, "
        "weakness, and internal pressure.",
        "Restore circulation with a controlled geothermal infusion.",
        evidence_combinations=(
            ("ULTRASOUND", "BLOOD CHEMISTRY"),
            ("TEMPERATURE", "ULTRASOUND"),
        ),
    ),
    "lactose_intolerance": Diagnosis(
        "Lactose Intolerance",
        "The patient's digestive tract cannot process lactose, a sugar "
        "commonly found in mammalian milk across the galaxy.",
        "Remove cheese and other dairy products from the patient's diet.",
        evidence_combinations=(
            ("ULTRASOUND", "BLOOD CHEMISTRY"),
            ("ALLERGY", "BLOOD CHEMISTRY"),
        ),
    ),
}


