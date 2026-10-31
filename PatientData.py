"""Patient records used by The Cosmic Clinic GUI."""

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
            "Species": "Bloopiter Magmoid",
            "Occupation": "Black Hole Tour Guide",
            "Home Planet": "Bloopiter",
        },
        medical_info={
            "Circulation": "4 micro-hearts; HOT lava",
            "Respiration": "1 thermal lung",
            "Core": "Thermal body core",
            "Normal temperature": "2,000°F",
            "Medical alert": "Avoid water contact",
        },
        dialogue=(
            "I can't stop shivering.",
            "Even the lights feel cold.",
            "It started after my last tour.",
        ),
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
            "Species": "Arcedian Resonid",
            "Occupation": "Pro Orb-Bowler",
            "Home Planet": "Arcedo",
        },
        medical_info={
            "Circulation": "No central heart",
            "Respiration": "2 rectangular lungs",
            "Skeleton": "Crystal resonance frame",
            "Normal temperature": "95°F",
            "Medical alert": "Rodent dander",
        },
        dialogue=(
            "My whole frame is buzzing.",
            "It gets worse when I tense up.",
            "I blamed orb-bowling at first.",
        ),
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
            "Species": "Goopian Ectomorph",
            "Occupation": "Orbital Tax Accountant",
            "Home Planet": "Goopus",
        },
        medical_info={
            "Circulation": "1 ecto-heart; Type BLOO",
            "Respiration": "3 orbicular lungs",
            "Skin": "Highly absorbent membrane",
            "Normal temperature": "50°F",
            "Allergy record": "None documented",
        },
        dialogue=(
            "My skin burns. I'm trembling.",
            "It started after the sprinklers.",
            "I've never reacted like this.",
        ),
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
            "Species": "Vaygan Oilblood",
            "Occupation": "Galactic Food Reviewer",
            "Home Planet": "Vaygus Neverada",
        },
        medical_info={
            "Circulation": "2 hearts; IMPORTED oil",
            "Respiration": "1 oversized lung",
            "Digestion": "3 fermentation chambers",
            "Normal temperature": "35°F",
            "Medical alert": "Cat allergy",
        },
        dialogue=(
            "My stomach may explode.",
            "I got bloated after lunch.",
            "I tried the moon-cheese special.",
        ),
    )
