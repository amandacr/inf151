"""Patient data shared by both the text-based and GUI versions of the game."""

from Diagnosis import DIAGNOSES
from Patient import Patient


def create_zorpa():
    return Patient(
        "Zorpa Voidwalker",
        None,
        None,
        "uncontrollable shaking",
        DIAGNOSES["hypothermia"],
        {
            "TEMPERATURE": "Current temperature: 1700°F",
            "X-RAY": "X-ray imaging found no fractures or visible bone damage.",
            "ULTRASOUND": "Ultrasound imaging found no unusual internal changes.",
            "ALLERGY": "Allergy screening produced no reaction.",
        },
        profile={
            "Occupation": "Black Hole Tour Guide",
            "Home Planet": "Bloopiter",
        },
        medical_info={
            "Hearts": "4 very small",
            "Lungs": "1 giant lung",
            "Blood": "Lava, Type HOT",
            "Normal temperature": "2,000°F",
            "Known allergy": "Water",
        },
    )


def create_zoogy():
    return Patient(
        "Zoogy Zinglestar",
        None,
        None,
        "straining, shaking",
        DIAGNOSES["skeletal_resonance"],
        {
            "TEMPERATURE": "Current temperature: 95°F",
            "X-RAY": "X-ray imaging displayed what appeared to be motion blur, perhaps caused by a vibration in the skeletal system.",
            "ULTRASOUND": "Ultrasound imaging found no unusual internal changes.",
            "ALLERGY": "Allergy screening produced no reaction.",
        },
        profile={
            "Occupation": "Professional Orb-Bowler",
            "Home Planet": "Arcedo",
        },
        medical_info={
            "Hearts": "None",
            "Lungs": "2 rectangular lungs",
            "Blood": "Acid, Type GREEN",
            "Normal temperature": "95°F",
            "Known allergy": "Mice",
        },
    )


def create_titus():
    return Patient(
        "Titus McMightus",
        None,
        None,
        "severe distress, tremors",
        DIAGNOSES["acute_water_reaction"],
        {
            "TEMPERATURE": "Current temperature: 50°F",
            "X-RAY": "X-ray imaging found no fractures or visible bone damage.",
            "ULTRASOUND": "Ultrasound imaging found no unusual internal changes.",
            "ALLERGY": "Severe allergic response detected from: water.",
        },
        profile={
            "Occupation": "Accountant",
            "Home Planet": "Goopus",
        },
        medical_info={
            "Hearts": "1",
            "Lungs": "3 orbicular lungs",
            "Blood": "Ectoplasm, Type Bloo",
            "Normal temperature": "50°F",
            "Known allergy": "None",
        },
    )


def create_conmann():
    return Patient(
        "Conmann Cheester",
        None,
        None,
        "stomach pain, indigestion, bloating",
        DIAGNOSES["lactose_intolerance"],
        {
            "TEMPERATURE": "Current temperature: 35°F",
            "X-RAY": "X-ray imaging found no fractures or visible bone damage.",
            "ULTRASOUND": "Ultrasound imaging found no unusual internal changes.",
            "ALLERGY": "Minor intolerant response detected from: lactose.",
        },
        profile={
            "Occupation": "Unemployed",
            "Home Planet": "Vaygus Neverada",
        },
        medical_info={
            "Hearts": "2",
            "Lungs": "1 very large lung",
            "Blood": "Oil, Type IMPORTED",
            "Normal temperature": "35°F",
            "Known allergy": "Cats",
        },
    )
