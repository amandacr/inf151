class Patient:
    """
    Initializes a new patient.

    Name = str patient name
    Card_front = asset for ID card front
    Card_back = asset for ID card back
    Symptoms = str patient's symptoms
    Diagnosis = str patient's correct diagnosis
    Test_results = dictionary in the form test_name (str) : test_result (str)
    Dialogue = ordered patient statements revealed during the interview

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
            dialogue=None,
    ):
        self.name = name
        self.card_front = card_front
        self.card_back = card_back
        self.symptoms = symptoms
        self.diagnosis = diagnosis
        self.test_results = test_results
        self.profile = profile or {}
        self.medical_info = medical_info or {}
        self.dialogue = tuple(dialogue or (symptoms,))

    def perform_test(self, test_name):
        return f"RESULTS: {self.test_results[test_name]}"

    def receive_diagnosis(self, diagnosis):
        return diagnosis == self.diagnosis

    def has_supporting_evidence(self, test_names):
        """Return whether the collected tests form a clue path for this condition."""

        return self.diagnosis.has_supporting_evidence(test_names)

    def get_evidence_progress(self, test_names):
        """Return progress toward the strongest evidence path for this patient."""

        return self.diagnosis.get_evidence_progress(test_names)
