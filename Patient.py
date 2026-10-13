class Patient:
    """
    Initializes a new patient.

    Name = str patient name
    Card_front = asset for ID card front
    Card_back = asset for ID card back
    Symptoms = str patient's symptoms
    Diagnosis = str patient's correct diagnosis
    Test_results = dictionary in the form test_name (str) : test_result (str)

    """
    def __init__(
            self,
            name,
            card_front,
            card_back,
            symptoms,
            diagnosis,
            test_results,
            profile=None,
            medical_info=None,
    ):
        self.name = name
        self.card_front = card_front
        self.card_back = card_back
        self.symptoms = symptoms
        self.diagnosis = diagnosis
        self.test_results = test_results
        self.profile = profile or {}
        self.medical_info = medical_info or {}

    def intro(self):
        print(f"Your next patient is: {self.name}")
        print(f"{self.name} complains of {self.symptoms}.")
        print("What would you like your first test to be?")

    def perform_test(self, test_name):
        return f"RESULTS: {self.test_results[test_name]}"

    def receive_diagnosis(self, diagnosis):
        if diagnosis == self.diagnosis:
            print("Congratulations! You have correctly diagnosed the patient!")
            return True
        else:
            print("That was not the correct diagnosis for this patient!")
            return False
