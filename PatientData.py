"""Patient data shared by the text and GUI prototypes.
    I moved patient data out of main and into here, so it can be shared between the 2 for now.
    This isnt being used in the GUI yet, except for the name
"""

from Diagnosis import DIAGNOSES
from Patient import Patient


def create_zorpa():
    return Patient(
        "Zorpa Voidwalker",
        None,
        None,
        "shivering, confusion, pale skin, and slurred speech",
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
