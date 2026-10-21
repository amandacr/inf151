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
            "TEMPERATURE": "Current temperature: 1700°F\nTypical body temperature: 2000°F",
            "X-RAY": "Nothing remarkable.",
            "ULTRASOUND": "Nothing remarkable.",
            "ALLERGY": "Nothing remarkable.",
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
