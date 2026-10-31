class Notebook:

    def __init__(self):
        """
        Stores contents in a dictionary in the form of patient : patient_contents, where patient_contents
        is a dictionary in the form test name : results.
        """
        self.contents = {}
        self.interviews = {}

    def add_patient(self, patient):
        """
        Adds a new patient to the notebook.
        """
        self.contents[patient] = {
            "No tests": "Run a test on your patient to learn more about their condition!"
        }
        self.interviews[patient] = list(patient.dialogue[:1])

    def add_interview(self, patient, statement):
        """Record a newly revealed patient statement without duplicating it."""

        statements = self.interviews.setdefault(patient, [])
        if statement not in statements:
            statements.append(statement)

    def add_test(self, patient, test_name, test_results):
        self.contents[patient].pop("No tests", None) # gets rid of the "No tests" entry if it still exists
        self.contents[patient][test_name] = test_results

    def get_entries(self, patient):
        return self.contents.get(patient, {})

    def get_interview(self, patient):
        """Return the interview statements revealed for a patient."""

        return tuple(self.interviews.get(patient, ()))
