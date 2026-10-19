class Notebook:

    def __init__(self):
        """
        Stores contents in a dictionary in the form of patient : patient_contents, where patient_contents
        is a dictionary in the form test name : results.
        """
        self.contents = {}

    def add_patient(self, patient):
        """
        Adds a new patient to the notebook.
        """
        self.contents[patient] = {"No tests" : "Run a test on your patient to learn more about their condition!"}

    def add_test(self, patient, test_name, test_results):
        self.contents[patient].pop("No tests", None) # gets rid of the "No tests" entry if it still exists
        self.contents[patient][test_name] = test_results

    def get_entries(self, patient):
        return self.contents.get(patient, {})