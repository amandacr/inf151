
class Diagnosis:

    def __init__(self, name, description, treatment):
        self.name = name
        self.description = description
        self.treatment = treatment

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
    ),
    "missing_intestine": Diagnosis(
        "Missing Intestine",
        "The patient's intestine appears to be missing, preventing normal "
        "digestion and nutrient absorption.",
        "Perform an intestinal transplant.",
    ),
    "acute_water_reaction": Diagnosis(
        "Acute Water Reaction",
        "The patient is experiencing a severe allergic response following "
        "contact with water, causing shaking and systemic distress.",
        "Remove all water exposure and administer a species-safe antihistamine.",
    ),
    "skeletal_resonance": Diagnosis(
        "Skeletal Resonance",
        "The patient's bones are vibrating at an unstable frequency, causing "
        "uncontrollable shaking and skeletal strain.",
        "Stabilize the patient in a resonance-dampening chamber.",
    ),
    "lava_flow_blockage": Diagnosis(
        "Lava-Flow Blockage",
        "The patient's lava blood is not circulating normally, causing shaking, "
        "weakness, and internal pressure.",
        "Restore circulation with a controlled geothermal infusion.",
    ),
    "lactose_intolerance": Diagnosis(
        "Lactose Intolerance",
        "The patient's digestive tract cannot process lactose, a sugar "
        "commonly found in mammalian milk across the galaxy.",
        "Remove cheese and other dairy products from the patient's diet.",
    ),
}


