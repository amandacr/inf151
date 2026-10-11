
class Diagnosis:

    def __init__(self, name, description, treatment):
        self.name = name
        self.description = description
        self.treatment = treatment

    def __str__(self):
        return f"{self.name}\n\nPatient appears to be {self.description}! Recommended treatment: {self.treatment}."

DIAGNOSES = {
    "hypothermia": Diagnosis("Hypothermia", "suffering from hypothermia, or a critically low body temperature", "Heated blankets, hot foods/beverages, and removal of any wet or cold clothing"),
    "missing_intestine": Diagnosis("Missing Intestine", "missing their intestine", "Transplant surgery")
}


