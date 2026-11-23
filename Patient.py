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
    Diagnosis_options = curated case files shown for this patient

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
            diagnosis_options=None,
            speech_style=None,
            bonus_tests=(),
            bespoke_voice=False,
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
        self.diagnosis_options = tuple(diagnosis_options or ())
        # Optional presentation/gameplay extras for unusual patients:
        #   speech_style  - alternate speech bubble look ("toe_tap", "terminal")
        #   bonus_tests   - patient-specific test cards added to the deck
        #   bespoke_voice - dialogue is already in character; destination-wide
        #                   rudeness rules must not rewrite it
        self.speech_style = speech_style
        self.bonus_tests = tuple(bonus_tests)
        self.bespoke_voice = bespoke_voice

    def perform_test(self, test_name):
        result = self.test_results.get(
            test_name,
            "No notable findings. This test does not apply to this patient.",
        )
        return f"RESULTS: {result}"

    def receive_diagnosis(self, diagnosis):
        return diagnosis == self.diagnosis

    def has_supporting_evidence(self, test_names):
        """Return whether the collected tests form a clue path for this condition."""

        return self.diagnosis.has_supporting_evidence(test_names)

    def get_evidence_progress(self, test_names):
        """Return progress toward the strongest evidence path for this patient."""

        return self.diagnosis.get_evidence_progress(test_names)
